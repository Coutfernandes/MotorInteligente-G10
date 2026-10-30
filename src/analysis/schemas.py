"""Modelos de dados da análise de sentimento e tópicos (F04)."""

import re
import unicodedata
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Sentimento(str, Enum):
    MUITO_POSITIVO = "muito_positivo"
    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"
    MUITO_NEGATIVO = "muito_negativo"


class Entidades(BaseModel):
    """Itens citados literalmente no texto da mensagem (nada inventado)."""

    cargos: list[str] = Field(default_factory=list)
    tecnologias: list[str] = Field(default_factory=list)
    organizacoes: list[str] = Field(default_factory=list)


def _normalizar_topico(topico: str) -> str:
    """Deixa o tópico em minúsculas, sem acento e com "_" no lugar de espaços."""
    sem_acento = unicodedata.normalize("NFKD", topico).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")


class RespostaLLM(BaseModel):
    """O que o Gemini devolve para UMA mensagem."""

    sentimento: Sentimento
    topicos: list[str] = Field(min_length=1, max_length=3)
    entidades: Entidades = Field(default_factory=Entidades)
    relevancia: int = Field(ge=0, le=100)
    insight: str = Field(min_length=1, max_length=280)

    @field_validator("topicos")
    @classmethod
    def normalizar_topicos(cls, topicos: list[str]) -> list[str]:
        normalizados = [_normalizar_topico(t) for t in topicos]
        if any(not t for t in normalizados):
            raise ValueError("tópico vazio")
        # remove repetidos mantendo a ordem
        return list(dict.fromkeys(normalizados))


class AnaliseInteracao(RespostaLLM):
    """Resultado final por mensagem: resposta do Gemini + dados da entrada."""

    interaction_id: str = Field(min_length=1)
    tipo: str = Field(min_length=1)
