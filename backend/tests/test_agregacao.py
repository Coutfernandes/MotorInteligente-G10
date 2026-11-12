import pytest

from src.ia.analise.agregacao import agregar
from src.ia.analise.schemas import MensagemRoteada, Rota, Sentimento


def mensagem(**mudancas):
    dados = {
        "interaction_id": "INT-001",
        "tipo": "depoimento",
        "sentimento": "muito_positivo",
        "topicos": ["contratacao"],
        "relevancia": 90,
        "insight": "Primeira vaga em IA conquistada com projeto de portfólio.",
        "consent_marketing": True,
        "rota": "case",
        "motivo": "relato positivo com relevância 90",
    }
    dados.update(mudancas)
    return MensagemRoteada(**dados)


def test_conta_total_e_sentimento_predominante():
    resumo = agregar([
        mensagem(sentimento="positivo"),
        mensagem(sentimento="neutro"),
        mensagem(sentimento="positivo"),
    ])
    assert resumo.total_interacoes_processadas == 3
    assert resumo.sentimento_predominante == Sentimento.POSITIVO


def test_sentimento_predominante_usa_a_media_e_nao_o_mais_frequente():
    # Caso do teste com o Gemini real: neutro foi o mais frequente (20), mas 24 eram positivas.
    sentimentos = ["neutro"] * 20 + ["positivo"] * 14 + ["muito_positivo"] * 10 + ["negativo"] * 6
    resumo = agregar([mensagem(sentimento=s) for s in sentimentos])
    assert resumo.sentimento_predominante == Sentimento.POSITIVO


@pytest.mark.parametrize(
    "sentimentos, esperado",
    [
        (["positivo", "negativo"], Sentimento.NEUTRO),  # média 0
        (["neutro", "neutro", "neutro", "positivo"], Sentimento.POSITIVO),  # média 0,25
        (["neutro"] * 5 + ["positivo"], Sentimento.NEUTRO),  # média 0,17
        (["muito_positivo", "positivo"], Sentimento.MUITO_POSITIVO),  # média 1,5
        (["negativo", "muito_negativo", "neutro"], Sentimento.NEGATIVO),  # média -1
        (["muito_negativo"], Sentimento.MUITO_NEGATIVO),
    ],
)
def test_media_vira_um_dos_cinco_niveis(sentimentos, esperado):
    resumo = agregar([mensagem(sentimento=s) for s in sentimentos])
    assert resumo.sentimento_predominante == esperado


def test_primeiro_topico_vale_mais():
    # "avaliacao_llm" aparece 3 vezes como 2º tópico (3 pontos);
    # "rag" e "langgraph" aparecem 2 vezes como 1º tópico (4 pontos cada).
    resumo = agregar([
        mensagem(topicos=["rag", "avaliacao_llm"]),
        mensagem(topicos=["rag", "avaliacao_llm"]),
        mensagem(topicos=["langgraph", "avaliacao_llm"]),
        mensagem(topicos=["langgraph"]),
        mensagem(topicos=["oci"]),
    ])
    assert resumo.topicos_principais == ["rag", "langgraph", "avaliacao_llm"]


def test_topico_generico_vai_para_o_fim():
    # "projeto_pratico" tem mais pontos, mas é genérico: os específicos vêm antes.
    resumo = agregar([
        mensagem(topicos=["projeto_pratico", "rag"]),
        mensagem(topicos=["projeto_pratico", "oci"]),
        mensagem(topicos=["projeto_pratico", "langgraph"]),
        mensagem(topicos=["rag"]),
    ])
    assert resumo.topicos_principais == ["rag", "oci", "langgraph"]


def test_topico_generico_completa_quando_faltam_especificos():
    resumo = agregar([mensagem(topicos=["comunidade", "rag"]), mensagem(topicos=["projeto_pratico"])])
    assert resumo.topicos_principais == ["rag", "comunidade", "projeto_pratico"]


def test_limita_a_tres_topicos():
    resumo = agregar([mensagem(topicos=["a", "b", "c"]), mensagem(topicos=["d"])])
    assert len(resumo.topicos_principais) == 3


def test_contagem_por_rota_inclui_rotas_vazias():
    resumo = agregar([mensagem(rota="case"), mensagem(rota="faq"), mensagem(rota="faq")])
    assert resumo.contagem_por_rota == {
        Rota.CASE: 1,
        Rota.LINKEDIN: 0,
        Rota.FAQ: 2,
        Rota.IGNORAR: 0,
    }


def test_lote_vazio():
    resumo = agregar([])
    assert resumo.total_interacoes_processadas == 0
    assert resumo.sentimento_predominante is None
    assert resumo.topicos_principais == []
    assert sum(resumo.contagem_por_rota.values()) == 0


def test_resumo_vira_json_com_codigos():
    dados = agregar([mensagem()]).model_dump(mode="json")
    assert dados["sentimento_predominante"] == "muito_positivo"
    assert dados["contagem_por_rota"]["case"] == 1
