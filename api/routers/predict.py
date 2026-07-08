"""Endpoints POST /predict, GET /health, GET /customers/sample."""
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from agent.guardrails_input import friendly_validation_error
from agent.orchestrator import get_pipeline, predict_and_explain
from agent.schema import CustomerInput, PredictionOutput
from api.logging_middleware import log_interaction
from model.train import ensure_dataset

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "telco_churn.csv"


@router.get("/health")
def health():
    model_loaded = True
    try:
        get_pipeline()
    except Exception:
        model_loaded = False
    return {
        "status": "ok" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "llm_configured": bool(os.environ.get("GEMINI_API_KEY")),
    }


@router.get("/customers/sample")
def customers_sample(n: int = 20):
    ensure_dataset()
    df = pd.read_csv(DATA_PATH)
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(str)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(df["MonthlyCharges"])
    sample = df.sample(n=min(n, len(df)), random_state=None)
    return sample.to_dict(orient="records")


@router.post("/predict", response_model=PredictionOutput)
async def predict(request: Request, payload: dict):
    try:
        customer = CustomerInput(**payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=friendly_validation_error(exc))

    result = await predict_and_explain(customer)

    log_interaction({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", None),
        "customer_id": result.customer_id,
        "input_summary": {
            "tenure": customer.tenure,
            "contract": customer.Contract,
            "internet_service": customer.InternetService,
            "monthly_charges": customer.MonthlyCharges,
        },
        "probabilidade_churn": result.probabilidade_churn,
        "fallback_used": result.fallback_used,
        "guardrail_triggered": result.guardrail_triggered,
        "latencia_total_ms": result.latencia_ms,
        "custo_estimado_usd": result.custo_estimado_usd,
    })

    return result
