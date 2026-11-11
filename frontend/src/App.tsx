import { useCallback, useEffect, useState } from 'react'
import { api, formatarData, type Pacote, type ResumoPacote, type StatusSistema } from './api'
import { Icone, type NomeIcone } from './icones'
import Curadoria from './visoes/Curadoria'
import Exportacao from './visoes/Exportacao'
import Ingestao from './visoes/Ingestao'
import VisaoGeral from './visoes/VisaoGeral'

export type Visao = 'geral' | 'ingestao' | 'curadoria' | 'exportacao'

interface ItemMenu {
  id: Visao
  nome: string
  icone: NomeIcone
}

const SECOES: { titulo: string; itens: ItemMenu[] }[] = [
  { titulo: 'Painel', itens: [{ id: 'geral', nome: 'Visão geral', icone: 'painel' }] },
  {
    titulo: 'Pipeline',
    itens: [
      { id: 'ingestao', nome: 'Ingestão e upload', icone: 'upload' },
      { id: 'curadoria', nome: 'Curadoria', icone: 'curadoria' },
      { id: 'exportacao', nome: 'Exportação', icone: 'exportar' },
    ],
  },
]

const NOME_VISAO: Record<Visao, string> = {
  geral: 'Visão geral',
  ingestao: 'Ingestão e upload',
  curadoria: 'Curadoria',
  exportacao: 'Exportação',
}

/** O que toda visão recebe para mostrar e trocar o pacote atual. */
export interface PropsVisao {
  pacote: Pacote | null
  pacotes: ResumoPacote[]
  status: StatusSistema | null
  selecionar: (id: string) => void
  aoAlterar: (p: Pacote) => void
  irPara: (v: Visao) => void
}

export default function App() {
  const [visao, setVisao] = useState<Visao>('geral')
  const [status, setStatus] = useState<StatusSistema | null>(null)
  const [pacotes, setPacotes] = useState<ResumoPacote[]>([])
  const [idPacote, setIdPacote] = useState<string | null>(null)
  const [pacote, setPacote] = useState<Pacote | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const recarregarLista = useCallback(async () => {
    const lista = await api.pacotes()
    setPacotes(lista)
    return lista
  }, [])

  useEffect(() => {
    api.status().then(setStatus).catch((e: Error) => setErro(`API indisponível: ${e.message}`))
    recarregarLista()
      .then((lista) => setIdPacote((atual) => atual ?? lista[0]?.id ?? null))
      .catch(() => undefined)
  }, [recarregarLista])

  useEffect(() => {
    if (!idPacote) return setPacote(null)
    api.pacote(idPacote).then(setPacote).catch((e: Error) => setErro(e.message))
  }, [idPacote])

  // Chamado pelas visões quando o pacote muda (edição, aprovação, exportação).
  const aoAlterar = useCallback(
    (novo: Pacote) => {
      setPacote(novo)
      recarregarLista().catch(() => undefined)
    },
    [recarregarLista],
  )

  const aoConcluirProcessamento = useCallback(
    async (id: string) => {
      await recarregarLista()
      setIdPacote(id)
      setVisao('curadoria')
    },
    [recarregarLista],
  )

  const pendentes = pacote?.ativos.filter((a) => a.status === 'pendente').length ?? 0
  const props: PropsVisao = { pacote, pacotes, status, selecionar: setIdPacote, aoAlterar, irPara: setVisao }

  return (
    <div className="layout">
      <aside className="lateral">
        <div className="marca">
          <strong>CommunityLab</strong>
          <span>Curadoria de comunidades</span>
        </div>

        <nav aria-label="Visões">
          {SECOES.map((secao) => (
            <div key={secao.titulo} className="secao">
              <span className="titulo-secao">{secao.titulo}</span>
              {secao.itens.map((v) => (
                <button key={v.id} aria-current={visao === v.id ? 'page' : undefined} onClick={() => setVisao(v.id)}>
                  <Icone nome={v.icone} />
                  <span className="nome">{v.nome}</span>
                  {v.id === 'curadoria' && pendentes > 0 ? (
                    <span className="pendentes" aria-label={`${pendentes} pendentes`}>
                      {pendentes}
                    </span>
                  ) : null}
                </button>
              ))}
            </div>
          ))}
        </nav>

        {status && (
          <div className="rodape">
            <span className="titulo-secao">Integrações</span>
            <div className="integracao">
              <Icone nome="ia" />
              <div>
                <strong>Google Gemini</strong>
                <small>{status.llm.simulado ? 'modo simulado' : (status.llm.modelo ?? 'não configurado')}</small>
              </div>
              <i className={`ponto ${status.llm.configurado && !status.llm.simulado ? 'ok' : 'alerta'}`} />
            </div>
            <div className="integracao">
              <Icone nome="nuvem" />
              <div>
                <strong>OCI Object Storage</strong>
                <small>{status.oci.configurado ? status.oci.bucket : 'não configurado'}</small>
              </div>
              <i className={`ponto ${status.oci.configurado ? 'ok' : 'alerta'}`} />
            </div>
          </div>
        )}
      </aside>

      <div className="conteudo">
        <header className="topo">
          <div className="trilha">
            <span>CommunityLab</span>
            <span aria-hidden="true">/</span>
            <strong>{NOME_VISAO[visao]}</strong>
          </div>
          {visao !== 'ingestao' && <SeletorPacote pacotes={pacotes} pacote={pacote} selecionar={setIdPacote} />}
        </header>

        <main>
          {erro && (
            <div className="erro" role="alert">
              {erro}
            </div>
          )}
          {visao === 'geral' && <VisaoGeral {...props} />}
          {visao === 'ingestao' && <Ingestao status={status} aoConcluir={aoConcluirProcessamento} />}
          {visao === 'curadoria' && <Curadoria {...props} />}
          {visao === 'exportacao' && <Exportacao {...props} />}
        </main>
      </div>
    </div>
  )
}

function SeletorPacote({ pacotes, pacote, selecionar }: Pick<PropsVisao, 'pacotes' | 'pacote' | 'selecionar'>) {
  if (pacotes.length === 0) return null
  return (
    <label className="seletor">
      <span>Pacote</span>
      <select value={pacote?.id ?? ''} onChange={(e) => selecionar(e.target.value)}>
        {pacotes.map((p) => (
          <option key={p.id} value={p.id}>
            {p.arquivo_origem} · {formatarData(p.criado_em)}
          </option>
        ))}
      </select>
    </label>
  )
}
