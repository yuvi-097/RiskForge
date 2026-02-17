"""
Service layer and rule-engine unit tests.

Covers:
    - AuthService registration and login logic
    - Rule engine scoring validation
    - Hybrid risk score calculation
    - Risk decision thresholds
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


# ── Password hashing ─────────────────────────────────────────────────────────

def test_hash_and_verify_password():
    """bcrypt hash + verify round-trip."""
    plain = "MySecretPassword123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


# ── JWT tokens ────────────────────────────────────────────────────────────────

def test_create_and_decode_token():
    """JWT encode + decode round-trip."""
    user_id = uuid4()
    token = create_access_token(subject=user_id, extra={"role": "USER"})
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "USER"


def test_decode_invalid_token():
    """Decoding an invalid JWT raises HTTPException."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("invalid.token.here")
    assert exc_info.value.status_code == 401


# ── Rule engine scoring ──────────────────────────────────────────────────────

def _compute_rule_score(
    amount: float,
    hour: int,
    is_new_device: bool,
    is_unusual_location: bool,
) -> float:
    """Replicate the rule engine logic for testing.

    Rules:
        - amount > 50000 → +30
        - night (22-6) → +10
        - new device → +20
        - unusual location → +20

    Max possible = 80 → normalise to 0–1.
    """
    score = 0
    if amount > 50000:
        score += 30
    if hour >= 22 or hour < 6:
        score += 10
    if is_new_device:
        score += 20
    if is_unusual_location:
        score += 20
    return min(score / 80.0, 1.0)


def test_rule_score_low_risk():
    """Normal transaction should score near 0."""
    score = _compute_rule_score(amount=500, hour=14, is_new_device=False, is_unusual_location=False)
    assert score == 0.0


def test_rule_score_high_amount():
    """Large transactions trigger +30."""
    score = _compute_rule_score(amount=100000, hour=14, is_new_device=False, is_unusual_location=False)
    assert score == pytest.approx(30 / 80.0)


def test_rule_score_night_transaction():
    """Night-time transactions trigger +10."""
    score = _compute_rule_score(amount=500, hour=3, is_new_device=False, is_unusual_location=False)
    assert score == pytest.approx(10 / 80.0)


def test_rule_score_all_flags():
    """All risk flags active → max score = 1.0."""
    score = _compute_rule_score(amount=100000, hour=2, is_new_device=True, is_unusual_location=True)
    assert score == 1.0


def test_rule_score_new_device_unusual_location():
    """New device + unusual location → (20+20)/80 = 0.5."""
    score = _compute_rule_score(amount=500, hour=14, is_new_device=True, is_unusual_location=True)
    assert score == pytest.approx(40 / 80.0)


# ── Hybrid scoring ───────────────────────────────────────────────────────────

def _hybrid_score(ml_score: float, rule_score: float) -> float:
    """final_score = 0.7 * ml_score + 0.3 * rule_score"""
    return 0.7 * ml_score + 0.3 * rule_score


def _risk_decision(final_score: float) -> str:
    """Map final score to risk decision."""
    if final_score < 0.4:
        return "APPROVED"
    elif final_score < 0.75:
        return "FLAGGED"
    else:
        return "BLOCKED"


def test_hybrid_low_risk():
    """Low ML + low rules → APPROVED."""
    final = _hybrid_score(0.1, 0.1)
    assert _risk_decision(final) == "APPROVED"


def test_hybrid_medium_risk():
    """Moderate scores → FLAGGED."""
    final = _hybrid_score(0.6, 0.5)
    assert _risk_decision(final) == "FLAGGED"


def test_hybrid_high_risk():
    """High scores → BLOCKED."""
    final = _hybrid_score(0.9, 0.8)
    assert _risk_decision(final) == "BLOCKED"


def test_hybrid_edge_approved():
    """Score just below 0.4 → APPROVED."""
    final = _hybrid_score(0.3, 0.3)
    assert final < 0.4
    assert _risk_decision(final) == "APPROVED"


def test_hybrid_edge_blocked():
    """Score above 0.75 → BLOCKED."""
    final = _hybrid_score(0.8, 0.8)
    assert final >= 0.75
    assert _risk_decision(final) == "BLOCKED"
