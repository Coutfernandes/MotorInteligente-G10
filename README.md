# CommunityLab

<div align="center">
  <img src="https://img.shields.io/badge/Project-CommunityLab-1F6FEB?style=for-the-badge&logo=github" alt="CommunityLab" />
  <h3>Gerador automático de conteúdo a partir da comunidade</h3>
  <p><strong>Hackathon ONE G10</strong> — Grupo 10 | Oracle Next Education & Alura</p>
</div>

## 🚀 Visão geral

O CommunityLab tem como objetivo transformar debates, interações e conquistas de comunidades digitais em conteúdos estruturados para LinkedIn, X (Twitter) e newsletters.

O fluxo planejado recebe dados da comunidade, identifica temas e sentimentos com IA, gera sugestões de conteúdo e permite que a equipe revise os materiais antes de utilizá-los.

> **Estado atual:** o projeto tem a estrutura inicial e uma tela Streamlit de demonstração. A leitura e análise reais dos arquivos, a geração de conteúdo com Gemini e o armazenamento no OCI ainda serão desenvolvidos.

### Objetivo do produto

1. Receber debates e interações da comunidade em JSON ou CSV
2. Identificar temas, sentimento, aprendizados e conquistas
3. Gerar rascunhos adaptados para LinkedIn, X e newsletters
4. Permitir revisão humana dos conteúdos
5. Exportar ou armazenar os materiais aprovados

## 🧠 Stack tecnológica

As dependências estão declaradas em `requirements.txt`. A presença de uma biblioteca na lista não significa que a integração correspondente já esteja implementada.

| Tecnologia | Uso previsto |
| --- | --- |
| Python | Linguagem principal |
| Streamlit | Interface web e demonstração atual |
| LangChain | Integração e composição de chamadas a modelos de linguagem |
| LangGraph | Orquestração do fluxo de processamento |
| Google Gemini (`langchain-google-genai`) | Análise e geração de conteúdo |
| OCI SDK (`oci`) | Integração planejada com OCI Object Storage |
| python-dotenv | Leitura de configurações locais do arquivo `.env` |
| Pydantic | Validação e modelagem dos dados |
| pandas | Manipulação de dados tabulares |
| pytest | Testes automatizados |
| GitHub e Trello | Versionamento, revisão de código e organização do trabalho |

Para detalhes de arquitetura, variáveis de ambiente e status de implementação, consulte a [documentação técnica](docs/ARQUITETURA_E_STACK.md).

## ▶️ Como rodar

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

Se o PowerShell bloquear a ativação do ambiente, use o Prompt de Comando:

```bat
.venv\Scripts\activate.bat
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

A tela atual pode ser executada sem credenciais. As integrações com Gemini e OCI ainda serão implementadas. Nunca envie o arquivo `.env` ao Git.

## 📁 Estrutura do projeto

```text
.
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   ├── analysis/       # Módulo planejado para análise com IA
│   ├── app/            # Aplicação Streamlit inicial
│   ├── generation/     # Módulo planejado para geração de conteúdo
│   ├── ingestion/      # Módulo planejado para entrada de dados
│   ├── orchestration/  # Módulo planejado para o pipeline
│   └── storage/        # Módulo planejado para OCI
├── tests/              # Testes em desenvolvimento
└── docs/               # Documentação técnica
```

As pastas dos módulos de backend ainda são estrutura inicial; veja o estado detalhado na [documentação técnica](docs/ARQUITETURA_E_STACK.md).

## 🌿 Fluxo de trabalho (GitHub)

O Trello é usado para organizar as tarefas; o GitHub é usado para versionar o código e revisar as alterações.

- `main`: versão estável; não desenvolver diretamente nesta branch
- `develop`: branch de integração da equipe
- `feature/Fxx-nome-da-tarefa`: branch isolada para uma tarefa do Trello

### Para começar uma tarefa

Clone o repositório uma vez:

```bash
git clone https://github.com/Coutfernandes/MotorInteligente-G10.git
cd MotorInteligente-G10
```

Antes de cada tarefa, atualize `develop` e crie sua branch:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/Fxx-nome-da-tarefa
```

### Ao concluir a tarefa

Revise os arquivos alterados e faça um commit claro:

```bash
git status
git add caminho/do/arquivo
git commit -m "feat: descreve a mudança"
git push -u origin feature/Fxx-nome-da-tarefa
```

Abra um Pull Request com destino `develop`, descreva o que mudou e como testou. Aguarde a revisão e aprovação antes do merge.

> Não faça commits diretamente em `main` ou `develop`. Nunca envie `.env`, chaves de API, arquivos `.pem`, tokens ou credenciais ao repositório. A integração em `main` é feita quando a equipe validar uma versão estável.

## 👥 Equipe — Grupo 10

| Papel | Responsabilidade |
| --- | --- |
| Tech Lead / Arquitetura | Gitflow, arquitetura, revisão de PRs, OCI e diagrama |
| Backend — LLM & Prompts | Análise de sentimento, tópicos e geração de conteúdo |
| Backend — Pipeline & Dados | Ingestão, validação, datasets e tratamento de erros |
| Frontend Streamlit | Upload, visualização, curadoria e download |
| Product / Docs & Demo | Documentação, qualidade, organização do Trello e demonstração |

## 📌 Escopo e documentação

Este projeto está em desenvolvimento como parte do Hackathon ONE G10. As funcionalidades descritas como futuras representam o objetivo do produto, não necessariamente recursos já implementados. O Trello contém as descrições e os critérios de aceite das tarefas.
