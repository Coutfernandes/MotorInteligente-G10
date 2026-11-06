import { NOME_ROTA, NOME_SENTIMENTO, formatarData, type Rota, type Sentimento } from '../api'
import type { PropsVisao } from '../App'
import { Icone, type NomeIcone } from '../icones'
import { Barras, Colunas, Rosca, SemPacote, TituloVisao } from './comuns'

const ORDEM_SENTIMENTO: Sentimento[] = ['muito_positivo', 'positivo', 'neutro', 'negativo', 'muito_negativo']
const ORDEM_ROTA: Rota[] = ['case', 'linkedin', 'faq', 'ignorar']

function Indicador({ icone, valor, rotulo, tom }: { icone: NomeIcone; valor: number | string; rotulo: string; tom: string }) {
  return (
    <div className="indicador">
      <span className={`icone-indicador ${tom}`}>
        <Icone nome={icone} tamanho={20} />
      </span>
      <div>
        <strong>{valor}</strong>
        <span>{rotulo}</span>
      </div>
    </div>
  )
}

export default function VisaoGeral({ pacote, pacotes, status, selecionar, irPara }: PropsVisao) {
  const titulo = (
    <TituloVisao
      sobretitulo="Visão geral"
      titulo="Painel do pipeline"
      descricao="Resumo do que a IA leu e gerou a partir das conversas da comunidade."
    >
      <button className="botao" onClick={() => irPara('ingestao')}>
        <Icone nome="upload" tamanho={16} /> Enviar novos dados
      </button>
    </TituloVisao>
  )

  if (!pacote) {
    return (
      <>
        {titulo}
        <SemPacote irPara={irPara} />
      </>
    )
  }

  const { resumo, mensagens, ativos } = pacote
  const porStatus = (s: string) => ativos.filter((a) => a.status === s).length
  const porTipo = (t: string) => ativos.filter((a) => a.tipo === t).length
  const porRota = (r: Rota) => resumo.contagem_por_rota[r] ?? 0
  const aprovados = porStatus('aprovado')
  const pendentes = porStatus('pendente')
  const rejeitados = porStatus('rejeitado')
  const exportados = pacotes.filter((p) => p.exportado_em)

  return (
    <>
      {titulo}

      {pacote.avisos.map((aviso) => (
        <div key={aviso} className="aviso">
          {aviso}
        </div>
      ))}

      <div className="grade indicadores">
        <Indicador icone="mensagens" valor={resumo.total_interacoes_processadas} rotulo="Mensagens" tom="tom-1" />
        <Indicador icone="post" valor={porTipo('linkedin')} rotulo="Posts LinkedIn" tom="tom-2" />
        <Indicador icone="faq" valor={porTipo('faq')} rotulo="FAQ" tom="tom-3" />
        <Indicador icone="newsletter" valor={porTipo('newsletter')} rotulo="Newsletter" tom="tom-4" />
        <Indicador icone="aprovado" valor={aprovados} rotulo="Aprovados" tom="tom-5" />
      </div>

      <div className="grade principal">
        <section className="cartao">
          <div className="cartao-topo">
            <div>
              <h3>Sentimento das mensagens</h3>
              <p className="apoio">
                {pacote.arquivo_origem}
                {pacote.rejeitadas_ingestao.length > 0 && ` · ${pacote.rejeitadas_ingestao.length} descartada(s) na ingestão`}
              </p>
            </div>
          </div>
          <div className="grafico-com-resumo">
            <Colunas
              itens={ORDEM_SENTIMENTO.map((s) => ({
                rotulo: NOME_SENTIMENTO[s],
                valor: mensagens.filter((m) => m.sentimento === s).length,
              }))}
            />
            <div className="resumo-lateral">
              <div>
                <span className="icone-indicador pequeno tom-2">
                  <Icone nome="post" tamanho={16} />
                </span>
                <div>
                  <small>Viram post ou case · RN01</small>
                  <strong>{porRota('case') + porRota('linkedin')}</strong>
                </div>
              </div>
              <div>
                <span className="icone-indicador pequeno tom-3">
                  <Icone nome="faq" tamanho={16} />
                </span>
                <div>
                  <small>Viram FAQ · RN02</small>
                  <strong>{porRota('faq')}</strong>
                </div>
              </div>
              <div>
                <span className="icone-indicador pequeno tom-neutro">
                  <Icone nome="mensagens" tamanho={16} />
                </span>
                <div>
                  <small>Sem destino</small>
                  <strong>{porRota('ignorar')}</strong>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="cartao">
          <div className="cartao-topo">
            <div>
              <h3>Fila de curadoria</h3>
              <p className="apoio">Aprovação humana obrigatória · RN04</p>
            </div>
          </div>
          <Rosca
            centro={String(ativos.length)}
            legendaCentro="ativos gerados"
            fatias={[
              { rotulo: 'Aprovados', valor: aprovados, classe: 'cor-aprovado' },
              { rotulo: 'Aguardando', valor: pendentes, classe: 'cor-pendente' },
              { rotulo: 'Rejeitados', valor: rejeitados, classe: 'cor-rejeitado' },
            ]}
          />
          <button className="botao largo" style={{ marginTop: 16 }} onClick={() => irPara('curadoria')}>
            {pendentes > 0 ? `Revisar ${pendentes} pendente(s)` : 'Abrir curadoria'}
          </button>
        </section>
      </div>

      <div className="grade tres">
        <section className="cartao">
          <h3>Destino de cada mensagem</h3>
          <p className="apoio" style={{ margin: '2px 0 14px' }}>
            Positivo com consentimento vira case ou post. Dúvida ou neutro vira FAQ.
          </p>
          <Barras itens={ORDEM_ROTA.map((r) => ({ rotulo: NOME_ROTA[r], valor: porRota(r) }))} />
          {resumo.topicos_principais.length > 0 && (
            <div className="etiquetas" style={{ marginTop: 16 }}>
              {resumo.topicos_principais.map((t) => (
                <span key={t} className="etiqueta verde">
                  {t}
                </span>
              ))}
            </div>
          )}
        </section>

        <section className="cartao">
          <h3 style={{ marginBottom: 14 }}>Últimas ingestões</h3>
          <ul className="lista">
            {pacotes.slice(0, 5).map((p) => (
              <li key={p.id}>
                <button aria-current={p.id === pacote.id} onClick={() => selecionar(p.id)}>
                  <span>
                    <strong>{p.arquivo_origem}</strong>
                    <small>
                      {p.total_interacoes} mensagens · {p.pendentes} pendente(s)
                    </small>
                  </span>
                  <span className="data">{formatarData(p.criado_em)}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="cartao">
          <h3>Pacotes exportados</h3>
          <p className="apoio mono" style={{ margin: '2px 0 14px' }}>
            {status?.oci.configurado ? status.oci.bucket : 'OCI não configurada · só local'}
          </p>
          {exportados.length === 0 ? (
            <div className="vazio">
              <p>Nenhum pacote exportado ainda.</p>
              <button className="botao neutro pequeno" onClick={() => irPara('exportacao')}>
                Ir para exportação
              </button>
            </div>
          ) : (
            <ul className="lista">
              {exportados.slice(0, 5).map((p) => (
                <li key={p.id}>
                  <div>
                    <span>
                      <strong>{p.arquivo_origem}</strong>
                      <small>
                        {p.aprovados} aprovado(s) · {p.oci_exportado === 'sucesso' ? 'no bucket' : 'só local'}
                      </small>
                    </span>
                    <span className="data">{formatarData(p.exportado_em!)}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  )
}
