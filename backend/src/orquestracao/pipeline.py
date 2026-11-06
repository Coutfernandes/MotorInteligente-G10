"""Orquestração do pipeline completo com LangGraph (F08).

analisar → rotear → agregar → gerar → salvar (OCI)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from src.ia.analise.agregacao import agregar
from src.ia.analise.roteador import rotear_lote
from src.ia.analise.schemas import AnaliseInteracao, MensagemRoteada, ResumoComunidade
from src.ia.analise.sentimento import INTERVALO_ENTRE_CHAMADAS, analisar_lote, criar_analisador
from src.ia.geracao.geradores import criar_gerador, gerar_ativos
from src.ia.geracao.schemas import Ativo
from src.orquestracao.schemas import Pacote
from src.armazenamento.repositorio import Repositorio

logger = logging.getLogger(__name__)

# RN05: todo processamento deve gerar pelo menos 2 tipos de ativo.
MINIMO_DE_FORMATOS = 2


class Estado(TypedDict, total=False):
    registros: list[dict]
    analises: list[AnaliseInteracao]
    mensagens: list[MensagemRoteada]
    resumo: ResumoComunidade
    ativos: list[Ativo]
    avisos: list[str]


# ao_progredir(etapa, atual, total)
Progresso = Callable[[str, int, int], None]


def _sem_progresso(etapa: str, atual: int, total: int) -> None:
    pass


def montar_grafo(analisador, gerador, intervalo: float, ao_progredir: Progresso = _sem_progresso):
    """Monta o grafo do LangGraph. Analisador e gerador são recebidos prontos (facilita os testes)."""

    def analisar(estado: Estado) -> Estado:
        analises = analisar_lote(
            estado["registros"], analisador, intervalo,
            ao_analisar=lambda atual, total: ao_progredir("analise", atual, total),
        )
        avisos = []
        falhas = len(estado["registros"]) - len(analises)
        if falhas:
            avisos.append(f"{falhas} mensagem(ns) não puderam ser analisadas pelo Gemini e ficaram de fora.")
        return {"analises": analises, "avisos": avisos}

    def rotear(estado: Estado) -> Estado:
        return {"mensagens": rotear_lote(estado["analises"], estado["registros"])}

    def resumir(estado: Estado) -> Estado:
        return {"resumo": agregar(estado["mensagens"])}

    def gerar(estado: Estado) -> Estado:
        ativos = gerar_ativos(
            estado["mensagens"], estado["registros"], estado["resumo"], gerador, intervalo,
            ao_gerar=lambda atual, total: ao_progredir("geracao", atual, total),
        )
        formatos = {a.tipo for a in ativos}
        avisos = list(estado["avisos"])
        if len(formatos) < MINIMO_DE_FORMATOS:
            avisos.append(
                f"RN05: só {len(formatos)} formato(s) gerado(s) "
                f"({', '.join(sorted(f.value for f in formatos)) or 'nenhum'}). "
                "O lote precisa de relatos positivos com consentimento e de dúvidas para gerar os dois tipos."
            )
        return {"ativos": ativos, "avisos": avisos}

    grafo = StateGraph(Estado)
    grafo.add_node("analisar", analisar)
    grafo.add_node("rotear", rotear)
    grafo.add_node("agregar", resumir)
    grafo.add_node("gerar", gerar)
    grafo.add_edge(START, "analisar")
    grafo.add_edge("analisar", "rotear")
    grafo.add_edge("rotear", "agregar")
    grafo.add_edge("agregar", "gerar")
    grafo.add_edge("gerar", END)
    return grafo.compile()


def executar_pipeline(
    registros: list[dict],
    arquivo_origem: str,
    analisador=None,
    gerador=None,
    repositorio: Repositorio | None = None,
    intervalo: float = INTERVALO_ENTRE_CHAMADAS,
    ao_progredir: Progresso = _sem_progresso,
    rejeitadas_ingestao: list | None = None,
    id_pacote: str | None = None,
) -> Pacote:
    """Roda o pipeline e salva o pacote gerado (RN03). Todos os ativos saem pendentes de curadoria (RN04)."""
    grafo = montar_grafo(analisador or criar_analisador(), gerador or criar_gerador(), intervalo, ao_progredir)
    estado = grafo.invoke({"registros": registros, "avisos": []})

    pacote = Pacote(
        id=id_pacote or novo_id(),
        criado_em=datetime.now(timezone.utc),
        arquivo_origem=arquivo_origem,
        resumo=estado["resumo"],
        mensagens=estado["mensagens"],
        ativos=estado["ativos"],
        rejeitadas_ingestao=rejeitadas_ingestao or [],
        avisos=estado["avisos"],
    )

    ao_progredir("salvando", 1, 1)
    repositorio = repositorio or Repositorio()
    pacote.armazenamento = {"gerado": repositorio.salvar(pacote.caminho_gerado, pacote.model_dump(mode="json"))}
    # Grava de novo só a cópia local, para ela também guardar o resultado do envio à OCI.
    repositorio.salvar_local(pacote.caminho_gerado, pacote.model_dump(mode="json"))
    return pacote


def novo_id() -> str:
    return f"pkg_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
