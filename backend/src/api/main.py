"""API HTTP do CommunityLab: liga a interface React ao pipeline Python.

Rodar (na pasta backend/): uvicorn src.api.main:app --reload
"""

import json
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from src.api.execucoes import Execucao, Gerenciador
from src.caminhos import PASTA_DADOS, PASTA_FRONTEND_BUILD
from src.ia.llm import modo_simulado
from src.ia.geracao.schemas import Ativo, StatusCuradoria
from src.ingestao.leitor import ErroIngestao, carregar_conteudo
from src.orquestracao import curadoria
from src.orquestracao.schemas import Pacote

load_dotenv()

TAMANHO_MAXIMO_ARQUIVO = 5 * 1024 * 1024  # 5 MB
AMOSTRA_NA_VALIDACAO = 10
PASTA_FRONTEND = PASTA_FRONTEND_BUILD
# Arquivo do botão "Usar dados de exemplo": 8 interações, rápido de processar com o Gemini real.
ARQUIVO_EXEMPLO = PASTA_DADOS / "interacoes_amostra.csv"

app = FastAPI(title="CommunityLab API")
gerenciador = Gerenciador()


class EdicaoAtivo(BaseModel):
    titulo: str | None = None
    conteudo: str | None = None
    status: StatusCuradoria | None = None


class ResumoPacote(BaseModel):
    id: str
    criado_em: str
    arquivo_origem: str
    total_interacoes: int
    total_ativos: int
    aprovados: int
    pendentes: int
    exportado_em: str | None
    oci_exportado: str | None  # status do envio do pacote aprovado: sucesso | erro | nao_configurado


# ---- auxiliares ----

async def _ler_upload(arquivo: UploadFile):
    conteudo = await arquivo.read(TAMANHO_MAXIMO_ARQUIVO + 1)
    if len(conteudo) > TAMANHO_MAXIMO_ARQUIVO:
        raise HTTPException(413, "Arquivo maior que 5 MB.")
    formato = Path(arquivo.filename or "").suffix
    try:
        return carregar_conteudo(conteudo, formato)
    except ErroIngestao as erro:
        raise HTTPException(422, str(erro)) from erro


def _pacote_ou_404(id_pacote: str) -> Pacote:
    pacote = gerenciador.pacote(id_pacote)
    if pacote is None:
        raise HTTPException(404, "Pacote não encontrado.")
    return pacote


def _llm_configurado() -> bool:
    chave = os.getenv("GOOGLE_API_KEY", "").strip()
    return modo_simulado() or (bool(chave) and chave != "sua_chave_gemini_aqui" and bool(os.getenv("LLM_MODEL")))


# ---- status ----

@app.get("/api/status")
def status():
    oci = gerenciador.repositorio.oci
    return {
        "llm": {
            "simulado": modo_simulado(),
            "modelo": "simulado" if modo_simulado() else os.getenv("LLM_MODEL", ""),
            "configurado": _llm_configurado(),
        },
        "oci": {"configurado": oci.configurado(), "bucket": oci.bucket_name},
    }


# ---- ingestão e processamento ----

@app.get("/api/exemplo")
def arquivo_exemplo():
    return FileResponse(ARQUIVO_EXEMPLO, media_type="text/csv", filename=ARQUIVO_EXEMPLO.name)


@app.post("/api/ingestao/validar")
async def validar(arquivo: UploadFile):
    """Só lê e valida o arquivo (não gasta cota). Mostra o que vai entrar no pipeline."""
    resultado = await _ler_upload(arquivo)
    return {
        "arquivo": arquivo.filename,
        "total_validas": len(resultado.interacoes),
        "rejeitadas": [r.model_dump() for r in resultado.rejeitadas],
        "por_tipo": Counter(i.interaction_type for i in resultado.interacoes),
        "por_canal": Counter(i.channel for i in resultado.interacoes),
        "com_consentimento": sum(i.consent_marketing for i in resultado.interacoes),
        "amostra": resultado.registros[:AMOSTRA_NA_VALIDACAO],
    }


