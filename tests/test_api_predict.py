from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

VALID_PAYLOAD = dict(
    customerID="T-1", gender="Female", SeniorCitizen="0", Partner="Yes", Dependents="No",
    tenure=2, PhoneService="Yes", MultipleLines="No", InternetService="Fiber optic",
    OnlineSecurity="No", OnlineBackup="No", DeviceProtection="No", TechSupport="No",
    StreamingTV="No", StreamingMovies="No", Contract="Month-to-month", PaperlessBilling="Yes",
    PaymentMethod="Electronic check", MonthlyCharges=95.5, TotalCharges=191.0,
)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["model_loaded"] is True


def test_customers_sample_endpoint():
    resp = client.get("/customers/sample?n=3")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_predict_valid_payload():
    resp = client.post("/predict", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["probabilidade_churn"] <= 1
    assert "explicacao" in body
    assert "acao_sugerida" in body
    assert isinstance(body["fallback_used"], bool)


def test_predict_missing_fields_returns_400_not_500():
    resp = client.post("/predict", json={"gender": "Male"})
    assert resp.status_code == 400
    assert "Traceback" not in resp.text


def test_predict_out_of_scope_payload_returns_400():
    resp = client.post("/predict", json={"foo": "bar", "baz": 123})
    assert resp.status_code == 400
