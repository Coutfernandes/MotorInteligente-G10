import { useState } from 'react'
import {
  api,
  NOME_STATUS,
  NOME_TIPO_ATIVO,
  TOM_DE_VOZ,
  type Ativo,
  type Pacote,
  type StatusCuradoria,
  type TipoAtivo,
} from '../api'
import type { PropsVisao } from '../App'
import { SemPacote, TituloVisao } from './comuns'

const TIPOS: TipoAtivo[] = ['linkedin', 'faq', 'newsletter']
const REGRAS: Record<TipoAtivo, string> = { linkedin: 'RN01 · RN06', newsletter: 'RN01 · RN06', faq: 'RN02 · RN06' }
const ORIGEM: Record<TipoAtivo, string> = {
  linkedin: 'a partir de um relato positivo com consentimento',
  newsletter: 'a partir dos relatos positivos do lote',
  faq: 'a partir das dúvidas e relatos neutros do lote',
}

type FiltroStatus = StatusCuradoria | 'todos'
const FILTROS: { id: FiltroStatus; nome: string }[] = [
  { id: 'pendente', nome: 'Aguardando' },
  { id: 'aprovado', nome: 'Aprovados' },
  { id: 'rejeitado', nome: 'Rejeitados' },
  { id: 'todos', nome: 'Todos' },
]

export default function Curadoria({ pacote, aoAlterar, irPara }: PropsVisao) {
  const [tipo, setTipo] = useState<TipoAtivo | 'todos'>('todos')
  const [filtro, setFiltro] = useState<FiltroStatus>('pendente')

  const titulo = (
    <TituloVisao
      sobretitulo="Curadoria"
      titulo="Curadoria e aprovação"
      descricao="Revise cada conteúdo gerado pela IA. Ajuste o texto se precisar e decida o que segue para publicação."
    />
  )

  if (!pacote) {
    return (
      <>
        {titulo}
        <SemPacote irPara={irPara} />
      </>
    )
  }

  const doTipo = pacote.ativos.filter((a) => tipo === 'todos' || a.tipo === tipo)
  const visiveis = doTipo.filter((a) => filtro === 'todos' || a.status === filtro)
  const aprovados = pacote.ativos.filter((a) => a.status === 'aprovado').length

  return (
    <>
      {titulo}

      <div className="aviso">
        <strong>Nenhum conteúdo é publicado sem aprovação humana nesta tela.</strong>
        <small>Regra de negócio RN04: só ativos com status "Aprovado" entram no pacote de exportação.</small>
      </div>

      <div className="filtros">
        <div className="abas" role="group" aria-label="Tipo de conteúdo">
          <button aria-pressed={tipo === 'todos'} onClick={() => setTipo('todos')}>
            Todos <span className="qtd">{pacote.ativos.length}</span>
          </button>
          {TIPOS.map((t) => (
            <button key={t} aria-pressed={tipo === t} onClick={() => setTipo(t)}>
              {NOME_TIPO_ATIVO[t]} <span className="qtd">{pacote.ativos.filter((a) => a.tipo === t).length}</span>
            </button>
          ))}
        </div>
        <div className="abas escuras" role="group" aria-label="Status">
          {FILTROS.map((f) => (
            <button key={f.id} aria-pressed={filtro === f.id} onClick={() => setFiltro(f.id)}>
              {f.nome}
            </button>
          ))}
        </div>
      </div>

      <div className="acoes" style={{ justifyContent: 'space-between' }}>
        <p className="apoio">
          {tipo === 'todos'
            ? `${aprovados} de ${pacote.ativos.length} aprovado(s).`
            : `Tom ${TOM_DE_VOZ[tipo].toLowerCase()}, ${ORIGEM[tipo]} (${REGRAS[tipo]}).`}
        </p>
        {aprovados > 0 && (
          <button className="botao secundario pequeno" onClick={() => irPara('exportacao')}>
            Ir para exportação ({aprovados})
          </button>
        )}
      </div>

      {visiveis.length === 0 ? (
        <div className="cartao vazio">
          <p>
            {pacote.ativos.length === 0
              ? pacote.avisos.join(' ') || 'Nenhum conteúdo foi gerado neste pacote.'
              : 'Nenhum conteúdo neste filtro.'}
          </p>
        </div>
      ) : (
        <div className="cartoes-ativos">
          {visiveis.map((a) => (
            <CartaoAtivo key={a.id} ativo={a} pacote={pacote} aoAlterar={aoAlterar} />
          ))}
        </div>
      )}
    </>
  )
}

