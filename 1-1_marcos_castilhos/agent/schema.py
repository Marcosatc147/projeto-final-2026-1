"""Schemas Pydantic para entrada e saída do agente de churn."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class CustomerInput(BaseModel):
    customerID: Optional[str] = None
    gender: Literal["Male", "Female"]
    SeniorCitizen: Literal["0", "1"]
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(ge=0, le=100)
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal[
        "Electronic check", "Mailed check",
        "Bank transfer (automatic)", "Credit card (automatic)",
    ]
    MonthlyCharges: float = Field(gt=0, le=1000)
    TotalCharges: float = Field(ge=0, le=100000)

    @model_validator(mode="after")
    def check_internet_service_consistency(self):
        internet_dependent_fields = [
            "OnlineSecurity", "OnlineBackup", "DeviceProtection",
            "TechSupport", "StreamingTV", "StreamingMovies",
        ]
        if self.InternetService == "No":
            for field_name in internet_dependent_fields:
                if getattr(self, field_name) != "No internet service":
                    raise ValueError(
                        f"{field_name} deve ser 'No internet service' quando "
                        "InternetService = 'No'"
                    )
        if self.PhoneService == "No" and self.MultipleLines != "No phone service":
            raise ValueError(
                "MultipleLines deve ser 'No phone service' quando PhoneService = 'No'"
            )
        return self


class Fator(BaseModel):
    nome: str
    impacto: str


class PredictionOutput(BaseModel):
    customer_id: Optional[str]
    probabilidade_churn: float
    fatores: list[Fator]
    explicacao: str
    acao_sugerida: str
    fallback_used: bool
    guardrail_triggered: bool
    latencia_ms: int
    custo_estimado_usd: float


class LLMStructuredResponse(BaseModel):
    """Formato esperado da resposta estruturada da Claude API."""
    explicacao: str
    fatores_citados: list[str]
    acao_sugerida: str
