"""Pastas do projeto, calculadas a partir deste arquivo (funciona de qualquer diretório de execução)."""

from pathlib import Path

PASTA_BACKEND = Path(__file__).resolve().parent.parent
PASTA_RAIZ = PASTA_BACKEND.parent

PASTA_DADOS = PASTA_RAIZ / "data"
PASTA_SAIDA = PASTA_DADOS / "saida"
PASTA_FRONTEND_BUILD = PASTA_RAIZ / "frontend" / "dist"


def caminho_do_projeto(caminho: str) -> Path:
    """Caminhos relativos do .env (ex.: ./oci_api_key.pem) valem a partir da raiz do projeto."""
    p = Path(caminho).expanduser()
    return p if p.is_absolute() else PASTA_RAIZ / p
