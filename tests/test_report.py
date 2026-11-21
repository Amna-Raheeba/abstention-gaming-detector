"""Tests for the report renderers."""

from abstention_gaming.baseline import baseline_scores
from abstention_gaming.counterfactual import counterfactual_report
from abstention_gaming.detector import audit_log
from abstention_gaming.evaluate import run_evaluation
from abstention_gaming.generate import build_log
from abstention_gaming.report import (render_audit_report,
                                      render_evaluation_summary,
                                      render_headline)


def _entry(policy, subtlety=0.0):
    log, truth = build_log(7, 600, 0.80, policy, 0.85,
                           subtlety=subtlety)
    return {"log": log, "truth": truth,
            "audit": audit_log(log, n_perm=99, seed=5),
            "counterfactual": counterfactual_report(log),
            "baseline": baseline_scores(log)}


def test_audit_report_contains_key_numbers():
    entry = _entry("threshold")
    text = render_audit_report(entry)
    assert "Reported selective accuracy" in text
    assert "Honest counterfactual" in text
    assert "Permutation p-value" in text
    assert "not flagged" in text


def test_audit_report_flags_gaming():
    entry = _entry("gaming", subtlety=1.0)
    text = render_audit_report(entry)
    assert "FLAGGED" in text


def test_evaluation_summary_and_headline_render():
    payload = run_evaluation(n_perm=49, seeds=(11,), qualities=(0.80,),
                             coverages=(0.85,))
    summary = render_evaluation_summary(payload)
    assert "Detection AUC" in summary
    assert "subtlety" in summary.lower()
    headline = render_headline(payload)
    assert headline.startswith("# Headline results")
    assert "AUC" in headline
