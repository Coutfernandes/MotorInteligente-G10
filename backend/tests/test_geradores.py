import pytest
from langchain_core.exceptions import OutputParserException

from src.ia.analise.schemas import MensagemRoteada, ResumoComunidade, Rota
from src.ia.geracao import geradores
from src.ia.geracao.schemas import ConteudoGerado, StatusCuradoria, TipoAtivo


class GeradorFalso:
    """Imita o Gemini: devolve (ou levanta) as respostas na ordem dada, sem gastar cota."""

    def __init__(self, respostas=None):
        self.respostas = list(respostas) if respostas is not None else None
        self.chamadas = []

    def invoke(self, mensagens):
        self.chamadas.append(mensagens)
        if self.respostas is None:
            return ConteudoGerado(titulo="Título", conteudo="Conteúdo")
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def mensagem(id_, rota, relevancia=80, tipo="depoimento"):
    return MensagemRoteada(
        interaction_id=id_, tipo=tipo, sentimento="positivo", topicos=["carreira"],
        relevancia=relevancia, insight="x", consent_marketing=True, rota=rota, motivo="teste",
    )


def registros_de(mensagens):
    return [{"interaction_id": m.interaction_id, "text": f"texto de {m.interaction_id}"} for m in mensagens]


RESUMO = ResumoComunidade(
    total_interacoes_processadas=10, sentimento_predominante="positivo",
    topicos_principais=["carreira"], contagem_por_rota={r: 0 for r in Rota},
)


def test_gera_linkedin_newsletter_e_faq():
    mensagens = [mensagem("INT-1", Rota.CASE), mensagem("INT-2", Rota.FAQ, tipo="pergunta_tecnica")]
    ativos = geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, GeradorFalso())

    assert [a.tipo for a in ativos] == [TipoAtivo.LINKEDIN, TipoAtivo.NEWSLETTER, TipoAtivo.FAQ]
    assert ativos[0].fontes == ["INT-1"]
    assert ativos[2].fontes == ["INT-2"]
    # RN04: tudo nasce pendente de curadoria
    assert all(a.status == StatusCuradoria.PENDENTE for a in ativos)


def test_rn01_ignorados_e_faq_nao_viram_post():
    mensagens = [mensagem("INT-1", Rota.IGNORAR), mensagem("INT-2", Rota.FAQ)]
    ativos = geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, GeradorFalso())
    assert [a.tipo for a in ativos] == [TipoAtivo.FAQ]


def test_posts_saem_dos_mais_relevantes_e_respeitam_o_limite():
    mensagens = [mensagem(f"INT-{r}", Rota.LINKEDIN, relevancia=r) for r in (50, 90, 70, 60, 80)]
    ativos = geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, GeradorFalso())

    posts = [a for a in ativos if a.tipo == TipoAtivo.LINKEDIN]
    assert len(posts) == geradores.MAX_POSTS_LINKEDIN
    assert [p.fontes[0] for p in posts] == ["INT-90", "INT-80", "INT-70"]


def test_faq_prefere_duvidas_a_debates():
    # O debate é o mais relevante, mas as dúvidas reais ocupam as vagas primeiro (RN02).
    debate = mensagem("DEB", Rota.FAQ, relevancia=95, tipo="debate")
    duvidas = [
        mensagem(f"DUV-{n}", Rota.FAQ, relevancia=50 + n, tipo="pergunta_tecnica")
        for n in range(geradores.MAX_MENSAGENS_FAQ)
    ]
    mensagens = [debate, *duvidas]
    ativos = geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, GeradorFalso())

    assert "DEB" not in ativos[0].fontes
    assert len(ativos[0].fontes) == geradores.MAX_MENSAGENS_FAQ


def test_faq_completa_com_debates_quando_sobra_vaga():
    mensagens = [
        mensagem("DEB", Rota.FAQ, relevancia=95, tipo="debate"),
        mensagem("DUV", Rota.FAQ, relevancia=60, tipo="pedido_ajuda"),
    ]
    ativos = geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, GeradorFalso())
    assert ativos[0].fontes == ["DUV", "DEB"]


def test_texto_original_vai_no_pedido_e_tom_no_prompt():
    mensagens = [mensagem("INT-1", Rota.CASE)]
    falso = GeradorFalso()
    geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, falso)

    sistema, pedido = falso.chamadas[0]
    assert "inspirador" in sistema.content  # RN06
    assert "texto de INT-1" in pedido.content


def test_pausa_entre_chamadas_e_informa_progresso():
    mensagens = [mensagem("INT-1", Rota.CASE), mensagem("INT-2", Rota.FAQ)]
    pausas, progresso = [], []
    geradores.gerar_ativos(
        mensagens, registros_de(mensagens), RESUMO, GeradorFalso(),
        intervalo=4, esperar=pausas.append, ao_gerar=lambda a, t: progresso.append((a, t)),
    )
    assert pausas == [4, 4]
    assert progresso == [(1, 3), (2, 3), (3, 3)]


def test_tenta_de_novo_e_pula_ativo_que_falha_sempre():
    mensagens = [mensagem("INT-1", Rota.CASE)]
    falhas = [OutputParserException("ruim")] * (1 + geradores.TENTATIVAS_EXTRAS)
    falso = GeradorFalso(falhas + [ConteudoGerado(titulo="Newsletter", conteudo="ok")])

    ativos = geradores.gerar_ativos(mensagens, registros_de(mensagens), RESUMO, falso)

    assert [a.tipo for a in ativos] == [TipoAtivo.NEWSLETTER]
    assert "resposta anterior foi inválida" in falso.chamadas[1][-1].content


@pytest.mark.parametrize("tipo", list(TipoAtivo))
def test_todo_prompt_tem_as_regras_comuns(tipo):
    assert "Não invente" in geradores.carregar_prompt(tipo)


@pytest.mark.parametrize("tipo", list(TipoAtivo))
def test_todo_prompt_tem_exemplos_de_estilo(tipo):
    # Seção 8 das diretrizes: 2 ou 3 exemplos (few-shot) por prompt de geração.
    assert 2 <= geradores.carregar_prompt(tipo).count("### Exemplo ") <= 3
