"""Modelos de dados da ingestão (F02): uma interação da comunidade e o resultado da leitura."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Valores de sim/não aceitos nas colunas booleanas do CSV (além dos que o Pydantic já entende).
VALORES_SIM = {"sim", "s"}
VALORES_NAO = {"nao", "não", "n"}


class Interacao(BaseModel):
    """Uma mensagem da comunidade, já validada."""

    interaction_id: str = Field(min_length=1)
    author_id: str | None = None
    channel: str = Field(min_length=1)
    interaction_type: str = Field(min_length=1)
    created_at: datetime
    text: str = Field(min_length=1)
    text_truncated: bool = False
    pii_redacted: bool = False
    reactions: int = Field(default=0, ge=0)
    # Sem a informação, a mensagem é tratada como sem consentimento (não vira post).
    consent_marketing: bool = False

    @field_validator("interaction_id", "author_id", "channel", "interaction_type", "text", mode="before")
    @classmethod
    def tirar_espacos(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("text_truncated", "pii_redacted", "consent_marketing", mode="before")
    @classmethod
    def aceitar_sim_nao(cls, valor):
        if isinstance(valor, str):
            texto = valor.strip().lower()
            if texto in VALORES_SIM:
                return True
            if texto in VALORES_NAO:
                return False
        return valor


class Rejeitada(BaseModel):
    """Registro que não passou na validação e ficou de fora do lote."""

    posicao: int  # 1 = primeiro registro do arquivo
    interaction_id: str | None
    motivo: str


class ResultadoIngestao(BaseModel):
    interacoes: list[Interacao]
    rejeitadas: list[Rejeitada]

    @property
    def registros(self) -> list[dict]:
        """As interações como dicts, no formato que a análise e o roteador recebem."""
        return [i.model_dump(mode="json") for i in self.interacoes]
