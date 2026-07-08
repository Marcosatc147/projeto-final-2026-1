"""Dashboard Streamlit principal — Agente de Previsão de Churn."""
import streamlit as st

from dashboard import api_client

st.set_page_config(page_title="Agente de Churn", page_icon="📉", layout="wide")

st.title("📉 Agente de Previsão de Churn")
st.markdown(
    "Sistema que classifica o risco de cancelamento de um cliente, explica os "
    "fatores e sugere uma ação de retenção — Trilha 1.1 do projeto final."
)

try:
    status = api_client.health()
    if status["status"] == "ok":
        st.success(f"API conectada — modelo carregado, LLM configurado: {status['llm_configured']}")
    else:
        st.warning("API respondendo em modo degradado (modelo não carregado).")
except Exception as exc:
    st.error(f"Não foi possível conectar à API em {api_client.API_URL}: {exc}")

st.markdown("Use o menu lateral para navegar entre **Simular Cliente** e **Monitoramento**.")