function CartaoAtivo({ ativo, pacote, aoAlterar }: { ativo: Ativo; pacote: Pacote; aoAlterar: (p: Pacote) => void }) {
  const [editando, setEditando] = useState(false)
  const [titulo, setTitulo] = useState(ativo.titulo)
  const [conteudo, setConteudo] = useState(ativo.conteudo)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const alterado = titulo !== ativo.titulo || conteudo !== ativo.conteudo
  const fontes = pacote.mensagens.filter((m) => ativo.fontes.includes(m.interaction_id))

  async function salvar(status?: StatusCuradoria) {
    setSalvando(true)
    setErro(null)
    try {
      const edicao = { ...(editando && alterado ? { titulo, conteudo } : {}), ...(status ? { status } : {}) }
      const novo = await api.editarAtivo(pacote.id, ativo.id, edicao)
      setEditando(false)
      aoAlterar({ ...pacote, ativos: pacote.ativos.map((a) => (a.id === novo.id ? novo : a)) })
    } catch (e) {
      setErro((e as Error).message)
    } finally {
      setSalvando(false)
    }
  }

  function cancelar() {
    setTitulo(ativo.titulo)
    setConteudo(ativo.conteudo)
    setEditando(false)
  }

  return (
    <article className={`ativo ${ativo.status}`}>
      <header>
        <div className="etiquetas">
          <span className="etiqueta verde">{NOME_TIPO_ATIVO[ativo.tipo]}</span>
          <span className="etiqueta">{ativo.editado ? 'Editado' : 'Gerado por IA'}</span>
          <span className={`etiqueta ${ativo.status}`}>{NOME_STATUS[ativo.status]}</span>
        </div>
        <span className="etiqueta mono">{REGRAS[ativo.tipo]}</span>
      </header>

      <div className="corpo">
        {editando ? (
          <>
            <label className="campo">
              Título
              <input type="text" value={titulo} maxLength={120} onChange={(e) => setTitulo(e.target.value)} />
            </label>
            <label className="campo">
              Conteúdo <span className="apoio">{conteudo.length} caracteres</span>
              <textarea value={conteudo} onChange={(e) => setConteudo(e.target.value)} />
            </label>
            {ativo.status === 'aprovado' && alterado && (
              <p className="apoio">Salvar a edição devolve o conteúdo para "Aguardando": ele precisa ser aprovado de novo.</p>
            )}
          </>
        ) : (
          <>
            <h3>{ativo.titulo}</h3>
            <p className="texto-ativo">{ativo.conteudo}</p>
          </>
        )}
        <p className="fonte">
          Fonte:{' '}
          {fontes.map((m, i) => (
            <span key={m.interaction_id} title={m.insight}>
              {i > 0 && ', '}
              <b>{m.interaction_id}</b> · {m.tipo}
            </span>
          ))}
        </p>
        {erro && (
          <div className="erro" role="alert">
            {erro}
          </div>
        )}
      </div>

      <footer>
        {editando ? (
          <>
            <div className="acoes">
              <button className="botao pequeno" disabled={salvando} onClick={() => salvar('aprovado')}>
                Salvar e aprovar
              </button>
              <button className="botao neutro pequeno" disabled={salvando || !alterado} onClick={() => salvar()}>
                Salvar
              </button>
            </div>
            <button className="botao neutro pequeno" disabled={salvando} onClick={cancelar}>
              Cancelar
            </button>
          </>
        ) : (
          <>
            <div className="acoes">
              {ativo.status !== 'aprovado' && (
                <button className="botao pequeno" disabled={salvando} onClick={() => salvar('aprovado')}>
                  Aprovar
                </button>
              )}
              <button className="botao secundario pequeno" disabled={salvando} onClick={() => setEditando(true)}>
                Editar
              </button>
              {ativo.status !== 'pendente' && (
                <button className="botao neutro pequeno" disabled={salvando} onClick={() => salvar('pendente')}>
                  Voltar para aguardando
                </button>
              )}
            </div>
            {ativo.status !== 'rejeitado' && (
              <button className="botao perigo pequeno" disabled={salvando} onClick={() => salvar('rejeitado')}>
                Rejeitar
              </button>
            )}
          </>
        )}
      </footer>
    </article>
  )
}
