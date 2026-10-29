"""Cliente do Google Gemini e leitura dos prompts da análise."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

PASTA_PROMPTS = Path(__file__).parent / "prompts"

# Tentativas automáticas da biblioteca em erros de rede/cota.
# Fica baixo de propósito: cada tentativa gasta cota gratuita.
TENTATIVAS_DE_REDE = 2


def criar_llm(temperatura: float = 0.0) -> ChatGoogleGenerativeAI:
    """Cria o cliente do Gemini com a chave e o modelo definidos no .env."""
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
    """Lê o arquivo src/analysis/prompts/<nome>.txt."""
    return (PASTA_PROMPTS / f"{nome}.txt").read_text(encoding="utf-8").strip()
