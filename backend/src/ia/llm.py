"""Cliente do Google Gemini, leitura dos prompts da análise e tratamento de erros temporários (T03)."""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.exceptions import OutputParserException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

logger = logging.getLogger(__name__)

PASTA_PROMPTS = Path(__file__).parent / "prompts" / "analise"

# Tentativas automáticas da biblioteca em erros de rede/cota.
# Fica baixo de propósito: cada tentativa gasta cota gratuita.
TENTATIVAS_DE_REDE = 2

# Esperas (segundos) antes de tentar de novo quando o Gemini está sobrecarregado (503)
# ou a cota por minuto acabou (429). Depois da última, a mensagem é pulada.
ESPERAS_ERRO_TEMPORARIO = (15.0, 30.0)

CODIGOS_TEMPORARIOS = {429, 500, 503, 504}
MARCAS_TEMPORARIAS = ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "high demand", "overloaded")


def erro_temporario(erro: Exception) -> bool:
    """True para falhas que passam sozinhas (sobrecarga ou cota por minuto).

    False para o resto: chave errada, modelo inexistente, resposta fora do formato etc.
    """
    if isinstance(erro, (OutputParserException, ValidationError)):
        return False
    # O LangChain embrulha o erro do Google: o código HTTP pode estar no erro original (__cause__).
    for candidato in (erro, erro.__cause__):
        for atributo in ("code", "status_code"):
            codigo = getattr(candidato, atributo, None)
            if isinstance(codigo, int):
                return codigo in CODIGOS_TEMPORARIOS
    texto = str(erro)
    return any(marca in texto for marca in MARCAS_TEMPORARIAS)


def chamar_com_espera(funcao, esperar=time.sleep, esperas=None):
    """Executa `funcao()`; em erro temporário espera e tenta de novo. Outros erros sobem na hora."""
    esperas = ESPERAS_ERRO_TEMPORARIO if esperas is None else esperas
    for numero, segundos in enumerate(esperas, start=1):
        try:
            return funcao()
        except Exception as erro:
            if not erro_temporario(erro):
                raise
            logger.warning("Gemini indisponível (%s). Nova tentativa %d em %.0f s.", erro, numero, segundos)
            esperar(segundos)
    return funcao()


def modo_simulado() -> bool:
    """LLM_PROVIDER=simulado no .env troca o Gemini por respostas fixas (sem cota, só para testes)."""
    load_dotenv()
    return os.getenv("LLM_PROVIDER", "").strip().lower() == "simulado"


def criar_llm(temperatura: float = 0.0) -> ChatGoogleGenerativeAI:
    """Cria o cliente do Gemini com a chave e o modelo definidos no .env."""
    if modo_simulado():
        from src.ia.llm_simulado import LLMSimulado

        return LLMSimulado()

    load_dotenv()
    chave = os.getenv("GOOGLE_API_KEY", "").strip()
    modelo = os.getenv("LLM_MODEL", "").strip()

    if not chave or chave == "sua_chave_gemini_aqui":
        raise RuntimeError("GOOGLE_API_KEY não configurada. Copie o .env.example para .env e preencha a chave.")
    if not modelo:
        raise RuntimeError("LLM_MODEL não configurado no .env.")

    return ChatGoogleGenerativeAI(
        model=modelo,
        google_api_key=chave,
        temperature=temperatura,
        max_retries=TENTATIVAS_DE_REDE,
    )


def carregar_prompt(nome: str) -> str:
    """Lê o arquivo src/ia/prompts/analise/<nome>.txt."""
    return (PASTA_PROMPTS / f"{nome}.txt").read_text(encoding="utf-8").strip()
