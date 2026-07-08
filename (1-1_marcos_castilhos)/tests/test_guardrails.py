import pytest
from pydantic import ValidationError

from agent.guardrails_input import friendly_validation_error
from agent.guardrails_output import validate_llm_output
from agent.schema import CustomerInput

VALID_PAYLOAD = dict(
    customerID="T-1", gender="Female", SeniorCitizen="0", Partner="Yes", Dependents="No",
    tenure=2, PhoneService="Yes", MultipleLines="No", InternetService="Fiber optic",
    OnlineSecurity="No", OnlineBackup="No", DeviceProtection="No", TechSupport="No",
    StreamingTV="No", StreamingMovies="No", Contract="Month-to-month", PaperlessBilling="Yes",
    PaymentMethod="Electronic check", MonthlyCharges=95.5, TotalCharges=191.0,
)


def test_valid_payload_accepted():
    customer = CustomerInput(**VALID_PAYLOAD)
    assert customer.tenure == 2


def test_missing_fields_rejected():
    with pytest.raises(ValidationError):
        CustomerInput(gender="Male")


def test_out_of_domain_value_rejected():
    payload = {**VALID_PAYLOAD, "Contract": "Yearly"}
    with pytest.raises(ValidationError):
        CustomerInput(**payload)


def test_internet_service_no_requires_no_internet_service_fields():
    payload = {**VALID_PAYLOAD, "InternetService": "No", "OnlineSecurity": "Yes"}
    with pytest.raises(ValidationError):
        CustomerInput(**payload)


def test_friendly_validation_error_no_stack_trace():
    try:
        CustomerInput(gender="Male")
    except ValidationError as exc:
        message = friendly_validation_error(exc)
        assert "Traceback" not in message
        assert "Field required" in message


def test_output_guardrail_rejects_short_explanation():
    valido, motivo = validate_llm_output(
        {"explicacao": "curto", "fatores_citados": ["tenure"], "acao_sugerida": "x"},
        probabilidade=0.7,
        fatores_reais=["tenure"],
    )
    assert not valido
    assert motivo == "explicacao_muito_curta"


def test_output_guardrail_rejects_hallucinated_factors():
    valido, motivo = validate_llm_output(
        {
            "explicacao": "Uma explicação longa o suficiente para passar no teste de tamanho mínimo.",
            "fatores_citados": ["fator_inventado_que_nao_existe"],
            "acao_sugerida": "Oferecer desconto.",
        },
        probabilidade=0.7,
        fatores_reais=["tenure", "Contract = Month-to-month"],
    )
    assert not valido
    assert motivo == "fatores_nao_batem_alucinacao"


def test_output_guardrail_accepts_consistent_response():
    valido, motivo = validate_llm_output(
        {
            "explicacao": "Cliente em risco alto devido ao baixo tenure e contrato mensal flexível.",
            "fatores_citados": ["tenure", "Contract = Month-to-month"],
            "acao_sugerida": "Oferecer desconto para migrar para contrato anual.",
        },
        probabilidade=0.7,
        fatores_reais=["tenure", "Contract = Month-to-month"],
    )
    assert valido
    assert motivo == ""
