"""Extrai os fatores mais importantes para a previsão de um cliente específico.

P0: usa os coeficientes do LogisticRegression multiplicados pelos valores
transformados (padronizados/one-hot) do cliente — dá a contribuição real de
cada feature transformada para o logit daquela instância, sem depender do
pacote `shap`.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


@dataclass
class Factor:
    nome: str
    contribuicao: float
    direcao: str  # "aumenta risco" | "reduz risco"


def _feature_names_out(pipeline: Pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocessor"]
    return list(preprocessor.get_feature_names_out())


def _readable_name(raw_name: str) -> str:
    # ex: "cat__Contract_Month-to-month" -> "Contract = Month-to-month"
    name = raw_name.split("__", 1)[-1]
    if "_" in name:
        base, _, value = name.rpartition("_")
        return f"{base} = {value}"
    return name


def top_factors(pipeline: Pipeline, customer_row: pd.DataFrame, top_n: int = 5) -> list[Factor]:
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    X_transformed = preprocessor.transform(customer_row)
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()
    X_transformed = X_transformed[0]

    coefs = classifier.coef_[0]
    contributions = coefs * X_transformed

    names = _feature_names_out(pipeline)
    order = np.argsort(-np.abs(contributions))[:top_n]

    factors = []
    for idx in order:
        contrib = float(contributions[idx])
        if abs(contrib) < 1e-9:
            continue
        factors.append(
            Factor(
                nome=_readable_name(names[idx]),
                contribuicao=round(contrib, 4),
                direcao="aumenta risco" if contrib > 0 else "reduz risco",
            )
        )
    return factors
