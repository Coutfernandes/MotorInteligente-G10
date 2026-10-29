import pytest
from pydantic import ValidationError

from src.analysis.schemas import AnaliseInteracao, RespostaLLM, Sentimento


def resposta_valida(**mudancas):
    dados = {
        "sentimento": "muito_positivo",
        "topicos": ["contratacao", "langchain"],
        "entidades": {"cargos": ["Desenvolvedora Júnior de IA"], "tecnologias": ["LangChain", "OCI"]},
        "relevancia": 90,
        "insight": "Primeira vaga em IA conquistada com projeto de portfólio.",
    }
    dados.update(mudancas)
    return dados


def test_aceita_resposta_valida():
    resposta = RespostaLLM(**resposta_valida())
    assert resposta.sentimento == Sentimento.MUITO_POSITIVO
    assert resposta.entidades.organizacoes == []


def test_normaliza_topicos():
    resposta = RespostaLLM(**resposta_valida(topicos=["LangGraph", "Ambiente Setup", "Contratação"]))
    assert resposta.topicos == ["langgraph", "ambiente_setup", "contratacao"]


def test_remove_topicos_repetidos():
    resposta = RespostaLLM(**resposta_valida(topicos=["RAG", "rag"]))
    assert resposta.topicos == ["rag"]


def test_entidades_sao_opcionais():
    dados = resposta_valida()
    del dados["entidades"]
    assert RespostaLLM(**dados).entidades.tecnologias == []


@pytest.mark.parametrize(
    "mudancas",
    [
        {"sentimento": "Altamente Positivo"},
        {"relevancia": 101},
        {"relevancia": -1},
        {"topicos": []},
        {"topicos": ["a", "b", "c", "d"]},
        {"topicos": ["!!!"]},
        {"insight": ""},
    ],
)
def test_rejeita_resposta_invalida(mudancas):
    with pytest.raises(ValidationError):
        RespostaLLM(**resposta_valida(**mudancas))


def test_analise_final_exige_id_e_tipo():
    with pytest.raises(ValidationError):
        AnaliseInteracao(**resposta_valida())


def test_analise_final_vira_json_simples():
    analise = AnaliseInteracao(**resposta_valida(), interaction_id="INT-001", tipo="depoimento")
    dados = analise.model_dump(mode="json")
    assert dados["interaction_id"] == "INT-001"
    assert dados["sentimento"] == "muito_positivo"
