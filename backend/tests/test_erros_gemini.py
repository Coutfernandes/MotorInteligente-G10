"""T03: o pipeline aguenta o Gemini sobrecarregado (503) ou sem cota (429) sem parar tudo."""

from pathlib import Path

import pytest
from langchain_core.exceptions import OutputParserException

from src.armazenamento.repositorio import Repositorio
from src.ia import llm
from src.ia.analise import sentimento
from src.ia.analise.schemas import MensagemRoteada, ResumoComunidade, RespostaLLM, Rota
from src.ia.geracao import geradores
from src.ia.geracao.schemas import ConteudoGerado, TipoAtivo
from src.ia.llm_simulado import LLMSimulado
from src.ingestao.leitor import carregar_arquivo
from src.orquestracao.pipeline import executar_pipeline

AMOSTRA = Path(__file__).parent / "fixtures" / "amostra_5.json"


class ErroGemini(Exception):
    """Imita o erro da biblioteca do Google, que traz o código HTTP no atributo `code`."""

    def __init__(self, code: int, mensagem: str = ""):
        super().__init__(f"{code} {mensagem}")
        self.code = code


SOBRECARGA = ErroGemini(503, "UNAVAILABLE. This model is currently experiencing high demand.")
SEM_COTA = ErroGemini(429, "RESOURCE_EXHAUSTED")


