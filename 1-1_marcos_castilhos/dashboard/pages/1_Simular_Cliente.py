"""Página: escolhe/edita um cliente e chama o agente via API."""
import streamlit as st

from dashboard import api_client

st.set_page_config(page_title="Simular Cliente", page_icon="🧑", layout="wide")
st.title("🧑 Simular Cliente")

FIELD_OPTIONS = {
    "gender": ["Male", "Female"],
    "SeniorCitizen": ["0", "1"],
    "Partner": ["Yes", "No"],
    "Dependents": ["Yes", "No"],
    "PhoneService": ["Yes", "No"],
    "MultipleLines": ["Yes", "No", "No phone service"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "OnlineSecurity": ["Yes", "No", "No internet service"],
    "OnlineBackup": ["Yes", "No", "No internet service"],
    "DeviceProtection": ["Yes", "No", "No internet service"],
    "TechSupport": ["Yes", "No", "No internet service"],
    "StreamingTV": ["Yes", "No", "No internet service"],
    "StreamingMovies": ["Yes", "No", "No internet service"],
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaperlessBilling": ["Yes", "No"],
    "PaymentMethod": [
        "Electronic check", "Mailed check",
        "Bank transfer (automatic)", "Credit card (automatic)",
    ],
}

if "customer_data" not in st.session_state:
    st.session_state.customer_data = None

modo = st.radio("Como deseja definir o cliente?", ["Escolher da base", "Inserir manualmente"], horizontal=True)

customer = {}

if modo == "Escolher da base":
    if st.button("Carregar amostra de clientes"):
        st.session_state.sample = api_client.sample_customers(n=20)

    sample = st.session_state.get("sample", [])
    if sample:
        options = {f"{c['customerID']} (tenure={c['tenure']}, {c['Contract']})": c for c in sample}
        choice = st.selectbox("Selecione um cliente", list(options.keys()))
        customer = options[choice]
    else:
        st.info("Clique em 'Carregar amostra de clientes' para escolher um perfil real da base.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        customer["customerID"] = st.text_input("ID do cliente", value="MANUAL-001")
        customer["tenure"] = st.number_input("Tenure (meses)", min_value=0, max_value=100, value=12)
        customer["MonthlyCharges"] = st.number_input("Cobrança mensal", min_value=0.0, value=70.0)
        customer["TotalCharges"] = st.number_input("Cobrança total", min_value=0.0, value=840.0)
    with col2:
        for field in ["gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService", "MultipleLines"]:
            customer[field] = st.selectbox(field, FIELD_OPTIONS[field])
    with col3:
        for field in ["InternetService", "Contract", "PaperlessBilling", "PaymentMethod"]:
            customer[field] = st.selectbox(field, FIELD_OPTIONS[field])
        for field in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]:
            customer[field] = st.selectbox(field, FIELD_OPTIONS[field])

if customer and st.button("🔍 Analisar", type="primary"):
    with st.spinner("Consultando o agente..."):
        try:
            result = api_client.predict(customer)
            st.session_state.last_result = result
        except Exception as exc:
            st.error(f"Erro ao consultar o agente: {exc}")
            st.session_state.last_result = None

result = st.session_state.get("last_result")
if result:
    if result["fallback_used"]:
        st.warning("⚠️ Resposta gerada sem IA generativa — modelo estatístico apenas (fallback).")

    prob = result["probabilidade_churn"]
    cor = "🔴" if prob > 0.6 else "🟡" if prob > 0.3 else "🟢"
    st.metric(f"{cor} Probabilidade de Churn", f"{prob:.1%}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Fatores")
        for f in result["fatores"]:
            emoji = "⬆️" if f["impacto"] == "aumenta risco" else "⬇️"
            st.write(f"{emoji} **{f['nome']}** — {f['impacto']}")
    with col_b:
        st.subheader("Explicação do agente")
        st.write(result["explicacao"])
        st.subheader("Ação sugerida")
        st.info(result["acao_sugerida"])

    st.caption(
        f"Latência: {result['latencia_ms']}ms | "
        f"Custo estimado: ${result['custo_estimado_usd']:.6f} | "
        f"Guardrail acionado: {result['guardrail_triggered']}"
    )
