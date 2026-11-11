"""F14: os 3 exemplos de demonstração (data/exemplos/) produzem o resultado descrito em docs/DEMONSTRACAO.md."""

from pathlib import Path

import pytest

from src.armazenamento.repositorio import Repositorio
from src.ia.analise.schemas import RespostaLLM, Rota
from src.ia.geracao.schemas import ConteudoGerado, TipoAtivo
from src.ia.llm_simulado import LLMSimulado
from src.ingestao.leitor import carregar_arquivo
from src.orquestracao.pipeline import executar_pipeline

PASTA_EXEMPLOS = Path(__file__).parent.parent.parent / "data" / "exemplos"


class OCIFalso:
    bucket_name = "bucket-teste"

    def configurado(self):
        return True

    def upload_json(self, caminho, payload):
        return {"status": "sucesso", "caminho_objeto": caminho}


def processar(nome, tmp_path):
    ingestao = carregar_arquivo(PASTA_EXEMPLOS / nome)
    simulado = LLMSimulado()
    pacote = executar_pipeline(
        ingestao.registros, nome,
        analisador=simulado.with_structured_output(RespostaLLM),
        gerador=simulado.with_structured_output(ConteudoGerado),
        repositorio=Repositorio(tmp_path, OCIFalso()),
        intervalo=0,
        rejeitadas_ingestao=ingestao.rejeitadas,
    )
    return ingestao, pacote


def rotas(pacote):
    return {m.interaction_id: m.rota for m in pacote.mensagens}


def tipos(pacote):
    return [a.tipo for a in pacote.ativos]


def test_exemplo_1_relatos_positivos_viram_posts_e_newsletter(tmp_path):
    ingestao, pacote = processar("01_relatos_positivos.json", tmp_path)
    assert len(ingestao.interacoes) == 5 and not ingestao.rejeitadas
    assert all(r in {Rota.CASE, Rota.LINKEDIN} for r in rotas(pacote).values())
    assert tipos(pacote).count(TipoAtivo.LINKEDIN) == 3  # limite de 3 posts por lote
    assert TipoAtivo.NEWSLETTER in tipos(pacote)
    assert TipoAtivo.FAQ not in tipos(pacote)
    assert not pacote.avisos  # 2 formatos: RN05 atendida


def test_exemplo_2_duvidas_viram_faq_e_avisam_rn05(tmp_path):
    ingestao, pacote = processar("02_duvidas_tecnicas.json", tmp_path)
    assert len(ingestao.interacoes) == 5
    assert set(rotas(pacote).values()) == {Rota.FAQ}
    assert tipos(pacote) == [TipoAtivo.FAQ]
    assert len(pacote.ativos[0].fontes) == 5
    assert any("RN05" in a for a in pacote.avisos)


def test_exemplo_3_lote_misto(tmp_path):
    ingestao, pacote = processar("03_lote_misto.csv", tmp_path)

    # ingestão: 3 registros inválidos ficam de fora com o motivo
    motivos = {r.interaction_id: r.motivo for r in ingestao.rejeitadas}
    assert set(motivos) == {"EX3-008", "EX3-001", "EX3-010"}
    assert "text" in motivos["EX3-008"]
    assert "repetido" in motivos["EX3-001"]
    assert "created_at" in motivos["EX3-010"]
    assert len(ingestao.interacoes) == 7

    r = rotas(pacote)
    assert r["EX3-002"] == Rota.IGNORAR  # RN01: positivo SEM consentimento não vira post
    assert r["EX3-006"] == Rota.IGNORAR  # negativo
    assert r["EX3-007"] == Rota.IGNORAR  # operacional
    assert r["EX3-004"] == r["EX3-005"] == Rota.FAQ  # RN02

    fontes_dos_posts = {f for a in pacote.ativos if a.tipo == TipoAtivo.LINKEDIN for f in a.fontes}
    assert fontes_dos_posts == {"EX3-001", "EX3-003"}
    assert set(tipos(pacote)) == {TipoAtivo.LINKEDIN, TipoAtivo.NEWSLETTER, TipoAtivo.FAQ}


@pytest.mark.parametrize("nome", ["01_relatos_positivos.json", "02_duvidas_tecnicas.json", "03_lote_misto.csv"])
def test_exemplos_nascem_pendentes_de_curadoria(nome, tmp_path):
    _, pacote = processar(nome, tmp_path)
    assert all(a.status.value == "pendente" for a in pacote.ativos)  # RN04
