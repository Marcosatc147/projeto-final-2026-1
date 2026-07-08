"""Treina o classificador de churn e salva os artefatos em model/artifacts/.

O dataset não é versionado no repositório — é baixado do Kaggle via
kagglehub na primeira execução e cacheado localmente (data/raw/, gitignored).
Requer autenticação Kaggle (variável de ambiente KAGGLEHUB_API_TOKEN ou
~/.kaggle/kaggle.json) configurada previamente.
"""
import json
import shutil
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "telco_churn.csv"
ARTIFACTS_DIR = BASE_DIR / "model" / "artifacts"

KAGGLE_DATASET = "blastchar/telco-customer-churn"


def ensure_dataset() -> None:
    """Baixa o dataset via kagglehub se ainda não estiver em cache local."""
    if DATA_PATH.exists():
        return
    import kagglehub

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset_dir = Path(kagglehub.dataset_download(KAGGLE_DATASET))
    csv_path = next(dataset_dir.glob("*.csv"))
    shutil.copy(csv_path, DATA_PATH)

TARGET_COL = "Churn"
ID_COL = "customerID"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_FEATURES = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]


def load_data() -> pd.DataFrame:
    ensure_dataset()
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(df["MonthlyCharges"])
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(str)
    return df


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", model)])


def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = (df[TARGET_COL] == "Yes").astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    joblib.dump(pipeline, ARTIFACTS_DIR / "churn_model.pkl")
    joblib.dump((X_test, y_test), ARTIFACTS_DIR / "test_split.pkl")

    feature_names = {
        "numeric": NUMERIC_FEATURES,
        "categorical": CATEGORICAL_FEATURES,
    }
    with open(ARTIFACTS_DIR / "feature_names.json", "w") as f:
        json.dump(feature_names, f, indent=2)

    print(f"Modelo treinado. Train: {len(X_train)} | Test: {len(X_test)}")
    print(f"Artefatos salvos em {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
