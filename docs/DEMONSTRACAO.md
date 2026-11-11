# Demonstração — CommunityLab (F14)

## Vídeo

[![Assistir à demonstração no YouTube](https://img.youtube.com/vi/cL1PbDTTmdc/hqdefault.jpg)](https://youtu.be/cL1PbDTTmdc)

**[Assistir no YouTube](https://youtu.be/cL1PbDTTmdc)**: fluxo completo com Gemini (`gemini-3.1-flash-lite`) e OCI Object Storage reais. Mostra a ingestão, a análise com IA, a curadoria humana e a exportação ao bucket.

## Como rodar os exemplos

1. API: `cd backend` e `uvicorn src.api.main:app --reload`
2. Interface: `cd frontend` e `npm run dev`. Abra http://localhost:5173
3. Em **Ingestão e upload**, arraste um dos arquivos de `data/exemplos/` e clique em **Processar pipeline de IA**.
4. Em **Curadoria**, aprove, edite ou rejeite. Em **Exportação**, envie ao bucket.

Com o Gemini real, cada exemplo leva de 1 a 2 minutos, por causa da pausa de 5 s entre chamadas que respeita a cota gratuita. Para testar só a interface, sem gastar cota, use `LLM_PROVIDER=simulado`.

O teste automático `backend/tests/test_exemplos.py` confere que os 3 exemplos continuam produzindo o resultado descrito abaixo.

---

## Exemplo 1: relatos positivos (RN01)

**Arquivo:** `data/exemplos/01_relatos_positivos.json` (5 interações, JSON)

| ID | Tipo | Consentimento | Destino |
|---|---|---|---|
| EX1-001 | depoimento (primeiro estágio) | sim | case / post |
| EX1-002 | entrega_projeto (agente LangGraph) | sim | case / post |
| EX1-003 | feedback_positivo (trilha de prompts) | sim | post |
| EX1-004 | depoimento (promoção a analista de IA) | sim | case / post |
| EX1-005 | entrega_projeto (painel para ONG) | sim | case / post |

**O que mostra:**
- Relatos positivos **com consentimento** viram conteúdo de marketing (RN01).
- No máximo **3 posts de LinkedIn** por lote, com os relatos mais relevantes, para economizar cota.
- **1 newsletter** reúne os destaques positivos, em tom celebrativo (RN06).
- Nenhuma FAQ é gerada, porque o lote não tem dúvidas.

**Resultado esperado:** 3 posts de LinkedIn e 1 newsletter, todos **aguardando aprovação** (RN04). São 2 formatos, então a RN05 é atendida.

---

## Exemplo 2: dúvidas técnicas (RN02)

**Arquivo:** `data/exemplos/02_duvidas_tecnicas.json` (5 interações, JSON)

| ID | Tipo | Assunto |
|---|---|---|
| EX2-001 | pergunta_tecnica | O que guardar no banco vetorial no RAG |
| EX2-002 | pergunta_tecnica | Voltar etapas no LangGraph |
| EX2-003 | pedido_ajuda | Erro 429 no plano gratuito do Gemini |
| EX2-004 | pergunta_tecnica | Embeddings multilíngues para português |
| EX2-005 | pedido_ajuda | Erro de autenticação no OCI Object Storage |

**O que mostra:**
- Dúvidas e pedidos de ajuda viram **FAQ** em tom didático (RN02 e RN06). Isso vale mesmo **sem** consentimento de marketing, porque a FAQ responde à dúvida e não expõe a pessoa.
- As 5 dúvidas são agrupadas numa única FAQ.
- A interface mostra o **aviso da RN05**: só 1 formato foi gerado, porque o lote não tem relatos positivos.

**Resultado esperado:** 1 FAQ com as 5 mensagens como fonte, e o aviso da RN05 na Visão geral.

---

## Exemplo 3: lote misto com problemas (ingestão, RN01, RN02 e RN04)

**Arquivo:** `data/exemplos/03_lote_misto.csv` (10 linhas, CSV com `sim`/`não` no consentimento)

| ID | Situação | O que acontece |
|---|---|---|
| EX3-001 | depoimento positivo, com consentimento | vira post |
| EX3-002 | depoimento positivo, **sem consentimento** | **não vira post** (RN01) |
| EX3-003 | entrega de projeto, com consentimento | vira post |
| EX3-004 | pergunta técnica | vai para a FAQ (RN02) |
| EX3-005 | pergunta técnica, sem consentimento | vai para a FAQ (RN02) |
| EX3-006 | feedback negativo | ignorado |
| EX3-007 | mensagem operacional (aviso de horário) | ignorada |
| EX3-008 | **texto vazio** | **rejeitado na ingestão** |
| EX3-001 (2ª vez) | **ID repetido** | **rejeitado na ingestão** |
| EX3-010 | **data inválida** ("ontem à tarde") | **rejeitado na ingestão** |

**O que mostra:**
- A **validação antes da IA**: 3 registros com problema são recusados, cada um com o motivo, e os 7 válidos seguem sem gastar cota com os inválidos.
- A **RN01 na prática**: o depoimento de EX3-002 é positivo, mas a pessoa não autorizou o uso, então ele não vira post.
- Mensagens negativas e operacionais não geram conteúdo.

**Resultado esperado:** 7 válidas e 3 rejeitadas, com uma tabela de motivos na tela de Ingestão. Depois do processamento: 2 posts (EX3-001 e EX3-003), 1 newsletter e 1 FAQ, todos aguardando curadoria.

---

## Roteiro do vídeo (referência)

| Tempo | Tela | O que mostrar |
|---|---|---|
| 0:00 | Visão geral | O problema: conversas da comunidade viram conteúdo com curadoria humana |
| 0:30 | Ingestão | Enviar o arquivo e mostrar a validação (válidas, rejeitadas e motivos) |
| 1:00 | Ingestão | Processar e acompanhar as 6 etapas do pipeline com o Gemini |
| 2:00 | Curadoria | Ler um post e uma FAQ, ver as mensagens de origem, editar e aprovar, rejeitar um |
| 3:00 | Exportação | Enviar os aprovados ao bucket e baixar o Markdown com **só** os aprovados |
| 3:30 | Console da OCI | Mostrar as pastas `pacotes/` e `aprovados/` no bucket |
| 4:00 | Visão geral | Indicadores, sentimento, fila de curadoria e pacotes exportados |
