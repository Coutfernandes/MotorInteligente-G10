# CommunityLab

<div align="center">
  <img src="https://img.shields.io/badge/Project-CommunityLab-1F6FEB?style=for-the-badge&logo=github" alt="CommunityLab" />
  <h3>Motor Inteligente de Transformação e Distribuição para Comunidades Digitais</h3>
  <p><strong>Hackathon ONE G10</strong> — Grupo 10 | Oracle Next Education & Alura</p>
</div>

## 🚀 Visão geral

O CommunityLab transforma interações de comunidades digitais em conteúdo de marketing pronto para publicação.

Ele coleta dados de plataformas como Discord e Slack, analisa sentimentos e temas com IA, cria materiais estratégicos e organiza tudo em um painel para revisão humana.

### O que ele faz

1. Recebe dados em JSON ou CSV
2. Analisa sentimento e tópicos com IA (Google Gemini)
3. Gera conteúdos como LinkedIn, newsletter e FAQ
4. Armazena arquivos no OCI Object Storage
5. Exibe os resultados em um dashboard com Streamlit para curadoria e aprovação

---

## ✨ Principais recursos

- Processamento inteligente de conversas comunitárias
- Extração de insights relevantes para marca e conteúdo
- Geração automática de textos para campanhas e comunicação
- Estrutura modular para ingestão, análise, geração e armazenamento
- Dashboard visual para aprovação e acompanhamento

---

## 🧠 Stack tecnológica

- Python
- LangChain / LangGraph
- Google Gemini
- Streamlit
- OCI Object Storage
- Gitflow + Trello (Kanban)

---

## 🏗️ Como funciona

```text
Dados de comunidade
        ↓
Ingestão e validação
        ↓
Análise com IA
        ↓
Geração de conteúdo
        ↓
Armazenamento e curadoria
        ↓
Dashboard / aprovação
```

---

## ▶️ Como rodar

```bash
git clone https://github.com/Coutfernandes/MotorInteligente-G10.git
cd MotorInteligente-G10
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

# Preencha o .env com suas chaves
streamlit run src/app/main.py
```

> Ajuste as variáveis de ambiente conforme o seu projeto antes de iniciar a aplicação.

---

## 📁 Estrutura do projeto

```text
src/
  ingestion/      # Leitura e validação de dados
  analysis/       # Análise com LLM
  generation/     # Geração de posts
  storage/        # Integração OCI
  orchestration/  # Pipeline completo
  app/            # Interface Streamlit

data/             # Arquivos de exemplo
tests/            # Testes
docs/            # Documentação
```

---

## 🌿 Fluxo de trabalho (Gitflow)

Adotamos o fluxo de trabalho Gitflow para manter organização e colaboração em equipe.

- `main`: código estável e pronto para produção
- `develop`: branch principal de integração
- `feature/nome-da-tarefa`: branches de desenvolvimento das funcionalidades

### Passo a passo

1. Atualize a branch de desenvolvimento antes de iniciar a tarefa:

```bash
git checkout develop
git pull origin develop
```

2. Crie uma branch para sua tarefa:

```bash
git checkout -b feature/nome-da-sua-tarefa
```

3. Faça commits durante o desenvolvimento com mensagens claras:

```bash
git add .
git commit -m "feat: implementa funcionalidade X"
```

4. Antes de finalizar, verifique se sua branch está atualizada com a `develop`:

```bash
git checkout develop
git pull origin develop
git checkout feature/nome-da-sua-tarefa
git merge develop
```

5. Quando a feature estiver pronta e validada, envie a branch para o repositório:

```bash
git push origin feature/nome-da-sua-tarefa
```

6. Abra um Pull Request para a `develop` e, após aprovação, volte para a branch principal:

```bash
git checkout develop
git pull origin develop
```

> Regra importante: nunca faça merge direto na `main` sem passar pela `develop`. A `main` deve receber apenas versões estáveis e já validadas.

---

## 👥 Equipe — Grupo 10

| Papel | Responsabilidade |
| --- | --- |
| Tech Lead / Arquitetura | Gitflow, OCI, revisão de PRs |
| Backend — LLM & Prompts | Análise e geração de copy |
| Backend — Pipeline & Dados | Ingestão e orquestração |
| Frontend Streamlit | Interface e curadoria |
| Product / Docs & Demo | Documentação e vídeo demo |

---

## 📌 Observação

Este projeto foi desenvolvido como parte do Hackathon ONE G10 e tem como foco transformar dados comunitários em insight estratégico e conteúdo prático para comunicação digital.
