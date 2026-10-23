import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="CommunityLab",
    page_icon="🚀",
    layout="wide",
)

st.title("CommunityLab")
st.caption("Motor Inteligente de Transformação e Distribuição para Comunidades Digitais")

with st.container():
    st.markdown(
        """
        O CommunityLab transforma conversas de comunidades digitais em conteúdo estratégico para redes sociais,
        newsletters e materiais de marketing.
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔎 Objetivo")
        st.write(
            "Analisar interações de comunidades, identificar temas relevantes e gerar posts prontos para publicação."
        )
    with col2:
        st.markdown("### 🧠 IA e automação")
        st.write(
            "A solução usa IA para analisar sentimento, tópicos e oportunidades de conteúdo, ajudando a transformar dados em ações."
        )

st.markdown("---")

st.subheader("Fluxo do projeto")
steps = [
    "1. Ingestão de dados em JSON/CSV",
    "2. Análise de sentimento e temas",
    "3. Geração de textos para LinkedIn, X e newsletter",
    "4. Armazenamento e curadoria",
    "5. Visualização em painel para revisão",
]
for step in steps:
    st.write(step)

st.markdown("---")

st.subheader("Configuração atual")
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    st.success("Chave da API do Gemini configurada.")
else:
    st.warning("GOOGLE_API_KEY não encontrada. Copie o arquivo .env.example para .env e preencha as variáveis.")

with st.sidebar:
    st.header("Menu")
    st.page_link("main.py", label="Dashboard principal")
    st.write("Projeto: CommunityLab")
    st.write("Status: em desenvolvimento")

st.markdown("---")

uploaded_file = st.file_uploader("Enviar arquivo JSON/CSV de comunidade", type=["json", "csv"])
if uploaded_file is not None:
    st.success(f"Arquivo recebido: {uploaded_file.name}")
    st.code(uploaded_file.getvalue()[:300].decode("utf-8", errors="ignore"))

st.markdown("---")

st.subheader("Preview de conteúdo gerado")

sample_post = {
    "titulo": "Comunidade impulsiona novas ideias e acelera aprendizado",
    "plataforma": "LinkedIn",
    "texto": "A comunidade tem demonstrado grande engajamento em torno de temas de IA, aprendizado prático e colaboração. Os debates mostram que as pessoas não apenas consomem conhecimento, mas também produzem insights valiosos e compartilham experiências reais.",
}

st.json(sample_post)

if st.button("Simular análise"):
    st.balloons()
    st.success("Análise simulada concluída com sucesso!")
