// Tipos e chamadas da API do CommunityLab (src/api/main.py).

export type Sentimento = 'muito_positivo' | 'positivo' | 'neutro' | 'negativo' | 'muito_negativo'
export type Rota = 'case' | 'linkedin' | 'faq' | 'ignorar'
export type TipoAtivo = 'linkedin' | 'newsletter' | 'faq'
export type StatusCuradoria = 'pendente' | 'aprovado' | 'rejeitado'

export interface ResultadoDestino {
  status: string
  mensagem?: string
  caminho?: string
  caminho_objeto?: string
  bucket?: string
}

export interface Armazenamento {
  local: ResultadoDestino
  oci: ResultadoDestino
}

export interface Ativo {
  id: string
  tipo: TipoAtivo
  titulo: string
  conteudo: string
  fontes: string[]
  status: StatusCuradoria
  editado: boolean
}

export interface Mensagem {
  interaction_id: string
  tipo: string
  sentimento: Sentimento
  topicos: string[]
  relevancia: number
  insight: string
  consent_marketing: boolean
  rota: Rota
  motivo: string
}

export interface Rejeitada {
  posicao: number
  interaction_id: string | null
  motivo: string
}

export interface Pacote {
  id: string
  criado_em: string
  arquivo_origem: string
  resumo: {
    total_interacoes_processadas: number
    sentimento_predominante: Sentimento | null
    topicos_principais: string[]
    contagem_por_rota: Record<Rota, number>
  }
  mensagens: Mensagem[]
  ativos: Ativo[]
  rejeitadas_ingestao: Rejeitada[]
  avisos: string[]
  armazenamento: { gerado?: Armazenamento; aprovado?: Armazenamento }
  exportado_em: string | null
}

export interface ResumoPacote {
  id: string
  criado_em: string
  arquivo_origem: string
  total_interacoes: number
  total_ativos: number
  aprovados: number
  pendentes: number
  exportado_em: string | null
  oci_exportado: 'sucesso' | 'erro' | 'nao_configurado' | null
}

export interface Validacao {
  arquivo: string
  total_validas: number
  rejeitadas: Rejeitada[]
  por_tipo: Record<string, number>
  por_canal: Record<string, number>
  com_consentimento: number
  amostra: Record<string, unknown>[]
}

export interface Execucao {
  id: string
  arquivo: string
  status: 'processando' | 'concluido' | 'erro'
  etapa: 'iniciando' | 'analise' | 'geracao' | 'salvando'
  atual: number
  total: number
  erro: string | null
}

export interface StatusSistema {
  llm: { simulado: boolean; modelo: string; configurado: boolean }
  oci: { configurado: boolean; bucket: string | null }
}

async function chamar<T>(caminho: string, opcoes?: RequestInit): Promise<T> {
  const resposta = await fetch(caminho, opcoes)
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    const detalhe = corpo?.detail
    throw new Error(typeof detalhe === 'string' ? detalhe : `Erro ${resposta.status} ao chamar a API.`)
  }
  return resposta.json() as Promise<T>
}

function comArquivo(arquivo: File): RequestInit {
  const dados = new FormData()
  dados.append('arquivo', arquivo)
  return { method: 'POST', body: dados }
}

export const api = {
  status: () => chamar<StatusSistema>('/api/status'),
  arquivoExemplo: async () => {
    const resposta = await fetch('/api/exemplo')
    if (!resposta.ok) throw new Error('Não foi possível carregar os dados de exemplo.')
    return new File([await resposta.blob()], 'interacoes_amostra.csv', { type: 'text/csv' })
  },
  validar: (arquivo: File) => chamar<Validacao>('/api/ingestao/validar', comArquivo(arquivo)),
  processar: (arquivo: File) => chamar<Execucao>('/api/processamentos', comArquivo(arquivo)),
  execucao: (id: string) => chamar<Execucao>(`/api/processamentos/${id}`),
  pacotes: () => chamar<ResumoPacote[]>('/api/pacotes'),
  pacote: (id: string) => chamar<Pacote>(`/api/pacotes/${id}`),
  editarAtivo: (idPacote: string, idAtivo: string, edicao: Partial<Pick<Ativo, 'titulo' | 'conteudo' | 'status'>>) =>
    chamar<Ativo>(`/api/pacotes/${idPacote}/ativos/${idAtivo}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(edicao),
    }),
  exportar: (id: string) =>
    chamar<{ exportado_em: string; armazenamento: Armazenamento; total_aprovados: number }>(
      `/api/pacotes/${id}/exportar`,
      { method: 'POST' },
    ),
  urlDownload: (id: string, formato: 'json' | 'markdown') => `/api/pacotes/${id}/download?formato=${formato}`,
}

// ---- textos exibidos na tela ----

export const NOME_SENTIMENTO: Record<Sentimento, string> = {
  muito_positivo: 'Muito positivo',
  positivo: 'Positivo',
  neutro: 'Neutro',
  negativo: 'Negativo',
  muito_negativo: 'Muito negativo',
}

export const NOME_ROTA: Record<Rota, string> = {
  case: 'Case',
  linkedin: 'Post LinkedIn',
  faq: 'FAQ',
  ignorar: 'Ignorada',
}

export const NOME_TIPO_ATIVO: Record<TipoAtivo, string> = {
  linkedin: 'Post LinkedIn',
  newsletter: 'Newsletter',
  faq: 'FAQ / Dica técnica',
}

export const TOM_DE_VOZ: Record<TipoAtivo, string> = {
  linkedin: 'Inspirador',
  newsletter: 'Celebrativo',
  faq: 'Didático',
}

export const NOME_STATUS: Record<StatusCuradoria, string> = {
  pendente: 'Pendente',
  aprovado: 'Aprovado',
  rejeitado: 'Rejeitado',
}

export function formatarData(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}
