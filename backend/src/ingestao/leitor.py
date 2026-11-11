"""Leitura e validação dos arquivos de interações da comunidade em JSON ou CSV (F02)."""

import csv
import io
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from src.ingestao.schemas import Interacao, Rejeitada, ResultadoIngestao

logger = logging.getLogger(__name__)

FORMATOS_ACEITOS = {"json", "csv"}
COLUNAS_OBRIGATORIAS = {"interaction_id", "channel", "interaction_type", "created_at", "text"}


class ErroIngestao(Exception):
    """O arquivo inteiro não pôde ser lido (formato, estrutura ou nenhum registro válido)."""


def carregar_arquivo(caminho: str | Path) -> ResultadoIngestao:
    """Lê um arquivo .json ou .csv do disco."""
    caminho = Path(caminho)
    formato = caminho.suffix.lower().lstrip(".")
    if not caminho.is_file():
        raise ErroIngestao(f"Arquivo não encontrado: {caminho}")
    return carregar_conteudo(caminho.read_bytes(), formato)


def carregar_conteudo(conteudo: bytes | str, formato: str) -> ResultadoIngestao:
    """Lê o conteúdo de um arquivo já em memória (ex: upload da interface).

    Registros inválidos ou repetidos ficam em `rejeitadas`; os demais seguem no lote.
    """
    formato = formato.lower().lstrip(".")
    if formato not in FORMATOS_ACEITOS:
        raise ErroIngestao(f"Formato '{formato}' não suportado. Use JSON ou CSV.")

    if isinstance(conteudo, bytes):
        try:
            # utf-8-sig remove o BOM que o Excel coloca no início do CSV
            conteudo = conteudo.decode("utf-8-sig")
        except UnicodeDecodeError as erro:
            raise ErroIngestao("O arquivo precisa estar em UTF-8.") from erro

    if not conteudo.strip():
        raise ErroIngestao("O arquivo está vazio.")

    registros = _ler_json(conteudo) if formato == "json" else _ler_csv(conteudo)
    return _validar(registros)


def _ler_json(conteudo: str) -> list[dict]:
    """Aceita uma lista de registros, {"records": [...]} ou o formato com lotes {"batches": [{"records": [...]}]}."""
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise ErroIngestao(f"JSON inválido (linha {erro.lineno}, coluna {erro.colno}): {erro.msg}") from erro

    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict) and isinstance(dados.get("records"), list):
        return dados["records"]
    if isinstance(dados, dict) and isinstance(dados.get("batches"), list):
        return [r for lote in dados["batches"] for r in lote.get("records", [])]
    raise ErroIngestao("JSON fora do formato esperado: use uma lista de interações, 'records' ou 'batches'.")


def _ler_csv(conteudo: str) -> list[dict]:
    """Lê o CSV com cabeçalho. Aceita vírgula ou ponto e vírgula (padrão do Excel em português)."""
    primeira_linha = conteudo.splitlines()[0]
    separador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","

    leitor = csv.DictReader(io.StringIO(conteudo), delimiter=separador)
    colunas = {c.strip() for c in leitor.fieldnames or []}
    faltando = COLUNAS_OBRIGATORIAS - colunas
    if faltando:
        raise ErroIngestao(f"Colunas obrigatórias ausentes no CSV: {', '.join(sorted(faltando))}")

    # Célula vazia conta como "não informado", para valer o valor padrão do modelo.
    return [
        {chave.strip(): valor for chave, valor in linha.items() if chave and valor not in (None, "")}
        for linha in leitor
    ]


def _validar(registros: list) -> ResultadoIngestao:
    interacoes, rejeitadas = [], []
    ids_vistos = set()

    for posicao, registro in enumerate(registros, start=1):
        id_informado = registro.get("interaction_id") if isinstance(registro, dict) else None
        motivo = None

        if not isinstance(registro, dict):
            motivo = "registro não é um objeto"
        else:
            try:
                interacao = Interacao(**registro)
            except ValidationError as erro:
                motivo = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in erro.errors())
            else:
                if interacao.interaction_id in ids_vistos:
                    motivo = "interaction_id repetido"
                else:
                    ids_vistos.add(interacao.interaction_id)
                    interacoes.append(interacao)

        if motivo:
            logger.warning("Registro %d (%s) rejeitado: %s", posicao, id_informado, motivo)
            rejeitadas.append(Rejeitada(posicao=posicao, interaction_id=id_informado, motivo=motivo))

    if not interacoes:
        raise ErroIngestao(f"Nenhuma interação válida no arquivo ({len(rejeitadas)} rejeitada(s)).")

    return ResultadoIngestao(interacoes=interacoes, rejeitadas=rejeitadas)


if __name__ == "__main__":
    # Teste rápido: python -m src.ingestao.leitor data/interacoes.json
    import sys

    resultado = carregar_arquivo(sys.argv[1])
    print(f"{len(resultado.interacoes)} interação(ões) válida(s), {len(resultado.rejeitadas)} rejeitada(s).")
    for rejeitada in resultado.rejeitadas:
        print(f"  - registro {rejeitada.posicao} ({rejeitada.interaction_id}): {rejeitada.motivo}")
