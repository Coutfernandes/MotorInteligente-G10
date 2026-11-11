/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Endereço do backend em produção. Vazio em desenvolvimento. */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
