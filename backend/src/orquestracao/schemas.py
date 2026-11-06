"""Pacote: tudo o que um processamento produz, do resumo aos ativos em curadoria."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.ia.analise.schemas import MensagemRoteada, ResumoComunidade
from src.ia.geracao.schemas import Ativo, StatusCuradoria
from src.ingestao.schemas import Rejeitada


class Pacote(BaseModel):
    id: str
    criado_em: datetime
    arquivo_origem: str
    resumo: ResumoComunidade
    mensagens: list[MensagemRoteada]
    ativos: list[Ativo]
    rejeitadas_ingestao: list[Rejeitada] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)
    # Resultado do último envio de cada versão: {"gerado": {...}, "aprovado": {...}}
    armazenamento: dict = Field(default_factory=dict)
    exportado_em: datetime | None = None

    @property
    def caminho_gerado(self) -> str:
        return f"pacotes/{self.id}.json"

    @property
    def caminho_aprovado(self) -> str:
        return f"aprovados/{self.id}.json"

    @property
    def aprovados(self) -> list[Ativo]:
        """RN04: só estes ativos podem sair do sistema (exportação e download)."""
        return [a for a in self.ativos if a.status == StatusCuradoria.APROVADO]
