"""
ML Model Training Pipeline.

Generates a synthetic fraud dataset, trains an XGBoost classifier,
evaluates it, and saves the model artifact to disk via joblib.

Usage:
    python -m app.ml.train_model
"""

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.joblib")
NUM_SAMPLES = 50_000
FRAUD_RATIO = 0.08  # 8 % fraud rate

FEATURE_COLUMNS = [
    "amount",
    "hour",
    "is_night",
    "is_new_device",
    "is_unusual_location",
    "amount_log",
    "amount_zscore",
]


def generate_synthetic_dataset(n: int = NUM_SAMPLES, fraud_ratio: float = FRAUD_RATIO) -> pd.DataFrame:
    """Generate a synthetic financial transaction dataset.

    Features:
        - amount: transaction value (log-normal distribution)
        - hour: hour of day (0–23)
        - is_night: 1 if hour ∈ [22, 6)
        - is_new_device: binary flag
        - is_unusual_location: binary flag
        - amount_log: log(amount + 1)
        - amount_zscore: z-score normalised amount

    Target:
        - is_fraud: 0 or 1
    """
    rng = np.random.default_rng(42)

    n_fraud = int(n * fraud_ratio)
    n_legit = n - n_fraud

    # --- Legitimate transactions ---
    legit_amounts = rng.lognormal(mean=6, sigma=1.2, size=n_legit).clip(1, 200_000)
    legit_hours = rng.choice(range(6, 23), size=n_legit)
    legit_new_device = rng.binomial(1, 0.05, size=n_legit)
    legit_unusual_loc = rng.binomial(1, 0.03, size=n_legit)

    # --- Fraudulent transactions (skewed towards risky patterns) ---
    fraud_amounts = rng.lognormal(mean=9, sigma=1.5, size=n_fraud).clip(5000, 500_000)
    fraud_hours = rng.choice([0, 1, 2, 3, 4, 5, 22, 23], size=n_fraud)
    fraud_new_device = rng.binomial(1, 0.6, size=n_fraud)
    fraud_unusual_loc = rng.binomial(1, 0.55, size=n_fraud)

    amounts = np.concatenate([legit_amounts, fraud_amounts])
    hours = np.concatenate([legit_hours, fraud_hours])
    new_dev = np.concatenate([legit_new_device, fraud_new_device])
    unusual_loc = np.concatenate([legit_unusual_loc, fraud_unusual_loc])
    labels = np.concatenate([np.zeros(n_legit), np.ones(n_fraud)])

    df = pd.DataFrame({
        "amount": amounts,
        "hour": hours,
        "is_night": ((hours >= 22) | (hours < 6)).astype(int),
        "is_new_device": new_dev,
        "is_unusual_location": unusual_loc,
        "is_fraud": labels.astype(int),
    })

    # Derived features
    df["amount_log"] = np.log1p(df["amount"])
    mean_amt, std_amt = df["amount"].mean(), df["amount"].std()
    df["amount_zscore"] = (df["amount"] - mean_amt) / std_amt

    return df.sample(frac=1, random_state=42).reset_index(drop=True)


def train_and_save() -> None:
    """Full training pipeline: generate data → train → evaluate → save."""
    print("━" * 60)
    print("FinShield ML Pipeline — Fraud Detection Model Training")
    print("━" * 60)

    # 1. Generate dataset
    print("\n[1/4] Generating synthetic dataset …")
    df = generate_synthetic_dataset()
    print(f"      Samples: {len(df)}  |  Fraud rate: {df['is_fraud'].mean():.2%}")

    # 2. Split
    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    print(f"\n[2/4] Train/test split — train={len(X_train)}, test={len(X_test)}")

    # 3. Train XGBoost
    print("\n[3/4] Training XGBoost classifier …")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=(1 - FRAUD_RATIO) / FRAUD_RATIO,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # 4. Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    print("\n[4/4] Evaluation results:")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    print(f"      ROC-AUC: {auc:.4f}")

    # 5. Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n✓ Model saved to {MODEL_PATH}")
    print("━" * 60)


if __name__ == "__main__":
    train_and_save()
