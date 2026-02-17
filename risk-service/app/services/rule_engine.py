"""
Rule-based fraud scoring engine.

Implements deterministic business rules that complement the ML model.

Rules:
    - amount > 50,000  → +30 risk points
    - night (22–06)    → +10 risk points
    - new device       → +20 risk points
    - unusual location → +20 risk points

Maximum raw score = 80 → normalised to 0–1 range.
"""

import structlog

logger = structlog.get_logger("rule_engine")

MAX_RAW_SCORE = 80.0


def compute_rule_score(
    *,
    amount: float,
    hour: int,
    is_new_device: bool,
    is_unusual_location: bool,
) -> float:
    """Calculate a normalised rule-based fraud score.

    Args:
        amount: Transaction value.
        hour: Hour of day (0–23).
        is_new_device: Whether the device ID is new for this user.
        is_unusual_location: Whether the location is unusual for this user.

    Returns:
        Normalised rule score in [0.0, 1.0].
    """
    raw_score = 0

    if amount > 50_000:
        raw_score += 30
        logger.debug("rule_triggered", rule="high_amount", amount=amount)

    if hour >= 22 or hour < 6:
        raw_score += 10
        logger.debug("rule_triggered", rule="night_transaction", hour=hour)

    if is_new_device:
        raw_score += 20
        logger.debug("rule_triggered", rule="new_device")

    if is_unusual_location:
        raw_score += 20
        logger.debug("rule_triggered", rule="unusual_location")

    normalised = min(raw_score / MAX_RAW_SCORE, 1.0)
    logger.info(
        "rule_score_computed",
        raw_score=raw_score,
        normalised=normalised,
    )
    return normalised