class Falso:
    """Devolve (ou levanta) as respostas na ordem dada."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = 0

    def invoke(self, _mensagens):
        self.chamadas += 1
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


class FalhaEmUmTexto:
    """Usa o LLM simulado, mas responde sempre 503 para a mensagem que contém `texto`."""

    def __init__(self, base, texto):
        self.base, self.texto = base, texto

    def invoke(self, mensagens):
        if self.texto in mensagens[-1].content:
            raise SOBRECARGA
        return self.base.invoke(mensagens)


def resposta_valida():
    return RespostaLLM(sentimento="positivo", topicos=["ia"], relevancia=70, insight="ok")


@pytest.fixture(autouse=True)
def sem_espera_real(monkeypatch):
    """Nos testes, as esperas de 15 s e 30 s não dormem de verdade."""
    monkeypatch.setattr(llm, "ESPERAS_ERRO_TEMPORARIO", (0.0, 0.0))


# ---- quais erros contam como temporários ----

@pytest.mark.parametrize(
    "erro, esperado",
    [
        (SOBRECARGA, True),
        (SEM_COTA, True),
        (Exception("503 UNAVAILABLE. {'error': {'code': 503}}"), True),  # erro só com a mensagem
        (ErroGemini(400, "API key not valid"), False),
        (ErroGemini(404, "model not found"), False),
        (OutputParserException("formato errado"), False),
        (ValueError("qualquer outra coisa"), False),
    ],
)
def test_classifica_erros_temporarios(erro, esperado):
    assert llm.erro_temporario(erro) is esperado


# ---- espera e nova tentativa ----

def test_espera_e_tenta_de_novo_ate_funcionar():
    falso = Falso([SOBRECARGA, SEM_COTA, "ok"])
    pausas = []
    assert llm.chamar_com_espera(lambda: falso.invoke(None), pausas.append, esperas=(15.0, 30.0)) == "ok"
    assert pausas == [15.0, 30.0]
    assert falso.chamadas == 3


def test_erro_definitivo_nao_espera():
    falso = Falso([ErroGemini(400, "API key not valid")])
    pausas = []
    with pytest.raises(ErroGemini):
        llm.chamar_com_espera(lambda: falso.invoke(None), pausas.append, esperas=(15.0, 30.0))
    assert pausas == []


def test_analise_se_recupera_de_um_503():
    registro = carregar_arquivo(AMOSTRA).registros[0]
    analise = sentimento.analisar_interacao(registro, Falso([SOBRECARGA, resposta_valida()]), esperar=lambda s: None)
    assert analise.interaction_id == registro["interaction_id"]


def test_analise_desiste_depois_das_esperas():
    registro = carregar_arquivo(AMOSTRA).registros[0]
    falso = Falso([SOBRECARGA, SOBRECARGA, SOBRECARGA])
    with pytest.raises(sentimento.FalhaNaAnalise):
        sentimento.analisar_interacao(registro, falso, esperar=lambda s: None)
    assert falso.chamadas == 3  # 1 chamada + 2 novas tentativas


def test_lote_pula_so_a_mensagem_que_falhou():
    registros = carregar_arquivo(AMOSTRA).registros
    analisador = FalhaEmUmTexto(LLMSimulado().with_structured_output(RespostaLLM), registros[1]["text"])
    analises = sentimento.analisar_lote(registros, analisador, intervalo=0, esperar=lambda s: None)
    ids = [a.interaction_id for a in analises]
    assert len(ids) == len(registros) - 1
    assert registros[1]["interaction_id"] not in ids


def test_chave_invalida_para_o_lote_na_hora():
    registros = carregar_arquivo(AMOSTRA).registros
    with pytest.raises(ErroGemini):
        sentimento.analisar_lote(registros, Falso([ErroGemini(400, "API key not valid")]), intervalo=0, esperar=lambda s: None)


# ---- geração ----

def test_geracao_pula_so_o_ativo_que_falhou():
    mensagens = [
        MensagemRoteada(
            interaction_id="INT-1", tipo="depoimento", sentimento="positivo", topicos=["ia"], relevancia=80,
            insight="x", consent_marketing=True, rota=Rota.CASE, motivo="teste",
        ),
        MensagemRoteada(
            interaction_id="INT-2", tipo="pergunta_tecnica", sentimento="neutro", topicos=["ia"], relevancia=60,
            insight="x", consent_marketing=False, rota=Rota.FAQ, motivo="teste",
        ),
    ]
    resumo = ResumoComunidade(
        total_interacoes_processadas=2, sentimento_predominante="positivo",
        topicos_principais=["ia"], contagem_por_rota={r: 0 for r in Rota},
    )
    conteudo = ConteudoGerado(titulo="Título", conteudo="Texto")
    # post ok; newsletter falha 3 vezes (503); FAQ ok
    gerador = Falso([conteudo, SOBRECARGA, SOBRECARGA, SOBRECARGA, conteudo])
    pulados = []
    ativos = geradores.gerar_ativos(
        mensagens, [{"interaction_id": m.interaction_id, "text": "t"} for m in mensagens], resumo, gerador,
        esperar=lambda s: None, ao_falhar=pulados.append,
    )
    assert [a.tipo for a in ativos] == [TipoAtivo.LINKEDIN, TipoAtivo.FAQ]
    assert len(pulados) == 1 and "newsletter" in pulados[0]


# ---- pipeline completo ----

class OCIFalso:
    bucket_name = "bucket-teste"

    def configurado(self):
        return True

    def upload_json(self, caminho, payload):
        return {"status": "sucesso", "caminho_objeto": caminho}


def test_pipeline_continua_e_avisa_quando_uma_mensagem_falha(tmp_path):
    registros = carregar_arquivo(AMOSTRA).registros
    simulado = LLMSimulado()
    pacote = executar_pipeline(
        registros, "amostra_5.json",
        analisador=FalhaEmUmTexto(simulado.with_structured_output(RespostaLLM), registros[0]["text"]),
        gerador=simulado.with_structured_output(ConteudoGerado),
        repositorio=Repositorio(tmp_path, OCIFalso()),
        intervalo=0,
    )
    assert pacote.resumo.total_interacoes_processadas == len(registros) - 1
    assert any("1 mensagem(ns) não puderam ser analisadas" in a for a in pacote.avisos)
    assert pacote.ativos  # o resto do lote gerou conteúdo normalmente
