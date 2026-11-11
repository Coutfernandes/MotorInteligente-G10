import pytest

from src.ia.analise.roteador import (
    RELEVANCIA_MINIMA_CASE,
    RELEVANCIA_MINIMA_LINKEDIN,
    rotear,
    rotear_lote,
)
from src.ia.analise.schemas import AnaliseInteracao, Rota


def analise(**mudancas):
    dados = {
        "interaction_id": "INT-001",
        "tipo": "depoimento",
        "sentimento": "muito_positivo",
        "topicos": ["contratacao", "langchain"],
        "relevancia": 90,
        "insight": "Primeira vaga em IA conquistada com projeto de portfólio.",
    }
    dados.update(mudancas)
    return AnaliseInteracao(**dados)


@pytest.mark.parametrize(
    "mudancas, consentimento, rota_esperada",
    [
        # mensagem operacional é sempre ignorada
        ({"tipo": "mensagem_operacional", "sentimento": "neutro"}, True, Rota.IGNORAR),
        # RN02: dúvidas viram FAQ, mesmo positivas e com consentimento
        ({"tipo": "pergunta_tecnica", "sentimento": "positivo"}, True, Rota.FAQ),
        ({"tipo": "pedido_ajuda", "sentimento": "negativo"}, False, Rota.FAQ),
        # RN01: positivos com consentimento viram case ou post
        ({"tipo": "depoimento", "sentimento": "muito_positivo"}, True, Rota.CASE),
        ({"tipo": "entrega_projeto", "sentimento": "positivo"}, True, Rota.CASE),
        ({"tipo": "debate", "sentimento": "positivo"}, True, Rota.LINKEDIN),
        ({"tipo": "feedback_positivo", "sentimento": "positivo"}, True, Rota.LINKEDIN),
        # sem consentimento, positivo não vira post
        ({"tipo": "depoimento", "sentimento": "muito_positivo"}, False, Rota.IGNORAR),
        # RN02: relatos neutros viram FAQ
        ({"tipo": "debate", "sentimento": "neutro"}, True, Rota.FAQ),
        ({"tipo": "debate", "sentimento": "neutro"}, False, Rota.FAQ),
        # negativos são ignorados
        ({"tipo": "feedback_negativo", "sentimento": "negativo"}, True, Rota.IGNORAR),
        ({"tipo": "depoimento", "sentimento": "muito_negativo"}, True, Rota.IGNORAR),
    ],
)
def test_regras_do_roteador(mudancas, consentimento, rota_esperada):
    assert rotear(analise(**mudancas), consentimento).rota == rota_esperada


def test_limite_de_relevancia_do_case():
    assert rotear(analise(relevancia=RELEVANCIA_MINIMA_CASE), True).rota == Rota.CASE
    # um ponto abaixo do limite do case ainda vira post de LinkedIn
    assert rotear(analise(relevancia=RELEVANCIA_MINIMA_CASE - 1), True).rota == Rota.LINKEDIN


def test_limite_de_relevancia_do_linkedin():
    assert rotear(analise(relevancia=RELEVANCIA_MINIMA_LINKEDIN), True).rota == Rota.LINKEDIN
    roteada = rotear(analise(relevancia=RELEVANCIA_MINIMA_LINKEDIN - 1), True)
    assert roteada.rota == Rota.IGNORAR
    assert "abaixo" in roteada.motivo


def test_mensagem_roteada_mantem_a_analise():
    original = analise()
    roteada = rotear(original, True)
    assert roteada.interaction_id == original.interaction_id
    assert roteada.topicos == original.topicos
    assert roteada.consent_marketing is True
    assert roteada.motivo


def test_motivo_explica_falta_de_consentimento():
    assert "consentimento" in rotear(analise(), False).motivo


def test_rotear_lote_busca_consentimento_nos_registros():
    analises = [analise(interaction_id="INT-001"), analise(interaction_id="INT-002")]
    registros = [
        {"interaction_id": "INT-002", "consent_marketing": False},
        {"interaction_id": "INT-001", "consent_marketing": True},
    ]
    roteadas = rotear_lote(analises, registros)
    assert [r.rota for r in roteadas] == [Rota.CASE, Rota.IGNORAR]


def test_rotear_lote_sem_consentimento_informado_nao_vira_post():
    roteadas = rotear_lote([analise()], [{"interaction_id": "INT-001"}])
    assert roteadas[0].rota == Rota.IGNORAR
