"""Tests for the evaluation suite, AUC and the headline payload."""

import pytest

from abstention_gaming.evaluate import auc, headline_numbers, run_evaluation

SMALL = dict(n_perm=99, seeds=(11,), qualities=(0.80,), coverages=(0.85,),
             conf_noises=(0.05,))


def test_auc_perfect_and_reversed():
    assert auc([0.9, 0.8], [0.1, 0.2]) == 1.0
    assert auc([0.1, 0.2], [0.9, 0.8]) == 0.0


def test_auc_ties_and_empty():
    assert auc([0.5], [0.5]) == 0.5
    assert auc([], [0.5]) is None
    assert auc([0.5], []) is None


def test_small_evaluation_shape():
    payload = run_evaluation(**SMALL)
    assert payload["n_runs"] == 6
    assert len(payload["runs"]) == 6
    for key in ("detector_auc", "baseline_auc_accuracy", "baseline_auc_lift",
                "honest_false_positive_rate", "gaming_detection_rate",
                "mean_recovery_error", "mean_baseline_recovery_error",
                "mean_planted_inflation", "mean_estimated_inflation",
                "naive_fpr_lift010", "naive_detection_lift010",
                "naive_detection_subtle_lift010"):
        assert key in payload["headline"], key
    assert set(payload["per_subtlety"]) == {"0.35", "0.60", "1.00"}


def test_small_evaluation_detector_beats_baseline():
    payload = run_evaluation(**SMALL)
    headline = payload["headline"]
    assert headline["detector_auc"] >= headline["baseline_auc_lift"]
    assert headline["detector_auc"] > 0.8


def test_small_evaluation_recovery_error_beats_trusting_report():
    payload = run_evaluation(**SMALL)
    headline = payload["headline"]
    assert headline["mean_recovery_error"] < 0.01
    assert (headline["mean_baseline_recovery_error"]
            > headline["mean_recovery_error"])


def test_evaluation_is_deterministic():
    first = headline_numbers(run_evaluation(**SMALL))
    second = headline_numbers(run_evaluation(**SMALL))
    assert first == second


def test_gaming_rows_carry_planted_inflation():
    payload = run_evaluation(**SMALL)
    gaming = [r for r in payload["runs"] if r["is_gaming"]]
    assert gaming
    for row in gaming:
        assert row["planted_inflation"] is not None
        assert row["estimated_inflation"] == pytest.approx(
            row["planted_inflation"], abs=1e-9)
