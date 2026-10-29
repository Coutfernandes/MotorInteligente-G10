import json
from pathlib import Path

import pytest
from langchain_core.exceptions import OutputParserException

from src.analysis import sentimento
from src.analysis.schemas import RespostaLLM, Sentimento

AMOSTRA = Path(__file__).parent / "fixtures" / "amostra_5.json"


def carregar_amostra() -> list[dict]:
    return json.loads(AMOSTRA.read_text(encoding="utf-8"))


def resposta_valida() -> RespostaLLM:
    return RespostaLLM(
        sentimento="positivo",
        topicos=["langgraph"],
        relevancia=70,
        insight="Resumo de teste.",
    )


class AnalisadorFalso:
    """Imita o Gemini: devolve (ou levanta) as respostas na ordem dada, sem gastar cota."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def invoke(self, mensagens):
        self.chamadas.append(mensagens)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def test_amostra_tem_5_mensagens_de_tipos_diferentes():
    amostra = carregar_amostra()
    assert len(amostra) == 5
    assert len({r["interaction_type"] for r in amostra}) == 5


def test_analisa_mensagem_com_uma_chamada():
    registro = carregar_amostra()[1]
    falso = AnalisadorFalso([resposta_valida()])

    analise = sentimento.analisar_interacao(registro, falso)

    assert len(falso.chamadas) == 1
    assert analise.interaction_id == "INT-002"
    assert analise.tipo == "pergunta_tecnica"
    assert registro["text"] in falso.chamadas[0][1].content


@pytest.mark.parametrize("primeira_resposta", [OutputParserException("json quebrado"), None])
def test_tenta_de_novo_quando_resposta_e_invalida(primeira_resposta):
    falso = AnalisadorFalso([primeira_resposta, resposta_valida()])

    analise = sentimento.analisar_interacao(carregar_amostra()[0], falso)

    assert analise.sentimento == Sentimento.POSITIVO
    assert len(falso.chamadas) == 2
    assert "resposta anterior foi inválida" in falso.chamadas[1][-1].content


def test_desiste_depois_de_2_tentativas_extras():
    falso = AnalisadorFalso([OutputParserException("ruim")] * 3)

    with pytest.raises(sentimento.FalhaNaAnalise):
        sentimento.analisar_interacao(carregar_amostra()[0], falso)

    assert len(falso.chamadas) == 1 + sentimento.TENTATIVAS_EXTRAS


def test_lote_pausa_entre_mensagens_e_pula_falhas():
    amostra = carregar_amostra()[:3]
    falha = OutputParserException("ruim")
    falso = AnalisadorFalso([resposta_valida(), falha, falha, falha, resposta_valida()])
    pausas = []

    analises = sentimento.analisar_lote(amostra, falso, intervalo=5.0, esperar=pausas.append)

    assert [a.interaction_id for a in analises] == ["INT-001", "INT-004"]
    assert pausas == [5.0, 5.0]


@pytest.mark.gemini
def test_gemini_de_verdade_com_amostra():
    """Gasta 5 chamadas (até 15 se houver respostas inválidas)."""
    amostra = carregar_amostra()

    analises = sentimento.analisar_lote(amostra)

    for analise in analises:
        print(json.dumps(analise.model_dump(mode="json"), ensure_ascii=False))

    por_id = {a.interaction_id: a for a in analises}
    assert list(por_id) == [r["interaction_id"] for r in amostra]
    assert por_id["INT-001"].sentimento in {Sentimento.POSITIVO, Sentimento.MUITO_POSITIVO}
    assert por_id["INT-009"].sentimento in {Sentimento.NEGATIVO, Sentimento.MUITO_NEGATIVO}
    assert por_id["INT-021"].relevancia < 50
    assert por_id["INT-001"].relevancia > por_id["INT-021"].relevancia