@app.post("/api/processamentos", status_code=202, response_model=Execucao)
async def processar(arquivo: UploadFile):
    if not _llm_configurado():
        raise HTTPException(400, "Gemini não configurado: preencha GOOGLE_API_KEY e LLM_MODEL no .env (ou use LLM_PROVIDER=simulado).")
    resultado = await _ler_upload(arquivo)
    return gerenciador.iniciar(resultado, arquivo.filename or "upload")


@app.get("/api/processamentos/{id_execucao}", response_model=Execucao)
def acompanhar(id_execucao: str):
    execucao = gerenciador.obter(id_execucao)
    if execucao is None:
        raise HTTPException(404, "Processamento não encontrado.")
    return execucao


# ---- pacotes e curadoria ----

@app.get("/api/pacotes", response_model=list[ResumoPacote])
def listar_pacotes():
    return [
        ResumoPacote(
            id=p.id,
            criado_em=p.criado_em.isoformat(),
            arquivo_origem=p.arquivo_origem,
            total_interacoes=p.resumo.total_interacoes_processadas,
            total_ativos=len(p.ativos),
            aprovados=len(p.aprovados),
            pendentes=sum(a.status == StatusCuradoria.PENDENTE for a in p.ativos),
            exportado_em=p.exportado_em.isoformat() if p.exportado_em else None,
            oci_exportado=p.armazenamento.get("aprovado", {}).get("oci", {}).get("status"),
        )
        for p in gerenciador.pacotes()
    ]


@app.get("/api/pacotes/{id_pacote}", response_model=Pacote)
def obter_pacote(id_pacote: str):
    return _pacote_ou_404(id_pacote)


@app.patch("/api/pacotes/{id_pacote}/ativos/{id_ativo}", response_model=Ativo)
def editar_ativo(id_pacote: str, id_ativo: str, edicao: EdicaoAtivo):
    with gerenciador.trava:
        pacote = _pacote_ou_404(id_pacote)
        try:
            ativo = curadoria.atualizar_ativo(pacote, id_ativo, edicao.titulo, edicao.conteudo, edicao.status)
        except curadoria.AtivoNaoEncontrado as erro:
            raise HTTPException(404, "Ativo não encontrado.") from erro
        except ValidationError as erro:
            raise HTTPException(422, "Título e conteúdo não podem ficar vazios (título até 120 caracteres).") from erro
        gerenciador.salvar(pacote)
    return ativo


@app.post("/api/pacotes/{id_pacote}/exportar")
def exportar(id_pacote: str):
    """RN03 + RN04: envia ao OCI somente os ativos aprovados."""
    with gerenciador.trava:
        pacote = _pacote_ou_404(id_pacote)
        try:
            resultado = curadoria.exportar(pacote, gerenciador.repositorio)
        except curadoria.SemAprovados as erro:
            raise HTTPException(409, str(erro)) from erro
    return {"exportado_em": pacote.exportado_em, "armazenamento": resultado, "total_aprovados": len(pacote.aprovados)}


@app.get("/api/pacotes/{id_pacote}/download")
def baixar(id_pacote: str, formato: str = "json"):
    """RN04: o download só contém ativos aprovados."""
    pacote = _pacote_ou_404(id_pacote)
    try:
        if formato == "markdown":
            corpo, tipo, extensao = curadoria.como_markdown(pacote), "text/markdown; charset=utf-8", "md"
        elif formato == "json":
            corpo = json.dumps(curadoria.conteudo_exportavel(pacote), ensure_ascii=False, indent=2)
            tipo, extensao = "application/json", "json"
        else:
            raise HTTPException(400, "Formato inválido: use json ou markdown.")
    except curadoria.SemAprovados as erro:
        raise HTTPException(409, str(erro)) from erro
    return Response(
        corpo,
        media_type=tipo,
        headers={"Content-Disposition": f'attachment; filename="communitylab_{pacote.id}.{extensao}"'},
    )


# Interface React já compilada (npm run build). Em desenvolvimento, o Vite serve a interface.
if PASTA_FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=PASTA_FRONTEND, html=True), name="frontend")
