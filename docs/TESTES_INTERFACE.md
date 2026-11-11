# Testes de interface (T02)

Roteiro manual para conferir as 4 telas. Preencha a coluna **OK?** e anexe prints quando quiser registrar evidências.

**Preparação**
- API: `cd backend` e `uvicorn src.api.main:app --reload`
- Interface: `cd frontend` e `npm run dev`. Abra http://localhost:5173
- Para testar sem gastar cota, rode a API com `LLM_PROVIDER=simulado`.

## Layout geral

| # | Ação | Resultado esperado | OK? |
|---|---|---|---|
| L1 | Abrir a página | Menu lateral claro com "Painel" e "Pipeline", **sem logotipo**, nas cores verde escuro, branco e cinza slate | |
| L2 | Olhar o rodapé do menu | "Google Gemini" e "OCI Object Storage", cada um com um ponto verde (configurado) ou amarelo (simulado ou não configurado) | |
| L3 | Clicar em cada item do menu | A tela muda, o item fica destacado em verde-claro e a barra superior mostra o nome da tela | |
| L4 | Passar o mouse e clicar nos botões | **Sem animações** de clique ou hover | |
| L5 | Diminuir a janela para a largura de um celular | O menu vira uma barra no topo e não aparece rolagem horizontal | |

## Ingestão e upload

| # | Ação | Resultado esperado | OK? |
|---|---|---|---|
| I1 | Clicar em **Usar dados de exemplo** | "8 interação(ões) válida(s)" e gráficos por tipo e por canal | |
| I2 | Arrastar `data/exemplos/03_lote_misto.csv` | "7 válidas, 3 rejeitadas" e a tabela de rejeitados com os motivos (texto ausente, ID repetido, data inválida) | |
| I3 | Enviar um arquivo `.txt` ou um JSON quebrado | Mensagem de erro em vermelho, sem travar a tela | |
| I4 | Clicar em **Processar pipeline de IA** | As 6 etapas ficam verdes uma a uma, com "x de y" na etapa atual e a barra de progresso andando | |
| I5 | Esperar terminar | A tela muda sozinha para **Curadoria** | |
| I6 | Rodar a API sem `GOOGLE_API_KEY` e sem o modo simulado | Aviso "Gemini não configurado" e o botão de processar desabilitado | |

## Curadoria

| # | Ação | Resultado esperado | OK? |
|---|---|---|---|
| C1 | Abrir a tela | Faixa amarela da RN04, cartões com etiqueta de tipo, a etiqueta "Gerado por IA" e as mensagens de origem | |
| C2 | Filtrar por tipo (Post LinkedIn, FAQ, Newsletter) e por status | Só os cartões do filtro aparecem; os números nas abas batem | |
| C3 | Clicar em **Aprovar** | O cartão sai de "Aguardando"; o contador do menu diminui | |
| C4 | **Editar**, mudar o texto e clicar em **Salvar e aprovar** | O cartão aparece em "Aprovados" com a etiqueta "Editado" | |
| C5 | Editar um cartão **já aprovado** e clicar em **Salvar** | Aviso de que ele volta para "Aguardando"; ao salvar, volta mesmo (RN04) | |
| C6 | Apagar todo o título e tentar salvar | Mensagem de erro; nada é salvo | |
| C7 | Clicar em **Rejeitar** | O cartão vai para "Rejeitados"; dá para clicar em "Voltar para aguardando" | |

## Exportação

| # | Ação | Resultado esperado | OK? |
|---|---|---|---|
| E1 | Abrir um pacote **sem** aprovados | "Nenhum conteúdo aprovado" e o botão de exportar desabilitado (RN04) | |
| E2 | Abrir um pacote com aprovados | Lista só dos aprovados e o aviso de quantos ainda aguardam | |
| E3 | Clicar em **Gerar pacote e enviar ao bucket** | "Enviado: communitylab-ativos-marketing/aprovados/pkg_….json" e o caminho da cópia local | |
| E4 | Baixar **Markdown** e **JSON** | Os arquivos têm **só** os aprovados | |
| E5 | Olhar "Pacotes no bucket" | O pacote aparece como "no bucket"; clicar nele troca o pacote selecionado | |
| E6 | Sem credenciais da OCI | O botão vira "Gerar pacote (OCI não configurada: só local)" e aparece o aviso de "não enviado" | |

## Visão geral

| # | Ação | Resultado esperado | OK? |
|---|---|---|---|
| V1 | Abrir com um pacote processado | 5 indicadores (mensagens, posts, FAQ, newsletter, aprovados) | |
| V2 | Gráfico de sentimento | As colunas somam o total de mensagens processadas; ao lado, quantas viraram post, FAQ ou ficaram sem destino | |
| V3 | Gráfico "Fila de curadoria" | Os números da legenda batem com a Curadoria | |
| V4 | Trocar o pacote no seletor da barra superior | Todos os números mudam para o pacote escolhido | |
| V5 | Processar `02_duvidas_tecnicas.json` | Aparece o aviso da **RN05** (só 1 formato gerado) | |
