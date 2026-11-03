# Arquitetura do Sistema - CommunityLab

O projeto está estruturado em uma arquitetura de três camadas para garantir a separação de responsabilidades, facilitando o trabalho em equipe sem conflitos entre frontend, lógica de IA e persistência.

## Diagrama de Arquitetura (Fluxo de Dados)

```mermaid
graph TD
    A[Dados de Entrada: JSON / CSV] -->|Ingestão e Validação| B[Camada de Apresentação: Streamlit Web App]
    B -->|Orquestração de Prompts| C[Camada de Serviço: Python + LangChain + Google Gemini]
    C -->|Geração de Ativos: Posts e FAQs| D[Curadoria Humana e Aprovação]
    D -->|Persistência Final| E[Camada de Persistência: OCI Object Storage Always Free]