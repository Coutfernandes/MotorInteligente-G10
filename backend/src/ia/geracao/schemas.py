"""Modelos dos ativos de marketing gerados (F05, F06, F07)."""

from enum import Enum

from pydantic import BaseModel, Field


class TipoAtivo(str, Enum):
    LINKEDIN = "linkedin"
    NEWSLETTER = "newsletter"
    FAQ = "faq"


class StatusCuradoria(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class ConteudoGerado(BaseModel):
    """O que o Gemini devolve para UM ativo."""

    titulo: str = Field(min_length=1, max_length=120)
    conteudo: str = Field(min_length=1)


class Ativo(ConteudoGerado):
    """Ativo pronto para a curadoria. RN04: nasce pendente e só sai do sistema se aprovado."""

    id: str = Field(min_length=1)
    tipo: TipoAtivo
    fontes: list[str] = Field(min_length=1)  # interaction_ids usados para gerar o ativo
    status: StatusCuradoria = StatusCuradoria.PENDENTE
    editado: bool = False
