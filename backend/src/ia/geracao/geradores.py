"""Geração dos ativos de marketing com o Gemini: post LinkedIn (F05), newsletter (F06) e FAQ (F07)."""

import logging
import time
from pathlib import Path

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from src.ia.llm import chamar_com_espera, criar_llm, erro_temporario
from src.ia.analise.roteador import TIPOS_DUVIDA
from src.ia.analise.schemas import MensagemRoteada, ResumoComunidade, Rota
from src.ia.geracao.schemas import Ativo, ConteudoGerado, TipoAtivo

logger = logging.getLogger(__name__)

PASTA_PROMPTS = Path(__file__).parent.parent / "prompts" / "geracao"

# ---- Limites da geração: cada ativo gasta 1 chamada do Gemini ----
MAX_POSTS_LINKEDIN = 3
MAX_MENSAGENS_FAQ = 5
MAX_DESTAQUES_NEWSLETTER = 5
TEMPERATURA_GERACAO = 0.7
TENTATIVAS_EXTRAS = 2
# Conteúdo maior que isso, sem nenhuma quebra de linha, é pedido de novo (o Markdown não aparece na tela).
CARACTERES_SEM_QUEBRA = 300
# ------------------------------------------------------------------

ROTAS_POSITIVAS = {Rota.CASE, Rota.LINKEDIN}


class FalhaNaGeracao(Exception):
    """O Gemini não devolveu um conteúdo válido depois de todas as tentativas."""


def carregar_prompt(tipo: TipoAtivo) -> str:
    """Prompt do tipo de ativo + regras comuns a todos."""
    especifico = (PASTA_PROMPTS / f"{tipo.value}.txt").read_text(encoding="utf-8").strip()
    comum = (PASTA_PROMPTS / "regras_comuns.txt").read_text(encoding="utf-8").strip()
    return f"{especifico}\n\n{comum}"


def criar_gerador(llm=None):
    """Prepara o Gemini para responder sempre no formato de ConteudoGerado."""
    llm = llm or criar_llm(temperatura=TEMPERATURA_GERACAO)
    return llm.with_structured_output(ConteudoGerado)


def _descrever(mensagem: MensagemRoteada, texto: str) -> str:
    return (
        f"Tipo: {mensagem.tipo}\n"
        f"Tópicos: {', '.join(mensagem.topicos)}\n"
        f"Texto: {texto}"
    )


def _mais_relevantes(mensagens: list[MensagemRoteada], rotas: set[Rota], limite: int) -> list[MensagemRoteada]:
    escolhidas = [m for m in mensagens if m.rota in rotas]
    return sorted(escolhidas, key=lambda m: m.relevancia, reverse=True)[:limite]


def _duvidas_primeiro(mensagens: list[MensagemRoteada], limite: int) -> list[MensagemRoteada]:
    """RN02: debates e relatos neutros também vão para o FAQ, mas as dúvidas reais têm a preferência.
    Os demais só entram se sobrar vaga."""
    escolhidas = [m for m in mensagens if m.rota == Rota.FAQ]
    return sorted(escolhidas, key=lambda m: (m.tipo in TIPOS_DUVIDA, m.relevancia), reverse=True)[:limite]


def _gerar(tipo: TipoAtivo, pedido: str, gerador, esperar=time.sleep) -> ConteudoGerado:
    """Faz a chamada ao Gemini, tentando de novo se a resposta vier fora do formato
    ou se o Gemini estiver sobrecarregado/sem cota (T03)."""
    mensagens = [SystemMessage(content=carregar_prompt(tipo)), HumanMessage(content=pedido)]

    for tentativa in range(1 + TENTATIVAS_EXTRAS):
        try:
            resposta = chamar_com_espera(lambda: gerador.invoke(mensagens), esperar)
            if resposta is None:
                raise OutputParserException("o modelo não devolveu nenhum conteúdo")
            conteudo = ConteudoGerado(**resposta.model_dump())
            if len(conteudo.conteudo) > CARACTERES_SEM_QUEBRA and "\n" not in conteudo.conteudo:
                if tentativa < TENTATIVAS_EXTRAS:
                    raise OutputParserException(
                        "o conteúdo veio em uma linha só; separe parágrafos, títulos e itens de lista com quebras de linha"
                    )
                # Na última tentativa, fica com o texto assim mesmo: a curadoria pode ajustar a formatação.
                logger.warning("%s gerado sem quebras de linha depois de todas as tentativas.", tipo.value)
            return conteudo
        except Exception as erro:
            if erro_temporario(erro):
                raise FalhaNaGeracao(f"Gemini indisponível ao gerar {tipo.value}: {erro}") from erro
            if not isinstance(erro, (OutputParserException, ValidationError)):
                raise
            logger.warning("Resposta inválida ao gerar %s (tentativa %d): %s", tipo.value, tentativa + 1, erro)
            mensagens = mensagens[:2] + [
                HumanMessage(
                    content=f"Sua resposta anterior foi inválida: {erro}. Responda de novo seguindo exatamente o formato pedido."
                )
            ]

    raise FalhaNaGeracao(f"Não foi possível gerar o ativo do tipo {tipo.value}.")


