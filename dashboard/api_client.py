"""Wrapper de chamadas HTTP à API do agente de churn."""
import os

import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000")


def health() -> dict:
    resp = requests.get(f"{API_URL}/health", timeout=5)
    resp.raise_for_status()
    return resp.json()


def sample_customers(n: int = 20) -> list[dict]:
    resp = requests.get(f"{API_URL}/customers/sample", params={"n": n}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def predict(customer_payload: dict) -> dict:
    resp = requests.post(f"{API_URL}/predict", json=customer_payload, timeout=30)
    if resp.status_code >= 400:
        detail = resp.json().get("detail", "Erro desconhecido na API.")
        raise RuntimeError(detail)
    return resp.json()
