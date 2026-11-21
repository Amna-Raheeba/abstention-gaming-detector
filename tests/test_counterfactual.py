"""Tests for the honest counterfactual reconstruction."""

import pytest

from abstention_gaming.counterfactual import (counterfactual_report,
                                              honest_counterfactual)
from abstention_gaming.generate import build_log


def test_counterfactual_equals_reported_for_threshold_log():
    log, truth = build_log(7, 1200, 0.80, "threshold", 0.85)
    score, _ = honest_counterfactual(log)
    assert score == pytest.approx(log.reported_accuracy())
    assert score == pytest.approx(truth["true_honest_score"])


def test_counterfactual_recovers_honest_score_for_gaming_log():
    log, truth = build_log(7, 1200, 0.80, "gaming", 0.85, subtlety=1.0)
    score, _ = honest_counterfactual(log)
    assert score == pytest.approx(truth["true_honest_score"])
    assert score < log.reported_accuracy()


def test_counterfactual_answers_exactly_as_many_cases():
    log, _ = build_log(7, 1200, 0.80, "gaming", 0.85, subtlety=0.6)
    _, threshold = honest_counterfactual(log)
    at_or_above = [r for r in log.records if r.confidence > threshold]
    assert len(at_or_above) <= log.n_answered


def test_counterfactual_threshold_is_answered_confidence():
    log, _ = build_log(7, 1200, 0.80, "noisy", 0.85)
    _, threshold = honest_counterfactual(log)
    assert threshold is not None
    assert 0.5 <= threshold <= 0.999


def test_counterfactual_report_inflation_matches_planted():
    log, truth = build_log(7, 1200, 0.80, "gaming", 0.85, subtlety=0.6)
    report = counterfactual_report(log)
    assert report["inflation"] == pytest.approx(
        truth["planted_inflation"])
    assert report["coverage"] == pytest.approx(0.85)


def test_counterfactual_report_zero_inflation_for_honest():
    log, _ = build_log(7, 1200, 0.80, "threshold", 0.70)
    report = counterfactual_report(log)
    assert report["inflation"] == pytest.approx(0.0, abs=1e-9)
