"""Agregação: resume o lote inteiro de mensagens da comunidade (resumo_comunidade)."""

from collections import Counter

from src.ia.analise.schemas import MensagemRoteada, ResumoComunidade, Rota

# ---- Ajustes da agregação ----
QUANTIDADE_TOPICOS_PRINCIPAIS = 3
# O 1º tópico de cada mensagem é o mais específico; os demais às vezes saem genéricos.
PESO_PRIMEIRO_TOPICO = 2
PESO_DEMAIS_TOPICOS = 1
# ------------------------------


def agregar(mensagens: list[MensagemRoteada]) -> ResumoComunidade:
    """Monta o resumo do lote. Mensagens que falharam na análise já ficaram de fora.

    Em caso de empate, vence o sentimento ou tópico que apareceu primeiro no lote.
    """
    sentimentos = Counter(m.sentimento for m in mensagens)

    pontos_por_topico = Counter()
    for mensagem in mensagens:
        for posicao, topico in enumerate(mensagem.topicos):
            pontos_por_topico[topico] += PESO_PRIMEIRO_TOPICO if posicao == 0 else PESO_DEMAIS_TOPICOS

    contagem_por_rota = {rota: 0 for rota in Rota}
    contagem_por_rota.update(Counter(m.rota for m in mensagens))

    return ResumoComunidade(
        total_interacoes_processadas=len(mensagens),
        sentimento_predominante=sentimentos.most_common(1)[0][0] if sentimentos else None,
        topicos_principais=[t for t, _ in pontos_por_topico.most_common(QUANTIDADE_TOPICOS_PRINCIPAIS)],
        contagem_por_rota=contagem_por_rota,
    )
