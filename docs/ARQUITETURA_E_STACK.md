# Documentação técnica — CommunityLab

## 1. Propósito

O CommunityLab é um projeto em desenvolvimento para transformar debates, interações e conquistas de comunidades digitais em sugestões de conteúdo para LinkedIn, X (Twitter) e newsletters.

O produto pretende ajudar a equipe a identificar temas e aprendizados relevantes, gerar rascunhos adequados a cada canal e revisar os textos antes de utilizá-los.

## 2. Estado atual

Esta documentação diferencia a base que já existe das funcionalidades planejadas.

### Implementado na base atual

- Repositório Python com módulos iniciais separados por responsabilidade.
- Aplicação Streamlit em `src/app/main.py`.
- Tela inicial com apresentação do projeto e etapas previstas para o fluxo.
- Verificação visual da variável `GOOGLE_API_KEY` carregada do `.env`.
- Upload de arquivo `.json` ou `.csv` para exibir nome e uma pequena prévia do conteúdo.
- Conteúdo de exemplo estático e botão que simula a conclusão de uma análise.
- Dependências listadas em `requirements.txt`.
- Arquivo `.env.example` com nomes das configurações planejadas.

### Ainda não implementado

- Parsing e validação funcional de arquivos JSON/CSV.
- Análise real de sentimentos e tópicos.
- Chamadas ao Google Gemini, prompts de produção e geração de textos.
- Pipeline integrado entre ingestão, análise, geração e interface.
- Upload/download real no OCI Object Storage.
- Fluxo persistente de curadoria e aprovação.
- Exportação de conteúdos gerados.
- Suíte de testes funcionais.

O upload atual apenas mostra uma prévia dos bytes do arquivo. O botão “Simular análise” não chama um modelo de IA. A existência de variáveis no `.env.example` ou de pacotes no `requirements.txt` não significa que a integração correspondente esteja pronta.

## 3. Stack tecnológica

| Tecnologia/dependência | Papel no projeto | Situação |
| --- | --- | --- |
| Python | Linguagem da aplicação e dos módulos | Em uso |
| Streamlit | Interface web | Tela inicial implementada |
| `python-dotenv` | Carregar variáveis do `.env` | Usado pela aplicação |
| LangChain | Composição de integrações com modelos de linguagem | Declarado; integração ainda pendente |
| `langchain-google-genai` | Integração planejada com Google Gemini | Declarado; integração ainda pendente |
| LangGraph | Orquestração de etapas do fluxo | Declarado; pipeline ainda pendente |
| `oci` | SDK para OCI Object Storage | Declarado; integração ainda pendente |
| Pydantic | Modelagem e validação de dados | Declarado; uso funcional ainda pendente |
| pandas | Manipulação de dados tabulares | Declarado; processamento ainda pendente |
| pytest | Execução de testes automatizados | Declarado; testes funcionais ainda pendentes |
| Git/GitHub | Versionamento e Pull Requests | Processo adotado pela equipe |
| Trello | Backlog, responsáveis e acompanhamento das tarefas | Processo adotado pela equipe |

As versões declaradas são limites mínimos (`>=`) em `requirements.txt`. O arquivo não fixa versões exatas.

## 4. Arquitetura planejada

O fluxo funcional esperado é:

```text
Arquivo ou dados da comunidade
              |
              v
Ingestão e validação (src/ingestion)
              |
              v
Análise de sentimento e tópicos (src/analysis)
              |
              v
Geração para LinkedIn, X e newsletter (src/generation)
              |
              v
Orquestração do fluxo (src/orchestration)
              |
        +-----+------+
        |            |
        v            v
OCI Object Storage  Interface Streamlit
 (src/storage)      (src/app)
                          |
                          v
                Revisão humana e exportação
```

Este diagrama representa o desenho planejado. Os módulos ainda precisam ser implementados e integrados.

## 5. Responsabilidade dos módulos

| Caminho | Responsabilidade prevista |
| --- | --- |
| `src/ingestion/` | Ler entradas JSON/CSV e validar formato e campos |
| `src/analysis/` | Extrair sentimento, tópicos, debates e conquistas com apoio de IA |
| `src/generation/` | Produzir rascunhos adaptados a LinkedIn, X e newsletters |
| `src/orchestration/` | Coordenar as etapas e tratar o fluxo de execução |
| `src/storage/` | Persistir e recuperar arquivos no OCI Object Storage |
| `src/app/` | Interface Streamlit para upload, visualização, curadoria e download |
| `tests/` | Testes unitários e de integração |
| `docs/` | Documentação técnica, diagramas e decisões do projeto |

No estado atual, as pastas dos módulos de backend contêm apenas a estrutura inicial; a tela Streamlit está em `src/app/main.py`.

## 6. Configuração e variáveis de ambiente

