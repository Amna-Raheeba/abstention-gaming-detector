"""Tests for the aggregate-only baseline - including its confound."""

import pytest

from abstention_gaming.baseline import baseline_scores, naive_flag
from abstention_gaming.detector import audit_log
from abstention_gaming.generate import build_log


def test_baseline_scores_shape():
    log, _ = build_log(7, 600, 0.80, "threshold", 0.85)
    scores = baseline_scores(log)
    assert scores["reported_accuracy"] == pytest.approx(
        log.reported_accuracy())
    assert scores["coverage"] == pytest.approx(0.85)
    assert scores["lift"] == pytest.approx(
        log.reported_accuracy() - log.overall_accuracy())


def test_baseline_lift_positive_for_threshold_abstention():
    log, _ = build_log(7, 1200, 0.80, "threshold", 0.85)
    assert baseline_scores(log)["lift"] > 0.0


def test_naive_flag_threshold_behaviour():
    log, _ = build_log(7, 1200, 0.88, "threshold", 0.70)
    scores = baseline_scores(log)
    assert naive_flag(log, lift_threshold=scores["lift"] + 0.01) is False
    assert naive_flag(log, lift_threshold=scores["lift"] - 0.01) is True


def test_baseline_confounded_where_detector_separates():
    """A strong honest model and a weak gaming model can report the
    same selective accuracy; the baseline ranks them alike while the
    permutation test separates them."""
    honest, _ = build_log(7, 1200, 0.88, "threshold", 0.85,
                          conf_noise=0.02)
    gaming, _ = build_log(7, 1200, 0.72, "gaming", 0.85, subtlety=1.0,
                          conf_noise=0.10)
    gap = abs(baseline_scores(honest)["reported_accuracy"]
              - baseline_scores(gaming)["reported_accuracy"])
    assert gap < 0.05
    honest_audit = audit_log(honest, n_perm=199, seed=5)
    gaming_audit = audit_log(gaming, n_perm=199, seed=5)
    assert gaming_audit.gaming_score > honest_audit.gaming_score + 3.0
    assert gaming_audit.p_value < 0.05
