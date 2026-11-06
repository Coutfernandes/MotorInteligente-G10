import type { ReactNode } from 'react'
import type { Visao } from '../App'

export function TituloVisao({
  sobretitulo,
  titulo,
  descricao,
  children,
}: {
  sobretitulo: string
  titulo: string
  descricao: string
  children?: ReactNode
}) {
  return (
    <div className="titulo-visao">
      <div>
        <span className="sobretitulo">{sobretitulo}</span>
        <h2>{titulo}</h2>
        <p>{descricao}</p>
      </div>
      {children && <div className="acoes">{children}</div>}
    </div>
  )
}

export function SemPacote({ irPara }: { irPara: (v: Visao) => void }) {
  return (
    <div className="cartao vazio">
      <h3>Nenhum pacote processado ainda</h3>
      <p>Envie um arquivo JSON ou CSV com as interações da comunidade para começar.</p>
      <button className="botao" onClick={() => irPara('ingestao')}>
        Ir para ingestão
      </button>
    </div>
  )
}

/** Colunas verticais de uma série só, com o valor escrito em cima de cada coluna. */
export function Colunas({ itens }: { itens: { rotulo: string; valor: number }[] }) {
  const maximo = Math.max(1, ...itens.map((i) => i.valor))
  return (
    <div className="colunas" role="img" aria-label={itens.map((i) => `${i.rotulo}: ${i.valor}`).join(', ')}>
      {itens.map((i) => (
        <div key={i.rotulo} className="coluna" title={`${i.rotulo}: ${i.valor}`}>
          <span className="trilho">
            <span className="valor">{i.valor}</span>
            <span className="preenchido" style={{ height: `calc((100% - 24px) * ${i.valor / maximo})` }} />
          </span>
          <span className="rotulo">{i.rotulo}</span>
        </div>
      ))}
    </div>
  )
}

/** Gráfico de rosca com o total no centro e a legenda (com valores) embaixo. */
export function Rosca({
  fatias,
  centro,
  legendaCentro,
}: {
  fatias: { rotulo: string; valor: number; classe: string }[]
  centro: string
  legendaCentro: string
}) {
  const raio = 70
  const circunferencia = 2 * Math.PI * raio
  const total = fatias.reduce((s, f) => s + f.valor, 0)
  const visiveis = fatias.filter((f) => f.valor > 0)
  const folga = visiveis.length > 1 ? 4 : 0
  let inicio = 0

  return (
    <div className="rosca">
      <div className="rosca-grafico">
        <svg viewBox="0 0 180 180" role="img" aria-label={fatias.map((f) => `${f.rotulo}: ${f.valor}`).join(', ')}>
          <circle cx="90" cy="90" r={raio} className="rosca-fundo" />
          {total > 0 &&
            visiveis.map((f) => {
              const tamanho = (f.valor / total) * circunferencia
              const arco = (
                <circle
                  key={f.rotulo}
                  cx="90"
                  cy="90"
                  r={raio}
                  className={`rosca-fatia ${f.classe}`}
                  strokeDasharray={`${Math.max(0, tamanho - folga)} ${circunferencia}`}
                  strokeDashoffset={-inicio}
                />
              )
              inicio += tamanho
              return arco
            })}
        </svg>
        <div className="rosca-centro">
          <strong>{centro}</strong>
          <span>{legendaCentro}</span>
        </div>
      </div>
      <ul className="rosca-legenda">
        {fatias.map((f) => (
          <li key={f.rotulo}>
            <i className={f.classe} />
            <span>{f.rotulo}</span>
            <b>{f.valor}</b>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Barras horizontais de uma série só; o valor fica escrito ao lado de cada barra. */
export function Barras({ itens }: { itens: { rotulo: string; valor: number }[] }) {
  const maximo = Math.max(1, ...itens.map((i) => i.valor))
  return (
    <ul className="barras">
      {itens.map((i) => (
        <li key={i.rotulo} title={`${i.rotulo}: ${i.valor}`}>
          <span className="rotulo">{i.rotulo}</span>
          <span className="trilho">
            <span className="preenchido" style={{ width: `${(i.valor / maximo) * 100}%` }} />
          </span>
          <span className="valor">{i.valor}</span>
        </li>
      ))}
    </ul>
  )
}
