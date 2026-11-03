# Arquitetura do Sistema — CommunityLab

Este documento descreve a organização técnica e o fluxo de dados planejado para o CommunityLab. A arquitetura utiliza três camadas principais para separar a interface, o processamento com inteligência artificial e a persistência dos dados aprovados.

## Visão geral

O CommunityLab recebe informações da comunidade em arquivos JSON ou CSV, processa os dados por meio de serviços de IA e apresenta os conteúdos gerados para revisão humana. Somente os ativos aprovados são enviados à camada de persistência.

Essa separação permite que a equipe desenvolva, teste e mantenha as interfaces, os componentes de IA e o armazenamento de forma independente.

## Diagrama de arquitetura

```mermaid
flowchart TD
    A["Dados de entrada: JSON / CSV"] -->|"Ingestão e validação"| B["Camada de apresentação: Streamlit Web App"]
    B -->|"Orquestração de prompts"| C["Camada de serviço: Python + LangChain + Google Gemini"]
    C -->|"Geração de ativos: posts e FAQs"| D["Curadoria humana e aprovação"]
    D -->|"Persistência final"| E["Camada de persistência: OCI Object Storage Always Free"]
```

## Camadas da aplicação

### Camada de apresentação

Responsável pela interação com os usuários. A aplicação web construída com Streamlit permite enviar os dados de entrada, acompanhar o processamento, visualizar os ativos gerados e realizar a curadoria dos resultados.

Tecnologias principais:

- Streamlit
- Interface web para usuários

### Camada de serviço

Contém as regras de negócio e o processamento do conteúdo. Nesta camada, os dados são preparados para os prompts, enviados ao modelo de linguagem e transformados em posts e FAQs.

Tecnologias principais:

- Python
- LangChain
- Google Gemini

### Camada de persistência

Armazena os ativos que passaram pela curadoria humana e receberam aprovação. O armazenamento final utiliza OCI Object Storage, no plano Always Free.

## Fluxo de dados

1. O usuário fornece dados da comunidade no formato JSON ou CSV.
2. A camada de apresentação envia os arquivos para a camada de serviço.
3. Os dados passam pela ingestão e validação.
4. Os prompts são preparados e enviados ao Google Gemini por meio do LangChain.
5. O modelo gera posts e FAQs.
6. Os ativos gerados são apresentados para curadoria humana.
7. Após a aprovação, os conteúdos são armazenados no OCI Object Storage.

## Responsabilidades por etapa

| Etapa | Responsabilidade | Resultado esperado |
| --- | --- | --- |
| Entrada de dados | Receber arquivos JSON ou CSV | Dados disponíveis para processamento |
| Ingestão | Validar estrutura, conteúdo e formato dos dados | Dados validados |
| Orquestração | Coordenar prompts e chamadas aos serviços de IA | Solicitações de IA padronizadas |
| Geração | Criar posts e FAQs a partir dos dados processados | Ativos de conteúdo gerados |
| Curadoria | Permitir análise, edição e aprovação humana | Conteúdos validados pela equipe |
| Persistência | Armazenar os ativos aprovados | Conteúdo disponível no OCI Object Storage |

## Considerações técnicas

- Os dados de entrada devem passar por validação antes do processamento.
- As integrações com serviços externos devem manter suas credenciais fora do controle de versão.
- O modelo de IA atua como componente gerador, enquanto a curadoria humana é responsável pela validação final.
- A camada de apresentação não deve implementar diretamente as regras de integração com o modelo ou com o armazenamento.
- Os componentes devem ser desacoplados para facilitar testes, substituições e evolução da arquitetura.

## Estado da implementação

Esta arquitetura representa o desenho planejado da aplicação. Tecnologias de IA e persistência podem permanecer declaradas ou em desenvolvimento até que suas integrações estejam implementadas. Para o estado detalhado da implementação e da infraestrutura, consulte a [Documentação técnica — CommunityLab](ARQUITETURA_E_STACK.md).
