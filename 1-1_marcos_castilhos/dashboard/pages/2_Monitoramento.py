"""Página: métricas agregadas de monitoramento a partir de logs/interactions.jsonl."""
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Monitoramento", page_icon="📊", layout="wide")
st.title("📊 Monitoramento")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_PATH = BASE_DIR / "logs" / "interactions.jsonl"

if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
    st.info("Ainda não há interações registradas. Use a página 'Simular Cliente' para gerar dados.")
    st.stop()

df = pd.read_json(LOG_PATH, lines=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de chamadas", len(df))
col2.metric("Taxa de fallback", f"{df['fallback_used'].mean():.1%}")
col3.metric("Taxa de guardrail acionado", f"{df['guardrail_triggered'].mean():.1%}")
col4.metric("Latência média", f"{df['latencia_total_ms'].mean():.0f}ms")

col5, col6 = st.columns(2)
col5.metric("Latência p95", f"{df['latencia_total_ms'].quantile(0.95):.0f}ms")
col6.metric("Custo total estimado", f"${df['custo_estimado_usd'].sum():.4f}")

st.subheader("Latência ao longo do tempo")
st.line_chart(df.set_index("timestamp")["latencia_total_ms"])

st.subheader("Últimas interações")
st.dataframe(
    df[["timestamp", "customer_id", "probabilidade_churn", "fallback_used",
        "guardrail_triggered", "latencia_total_ms", "custo_estimado_usd"]].tail(20).iloc[::-1],
    use_container_width=True,
)
