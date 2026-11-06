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


def test_empate_de_sentimento_vence_o_primeiro():
    resumo = agregar([mensagem(sentimento="neutro"), mensagem(sentimento="positivo")])
    assert resumo.sentimento_predominante == Sentimento.NEUTRO


def test_primeiro_topico_vale_mais():
    # "projeto_pratico" aparece 3 vezes como 2º tópico (3 pontos);
    # "rag" e "langgraph" aparecem 2 vezes como 1º tópico (4 pontos cada).
    resumo = agregar([
        mensagem(topicos=["rag", "projeto_pratico"]),
        mensagem(topicos=["rag", "projeto_pratico"]),
        mensagem(topicos=["langgraph", "projeto_pratico"]),
        mensagem(topicos=["langgraph"]),
        mensagem(topicos=["oci"]),
    ])
    assert resumo.topicos_principais == ["rag", "langgraph", "projeto_pratico"]


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
