"""LLM simulado (LLM_PROVIDER=simulado): testa a aplicação inteira sem chave e sem gastar cota.

As respostas são regras fixas, marcadas com [Simulado]. Não servem como conteúdo real.
"""

import re

from src.ia.analise.schemas import RespostaLLM
from src.ia.geracao.schemas import ConteudoGerado

# tipo da interação -> (sentimento, relevância)
POR_TIPO = {
    "depoimento": ("muito_positivo", 85),
    "entrega_projeto": ("positivo", 80),
    "feedback_positivo": ("positivo", 65),
    "debate": ("neutro", 55),
    "pergunta_tecnica": ("neutro", 70),
    "pedido_ajuda": ("negativo", 60),
    "feedback_negativo": ("negativo", 55),
    "mensagem_operacional": ("neutro", 10),
}

# palavra no texto -> tópico
PALAVRAS_TOPICO = {
    "langgraph": "langgraph",
    "langchain": "langchain",
    "rag": "rag",
    "oci": "oci",
    "vaga": "contratacao",
    "estágio": "contratacao",
    "portf": "portfolio",
    "prompt": "prompts",
    "agente": "agentes",
    "n8n": "n8n",
    "dados": "dados",
    "projeto": "projeto_pratico",
}

NOMES_ATIVO = {"LinkedIn": "Post LinkedIn", "newsletter": "Newsletter", "FAQ": "FAQ"}


def _campo(texto: str, nome: str) -> str:
    achado = re.search(rf"^{nome}: (.*)$", texto, re.MULTILINE)
    return achado.group(1) if achado else ""


class _Estruturado:
    def __init__(self, schema):
        self.schema = schema

    def invoke(self, mensagens):
        sistema, pedido = mensagens[0].content, mensagens[1].content
        if self.schema is RespostaLLM:
            return self._analise(pedido)
        if self.schema is ConteudoGerado:
            return self._conteudo(sistema, pedido)
        raise ValueError(f"Schema não suportado no modo simulado: {self.schema.__name__}")

    def _analise(self, pedido: str) -> RespostaLLM:
        texto = _campo(pedido, "Texto")
        sentimento, relevancia = POR_TIPO.get(_campo(pedido, "Tipo"), ("neutro", 40))
        topicos = [t for p, t in PALAVRAS_TOPICO.items() if p in texto.lower()]
        return RespostaLLM(
            sentimento=sentimento,
            topicos=list(dict.fromkeys(topicos))[:3] or ["comunidade"],
            relevancia=relevancia,
            insight=f"[Simulado] {texto[:150]}",
        )

    def _conteudo(self, sistema: str, pedido: str) -> ConteudoGerado:
        nome = next((n for chave, n in NOMES_ATIVO.items() if chave in sistema.splitlines()[1]), "Conteúdo")
        textos = re.findall(r"^Texto: (.*)$", pedido, re.MULTILINE)
        trechos = "\n".join(f"- {t[:160]}" for t in textos)
        return ConteudoGerado(
            titulo=f"[Simulado] {nome}",
            conteudo=(
                f"Conteúdo SIMULADO, gerado sem o Gemini, só para testar a interface.\n\n"
                f"Mensagens usadas ({len(textos)}):\n{trechos}"
            ),
        )


class LLMSimulado:
    def with_structured_output(self, schema):
        return _Estruturado(schema)
