"""Persistência dos pacotes: cópia local (usada pela curadoria) + OCI Object Storage (RN03)."""

import json
import logging
from pathlib import Path

from src.armazenamento.oci_client import OCIStorageClient
from src.caminhos import PASTA_SAIDA

logger = logging.getLogger(__name__)


class Repositorio:
    def __init__(self, pasta: Path = PASTA_SAIDA, oci_client: OCIStorageClient | None = None):
        self.pasta = Path(pasta)
        self.oci = oci_client or OCIStorageClient()

    def salvar_local(self, caminho: str, payload: dict) -> Path:
        """Grava só a cópia local (ex: mudanças de status durante a curadoria)."""
        arquivo = self.pasta / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return arquivo

    def salvar(self, caminho: str, payload: dict) -> dict:
        """Grava o JSON localmente e envia ao bucket OCI. Devolve o resultado de cada destino."""
        arquivo = self.salvar_local(caminho, payload)

        if self.oci.configurado():
            resultado_oci = self.oci.upload_json(caminho, payload)
            if resultado_oci["status"] == "erro":
                logger.error("Falha ao enviar %s para a OCI: %s", caminho, resultado_oci["mensagem"])
        else:
            resultado_oci = {"status": "nao_configurado", "mensagem": "Credenciais da OCI não preenchidas no .env."}
            logger.warning("OCI não configurada: %s salvo apenas localmente.", caminho)

        return {"local": {"status": "sucesso", "caminho": str(arquivo)}, "oci": resultado_oci}

    def ler(self, caminho: str) -> dict | None:
        arquivo = self.pasta / caminho
        if not arquivo.is_file():
            return None
        return json.loads(arquivo.read_text(encoding="utf-8"))

    def listar(self, pasta: str) -> list[str]:
        """Caminhos (relativos) dos JSONs de uma subpasta, do mais novo para o mais antigo."""
        base = self.pasta / pasta
        if not base.is_dir():
            return []
        arquivos = sorted(base.glob("*.json"), key=lambda a: a.stat().st_mtime, reverse=True)
        return [f"{pasta}/{a.name}" for a in arquivos]
