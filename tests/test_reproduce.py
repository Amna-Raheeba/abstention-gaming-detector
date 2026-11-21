"""Stored-results guards: the shipped numbers exist and are sane."""

import json
import os

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results",
                       "evaluation.json")


def _load():
    with open(RESULTS) as fh:
        return json.load(fh)


def test_stored_results_exist_and_parse():
    assert os.path.isfile(RESULTS)
    payload = _load()
    for key in ("seeds", "qualities", "coverages", "conf_noises",
                "subtleties", "n_cases", "n_perm", "n_runs", "runs",
                "per_subtlety", "headline"):
        assert key in payload, key
    assert payload["n_runs"] == 324
    assert len(payload["runs"]) == 324


def test_stored_headline_detector_beats_baselines():
    headline = _load()["headline"]
    assert headline["detector_auc"] > headline["baseline_auc_accuracy"]
    assert headline["detector_auc"] > headline["baseline_auc_lift"]
    assert headline["detector_auc"] > 0.9


def test_stored_headline_recovery_and_fpr_sane():
    headline = _load()["headline"]
    assert headline["mean_recovery_error"] < 0.01
    assert (headline["mean_baseline_recovery_error"]
            > headline["mean_recovery_error"])
    assert headline["honest_false_positive_rate"] <= 0.25
    assert headline["gaming_detection_rate"] > 0.5
    assert (headline["naive_detection_subtle_lift010"]
            < headline["gaming_detection_rate"])
