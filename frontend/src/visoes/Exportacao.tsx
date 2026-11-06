import { useState } from 'react'
import { api, formatarData, NOME_TIPO_ATIVO, type Armazenamento } from '../api'
import type { PropsVisao } from '../App'
import { SemPacote, TituloVisao } from './comuns'

function Destinos({ armazenamento }: { armazenamento: Armazenamento }) {
  const { oci, local } = armazenamento
  return (
    <dl className="destino">
      <dt>OCI</dt>
      <dd>
        {oci.status === 'sucesso' && `Enviado: ${oci.bucket ?? ''}/${oci.caminho_objeto}`}
        {oci.status === 'nao_configurado' && 'Não enviado: credenciais da OCI ausentes no .env'}
        {oci.status === 'erro' && `Falha: ${oci.mensagem}`}
      </dd>
      <dt>Cópia local</dt>
      <dd>{local.caminho}</dd>
    </dl>
  )
}

export default function Exportacao({ pacote, pacotes, status, selecionar, aoAlterar, irPara }: PropsVisao) {
  const [exportando, setExportando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const titulo = (
    <TituloVisao
      sobretitulo="Exportação"
      titulo="Exportação"
      descricao="Empacote os ativos aprovados e envie ao bucket do OCI Object Storage."
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

  const aprovados = pacote.ativos.filter((a) => a.status === 'aprovado')
  const pendentes = pacote.ativos.filter((a) => a.status === 'pendente').length
  const ultimoEnvio = pacote.armazenamento.aprovado
  const exportados = pacotes.filter((p) => p.exportado_em)

  async function exportar() {
    if (!pacote) return
    setExportando(true)
    setErro(null)
    try {
      const resultado = await api.exportar(pacote.id)
      aoAlterar({
        ...pacote,
        exportado_em: resultado.exportado_em,
        armazenamento: { ...pacote.armazenamento, aprovado: resultado.armazenamento },
      })
    } catch (e) {
      setErro((e as Error).message)
    } finally {
      setExportando(false)
    }
  }

  return (
    <>
      {titulo}

      <div className="grade principal">
        <section className="cartao" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <h3>Novo pacote</h3>
            <p className="apoio">
              {aprovados.length} ativo(s) aprovado(s) pronto(s) · {pacote.arquivo_origem}
            </p>
          </div>

          <div className="regra">RN04: só os itens aprovados manualmente entram no pacote.</div>

          {aprovados.length === 0 ? (
            <div className="vazio">
              <p>Nenhum conteúdo aprovado neste pacote.</p>
              <button className="botao neutro pequeno" onClick={() => irPara('curadoria')}>
                Ir para curadoria
              </button>
            </div>
          ) : (
            <ul className="lista">
              {aprovados.map((a) => (
                <li key={a.id}>
                  <div>
                    <strong>{a.titulo}</strong>
                    <span className="etiqueta mono">{NOME_TIPO_ATIVO[a.tipo].toUpperCase()}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {pendentes > 0 && aprovados.length > 0 && (
            <p className="apoio">{pendentes} conteúdo(s) ainda aguardando revisão não entram no pacote.</p>
          )}
          {erro && (
            <div className="erro" role="alert">
              {erro}
            </div>
          )}

          <button className="botao largo" onClick={exportar} disabled={exportando || aprovados.length === 0}>
            {exportando
              ? 'Exportando…'
              : status?.oci.configurado
                ? 'Gerar pacote e enviar ao bucket'
                : 'Gerar pacote (OCI não configurada: só local)'}
          </button>

          {ultimoEnvio && pacote.exportado_em && (
            <div className={ultimoEnvio.oci.status === 'sucesso' ? 'sucesso' : 'aviso'}>
              <strong>Exportado em {formatarData(pacote.exportado_em)}</strong>
              <Destinos armazenamento={ultimoEnvio} />
            </div>
          )}

          {aprovados.length > 0 && (
            <div className="acoes">
              <span className="apoio">Baixar só os aprovados:</span>
              <a className="botao secundario pequeno" href={api.urlDownload(pacote.id, 'markdown')}>
                Markdown
              </a>
              <a className="botao secundario pequeno" href={api.urlDownload(pacote.id, 'json')}>
                JSON
              </a>
            </div>
          )}
        </section>

        <section className="cartao">
          <h3>Pacotes no bucket</h3>
          <p className="apoio" style={{ marginBottom: 14, fontFamily: 'Consolas, monospace' }}>
            {status?.oci.configurado ? status.oci.bucket : 'OCI não configurada'}
          </p>
          {exportados.length === 0 ? (
            <div className="vazio">
              <p>Nenhum pacote exportado ainda.</p>
            </div>
          ) : (
            <ul className="lista">
              {exportados.map((p) => (
                <li key={p.id}>
                  <button aria-current={p.id === pacote.id} onClick={() => selecionar(p.id)}>
                    <span>
                      <strong>{p.arquivo_origem}</strong>
                      <small>
                        {p.aprovados} aprovado(s) · {p.oci_exportado === 'sucesso' ? 'no bucket' : 'só local'}
                      </small>
                    </span>
                    <span className="data">{formatarData(p.exportado_em!)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  )
}
