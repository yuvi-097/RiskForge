"""
Risk scoring service — hybrid ML + rule-based scoring and decision logic.
"""

import structlog

from app.ml.predictor import predict_fraud_probability
from app.services.rule_engine import compute_rule_score

logger = structlog.get_logger("risk_scorer")

# ── Weight configuration ──────────────────────────────────────────────────────
ML_WEIGHT = 0.7
RULE_WEIGHT = 0.3

# ── Decision thresholds ──────────────────────────────────────────────────────
APPROVED_THRESHOLD = 0.4
BLOCKED_THRESHOLD = 0.75


def compute_hybrid_score(ml_score: float, rule_score: float) -> float:
    """Compute weighted hybrid risk score.

    Formula: final_score = 0.7 * ml_score + 0.3 * rule_score
    """
    return ML_WEIGHT * ml_score + RULE_WEIGHT * rule_score


def determine_risk_decision(final_score: float) -> tuple[str, str]:
    """Map a final score to a status and risk level.

    Returns:
        (status, risk_level) tuple.
            - final_score < 0.4  → (APPROVED, LOW)
            - 0.4 ≤ score < 0.75 → (FLAGGED, MEDIUM)
            - score ≥ 0.75       → (BLOCKED, HIGH)
    """
    if final_score < APPROVED_THRESHOLD:
        return "APPROVED", "LOW"
    elif final_score < BLOCKED_THRESHOLD:
        return "FLAGGED", "MEDIUM"
    else:
        return "BLOCKED", "HIGH"


def evaluate_transaction_risk(
    *,
    amount: float,
    hour: int,
    is_new_device: bool,
    is_unusual_location: bool,
) -> dict:
    """Run full risk evaluation pipeline on a transaction.

    Steps:
        1. Compute ML fraud probability.
        2. Compute rule-based score.
        3. Compute hybrid final score.
        4. Determine risk decision.

    Returns:
        dict with ml_score, rule_score, final_score, status, risk_level.
    """
    import numpy as np

    # Build feature dict for the ML model
    features = {
        "amount": amount,
        "hour": hour,
        "is_night": int(hour >= 22 or hour < 6),
        "is_new_device": int(is_new_device),
        "is_unusual_location": int(is_unusual_location),
        "amount_log": float(np.log1p(amount)),
        "amount_zscore": 0.0,  # Will be approximated — ideally from training set stats
    }

    ml_score = predict_fraud_probability(features)
    rule_score = compute_rule_score(
        amount=amount,
        hour=hour,
        is_new_device=is_new_device,
        is_unusual_location=is_unusual_location,
    )
    final_score = compute_hybrid_score(ml_score, rule_score)
    status, risk_level = determine_risk_decision(final_score)

    logger.info(
        "risk_evaluation_complete",
        ml_score=round(ml_score, 4),
        rule_score=round(rule_score, 4),
        final_score=round(final_score, 4),
        status=status,
        risk_level=risk_level,
    )

    return {
        "ml_score": round(ml_score, 4),
        "rule_score": round(rule_score, 4),
        "final_score": round(final_score, 4),
        "status": status,
        "risk_level": risk_level,
    }
