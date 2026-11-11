"""Deploy: só o frontend configurado em CORS_ORIGINS pode chamar a API pelo navegador."""

import importlib

import pytest
from fastapi.testclient import TestClient

from src.api import main

VERCEL = "https://communitylab-g10.vercel.app"


@pytest.fixture
def cliente_com_cors(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", f"{VERCEL}/, http://localhost:5173")
    monkeypatch.setenv("LLM_PROVIDER", "simulado")
    modulo = importlib.reload(main)
    yield TestClient(modulo.app)
    monkeypatch.delenv("CORS_ORIGINS")
    importlib.reload(main)  # devolve o app sem CORS para os outros testes


def test_le_varias_origens_e_tira_a_barra_final(cliente_com_cors):
    assert main.ORIGENS_PERMITIDAS == [VERCEL, "http://localhost:5173"]


def test_frontend_da_vercel_e_aceito(cliente_com_cors):
    resposta = cliente_com_cors.get("/api/status", headers={"Origin": VERCEL})
    assert resposta.headers.get("access-control-allow-origin") == VERCEL


def test_preflight_do_patch_da_curadoria(cliente_com_cors):
    resposta = cliente_com_cors.options(
        "/api/pacotes/x/ativos/y",
        headers={"Origin": VERCEL, "Access-Control-Request-Method": "PATCH", "Access-Control-Request-Headers": "content-type"},
    )
    assert resposta.status_code == 200
    assert "PATCH" in resposta.headers.get("access-control-allow-methods", "")


def test_outro_site_nao_e_aceito(cliente_com_cors):
    resposta = cliente_com_cors.get("/api/status", headers={"Origin": "https://site-qualquer.com"})
    assert "access-control-allow-origin" not in resposta.headers


def test_sem_cors_origins_nao_libera_nada(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    modulo = importlib.reload(main)
    resposta = TestClient(modulo.app).get("/api/status", headers={"Origin": VERCEL})
    assert "access-control-allow-origin" not in resposta.headers
