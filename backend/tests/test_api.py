from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api import main
from src.api.execucoes import Gerenciador
from src.armazenamento.repositorio import Repositorio
from tests.test_pipeline_curadoria import OCIFalso

AMOSTRA = Path(__file__).parent / "fixtures" / "amostra_5.json"


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "simulado")
    gerenciador = Gerenciador(Repositorio(tmp_path, OCIFalso()))
    # roda o pipeline na hora (sem thread), para o teste não precisar esperar
    iniciar = gerenciador.iniciar
    monkeypatch.setattr(gerenciador, "iniciar", lambda ing, arq: iniciar(ing, arq, em_segundo_plano=False))
    monkeypatch.setattr(main, "gerenciador", gerenciador)
    return TestClient(main.app)


def enviar(cliente, rota, nome="amostra_5.json", conteudo=None):
    conteudo = conteudo if conteudo is not None else AMOSTRA.read_bytes()
    return cliente.post(rota, files={"arquivo": (nome, conteudo)})


@pytest.fixture
def id_pacote(cliente):
    resposta = enviar(cliente, "/api/processamentos")
    assert resposta.status_code == 202
    execucao = cliente.get(f"/api/processamentos/{resposta.json()['id']}").json()
    assert execucao["status"] == "concluido"
    return execucao["id"]


def test_status_informa_modo_simulado(cliente):
    dados = cliente.get("/api/status").json()
    assert dados["llm"]["simulado"] is True
    assert dados["oci"]["configurado"] is True


def test_validar_nao_processa(cliente):
    dados = enviar(cliente, "/api/ingestao/validar").json()
    assert dados["total_validas"] == 5
    assert dados["rejeitadas"] == []
    assert cliente.get("/api/pacotes").json() == []


def test_validar_arquivo_invalido(cliente):
    resposta = enviar(cliente, "/api/ingestao/validar", nome="dados.txt", conteudo=b"oi")
    assert resposta.status_code == 422
    assert "não suportado" in resposta.json()["detail"]


def test_processar_sem_gemini_configurado(cliente, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    resposta = enviar(cliente, "/api/processamentos")
    assert resposta.status_code == 400
    assert "GOOGLE_API_KEY" in resposta.json()["detail"]


def test_fluxo_completo_de_curadoria(cliente, id_pacote):
    pacote = cliente.get(f"/api/pacotes/{id_pacote}").json()
    primeiro = pacote["ativos"][0]["id"]

    # RN04: sem aprovação, nada sai
    assert cliente.post(f"/api/pacotes/{id_pacote}/exportar").status_code == 409
    assert cliente.get(f"/api/pacotes/{id_pacote}/download").status_code == 409

    editado = cliente.patch(
        f"/api/pacotes/{id_pacote}/ativos/{primeiro}", json={"conteudo": "Revisado", "status": "aprovado"}
    ).json()
    assert editado["status"] == "aprovado"
    assert editado["editado"] is True

    exportado = cliente.post(f"/api/pacotes/{id_pacote}/exportar").json()
    assert exportado["total_aprovados"] == 1
    assert exportado["armazenamento"]["oci"]["status"] == "sucesso"

    download = cliente.get(f"/api/pacotes/{id_pacote}/download?formato=markdown")
    assert download.status_code == 200
    assert "Revisado" in download.text

    lista = cliente.get("/api/pacotes").json()
    assert lista[0]["aprovados"] == 1
    assert lista[0]["exportado_em"] is not None
    assert lista[0]["oci_exportado"] == "sucesso"


def test_titulo_vazio_e_recusado(cliente, id_pacote):
    primeiro = cliente.get(f"/api/pacotes/{id_pacote}").json()["ativos"][0]["id"]
    resposta = cliente.patch(f"/api/pacotes/{id_pacote}/ativos/{primeiro}", json={"titulo": ""})
    assert resposta.status_code == 422


def test_arquivo_de_exemplo_e_valido(cliente):
    exemplo = cliente.get("/api/exemplo")
    assert exemplo.status_code == 200
    dados = enviar(cliente, "/api/ingestao/validar", nome="interacoes_amostra.csv", conteudo=exemplo.content).json()
    assert dados["total_validas"] == 8


def test_pacote_inexistente(cliente):
    assert cliente.get("/api/pacotes/nao-existe").status_code == 404
