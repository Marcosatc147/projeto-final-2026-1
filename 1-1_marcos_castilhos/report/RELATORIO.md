# Relatório Final — Agente de Previsão de Churn

**Link da aplicação:** _pendente de deploy — ver [`DEPLOY.md`](DEPLOY.md)_
**Link do repositório:** https://github.com/Marcosatc147/projeto-final-2026-1
**Integrante:** Marcos Castilhos (trabalho individual)

---

## Definição do problema

**Trilha escolhida:** Trilha 1 — Predição tabular, Projeto 1.1 — Previsão de churn.

### Que dor é essa e por que importa?

Empresas de telecomunicações perdem receita recorrente quando clientes cancelam o
serviço (churn). Identificar clientes em risco *antes* do cancelamento permite ao
time de retenção agir de forma direcionada (desconto, upgrade, contato proativo) em
vez de reagir depois que o cliente já saiu — quando o custo de reconquista é muito
maior que o custo de retenção.

### Quem são os stakeholders?

- **Time de retenção/CRM:** usa a previsão e a explicação para priorizar quais
  clientes abordar e com qual argumento.
- **Cliente final:** é afetado indiretamente — uma previsão errada pode significar
  receber uma oferta desnecessária (falso positivo) ou não receber uma oferta que
  precisava (falso negativo, e nesse caso perde o cliente).
- **Gestão comercial:** usa os agregados do sistema para medir eficácia das ações de
  retenção e o custo operacional do agente (custo por chamada de LLM).

### Métrica de sucesso

- **Negócio:** redução na taxa de churn mensal após ações de retenção direcionadas
  pelas previsões do agente (não medido neste projeto — seria o próximo passo com
  dados de produção reais).
- **Técnica:** recall da classe minoritária (churn = "Yes") e PR-AUC, priorizados
  sobre acurácia dado o desbalanceamento de classes (~26,5% churn). Um falso
  negativo (cliente em risco não identificado) custa mais caro ao negócio do que um
  falso positivo (oferta a um cliente que não ia cancelar).

---

## Como o sistema é montado

### Diagrama de arquitetura

Ver [`diagrama_arquitetura.md`](diagrama_arquitetura.md) para o diagrama completo
(Mermaid) e a descrição de cada componente. Resumo do fluxo:

```
Dashboard (Streamlit) → API (FastAPI) → Guardrail de entrada → Classificador (LogReg)
  → Explicabilidade (coeficientes) → [Gemini LLM ou Fallback determinístico]
  → Guardrail de saída → Resposta → Log JSONL → Dashboard (Monitoramento)
```

### Agent/model exploration

Decisões consideradas antes de fechar a versão final:

