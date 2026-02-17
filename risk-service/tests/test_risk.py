"""
Risk Service tests — rule engine, scoring, and decision logic.
"""

import pytest

from app.services.rule_engine import compute_rule_score
from app.services.risk_scorer import (
    compute_hybrid_score,
    determine_risk_decision,
)


# ── Rule Engine Tests ─────────────────────────────────────────────────────────

class TestRuleEngine:
    """Tests for the deterministic rule-based scoring."""

    def test_no_risk_flags(self):
        """Normal transaction → score = 0."""
        score = compute_rule_score(
            amount=500, hour=14, is_new_device=False, is_unusual_location=False,
        )
        assert score == 0.0

    def test_high_amount(self):
        """amount > 50000 triggers +30 → 30/80."""
        score = compute_rule_score(
            amount=100_000, hour=14, is_new_device=False, is_unusual_location=False,
        )
        assert score == pytest.approx(30 / 80)

    def test_night_transaction(self):
        """Night hour triggers +10 → 10/80."""
        score = compute_rule_score(
            amount=500, hour=3, is_new_device=False, is_unusual_location=False,
        )
        assert score == pytest.approx(10 / 80)

    def test_late_night_boundary(self):
        """Hour 22 is still night."""
        score = compute_rule_score(
            amount=500, hour=22, is_new_device=False, is_unusual_location=False,
        )
        assert score == pytest.approx(10 / 80)

    def test_new_device(self):
        """New device triggers +20 → 20/80."""
        score = compute_rule_score(
            amount=500, hour=14, is_new_device=True, is_unusual_location=False,
        )
        assert score == pytest.approx(20 / 80)

    def test_unusual_location(self):
        """Unusual location triggers +20 → 20/80."""
        score = compute_rule_score(
            amount=500, hour=14, is_new_device=False, is_unusual_location=True,
        )
        assert score == pytest.approx(20 / 80)

    def test_all_flags_active(self):
        """All rules triggered → max = 1.0."""
        score = compute_rule_score(
            amount=100_000, hour=2, is_new_device=True, is_unusual_location=True,
        )
        assert score == 1.0

    def test_multiple_flags(self):
        """New device + unusual location → (20+20)/80 = 0.5."""
        score = compute_rule_score(
            amount=500, hour=14, is_new_device=True, is_unusual_location=True,
        )
        assert score == pytest.approx(40 / 80)


# ── Hybrid Scoring Tests ─────────────────────────────────────────────────────

class TestHybridScoring:
    """Tests for the weighted hybrid score combination."""

    def test_formula(self):
        """Verify: 0.7 * ml + 0.3 * rule."""
        assert compute_hybrid_score(0.5, 0.5) == pytest.approx(0.5)

    def test_zero_scores(self):
        """Both zero → zero."""
        assert compute_hybrid_score(0.0, 0.0) == 0.0

    def test_max_scores(self):
        """Both 1.0 → 1.0."""
        assert compute_hybrid_score(1.0, 1.0) == 1.0

    def test_ml_dominated(self):
        """High ML, low rules → weighted towards ML."""
        result = compute_hybrid_score(0.9, 0.1)
        assert result == pytest.approx(0.7 * 0.9 + 0.3 * 0.1)


# ── Risk Decision Tests ──────────────────────────────────────────────────────

class TestRiskDecision:
    """Tests for score → status + risk_level mapping."""

    def test_approved_low(self):
        status, level = determine_risk_decision(0.2)
        assert status == "APPROVED"
        assert level == "LOW"

    def test_approved_boundary(self):
        status, level = determine_risk_decision(0.39)
        assert status == "APPROVED"
        assert level == "LOW"

    def test_flagged_at_boundary(self):
        status, level = determine_risk_decision(0.4)
        assert status == "FLAGGED"
        assert level == "MEDIUM"

    def test_flagged_mid(self):
        status, level = determine_risk_decision(0.6)
        assert status == "FLAGGED"
        assert level == "MEDIUM"

    def test_blocked_at_boundary(self):
        status, level = determine_risk_decision(0.75)
        assert status == "BLOCKED"
        assert level == "HIGH"

    def test_blocked_high(self):
        status, level = determine_risk_decision(0.95)
        assert status == "BLOCKED"
        assert level == "HIGH"
