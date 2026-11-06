"""Verifica, passo a passo, se as credenciais da OCI no .env funcionam.

Uso (na pasta backend/):  python scripts/verificar_oci.py

1. Confere se todas as variáveis estão preenchidas e se a chave .pem existe.
2. Valida o formato da configuração (OCIDs, fingerprint, região).
3. Conecta e lê o bucket (testa chave, fingerprint, namespace e permissão).
4. Envia um objeto de teste, confirma que ele está lá e apaga em seguida.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Permite rodar como "python scripts/verificar_oci.py" a partir da pasta backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.armazenamento.oci_client import OCIStorageClient  # noqa: E402

VARIAVEIS = [
    "OCI_USER_OCID",
    "OCI_TENANCY_OCID",
    "OCI_FINGERPRINT",
    "OCI_PRIVATE_KEY_PATH",
    "OCI_REGION",
    "OCI_BUCKET_NAME",
    "OCI_NAMESPACE",
]


def ok(msg: str) -> None:
    print(f"  [OK]    {msg}")


def falha(msg: str, dica: str = "") -> None:
    print(f"  [FALHA] {msg}")
    if dica:
        print(f"          Dica: {dica}")
    sys.exit(1)


def verificar() -> None:
    cliente = OCIStorageClient()

    print("\n1. Variáveis do .env")
    faltando = [v for v in VARIAVEIS if not os.getenv(v)]
    if faltando:
        falha(f"Vazias: {', '.join(faltando)}", "preencha no arquivo .env na raiz do projeto.")
    ok("todas preenchidas")
    chave = cliente.config["key_file"]
    if not os.path.isfile(chave):
        falha(f"Chave privada não encontrada em '{chave}'", "coloque o oci_api_key.pem na raiz do projeto.")
    ok(f"chave privada encontrada ({chave})")

    print("\n2. Formato da configuração")
    try:
        servico = cliente._get_client()
    except Exception as e:
        falha(str(e), "confira se copiou os OCIDs e o fingerprint inteiros, sem espaços ou aspas.")
    ok(f"região {cliente.config['region']}")

    print("\n3. Conexão com o bucket")
    try:
        bucket = servico.get_bucket(cliente.namespace, cliente.bucket_name).data
    except Exception as e:
        status = getattr(e, "status", None)
        dicas = {
            401: "chave .pem e fingerprint não batem, ou o user OCID está errado. Gere uma nova API key.",
            404: "bucket ou namespace não existe nessa região (ou o usuário não tem permissão para vê-lo).",
        }
        falha(f"{getattr(e, 'message', e)} (HTTP {status})", dicas.get(status, "confira a região e a conexão."))
    ok(f"bucket '{bucket.name}' encontrado no compartimento {bucket.compartment_id[:30]}…")

    print("\n4. Envio de teste")
    objeto = f"teste_conexao/{datetime.now():%Y%m%d_%H%M%S}.json"
    resultado = cliente.upload_json(objeto, {"teste": "CommunityLab", "quando": datetime.now().isoformat()})
    if resultado["status"] != "sucesso":
        falha(resultado.get("mensagem", "erro desconhecido"), "o usuário precisa de permissão de escrita no bucket.")
    ok(f"enviado: {cliente.bucket_name}/{objeto}")
    servico.head_object(cliente.namespace, cliente.bucket_name, objeto)
    ok("confirmado no bucket")
    servico.delete_object(cliente.namespace, cliente.bucket_name, objeto)
    ok("objeto de teste apagado")

    print("\nTudo certo: a OCI está pronta para receber os pacotes.\n")


if __name__ == "__main__":
    verificar()
