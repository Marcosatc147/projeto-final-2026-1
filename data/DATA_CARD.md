# Data Card — Telco Customer Churn

## Origem
- **Fonte:** Kaggle, dataset [`blastchar/telco-customer-churn`](https://www.kaggle.com/datasets/blastchar/telco-customer-churn).
- **Proveniência:** amostra da IBM, distribuída publicamente como dataset de exemplo para análise de churn (IBM Sample Data Sets).
- **Licença:** dataset publicado no Kaggle sob os termos padrão de uso do Kaggle (uso educacional/não comercial); é uma amostra sintética/anonimizada da IBM, sem CPF, nome ou dado pessoal identificável.
- **Data de download:** 2026-07-08, via `kagglehub.dataset_download`.
- **Nota:** o CSV bruto não é versionado no repositório (ver `.gitignore`) — `model/train.py::ensure_dataset()` baixa automaticamente na primeira execução, exigindo um token Kaggle (`KAGGLEHUB_API_TOKEN`) configurado no ambiente.

## Estrutura
- **Linhas:** 7.043 clientes.
- **Colunas:** 21 (20 features + 1 alvo).
- **Alvo:** `Churn` (`Yes`/`No`) — classificação binária.
- **Desbalanceamento:** ~26,5% `Yes` / ~73,5% `No` — desbalanceamento moderado, tratado no treino via `class_weight="balanced"` (ver `model/train.py`).

## Colunas principais
| Coluna | Tipo | Descrição |
|---|---|---|
| `customerID` | string | identificador único, não usado como feature |
| `gender`, `SeniorCitizen`, `Partner`, `Dependents` | categórica/binária | perfil demográfico |
| `tenure` | numérica | meses de permanência |
| `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` | categórica | serviços contratados |
| `Contract`, `PaperlessBilling`, `PaymentMethod` | categórica | condições contratuais |
| `MonthlyCharges`, `TotalCharges` | numérica | valores cobrados (`TotalCharges` contém strings vazias para clientes novos — tratado como NaN e imputado) |
| `Churn` | binária | alvo |

## Vieses e limitações conhecidas
- Dataset sintético/de exemplo da IBM — não reflete necessariamente a distribuição real de uma operadora específica; usar como prova de conceito, não como base para decisão de negócio real sem revalidação.
- Não há colunas de raça/etnia ou renda diretamente, mas `Contract`, `PaymentMethod` e `InternetService` podem correlacionar indiretamente com faixa de renda — risco de viés indireto discutido na seção de Impactos e Ética do relatório.
- Sem dados temporais (não é uma série temporal) — o modelo prevê risco em um corte transversal, não tendência ao longo do tempo.
- `SeniorCitizen` é a única variável demográfica sensível explícita; deve ser tratada com cautela na interpretação das explicações do agente.

## Uso no projeto
- Treina o classificador de churn (`model/train.py`).
- Alimenta o agente como contexto estruturado (perfil do cliente + saída do modelo) — não é usado para RAG/few-shot, é consultado em tempo real via `GET /customers/sample` para popular o dashboard de demonstração.