Copie `.env.example` para `.env` e preencha apenas as credenciais necessárias quando as integrações forem desenvolvidas. Nunca versione o `.env`, chaves privadas ou credenciais.

| Variável | Finalidade prevista |
| --- | --- |
| `GOOGLE_API_KEY` | Chave de acesso ao Google Gemini |
| `LLM_PROVIDER` | Provedor de modelo configurado (atualmente indicado como `gemini`) |
| `LLM_MODEL` | Nome do modelo configurado |
| `OCI_USER_OCID` | OCID do usuário OCI |
| `OCI_TENANCY_OCID` | OCID da tenancy OCI |
| `OCI_FINGERPRINT` | Fingerprint da chave OCI |
| `OCI_PRIVATE_KEY_PATH` | Caminho local para a chave privada OCI |
| `OCI_REGION` | Região da OCI |
| `OCI_BUCKET_NAME` | Nome previsto para o bucket |
| `OCI_NAMESPACE` | Namespace do Object Storage |
| `APP_ENV` | Ambiente da aplicação |
| `LOG_LEVEL` | Nível de logging previsto |

As variáveis OCI e Gemini estão documentadas para uso futuro. Atualmente a aplicação apenas verifica se `GOOGLE_API_KEY` está definida; não valida a chave nem executa chamadas ao serviço.

## 7. Instalação e execução

### Windows — PowerShell

```powershell
git clone https://github.com/Coutfernandes/MotorInteligente-G10.git
cd MotorInteligente-G10
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run src/app/main.py
```

### Windows — Prompt de Comando

```bat
git clone https://github.com/Coutfernandes/MotorInteligente-G10.git
cd MotorInteligente-G10
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
streamlit run src/app/main.py
```

### Linux/macOS

```bash
git clone https://github.com/Coutfernandes/MotorInteligente-G10.git
cd MotorInteligente-G10
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run src/app/main.py
```

Depois de iniciar, o Streamlit informa o endereço local no terminal, normalmente `http://localhost:8501`.

## 8. Regras de colaboração

- `main`: versão estável; não desenvolver diretamente nela.
- `develop`: branch de integração; não desenvolver diretamente nela.
- `feature/Fxx-descricao`: branch isolada para uma tarefa do Trello.
- Cada tarefa deve ser enviada por Pull Request com destino `develop`.
- O PR deve explicar as alterações e os testes executados; outra pessoa deve revisar antes do merge.
- Use commits pequenos com mensagens que expliquem a mudança, por exemplo: `feat: valida arquivos de entrada`.
- Atualize a branch com `develop` antes de abrir o PR, resolvendo conflitos localmente quando necessário.
- Nunca envie `.env`, chaves, arquivos `.pem`, tokens ou credenciais ao repositório.

Exemplo para iniciar uma tarefa:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/F02-ingestao-dados
```

Ao concluir:

```bash
git status
git add caminho/dos/arquivos
git commit -m "feat: adiciona ingestao de arquivos"
git push -u origin feature/F02-ingestao-dados
```

Em seguida, abra no GitHub um Pull Request de `feature/F02-ingestao-dados` para `develop`. Faça o merge somente após revisão e validação.

## 9. Organização das tarefas

O Trello é o backlog do time. Cada cartão já possui sua descrição; a equipe deve manter nele responsável, status, critérios de aceite e dependências.

Distribuição de papéis conforme o planejamento:

| Integrante | Papel | Escopo |
| --- | --- | --- |
| 1 | Tech Lead / Arquitetura | Gitflow, arquitetura, revisão de PRs, OCI e diagrama |
| 2 | Backend — LLM & Prompts | Análise de sentimento, tópicos e geração de conteúdo |
| 3 | Backend — Pipeline & Dados | Ingestão, validação, datasets e tratamento de erros |
| 4 | Frontend Streamlit | Upload, visualização, curadoria e download |
| 5 | Product / Docs & Demo | Documentação, qualidade, Trello e demonstração |

As dependências entre tarefas devem ser confirmadas nos cartões do Trello antes do início de cada feature. A descrição e os critérios do Trello são a referência para escopo e aceite.

## 10. Testes e qualidade

O projeto declara `pytest` como dependência, mas ainda não há testes funcionais implementados. Ao adicionar funcionalidades, inclua testes para os critérios de aceite do cartão e execute-os antes de abrir o Pull Request:

```bash
pytest
```

Para validar apenas a inicialização da interface:

```bash
streamlit run src/app/main.py
```

## 11. Histórico e manutenção da documentação

Atualize esta documentação e o README quando houver mudanças na stack, nos comandos de instalação, na arquitetura ou no estado de implementação. Descreva como implementado apenas o que já foi desenvolvido e validado; mantenha o restante identificado como planejado.
