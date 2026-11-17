"""Agregação: resume o lote inteiro de mensagens da comunidade (resumo_comunidade)."""

from collections import Counter

from src.ia.analise.schemas import MensagemRoteada, ResumoComunidade, Rota, Sentimento

# ---- Ajustes da agregação ----
QUANTIDADE_TOPICOS_PRINCIPAIS = 3
# O 1º tópico de cada mensagem é o mais específico; os demais às vezes saem genéricos.
PESO_PRIMEIRO_TOPICO = 2
PESO_DEMAIS_TOPICOS = 1
# Tópicos que dizem pouco sobre o assunto: só entram no resumo se faltarem tópicos específicos.
TOPICOS_GENERICOS = {"projeto_pratico", "comunidade", "operacional"}
# O sentimento predominante sai da média destes pontos.
PONTOS_SENTIMENTO = {
    Sentimento.MUITO_NEGATIVO: -2,
    Sentimento.NEGATIVO: -1,
    Sentimento.NEUTRO: 0,
    Sentimento.POSITIVO: 1,
    Sentimento.MUITO_POSITIVO: 2,
}
LIMITE_NEUTRO = 0.25  # média entre -0,25 e +0,25 conta como neutro
LIMITE_MUITO = 1.25  # a partir de ±1,25 conta como muito positivo / muito negativo
# ------------------------------


def sentimento_medio(sentimentos: list[Sentimento]) -> Sentimento | None:
    """Converte a média dos pontos de volta para um dos 5 níveis."""
    if not sentimentos:
        return None
    media = sum(PONTOS_SENTIMENTO[s] for s in sentimentos) / len(sentimentos)
    if abs(media) < LIMITE_NEUTRO:
        return Sentimento.NEUTRO
    if media > 0:
        return Sentimento.MUITO_POSITIVO if media >= LIMITE_MUITO else Sentimento.POSITIVO
    return Sentimento.MUITO_NEGATIVO if media <= -LIMITE_MUITO else Sentimento.NEGATIVO


def agregar(mensagens: list[MensagemRoteada]) -> ResumoComunidade:
    """Monta o resumo do lote. Mensagens que falharam na análise já ficaram de fora.

    Em caso de empate de pontos, vence o tópico que apareceu primeiro no lote.
    """
    pontos_por_topico = Counter()
    for mensagem in mensagens:
        for posicao, topico in enumerate(mensagem.topicos):
            pontos_por_topico[topico] += PESO_PRIMEIRO_TOPICO if posicao == 0 else PESO_DEMAIS_TOPICOS

    ranking = [t for t, _ in pontos_por_topico.most_common()]
    ranking.sort(key=lambda t: t in TOPICOS_GENERICOS)  # genéricos vão para o fim, sem mudar a ordem dos demais

    contagem_por_rota = {rota: 0 for rota in Rota}
    contagem_por_rota.update(Counter(m.rota for m in mensagens))

    return ResumoComunidade(
        total_interacoes_processadas=len(mensagens),
        sentimento_predominante=sentimento_medio([m.sentimento for m in mensagens]),
        topicos_principais=ranking[:QUANTIDADE_TOPICOS_PRINCIPAIS],
        contagem_por_rota=contagem_por_rota,
    )