- **Tipo de agente — prompt estruturado vs. tool-use/function-calling.** Optamos por
  um orquestrador Python que decide o fluxo (validar → classificar → explicar →
  chamar LLM ou fallback) com **uma única chamada estruturada ao LLM**, em vez de dar
  ao LLM tools para "buscar dados do cliente" via function-calling. Justificativa: o
  fluxo é sempre o mesmo para qualquer cliente (não há decisão dinâmica de "quais
  dados buscar") — os dados já estão pré-computados quando o LLM é chamado. Isso é o
  padrão "single LLM call com contexto pré-computado", suficiente e mais simples de
  operar/depurar do que um agente com tool-use real. O "raciocínio" e a "ação" do
  agente vêm da combinação do racional estatístico do classificador+coeficientes com
  o racional em linguagem natural do LLM, orquestrados por lógica determinística.
- **Classificador — LogisticRegression vs. Gradient Boosting/XGBoost.** Optamos por
  `LogisticRegression(class_weight="balanced")` como baseline: lida com o
  desbalanceamento sem precisar de SMOTE, é rápido de treinar/servir, e sua
  explicabilidade (coeficientes × valores do cliente) é direta, sem depender do
  pacote `shap`. XGBoost+SHAP foi considerado como upgrade (métricas potencialmente
  melhores), mas não foi implementado dado o prazo — fica como próximo passo.
- **LLM — Claude vs. Gemini.** A primeira versão do plano usava a API da Claude
  (Sonnet 5). Trocamos para o **Gemini 3.1 Flash Lite** (Google AI Studio) a pedido
  do autor, que queria testar uma opção com tier gratuito antes de decidir por um
  provedor pago — Groq foi cogitado como alternativa futura. A troca não exigiu
  mudanças na arquitetura: `agent/llm_client.py` mantém a mesma interface
  (`explain_churn`) usada pelo orquestrador.

### Deployment

- **Empacotamento:** dois `Dockerfile`s (API e dashboard) e um `docker-compose.yml`
  que sobe os dois serviços com `docker compose up --build`. Modelo treinado
  (`churn_model.pkl`) é versionado no repositório — não precisa re-treinar no build.
  O dataset bruto (CSV) **não** é versionado; é baixado via `kagglehub` na primeira
  execução (requer `KAGGLEHUB_API_TOKEN`).
- **Hospedagem:** API no Render (Docker), dashboard no Streamlit Community Cloud —
  ver [`DEPLOY.md`](DEPLOY.md) para o passo a passo e para os links finais.
- **Entrada em produção:** o dashboard consome a API publicada via variável de
  ambiente `API_URL`; localmente, a rede Docker resolve o hostname `api` entre os
  containers (testado com `docker compose exec dashboard python -c "requests.get('http://api:8000/health')"`).

### CI/CD

Não implementado neste projeto dado o prazo — os testes (`pytest`) e a avaliação do
agente (`eval/run_agent_eval.py`) são rodados manualmente antes de cada commit
importante. Próximo passo natural: GitHub Actions rodando `pytest` a cada PR.

**Estratégia de confiabilidade (fallback):** ver seção "Guardrails" abaixo — quando o
LLM falha, tem timeout, ou sua resposta é rejeitada pelo guardrail de saída, o
sistema cai em um template determinístico sem chamada de rede, sempre disponível.

---

## Descrição do agente

### Modelo base e ferramentas

- **Classificador:** `LogisticRegression` (scikit-learn) com `class_weight="balanced"`,
  dentro de um `Pipeline` com `OneHotEncoder` + `StandardScaler`. Métricas no split de
  teste (20%, estratificado):

  | Métrica | Valor |
  |---|---|
  | ROC-AUC | 0.8415 |
  | PR-AUC (average precision) | 0.6325 |
  | F1 (classe "Yes") | 0.6136 |
  | Recall (classe "Yes") | 0.7834 |

  Acurácia foi deliberadamente omitida como métrica principal — não é confiável dado
  o desbalanceamento (~26,5% de churn na base).

- **LLM:** Gemini 3.1 Flash Lite (Google AI Studio), escolhido por ter um tier
  gratuito viável para um projeto acadêmico de curta duração. Chamado uma única vez
  por predição, com saída JSON estruturada (`response_schema`), sem tool-use.

- **Ferramentas do agente:** o classificador e a função de explicabilidade
  (`model/explain.py`) são as "ferramentas" que o orquestrador consulta antes de
  formar o contexto passado ao LLM — não são tools expostas via function-calling ao
  próprio LLM, e sim chamadas diretas de código Python.

### Dados e contexto

Dataset Telco Customer Churn (Kaggle/IBM), 7.043 clientes, 21 colunas. Usado para
treinar o classificador (offline) e, em tempo real, para popular o seletor de
clientes de demonstração no dashboard (`GET /customers/sample`). Ver
[`data/DATA_CARD.md`](../data/DATA_CARD.md) para origem, licença e vieses conhecidos.

### Guardrails

**Entrada** (`agent/guardrails_input.py` + `agent/schema.py`):
- Validação de schema via Pydantic — tipos, valores dentro do domínio esperado
  (ex: `Contract` só aceita `"Month-to-month"`, `"One year"`, `"Two year"`).
- Validação de coerência entre campos (ex: se `InternetService == "No"`, os campos
  de serviços de internet devem ser `"No internet service"`).
- Payload inválido → HTTP 400 com mensagem amigável, nunca stack trace cru.

**Saída** (`agent/guardrails_output.py`):
- Rejeita explicações muito curtas ou boilerplate.
- Rejeita respostas contraditórias com a probabilidade prevista (ex: sugerir
  retenção urgente para um cliente de baixo risco).
- Rejeita respostas cujos "fatores citados" não têm overlap com os fatores reais
  calculados pelo classificador — sinal de alucinação.
- Quando qualquer guardrail de saída dispara, o sistema cai no fallback determinístico.

### Iterações de prompt e design

- O prompt inicial não pedia explicitamente para "não sugerir retenção agressiva em
  caso de baixo risco" — isso foi adicionado ao `SYSTEM_PROMPT`
  (`agent/prompts.py`) depois de observar, nos casos de teste, que era importante
  reforçar esse comportamento explicitamente para casos de risco baixo (< 0.3).
- Consideramos usar `additionalProperties: false` no schema JSON (boa prática comum
  em outras APIs de LLM), mas a API do Gemini rejeita esse campo — o schema teve que
  ser ajustado para omiti-lo.
- O guardrail de saída original comparava fatores citados por igualdade exata de
  string; isso rejeitava respostas válidas do LLM que citavam os fatores com
  fraseio ligeiramente diferente do formato interno (ex: "Contract mensal" vs.
  `"Contract = Month-to-month"`). Ajustamos para uma checagem de overlap por
  substring no nome-base do fator.

---

## Avaliação do sistema

### Performance

- **Classificador:** ver métricas acima (`model/artifacts/metrics.json`).
- **Agente:** 12 casos de teste end-to-end (`eval/agent_test_cases.yaml`, executados
  por `eval/run_agent_eval.py`), cobrindo casos normais (risco alto/médio/baixo),
  dados faltantes, valores fora do domínio, payload completamente fora de escopo,
  tentativa de prompt injection via `customerID`, e fallback forçado (sem API key).
  **Resultado: 12/12 casos passaram** — ver [`../eval/eval_report.md`](../eval/eval_report.md).
- **Testes automatizados:** 17 testes `pytest` cobrindo guardrails, fallback e
  endpoints da API — todos passando.

### UX

- O dashboard mostra a probabilidade de churn com indicador visual de cor
  (verde/amarelo/vermelho), os fatores com seta de direção do impacto, a explicação
  em texto corrido e a ação sugerida em destaque.
- Quando o fallback é acionado, um aviso visual explícito aparece
  ("⚠️ Resposta gerada sem IA generativa"), para que o usuário saiba que está vendo
  uma resposta degradada, não a explicação completa do LLM.
- Latência típica observada: ~1.5-2.5s por chamada (dominada pela chamada ao
  Gemini); o fallback responde em ~15-20ms.
- Erros de validação (payload incompleto/inválido) retornam mensagem clara sobre
  quais campos estão faltando/errados, sem stack trace.

---

## Demonstração

_Link do vídeo: pendente de gravação — a ser adicionado antes da entrega final
(13/07/2026)._

---

## Reflexão sobre o que aprenderam

**O que funcionou bem:**
- A decisão de não usar tool-use/function-calling simplificou bastante a
  implementação e a depuração, sem perder o caráter de "agente" (o orquestrador
  Python é o verdadeiro tomador de decisão do fluxo).
- O guardrail de saída baseado em overlap de fatores citados é simples e barato
  (sem precisar de um segundo LLM como "juiz"), e pegou casos reais de
  inconsistência durante o desenvolvimento.
- Trocar de provedor de LLM (Claude → Gemini) foi rápido porque a interface do
  `llm_client.py` já estava isolada do resto do agente desde o início.

**O que não funcionou como planejado:**
- O plano original previa usar a Claude API; o autor preferiu testar uma opção
  gratuita (Gemini) primeiro. Isso é documentado como decisão consciente, não como
  limitação.
- SHAP e XGBoost (considerados no plano como upgrade) não foram implementados —
  LogisticRegression com coeficientes já atendeu bem ao prazo e à necessidade de
  explicabilidade.
- CI/CD não foi implementado — os testes rodam manualmente.
- O deploy em produção (Render + Streamlit Cloud) ainda está pendente no momento
  da escrita deste relatório — requer login manual em serviços de terceiros.

**Próximos passos com mais tempo:**
- Implementar CI (GitHub Actions rodando `pytest` a cada PR).
- Avaliar XGBoost + SHAP como upgrade de classificador/explicabilidade.
- Adicionar uma tool real ao LLM (ex: `get_similar_retained_customers`) para
  reforçar a sugestão de ação com um exemplo real de cliente parecido retido —
  tornaria o "agente" mais próximo de tool-use de fato, hoje é um upgrade opcional
  já identificado no plano técnico do projeto.
- Medir a métrica de negócio real (redução de churn após ação) com dados de
  produção, hoje impossível de avaliar com um dataset estático.

---

## Impactos e ética

- **Quem pode ser prejudicado por um erro do sistema?** Um falso negativo (cliente
  em risco não identificado) significa que a empresa não tenta reter esse cliente —
  o cliente não é diretamente prejudicado, mas a empresa perde receita. Um falso
  positivo pode gerar uma oferta desnecessária a um cliente estável, um custo
  pequeno mas real.
- **Risco de viés entre grupos.** O dataset não tem colunas diretas de raça/etnia ou
  renda, mas `Contract`, `PaymentMethod` e `InternetService` podem correlacionar
  indiretamente com faixa socioeconômica — um viés indireto que pode levar o
  classificador (e por extensão o agente) a associar certos perfis de pagamento a
  maior risco de forma que reflita desigualdade estrutural, não comportamento real.
  Isso não foi auditado neste projeto (P1 natural: análise de fairness por subgrupo).
- **Privacidade e segurança.** O dataset é uma amostra sintética/anonimizada da IBM,
  sem PII real. Ainda assim, o sistema foi desenhado para **não logar o payload
  completo do cliente** (`api/routers/predict.py`) — apenas um resumo com os campos
  relevantes para a explicação — como boa prática caso o sistema um dia processe
  dados reais de clientes.
- **Segurança do agente.** O único campo de texto livre no schema é `customerID`,
  testado explicitamente contra tentativa de prompt injection (caso 10 da avaliação)
  — o agente não segue instruções embutidas nesse campo, porque ele é tratado como
  dado estruturado, nunca como instrução ao LLM.

---

## Referências

- **Dataset:** [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
  (Kaggle, amostra IBM).
- **Modelo/LLM:** [Gemini API](https://ai.google.dev/) (Google AI Studio),
  modelo `gemini-3.1-flash-lite`.
- **Bibliotecas:** scikit-learn, FastAPI, Streamlit, `google-genai`, pandas, pytest.
- **Kaggle download:** `kagglehub`.
