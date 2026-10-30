"""Análise de sentimento, tópicos e relevância de cada mensagem da comunidade (F04)."""

import logging
import time

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from src.analysis.llm import carregar_prompt, criar_llm
from src.analysis.schemas import AnaliseInteracao, RespostaLLM

logger = logging.getLogger(__name__)

# Novas tentativas quando o Gemini devolve uma resposta fora do formato.
TENTATIVAS_EXTRAS = 2

# Pausa (segundos) entre mensagens de um lote.
# O plano gratuito do gemini-3.5-flash-lite permite 15 chamadas por minuto.
INTERVALO_ENTRE_CHAMADAS = 5.0


class FalhaNaAnalise(Exception):
    """O Gemini não devolveu uma resposta válida depois de todas as tentativas."""


def criar_analisador(llm=None):
    """Prepara o Gemini para responder sempre no formato de RespostaLLM."""
    llm = llm or criar_llm()
    return llm.with_structured_output(RespostaLLM)


def _montar_mensagem(registro: dict) -> str:
    return (
        f"Tipo: {registro['interaction_type']}\n"
        f"Canal: {registro['channel']}\n"
        f"Texto: {registro['text']}"
    )


def analisar_interacao(registro: dict, analisador=None) -> AnaliseInteracao:
    """Analisa UMA mensagem com o Gemini (1 chamada, ou até 3 se a resposta vier inválida)."""
    analisador = analisador or criar_analisador()
    mensagens = [
        SystemMessage(content=carregar_prompt("analise_sentimento")),
        HumanMessage(content=_montar_mensagem(registro)),
    ]

    for tentativa in range(1 + TENTATIVAS_EXTRAS):
        try:
            resposta = analisador.invoke(mensagens)
            if resposta is None:
                raise OutputParserException("o modelo não devolveu nenhum conteúdo")
            return AnaliseInteracao(
                **resposta.model_dump(),
                interaction_id=registro["interaction_id"],
                tipo=registro["interaction_type"],
            )
        except (OutputParserException, ValidationError) as erro:
            logger.warning(
                "Resposta inválida para %s (tentativa %d): %s",
                registro["interaction_id"], tentativa + 1, erro,
            )
            mensagens = mensagens[:2] + [
                HumanMessage(
                    content=f"Sua resposta anterior foi inválida: {erro}. Responda de novo seguindo exatamente o formato pedido."
                )
            ]

    raise FalhaNaAnalise(f"Não foi possível analisar {registro['interaction_id']}.")


def analisar_lote(
    registros: list[dict],
    analisador=None,
    intervalo: float = INTERVALO_ENTRE_CHAMADAS,
    esperar=time.sleep,
) -> list[AnaliseInteracao]:
    """Analisa as mensagens uma a uma, com pausa entre elas para respeitar a cota.

    Mensagens que falham em todas as tentativas são registradas no log e puladas.
    """
    analisador = analisador or criar_analisador()
    analises = []

    for posicao, registro in enumerate(registros):
        if posicao > 0:
            esperar(intervalo)
        try:
            analises.append(analisar_interacao(registro, analisador))
        except FalhaNaAnalise as erro:
            logger.error("%s Mensagem pulada.", erro)

    return analises
