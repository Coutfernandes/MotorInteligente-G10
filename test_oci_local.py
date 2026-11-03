from src.storage.oci_client import OCIStorageClient

def test_oci_initialization():
    client = OCIStorageClient()
    print("Cliente OCI instanciado com sucesso!")
    print(f"Bucket configurado: {client.bucket_name}")
    print(f"Região configurada: {client.config.get('region')}")

if __name__ == "__main__":
    test_oci_initialization()