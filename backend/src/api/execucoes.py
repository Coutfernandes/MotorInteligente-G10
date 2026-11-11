"""Processamentos em segundo plano: o pipeline leva minutos com o Gemini real, então a API não espera por ele."""

import logging
import threading
from datetime import datetime, timezone

from pydantic import BaseModel

from src.ia.llm import modo_simulado
from src.ia.analise.sentimento import INTERVALO_ENTRE_CHAMADAS
from src.ingestao.schemas import ResultadoIngestao
from src.orquestracao.pipeline import executar_pipeline, novo_id
from src.orquestracao.schemas import Pacote
from src.armazenamento.repositorio import Repositorio

logger = logging.getLogger(__name__)


class Execucao(BaseModel):
    id: str
    arquivo: str
    status: str = "processando"  # processando | concluido | erro
    etapa: str = "iniciando"  # iniciando | analise | geracao | salvando
    atual: int = 0
    total: int = 0
    erro: str | None = None
    iniciado_em: datetime


class Gerenciador:
    def __init__(self, repositorio: Repositorio | None = None, executar=executar_pipeline):
        self.repositorio = repositorio or Repositorio()
        self.executar = executar
        self.execucoes: dict[str, Execucao] = {}
        self.trava = threading.Lock()

    # ---- processamentos ----

    def iniciar(self, ingestao: ResultadoIngestao, arquivo: str, em_segundo_plano: bool = True) -> Execucao:
        execucao = Execucao(id=novo_id(), arquivo=arquivo, iniciado_em=datetime.now(timezone.utc))
        self.execucoes[execucao.id] = execucao
        if em_segundo_plano:
            threading.Thread(target=self._rodar, args=(execucao, ingestao), daemon=True).start()
        else:
            self._rodar(execucao, ingestao)
        return execucao

    def _rodar(self, execucao: Execucao, ingestao: ResultadoIngestao) -> None:
        def ao_progredir(etapa: str, atual: int, total: int) -> None:
            execucao.etapa, execucao.atual, execucao.total = etapa, atual, total

        try:
            self.executar(
                ingestao.registros,
                execucao.arquivo,
                repositorio=self.repositorio,
                intervalo=0.0 if modo_simulado() else INTERVALO_ENTRE_CHAMADAS,
                ao_progredir=ao_progredir,
                rejeitadas_ingestao=ingestao.rejeitadas,
                id_pacote=execucao.id,
            )
            execucao.status = "concluido"
        except Exception as erro:  # qualquer falha vira mensagem na tela, em vez de derrubar a API
            logger.exception("Falha no processamento %s", execucao.id)
            execucao.status, execucao.erro = "erro", str(erro)

    def obter(self, id_execucao: str) -> Execucao | None:
        return self.execucoes.get(id_execucao)

    # ---- pacotes salvos ----

    def pacote(self, id_pacote: str) -> Pacote | None:
        dados = self.repositorio.ler(f"pacotes/{id_pacote}.json")
        return Pacote(**dados) if dados else None

    def salvar(self, pacote: Pacote) -> None:
        self.repositorio.salvar_local(pacote.caminho_gerado, pacote.model_dump(mode="json"))

    def pacotes(self) -> list[Pacote]:
        return [Pacote(**self.repositorio.ler(c)) for c in self.repositorio.listar("pacotes")]
