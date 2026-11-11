# Checklist final (T04)

Cada requisito do projeto, onde ele está no código e como foi verificado.

**Resumo dos testes automatizados:** `cd backend && pytest`: 123 passaram e 1 foi pulado. O pulado chama o Gemini real e roda com `pytest -m gemini`. Os testes usam IA e OCI simuladas e não gastam cota.

## Funcionalidades

| Item | Requisito | Onde está | Como foi verificado | Status |
|---|---|---|---|---|
| F01 | Estrutura do projeto | `backend/`, `frontend/`, `data/`, `docs/` | PR #1 e reorganização no PR #9 | ✅ |
| F02 | Ingestão e validação de JSON e CSV | `backend/src/ingestao/` | `test_ingestao.py` (15 testes); exemplo 3 | ✅ |
| F03 | Dataset de teste | `data/interacoes.json` (50), `data/interacoes_amostra.csv` (8) | `test_le_dataset_completo_com_lotes` | ✅ |
| F04 | Análise de sentimento, tópicos e relevância | `backend/src/ia/analise/sentimento.py` | `test_sentimento.py`, `test_llm_analise.py` | ✅ |
| F05 | Post de LinkedIn | `backend/src/ia/geracao/geradores.py` | `test_geradores.py`; exemplos 1 e 3 | ✅ |
| F06 | Newsletter | `backend/src/ia/geracao/geradores.py` | `test_gera_linkedin_newsletter_e_faq`; exemplo 1 | ✅ |
| F07 | FAQ | `backend/src/ia/geracao/geradores.py` | `test_gera_linkedin_newsletter_e_faq`; exemplo 2 | ✅ |
| F08 | Pipeline LangGraph | `backend/src/orquestracao/pipeline.py` | `test_pipeline_curadoria.py` | ✅ |
| F09 | Arquitetura e OCI Object Storage | `docs/arquitetura.md`, `backend/src/armazenamento/` | `scripts/verificar_oci.py` com o bucket real | ✅ |
| F10 | Tela de Ingestão | `frontend/src/visoes/Ingestao.tsx` | `TESTES_INTERFACE.md` I1–I6 | ✅ |
| F11 | Tela de Curadoria | `frontend/src/visoes/Curadoria.tsx` | `TESTES_INTERFACE.md` C1–C7; `test_fluxo_completo_de_curadoria` | ✅ |
| F12 | Tela de Exportação | `frontend/src/visoes/Exportacao.tsx` | `TESTES_INTERFACE.md` E1–E6 | ✅ |
| F14 | Demonstração (3 exemplos + vídeo) | `data/exemplos/`, `docs/DEMONSTRACAO.md` | `test_exemplos.py`; [vídeo](https://youtu.be/cL1PbDTTmdc) | ✅ |
| F15 | README e documentação | `README.md`, `docs/` | Revisão | ✅ |

## Regras de negócio

| Regra | Descrição | Onde está | Teste | Status |
|---|---|---|---|---|
| RN01 | Só relatos positivos **com consentimento** viram post ou case | `ia/analise/roteador.py` | `test_regras_do_roteador`, `test_motivo_explica_falta_de_consentimento`, `test_rn01_ignorados_e_faq_nao_viram_post`, `test_exemplo_3_lote_misto` | ✅ |
| RN02 | Dúvidas e relatos neutros viram FAQ | `ia/analise/roteador.py`, `ia/geracao/geradores.py` | `test_regras_do_roteador`, `test_exemplo_2_duvidas_viram_faq_e_avisam_rn05` | ✅ |
| RN03 | Todo pacote vai para o OCI (`pacotes/`); os aprovados vão para `aprovados/` | `armazenamento/repositorio.py` | `test_pipeline_salva_pacote_gerado_na_oci`, `test_exporta_somente_aprovados`, `test_sem_oci_configurada_salva_local_e_avisa` | ✅ |
| RN04 | Nada sai sem aprovação humana; editar um aprovado o devolve para revisão | `orquestracao/curadoria.py`, `api/main.py` | `test_nada_exporta_sem_aprovacao`, `test_editar_ativo_aprovado_volta_para_pendente`, `test_markdown_tem_so_os_aprovados`, `test_fluxo_completo_de_curadoria` | ✅ |
| RN05 | Cada processamento deve gerar pelo menos 2 formatos; se não gerar, a interface avisa | `orquestracao/pipeline.py` | `test_pipeline_gera_pelo_menos_2_formatos`, `test_pipeline_avisa_quando_nao_atinge_2_formatos` | ✅ |
| RN06 | Tom por canal: LinkedIn inspirador, newsletter celebrativa, FAQ didática | `ia/prompts/geracao/*.txt` | `test_texto_original_vai_no_pedido_e_tom_no_prompt`, `test_todo_prompt_tem_as_regras_comuns` | ✅ |

## Testes (T01–T04)

| Item | Escopo | Onde está | Status |
|---|---|---|---|
| T01 | Integração: API → pipeline → curadoria → exportação | `test_api.py` (`test_fluxo_completo_de_curadoria`), `test_pipeline_curadoria.py`, `test_exemplos.py`; teste manual com Gemini e OCI reais (vídeo) | ✅ |
| T02 | Interface | `docs/TESTES_INTERFACE.md` (roteiro manual das 4 telas); `npm run lint && npm run build` sem erros | ✅ |
| T03 | Erros | `test_erros_gemini.py`: 503/429 com espera e nova tentativa, só a mensagem com falha é pulada, chave inválida para na hora. Também: arquivo inválido, registros rejeitados, exportar sem aprovados (409), título vazio, pacote inexistente (404), OCI sem credenciais | ✅ |
| T04 | Checklist final | Este documento | ✅ |

## Identidade visual (frontend)

| Requisito | Status |
|---|---|
| Transição de Streamlit para React SPA | ✅ (`src/app` removido; `frontend/` com Vite + React + TypeScript) |
| Cores verde escuro, branco e cinza slate | ✅ (`frontend/src/index.css`, variáveis `--verde-*` e `--slate-*`) |
| Sem logotipo no cabeçalho | ✅ (nome em texto) |
| Sem animações excessivas de clique ou hover | ✅ (`transition` e `animation` desligadas globalmente) |
| 4 telas: Visão Geral, Ingestão, Curadoria, Exportação | ✅ |

## Segurança e boas práticas

| Item | Status |
|---|---|
| `.env` e `*.pem` fora do Git (`.gitignore`) | ✅ |
| Validação dos dados antes de chamar a IA (não gasta cota com dados inválidos) | ✅ |
| Prompts com proteção contra instruções escondidas nas mensagens da comunidade | ✅ (`ia/prompts/geracao/regras_comuns.txt`) |
| Limite de 5 MB por arquivo enviado | ✅ (`api/main.py`) |
| Respeito à cota gratuita do Gemini (pausa entre chamadas e limite de chamadas na geração) | ✅ |
