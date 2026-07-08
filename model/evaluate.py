"""Avalia o classificador treinado no split de teste e salva metrics.json."""
import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "model" / "artifacts"


def main():
    pipeline = joblib.load(ARTIFACTS_DIR / "churn_model.pkl")
    X_test, y_test = joblib.load(ARTIFACTS_DIR / "test_split.pkl")

    y_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "pr_auc": round(average_precision_score(y_test, y_proba), 4),
        "f1_minority": round(f1_score(y_test, y_pred), 4),
        "recall_minority": round(recall_score(y_test, y_pred), 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "test_size": len(y_test),
        "note": "Acurácia deliberadamente omitida como métrica principal — dataset "
                "desbalanceado (~26.5% churn); ROC-AUC/PR-AUC/recall da classe "
                "minoritária são mais informativas.",
    }

    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
