import { useEffect, useRef, useState } from 'react'
import { api, type Execucao, type StatusSistema, type Validacao } from '../api'
import { Barras, TituloVisao } from './comuns'

const INTERVALO_CONSULTA_MS = 1500

const ETAPAS = [
  'Lendo e validando o arquivo',
  'Análise de sentimento e tópicos (Gemini)',
  'Aplicando regras de negócio RN01 · RN02',
  'Gerando posts, FAQ e newsletter (RN05 · RN06)',
  'Salvando no OCI Object Storage (RN03)',
  'Enviando para a fila de curadoria (RN04)',
]

/** Quantas etapas já terminaram, a partir do estado da tela e do processamento. */
function etapasConcluidas(validacao: Validacao | null, execucao: Execucao | null): number {
  if (!validacao) return 0
  if (!execucao) return 1
  if (execucao.status === 'concluido') return ETAPAS.length
  return { iniciando: 1, analise: 1, geracao: 3, salvando: 4 }[execucao.etapa]
}

interface Props {
  status: StatusSistema | null
  aoConcluir: (idPacote: string) => void
}

export default function Ingestao({ status, aoConcluir }: Props) {
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [validacao, setValidacao] = useState<Validacao | null>(null)
  const [execucao, setExecucao] = useState<Execucao | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [arrastando, setArrastando] = useState(false)
  const entrada = useRef<HTMLInputElement>(null)

  async function escolher(novo: File | undefined) {
    if (!novo) return
    setArquivo(novo)
    setValidacao(null)
    setExecucao(null)
    setErro(null)
    try {
      setValidacao(await api.validar(novo))
    } catch (e) {
      setErro((e as Error).message)
    }
  }

  async function usarExemplo() {
    try {
      await escolher(await api.arquivoExemplo())
    } catch (e) {
      setErro((e as Error).message)
    }
  }

  async function processar() {
    if (!arquivo) return
    setErro(null)
    try {
      setExecucao(await api.processar(arquivo))
    } catch (e) {
      setErro((e as Error).message)
    }
  }

  // Acompanha o processamento até terminar.
  useEffect(() => {
    if (!execucao || execucao.status !== 'processando') return
    const relogio = setTimeout(async () => {
      try {
        const atual = await api.execucao(execucao.id)
        setExecucao(atual)
        if (atual.status === 'concluido') aoConcluir(atual.id)
        if (atual.status === 'erro') setErro(atual.erro ?? 'Falha no processamento.')
      } catch (e) {
        setErro((e as Error).message)
      }
    }, INTERVALO_CONSULTA_MS)
    return () => clearTimeout(relogio)
  }, [execucao, aoConcluir])

  const processando = execucao?.status === 'processando'
  const semIA = status !== null && !status.llm.configurado
  const concluidas = etapasConcluidas(validacao, execucao)
  const percentual = Math.round((concluidas / ETAPAS.length) * 100)

  function detalheDaEtapa(indice: number): string | null {
    if (!execucao || !processando || indice !== concluidas || execucao.total === 0) return null
    return `${execucao.atual} de ${execucao.total}`
  }

  return (
    <>
      <TituloVisao
        sobretitulo="Ingestão"
        titulo="Ingestão e upload"
        descricao="Envie as interações da comunidade. O arquivo é validado antes de gastar cota da IA."
      />

      <div className="grade principal">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div
            className={`area-upload ${arrastando ? 'ativa' : ''}`}
            role="button"
            tabIndex={0}
            onClick={() => !processando && entrada.current?.click()}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && !processando && entrada.current?.click()}
            onDragOver={(e) => {
              e.preventDefault()
              setArrastando(true)
            }}
            onDragLeave={() => setArrastando(false)}
            onDrop={(e) => {
              e.preventDefault()
              setArrastando(false)
              if (!processando) escolher(e.dataTransfer.files[0])
            }}
          >
            <strong>Arraste seu arquivo aqui</strong>
            <span>ou clique para escolher · formatos aceitos</span>
            <span className="acoes">
              <span className="formato">.json</span>
              <span className="formato">.csv</span>
            </span>
            {arquivo && <span className="arquivo">{arquivo.name}</span>}
            <input
              ref={entrada}
              type="file"
              accept=".json,.csv"
              hidden
              onChange={(e) => {
                escolher(e.target.files?.[0])
                e.target.value = ''
              }}
            />
          </div>
          <p className="apoio">
            Colunas obrigatórias: <code>interaction_id</code>, <code>channel</code>, <code>interaction_type</code>,{' '}
            <code>created_at</code>, <code>text</code>. Opcionais: <code>consent_marketing</code>, <code>reactions</code>. Até 5 MB.
          </p>

          <div className="acoes" style={{ flexWrap: 'nowrap' }}>
            <button className="botao neutro" onClick={usarExemplo} disabled={processando}>
              Usar dados de exemplo
            </button>
            <button
              className="botao largo"
              onClick={processar}
              disabled={!validacao || processando || semIA || validacao.total_validas === 0}
            >
              {processando ? 'Processando…' : 'Processar pipeline de IA'}
            </button>
          </div>

          {semIA && (
            <div className="aviso">
              <strong>Gemini não configurado</strong>
              <small>Preencha GOOGLE_API_KEY e LLM_MODEL no .env, ou rode a API com LLM_PROVIDER=simulado.</small>
            </div>
          )}
          {erro && (
            <div className="erro" role="alert">
              {erro}
            </div>
          )}
        </div>

        <section className="cartao">
          <h3>Pipeline Python · LangGraph</h3>
          <p className="apoio">
            {!validacao
              ? 'Aguardando arquivo para iniciar.'
              : processando
                ? 'Processando…'
                : execucao?.status === 'concluido'
                  ? 'Concluído. Abrindo a curadoria.'
                  : status?.llm.simulado
                    ? 'Modo simulado: respostas fixas, sem gastar cota.'
                    : 'Cerca de 5 s por mensagem, para respeitar a cota gratuita do Gemini.'}
          </p>
          <div className="progresso" role="progressbar" aria-valuenow={percentual} aria-valuemin={0} aria-valuemax={100}>
            <div style={{ width: `${percentual}%` }} />
          </div>
          <ol className="etapas">
            {ETAPAS.map((nome, i) => {
              const estado = i < concluidas ? 'feita' : i === concluidas && processando ? 'atual' : ''
              return (
                <li key={nome} className={estado}>
                  <span className="marcador">{i < concluidas ? '✓' : i + 1}</span>
                  <span>
                    {nome}
                    {detalheDaEtapa(i) && <small>{detalheDaEtapa(i)}</small>}
                  </span>
                </li>
              )
            })}
          </ol>
        </section>
      </div>

      {validacao && (
        <>
          <div className={validacao.rejeitadas.length ? 'aviso' : 'sucesso'}>
            <strong>
              {validacao.arquivo}: {validacao.total_validas} interação(ões) válida(s)
              {validacao.rejeitadas.length > 0 && `, ${validacao.rejeitadas.length} rejeitada(s)`}
            </strong>
            <small>
              {validacao.com_consentimento} com consentimento de marketing.
              {validacao.rejeitadas.length > 0 && ' As rejeitadas ficam de fora do processamento.'}
            </small>
          </div>

          {validacao.rejeitadas.length > 0 && (
            <section className="cartao">
              <h3 style={{ marginBottom: 10 }}>Registros rejeitados</h3>
              <div className="tabela-rolagem">
                <table>
                  <thead>
                    <tr>
                      <th>Posição</th>
                      <th>ID</th>
                      <th>Motivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {validacao.rejeitadas.map((r) => (
                      <tr key={r.posicao}>
                        <td>{r.posicao}</td>
                        <td>{r.interaction_id ?? '—'}</td>
                        <td className="texto">{r.motivo}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <div className="grade duas">
            <section className="cartao">
              <h3 style={{ marginBottom: 14 }}>Por tipo de interação</h3>
              <Barras itens={Object.entries(validacao.por_tipo).map(([rotulo, valor]) => ({ rotulo, valor }))} />
            </section>
            <section className="cartao">
              <h3 style={{ marginBottom: 14 }}>Por canal</h3>
              <Barras itens={Object.entries(validacao.por_canal).map(([rotulo, valor]) => ({ rotulo, valor }))} />
            </section>
          </div>
        </>
      )}
    </>
  )
}
