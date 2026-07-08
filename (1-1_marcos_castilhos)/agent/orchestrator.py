"""Orquestrador do agente: decide validar, classificar, explicar, chamar o LLM ou usar fallback."""
import time
from pathlib import Path

import joblib
import pandas as pd

from agent.fallback import template_fallback
from agent.guardrails_output import validate_llm_output
from agent.llm_client import LLMProviderError, explain_churn
from agent.schema import CustomerInput, Fator, PredictionOutput
from model.explain import top_factors
from model.train import CATEGORICAL_FEATURES, NUMERIC_FEATURES

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "artifacts" / "churn_model.pkl"

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = joblib.load(MODEL_PATH)
    return _pipeline


def _customer_summary(customer: CustomerInput) -> str:
    fields = ["tenure", "Contract", "InternetService", "MonthlyCharges", "PaymentMethod", "PaperlessBilling"]
    parts = [f"{f}={getattr(customer, f)}" for f in fields]
    return ", ".join(parts)


async def predict_and_explain(customer: CustomerInput) -> PredictionOutput:
    start = time.monotonic()

    pipeline = get_pipeline()
    row = pd.DataFrame([{
        **{f: getattr(customer, f) for f in NUMERIC_FEATURES},
        **{f: getattr(customer, f) for f in CATEGORICAL_FEATURES},
    }])
    probabilidade = float(pipeline.predict_proba(row)[0, 1])
    fatores = top_factors(pipeline, row)
    fatores_nomes = [f.nome for f in fatores]

    guardrail_triggered = False
    fallback_used = False

    try:
        llm_result = await explain_churn(_customer_summary(customer), probabilidade, fatores)
        valido, motivo = validate_llm_output(llm_result.data, probabilidade, fatores_nomes)
        if valido:
            resultado = llm_result.data
            custo = llm_result.custo_estimado_usd
        else:
            guardrail_triggered = True
            fallback_used = True
            resultado = template_fallback(probabilidade, fatores)
            custo = 0.0
    except LLMProviderError:
        fallback_used = True
        resultado = template_fallback(probabilidade, fatores)
        custo = 0.0

    latencia_ms = int((time.monotonic() - start) * 1000)

    return PredictionOutput(
        customer_id=customer.customerID,
        probabilidade_churn=round(probabilidade, 4),
        fatores=[Fator(nome=f.nome, impacto=f.direcao) for f in fatores],
        explicacao=resultado["explicacao"],
        acao_sugerida=resultado["acao_sugerida"],
        fallback_used=fallback_used,
        guardrail_triggered=guardrail_triggered,
        latencia_ms=latencia_ms,
        custo_estimado_usd=custo,
    )
