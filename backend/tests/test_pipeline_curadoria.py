import json
from pathlib import Path

import pytest

from src.ia.llm_simulado import LLMSimulado
from src.ia.analise.schemas import RespostaLLM
from src.ia.geracao.schemas import ConteudoGerado, StatusCuradoria, TipoAtivo
from src.ingestao.leitor import carregar_arquivo
from src.orquestracao import curadoria
from src.orquestracao.pipeline import executar_pipeline
from src.armazenamento.repositorio import Repositorio

AMOSTRA = Path(__file__).parent / "fixtures" / "amostra_5.json"


class OCIFalso:
    def __init__(self, configurado=True):
        self._configurado = configurado
        self.envios = []
        self.bucket_name = "bucket-teste"

    def configurado(self):
        return self._configurado

    def upload_json(self, caminho, payload):
        self.envios.append((caminho, payload))
        return {"status": "sucesso", "caminho_objeto": caminho}


@pytest.fixture
def oci():
    return OCIFalso()


@pytest.fixture
def pacote(tmp_path, oci):
    simulado = LLMSimulado()
    return executar_pipeline(
        carregar_arquivo(AMOSTRA).registros,
        "amostra_5.json",
        analisador=simulado.with_structured_output(RespostaLLM),
        gerador=simulado.with_structured_output(ConteudoGerado),
        repositorio=Repositorio(tmp_path, oci),
        intervalo=0,
    )


# ---- pipeline (F08) ----

def test_pipeline_gera_pelo_menos_2_formatos(pacote):
    # RN05
    assert {TipoAtivo.LINKEDIN, TipoAtivo.FAQ} <= {a.tipo for a in pacote.ativos}
    assert pacote.resumo.total_interacoes_processadas == 5
    assert pacote.avisos == []


def test_pipeline_salva_pacote_gerado_na_oci(pacote, oci, tmp_path):
    # RN03
    assert oci.envios[0][0] == f"pacotes/{pacote.id}.json"
    assert pacote.armazenamento["gerado"]["oci"]["status"] == "sucesso"
    salvo = json.loads((tmp_path / "pacotes" / f"{pacote.id}.json").read_text(encoding="utf-8"))
    assert salvo["armazenamento"]["gerado"]["oci"]["status"] == "sucesso"


def test_sem_oci_configurada_salva_local_e_avisa(tmp_path):
    simulado = LLMSimulado()
    pacote = executar_pipeline(
        carregar_arquivo(AMOSTRA).registros, "amostra_5.json",
        analisador=simulado.with_structured_output(RespostaLLM),
        gerador=simulado.with_structured_output(ConteudoGerado),
        repositorio=Repositorio(tmp_path, OCIFalso(configurado=False)), intervalo=0,
    )
    assert pacote.armazenamento["gerado"]["oci"]["status"] == "nao_configurado"
    assert (tmp_path / "pacotes" / f"{pacote.id}.json").is_file()


def test_pipeline_avisa_quando_nao_atinge_2_formatos(tmp_path):
    simulado = LLMSimulado()
    so_duvidas = [r for r in carregar_arquivo(AMOSTRA).registros if r["interaction_type"] == "pergunta_tecnica"]
    pacote = executar_pipeline(
        so_duvidas, "duvidas.json",
        analisador=simulado.with_structured_output(RespostaLLM),
        gerador=simulado.with_structured_output(ConteudoGerado),
        repositorio=Repositorio(tmp_path, OCIFalso()), intervalo=0,
    )
    assert "RN05" in pacote.avisos[0]


# ---- curadoria (RN04) ----

def test_nada_exporta_sem_aprovacao(pacote, oci, tmp_path):
    with pytest.raises(curadoria.SemAprovados):
        curadoria.exportar(pacote, Repositorio(tmp_path, oci))
    with pytest.raises(curadoria.SemAprovados):
        curadoria.como_markdown(pacote)


def test_exporta_somente_aprovados(pacote, oci, tmp_path):
    aprovado, rejeitado = pacote.ativos[0], pacote.ativos[1]
    curadoria.atualizar_ativo(pacote, aprovado.id, status=StatusCuradoria.APROVADO)
    curadoria.atualizar_ativo(pacote, rejeitado.id, status=StatusCuradoria.REJEITADO)

    curadoria.exportar(pacote, Repositorio(tmp_path, oci))

    caminho, enviado = oci.envios[-1]
    assert caminho == f"aprovados/{pacote.id}.json"
    assert [a["id"] for a in enviado["ativos"]] == [aprovado.id]
    assert pacote.exportado_em is not None
    assert pacote.armazenamento["aprovado"]["oci"]["status"] == "sucesso"


def test_editar_ativo_aprovado_volta_para_pendente(pacote):
    ativo = pacote.ativos[0]
    curadoria.atualizar_ativo(pacote, ativo.id, status=StatusCuradoria.APROVADO)

    editado = curadoria.atualizar_ativo(pacote, ativo.id, conteudo="Texto revisado")

    assert editado.status == StatusCuradoria.PENDENTE
    assert editado.editado is True
    assert pacote.ativos[0].conteudo == "Texto revisado"


def test_editar_e_aprovar_na_mesma_acao(pacote):
    ativo = curadoria.atualizar_ativo(pacote, pacote.ativos[0].id, titulo="Novo", status=StatusCuradoria.APROVADO)
    assert ativo.status == StatusCuradoria.APROVADO
    assert ativo.titulo == "Novo"


def test_markdown_tem_so_os_aprovados(pacote):
    curadoria.atualizar_ativo(pacote, pacote.ativos[0].id, titulo="Aprovado", status=StatusCuradoria.APROVADO)
    texto = curadoria.como_markdown(pacote)
    assert "Aprovado" in texto
    assert pacote.ativos[1].titulo not in texto


def test_ativo_inexistente(pacote):
    with pytest.raises(curadoria.AtivoNaoEncontrado):
        curadoria.atualizar_ativo(pacote, "nao-existe", status=StatusCuradoria.APROVADO)
