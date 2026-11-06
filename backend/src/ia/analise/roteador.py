"""Roteador: decide que tipo de conteúdo cada mensagem analisada vai virar (RN01 e RN02)."""

from src.ia.analise.schemas import AnaliseInteracao, MensagemRoteada, Rota, Sentimento

# ---- Limites do roteador: ajuste aqui ----
RELEVANCIA_MINIMA_CASE = 75
RELEVANCIA_MINIMA_LINKEDIN = 50
TIPOS_DUVIDA = {"pergunta_tecnica", "pedido_ajuda"}
TIPOS_CASE = {"depoimento", "entrega_projeto"}
TIPOS_IGNORADOS = {"mensagem_operacional"}
# ------------------------------------------

SENTIMENTOS_POSITIVOS = {Sentimento.POSITIVO, Sentimento.MUITO_POSITIVO}


def decidir_rota(analise: AnaliseInteracao, consent_marketing: bool) -> tuple[Rota, str]:
    """Aplica as regras em ordem; a primeira que servir decide a rota e o motivo."""
    positivo = analise.sentimento in SENTIMENTOS_POSITIVOS

    if analise.tipo in TIPOS_IGNORADOS:
        return Rota.IGNORAR, "mensagem operacional"
    if analise.tipo in TIPOS_DUVIDA:
        return Rota.FAQ, "dúvida da comunidade"
    # RN01: só relatos positivos, e com consentimento, viram case ou post
    if positivo and consent_marketing:
        if analise.tipo in TIPOS_CASE and analise.relevancia >= RELEVANCIA_MINIMA_CASE:
            return Rota.CASE, f"relato positivo com relevância {analise.relevancia}"
        if analise.relevancia >= RELEVANCIA_MINIMA_LINKEDIN:
            return Rota.LINKEDIN, f"relato positivo com relevância {analise.relevancia}"
    if analise.sentimento == Sentimento.NEUTRO:
        return Rota.FAQ, "relato neutro"
    if positivo and not consent_marketing:
        return Rota.IGNORAR, "positivo, mas sem consentimento de marketing"
    if positivo:
        return Rota.IGNORAR, f"positivo, mas relevância {analise.relevancia} abaixo de {RELEVANCIA_MINIMA_LINKEDIN}"
    return Rota.IGNORAR, "sentimento negativo"


def rotear(analise: AnaliseInteracao, consent_marketing: bool) -> MensagemRoteada:
    rota, motivo = decidir_rota(analise, consent_marketing)
    return MensagemRoteada(
        **analise.model_dump(),
        consent_marketing=consent_marketing,
        rota=rota,
        motivo=motivo,
    )


def rotear_lote(analises: list[AnaliseInteracao], registros: list[dict]) -> list[MensagemRoteada]:
    """Roteia as análises do lote, buscando o consent_marketing de cada uma nos registros de entrada.

    Sem a informação de consentimento, a mensagem é tratada como sem consentimento (não vira post).
    """
    consentimentos = {r["interaction_id"]: bool(r.get("consent_marketing", False)) for r in registros}
    return [rotear(a, consentimentos.get(a.interaction_id, False)) for a in analises]
