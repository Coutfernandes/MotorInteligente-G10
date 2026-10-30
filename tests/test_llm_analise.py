import json
import re

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI

from src.analysis import llm
from src.analysis.schemas import RespostaLLM, Sentimento


@pytest.fixture
def sem_arquivo_env(monkeypatch):
    """Impede que o .env real seja lido, para o teste controlar as variáveis."""
    monkeypatch.setattr(llm, "load_dotenv", lambda: None)


def test_cria_cliente_com_dados_do_env(sem_arquivo_env, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "chave-falsa-de-teste")
    monkeypatch.setenv("LLM_MODEL", "modelo-de-teste")

    cliente = llm.criar_llm()

    assert isinstance(cliente, ChatGoogleGenerativeAI)
    assert cliente.model.endswith("modelo-de-teste")
    assert cliente.temperature == 0.0
    assert cliente.max_retries == llm.TENTATIVAS_DE_REDE


@pytest.mark.parametrize("chave", ["", "sua_chave_gemini_aqui"])
def test_erro_claro_sem_chave(sem_arquivo_env, monkeypatch, chave):
    monkeypatch.setenv("GOOGLE_API_KEY", chave)
    monkeypatch.setenv("LLM_MODEL", "modelo-de-teste")
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        llm.criar_llm()


def test_erro_claro_sem_modelo(sem_arquivo_env, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "chave-falsa-de-teste")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="LLM_MODEL"):
        llm.criar_llm()


def test_prompt_cita_todos_os_sentimentos():
    prompt = llm.carregar_prompt("analise_sentimento")
    for sentimento in Sentimento:
        assert sentimento.value in prompt


def test_exemplos_do_prompt_seguem_o_schema():
    prompt = llm.carregar_prompt("analise_sentimento")
    respostas = re.findall(r"^Resposta: (\{.*\})$", prompt, flags=re.MULTILINE)

    assert 2 <= len(respostas) <= 3
    for resposta in respostas:
        RespostaLLM(**json.loads(resposta))
