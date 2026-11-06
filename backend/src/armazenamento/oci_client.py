import json
import os
from dotenv import load_dotenv
import oci

from src.caminhos import caminho_do_projeto

load_dotenv()


class OCIStorageClient:
    """Cliente para integração com o OCI Object Storage (Always Free)."""

    def __init__(self):
        self.bucket_name = os.getenv("OCI_BUCKET_NAME")
        self.namespace = os.getenv("OCI_NAMESPACE")
        chave = os.getenv("OCI_PRIVATE_KEY_PATH")

        self.config = {
            "user": os.getenv("OCI_USER_OCID"),
            "fingerprint": os.getenv("OCI_FINGERPRINT"),
            "key_file": str(caminho_do_projeto(chave)) if chave else None,
            "tenancy": os.getenv("OCI_TENANCY_OCID"),
            "region": os.getenv("OCI_REGION"),
        }

    def configurado(self) -> bool:
        """True quando todas as variáveis da OCI estão preenchidas e a chave privada existe."""
        valores = [self.bucket_name, self.namespace, *self.config.values()]
        return all(valores) and os.path.isfile(self.config["key_file"])

    def _get_client(self):
        """Inicializa e retorna o cliente de Object Storage da OCI."""
        oci.config.validate_config(self.config)
        return oci.object_storage.ObjectStorageClient(self.config)

    def upload_json(self, object_name: str, payload: dict) -> dict:
        """Envia um dicionário/JSON para o Bucket Always Free do OCI.

        :param object_name: Caminho/Nome do objeto (ex:
            'ativos/2026-semana-04/pacote.json')
        :param payload: Dados em formato de dicionário a serem salvos
        """
        try:
            client = self._get_client()
            json_data = json.dumps(payload, ensure_ascii=False, indent=2).encode(
                "utf-8"
            )

            response = client.put_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_name,
                put_object_body=json_data,
                content_type="application/json",
            )

            return {
                "status": "sucesso",
                "bucket": self.bucket_name,
                "caminho_objeto": object_name,
                "etag": response.headers.get("etag"),
            }
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}