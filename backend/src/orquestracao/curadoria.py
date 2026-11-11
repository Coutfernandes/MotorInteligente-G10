"""Curadoria humana (RN04): edição, aprovação e exportação somente dos ativos aprovados."""

from datetime import datetime, timezone

from src.ia.geracao.schemas import Ativo, StatusCuradoria, TipoAtivo
from src.orquestracao.schemas import Pacote
from src.armazenamento.repositorio import Repositorio

NOMES_TIPO = {
    TipoAtivo.LINKEDIN: "Post LinkedIn",
    TipoAtivo.NEWSLETTER: "Newsletter",
    TipoAtivo.FAQ: "FAQ / Dica técnica",
}


class AtivoNaoEncontrado(Exception):
    pass


class SemAprovados(Exception):
    """RN04: nada sai do sistema sem pelo menos um ativo aprovado."""


def atualizar_ativo(
    pacote: Pacote,
    ativo_id: str,
    titulo: str | None = None,
    conteudo: str | None = None,
    status: StatusCuradoria | None = None,
) -> Ativo:
    """Edita e/ou muda o status de um ativo.

    Editar um ativo já aprovado devolve ele para pendente: o texto novo precisa de nova aprovação.
    """
    ativo = next((a for a in pacote.ativos if a.id == ativo_id), None)
    if ativo is None:
        raise AtivoNaoEncontrado(ativo_id)

    mudou_texto = (titulo is not None and titulo != ativo.titulo) or (conteudo is not None and conteudo != ativo.conteudo)
    dados = ativo.model_dump()
    if mudou_texto:
        dados.update(
            titulo=titulo if titulo is not None else ativo.titulo,
            conteudo=conteudo if conteudo is not None else ativo.conteudo,
            editado=True,
            status=StatusCuradoria.PENDENTE,
        )
    if status is not None:
        dados["status"] = status

    # Revalida (título vazio, por exemplo, levanta ValidationError).
    novo = Ativo(**dados)
    pacote.ativos = [novo if a.id == ativo_id else a for a in pacote.ativos]
    return novo


def conteudo_exportavel(pacote: Pacote) -> dict:
    """O pacote final, só com os ativos aprovados."""
    if not pacote.aprovados:
        raise SemAprovados("Aprove pelo menos um ativo na curadoria antes de exportar.")
    return {
        "id": pacote.id,
        "arquivo_origem": pacote.arquivo_origem,
        "gerado_em": pacote.criado_em.isoformat(),
        "resumo": pacote.resumo.model_dump(mode="json"),
        "ativos": [a.model_dump(mode="json", exclude={"status"}) for a in pacote.aprovados],
    }


def exportar(pacote: Pacote, repositorio: Repositorio) -> dict:
    """Salva o pacote aprovado no OCI (e localmente) e registra o resultado no pacote."""
    payload = conteudo_exportavel(pacote)
    resultado = repositorio.salvar(pacote.caminho_aprovado, payload)
    pacote.armazenamento["aprovado"] = resultado
    pacote.exportado_em = datetime.now(timezone.utc)
    repositorio.salvar_local(pacote.caminho_gerado, pacote.model_dump(mode="json"))
    return resultado


def como_markdown(pacote: Pacote) -> str:
    """Versão em Markdown do pacote aprovado, para download."""
    payload = conteudo_exportavel(pacote)
    partes = [f"# CommunityLab — pacote {payload['id']}", f"Origem: {payload['arquivo_origem']}"]
    for ativo in pacote.aprovados:
        partes.append(f"---\n\n## {NOMES_TIPO[ativo.tipo]}: {ativo.titulo}\n\n{ativo.conteudo}")
    return "\n\n".join(partes) + "\n"
