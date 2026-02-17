"""
ML Model Predictor — loads the trained model and provides inference.

The model is loaded once at module import (or startup) and reused
for all subsequent predictions.
"""

import os

import joblib
import numpy as np
import structlog

logger = structlog.get_logger("ml_predictor")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "fraud_model.joblib")

_model = None


def load_model() -> None:
    """Load the serialised model from disk into module-level cache."""
    global _model  # noqa: PLW0603
    if not os.path.exists(MODEL_PATH):
        logger.warning("model_not_found", path=MODEL_PATH)
        _model = None
        return
    _model = joblib.load(MODEL_PATH)
    logger.info("model_loaded", path=MODEL_PATH)


def predict_fraud_probability(features: dict) -> float:
    """Predict the fraud probability for a single transaction.

    Args:
        features: dict with keys matching FEATURE_COLUMNS from training:
            amount, hour, is_night, is_new_device, is_unusual_location,
            amount_log, amount_zscore

    Returns:
        Probability of fraud (0.0 – 1.0).
        Returns 0.5 if the model hasn't been loaded (safe default).
    """
    if _model is None:
        logger.warning("model_not_loaded_returning_default")
        return 0.5

    feature_order = [
        "amount",
        "hour",
        "is_night",
        "is_new_device",
        "is_unusual_location",
        "amount_log",
        "amount_zscore",
    ]
    X = np.array([[features.get(f, 0) for f in feature_order]])
    proba = _model.predict_proba(X)[0][1]
    return float(proba)
