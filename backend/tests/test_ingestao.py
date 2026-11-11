import json
from pathlib import Path

import pytest

from src.ingestao.leitor import ErroIngestao, carregar_arquivo, carregar_conteudo

PASTA_DATA = Path(__file__).parent.parent.parent / "data"
PASTA_FIXTURES = Path(__file__).parent / "fixtures"

CABECALHO_CSV = "interaction_id,channel,interaction_type,created_at,text,reactions,consent_marketing"


def registro(**mudancas):
    dados = {
        "interaction_id": "INT-001",
        "channel": "conquistas-e-vagas",
        "interaction_type": "depoimento",
        "created_at": "2026-10-13T12:12:00Z",
        "text": "Fui aprovada na minha primeira vaga de IA!",
        "reactions": 42,
        "consent_marketing": True,
    }
    dados.update(mudancas)
    return dados


# ---- arquivos reais do repositório ----

def test_le_dataset_completo_com_lotes():
    resultado = carregar_arquivo(PASTA_DATA / "interacoes.json")
    assert len(resultado.interacoes) == 50
    assert resultado.rejeitadas == []


def test_le_fixture_em_lista():
    resultado = carregar_arquivo(PASTA_FIXTURES / "amostra_5.json")
    assert len(resultado.interacoes) == 5


def test_le_csv_de_amostra():
    resultado = carregar_arquivo(PASTA_DATA / "interacoes_amostra.csv")
    assert len(resultado.interacoes) == 8
    assert resultado.rejeitadas == []


def test_csv_e_json_geram_os_mesmos_registros():
    do_csv = carregar_arquivo(PASTA_DATA / "interacoes_amostra.csv").registros
    do_json = carregar_arquivo(PASTA_DATA / "interacoes.json").registros[:8]
    assert do_csv == do_json


# ---- formatos de JSON aceitos ----

@pytest.mark.parametrize(
    "dados",
    [
        [registro()],
        {"records": [registro()]},
        {"batches": [{"records": [registro()]}]},
    ],
)
def test_aceita_os_tres_formatos_de_json(dados):
    resultado = carregar_conteudo(json.dumps(dados), "json")
    assert resultado.interacoes[0].interaction_id == "INT-001"


def test_registros_saem_no_formato_do_roteador():
    registros = carregar_conteudo(json.dumps([registro()]), "json").registros
    assert registros[0]["interaction_type"] == "depoimento"
    assert registros[0]["consent_marketing"] is True


# ---- CSV ----

def test_csv_com_ponto_e_virgula_e_bom_do_excel():
    conteudo = (
        "﻿interaction_id;channel;interaction_type;created_at;text;consent_marketing\n"
        "INT-001;projetos;entrega_projeto;2026-10-13T12:00:00Z;Entreguei o projeto, com vírgula no texto;sim\n"
    ).encode("utf-8")
    interacao = carregar_conteudo(conteudo, "csv").interacoes[0]
    assert interacao.text == "Entreguei o projeto, com vírgula no texto"
    assert interacao.consent_marketing is True


def test_celula_vazia_usa_valor_padrao():
    conteudo = f"{CABECALHO_CSV}\nINT-001,projetos,debate,2026-10-13T12:00:00Z,Texto,,\n"
    interacao = carregar_conteudo(conteudo, "csv").interacoes[0]
    assert interacao.reactions == 0
    assert interacao.consent_marketing is False


def test_csv_sem_coluna_obrigatoria():
    with pytest.raises(ErroIngestao, match="text"):
        carregar_conteudo("interaction_id,channel,interaction_type,created_at\nINT-1,a,b,2026-10-13\n", "csv")


# ---- registros inválidos são rejeitados, o resto do lote segue ----

@pytest.mark.parametrize(
    "mudancas, campo_no_motivo",
    [
        ({"text": "   "}, "text"),
        ({"created_at": "ontem"}, "created_at"),
        ({"reactions": -1}, "reactions"),
        ({"consent_marketing": "talvez"}, "consent_marketing"),
    ],
)
def test_rejeita_registro_invalido_e_mantem_os_validos(mudancas, campo_no_motivo):
    dados = [registro(), registro(interaction_id="INT-002", **mudancas)]
    resultado = carregar_conteudo(json.dumps(dados), "json")
    assert [i.interaction_id for i in resultado.interacoes] == ["INT-001"]
    assert resultado.rejeitadas[0].posicao == 2
    assert campo_no_motivo in resultado.rejeitadas[0].motivo


def test_rejeita_campo_obrigatorio_ausente():
    sem_texto = registro(interaction_id="INT-002")
    del sem_texto["text"]
    resultado = carregar_conteudo(json.dumps([registro(), sem_texto]), "json")
    assert "text" in resultado.rejeitadas[0].motivo


def test_rejeita_id_repetido():
    resultado = carregar_conteudo(json.dumps([registro(), registro()]), "json")
    assert len(resultado.interacoes) == 1
    assert resultado.rejeitadas[0].motivo == "interaction_id repetido"


def test_rejeita_item_que_nao_e_objeto():
    resultado = carregar_conteudo(json.dumps([registro(), "texto solto"]), "json")
    assert resultado.rejeitadas[0].motivo == "registro não é um objeto"


# ---- erros que impedem a leitura do arquivo inteiro ----

@pytest.mark.parametrize(
    "conteudo, formato, mensagem",
    [
        ("[]", "xlsx", "não suportado"),
        ("   ", "json", "vazio"),
        ("{sem aspas}", "json", "JSON inválido"),
        ('{"dados": []}', "json", "fora do formato"),
        (b"\xff\xfe\x00", "csv", "UTF-8"),
        (json.dumps([{"interaction_id": "INT-1"}]), "json", "Nenhuma interação válida"),
    ],
)
def test_erros_de_arquivo(conteudo, formato, mensagem):
    with pytest.raises(ErroIngestao, match=mensagem):
        carregar_conteudo(conteudo, formato)


def test_arquivo_inexistente():
    with pytest.raises(ErroIngestao, match="não encontrado"):
        carregar_arquivo("data/nao_existe.json")