def gerar_post_linkedin(mensagem: MensagemRoteada, texto: str, gerador, numero: int = 1, esperar=time.sleep) -> Ativo:
    """F05 / RN01: um post inspirador a partir de UM relato positivo."""
    pedido = f"Relato da comunidade:\n{_descrever(mensagem, texto)}"
    conteudo = _gerar(TipoAtivo.LINKEDIN, pedido, gerador, esperar)
    return Ativo(**conteudo.model_dump(), id=f"linkedin-{numero}", tipo=TipoAtivo.LINKEDIN, fontes=[mensagem.interaction_id])


def gerar_newsletter(
    mensagens: list[MensagemRoteada], textos: dict[str, str], resumo: ResumoComunidade, gerador, esperar=time.sleep
) -> Ativo:
    """F06 / RN01: destaques celebrativos a partir dos relatos positivos do lote."""
    relatos = "\n\n".join(_descrever(m, textos[m.interaction_id]) for m in mensagens)
    pedido = (
        f"Temas mais falados no período: {', '.join(resumo.topicos_principais) or 'não identificados'}\n"
        f"Total de interações analisadas: {resumo.total_interacoes_processadas}\n\n"
        f"Relatos positivos:\n\n{relatos}"
    )
    conteudo = _gerar(TipoAtivo.NEWSLETTER, pedido, gerador, esperar)
    return Ativo(
        **conteudo.model_dump(), id="newsletter-1", tipo=TipoAtivo.NEWSLETTER, fontes=[m.interaction_id for m in mensagens]
    )


def gerar_faq(mensagens: list[MensagemRoteada], textos: dict[str, str], gerador, esperar=time.sleep) -> Ativo:
    """F07 / RN02: FAQ didático a partir das dúvidas e relatos neutros do lote."""
    duvidas = "\n\n".join(_descrever(m, textos[m.interaction_id]) for m in mensagens)
    conteudo = _gerar(TipoAtivo.FAQ, f"Dúvidas e relatos da comunidade:\n\n{duvidas}", gerador, esperar)
    return Ativo(**conteudo.model_dump(), id="faq-1", tipo=TipoAtivo.FAQ, fontes=[m.interaction_id for m in mensagens])


def gerar_ativos(
    mensagens: list[MensagemRoteada],
    registros: list[dict],
    resumo: ResumoComunidade,
    gerador=None,
    intervalo: float = 0.0,
    esperar=time.sleep,
    ao_gerar=None,
    ao_falhar=None,
) -> list[Ativo]:
    """Gera todos os ativos possíveis para o lote, respeitando as rotas decididas pelo roteador.

    Ativos que falham em todas as tentativas são registrados no log e pulados.
    `ao_gerar(atual, total)` é chamado antes de cada chamada ao Gemini (para mostrar progresso).
    `ao_falhar(motivo)` é chamado para cada ativo pulado (para avisar na interface).
    """
    gerador = gerador or criar_gerador()
    textos = {r["interaction_id"]: r["text"] for r in registros}

    positivas = _mais_relevantes(mensagens, ROTAS_POSITIVAS, max(MAX_POSTS_LINKEDIN, MAX_DESTAQUES_NEWSLETTER))
    duvidas = _duvidas_primeiro(mensagens, MAX_MENSAGENS_FAQ)

    tarefas = [
        lambda m=m, n=n: gerar_post_linkedin(m, textos[m.interaction_id], gerador, n, esperar)
        for n, m in enumerate(positivas[:MAX_POSTS_LINKEDIN], start=1)
    ]
    if positivas:
        tarefas.append(lambda: gerar_newsletter(positivas[:MAX_DESTAQUES_NEWSLETTER], textos, resumo, gerador, esperar))
    if duvidas:
        tarefas.append(lambda: gerar_faq(duvidas, textos, gerador, esperar))

    ativos = []
    for posicao, tarefa in enumerate(tarefas):
        if posicao > 0:
            esperar(intervalo)
        if ao_gerar:
            ao_gerar(posicao + 1, len(tarefas))
        try:
            ativos.append(tarefa())
        except FalhaNaGeracao as erro:
            logger.error("%s Ativo pulado.", erro)
            if ao_falhar:
                ao_falhar(str(erro))

    return ativos
