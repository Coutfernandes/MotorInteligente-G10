# Documentação técnica — CommunityLab

## 1. Propósito

O CommunityLab transforma interações de comunidades digitais (depoimentos, conquistas, dúvidas e debates) em conteúdos de marketing: posts para LinkedIn, newsletter e FAQ. Todo conteúdo passa por curadoria humana antes de sair do sistema.

## 2. Estado atual

| Feature | Componente | Situação |
| --- | --- | --- |
| F02 | Ingestão e validação de JSON/CSV (`backend/src/ingestao`) | Implementado e testado |
| F03 | Dataset de teste (`data/interacoes.json`, 50 interações; `data/interacoes_amostra.csv`, 8) | Implementado |
| F04 | Análise de sentimento, tópicos e relevância com Gemini (`backend/src/ia/analise`) | Implementado e testado |
| RN01/RN02 | Roteador: positivo com consentimento → case/LinkedIn; dúvida/neutro → FAQ | Implementado e testado |
| F05/F06/F07 | Geração de post LinkedIn, newsletter e FAQ (`backend/src/ia/geracao`) | Implementado e testado |
| F08 | Pipeline LangGraph: analisar → rotear → agregar → gerar → salvar (`backend/src/orquestracao`) | Implementado e testado |
| F09/RN03 | Persistência no OCI Object Storage + cópia local (`backend/src/armazenamento`) | Implementado; depende das credenciais no `.env` |
| RN04 | Curadoria: aprovar, editar, rejeitar; exportação só de aprovados | Implementado e testado |
| F10/F11/F12 | Interface React: Visão Geral, Ingestão, Curadoria, Exportação (`frontend/`) | Implementado |
| — | API HTTP FastAPI (`backend/src/api`) | Implementado e testado |

## 3. Stack tecnológica

| Tecnologia | Papel |
| --- | --- |
| Python 3.10+ | Backend, IA e pipeline |
| LangChain + `langchain-google-genai` | Chamadas ao Gemini com saída estruturada (Pydantic) |
| LangGraph | Orquestração das etapas do pipeline |
| Google Gemini | Análise e geração de conteúdo |
| Pydantic | Validação de entrada, respostas da IA e pacotes |
| FastAPI + Uvicorn | API entre a interface e o pipeline |
| React + TypeScript + Vite | Interface web |
| SDK `oci` | OCI Object Storage (Always Free) |
| pytest | Testes automatizados |

## 4. Arquitetura

```text
Interface React (frontend/)
        |  HTTP /api
        v
API FastAPI (backend/src/api) ---- processamento em segundo plano + progresso
        |
        v
Ingestão (backend/src/ingestao) -> Pipeline LangGraph (backend/src/orquestracao)
                               analisar  (backend/src/ia/analise, Gemini)
                               rotear    (RN01, RN02)
                               agregar   (resumo da comunidade)
                               gerar     (backend/src/ia/geracao, Gemini, RN05/RN06)
        |
        v
Repositório (backend/src/armazenamento) -> data/saida/ (cópia local) + OCI Object Storage (RN03)
        ^
        |
Curadoria (backend/src/orquestracao/curadoria.py) -> exporta só aprovados (RN04)
```

Caminhos no bucket:

- `pacotes/<id>.json` — pacote completo gerado pelo pipeline (todos os ativos pendentes).
- `aprovados/<id>.json` — pacote exportado após a curadoria, somente com os ativos aprovados.

### Cota do Gemini

A análise faz 1 chamada por interação, com pausa de 5 s entre chamadas (plano gratuito). A geração faz no máximo 5 chamadas por processamento: até 3 posts LinkedIn (relatos positivos mais relevantes), 1 newsletter e 1 FAQ. Os limites ficam no topo de `backend/src/ia/geracao/geradores.py` e `backend/src/ia/analise/sentimento.py`.

### Modo simulado

Com `LLM_PROVIDER=simulado` no `.env`, o Gemini é trocado por respostas fixas (`backend/src/ia/llm_simulado.py`), sem chave e sem cota. Serve só para testar a interface; os textos saem marcados com `[Simulado]` e a interface mostra o selo "IA: modo simulado".

## 5. Configuração (.env)

| Variável | Finalidade |
| --- | --- |
| `GOOGLE_API_KEY` | Chave do Google Gemini |
| `LLM_PROVIDER` | `gemini` (real) ou `simulado` |
| `LLM_MODEL` | Modelo do Gemini |
| `OCI_USER_OCID`, `OCI_TENANCY_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY_PATH`, `OCI_REGION` | Credenciais da API da OCI |
| `OCI_BUCKET_NAME`, `OCI_NAMESPACE` | Bucket do Object Storage |

Sem as variáveis da OCI, os pacotes são salvos apenas localmente e a interface avisa.

## 6. Execução

Backend (na raiz, com o `.venv` ativo):

```bash
pip install -r backend/requirements.txt
cd backend
uvicorn src.api.main:app --reload
```

Frontend em desenvolvimento (outro terminal):

```bash
cd frontend
npm install
npm run dev
```

Acesse `http://localhost:5173`. O Vite repassa as chamadas `/api` para o FastAPI na porta 8000.

Para servir tudo por um só endereço, rode `npm run build` dentro de `frontend/` e acesse `http://localhost:8000`: o FastAPI serve a interface compilada.

## 7. Testes

```bash
cd backend
pytest                  # tudo, sem gastar cota
pytest -m gemini        # testes que chamam o Gemini de verdade
cd frontend && npm run lint && npm run build
```

## 8. Regras de colaboração

- `main`: versão estável; `develop`: integração; `feature/Fxx-descricao`: uma tarefa.
- Cada tarefa vai por Pull Request para `develop`, com revisão de outra pessoa.
- Nunca envie `.env`, chaves `.pem`, tokens ou credenciais ao repositório.
