"""The headline experiment: seeded honest vs gaming abstention logs.

Suite design (all planted ground truth, all coverage-matched):
- honest policies: threshold, noisy, random
- gaming policy at subtlety 0.35 / 0.60 / 1.00
- underlying model quality 0.72 / 0.80 / 0.88 (varied so that raw
  reported accuracy cannot separate honest from gaming logs)
- confidence sharpness (noise 0.02 / 0.05 / 0.10) varied so that raw
  accuracy lift cannot separate them either: a sharp-confidence
  honest system earns a large lift legitimately
- coverage 0.50 / 0.70 / 0.85, two seeds per cell, 1200 cases per log

Measured per log: the permutation test's gaming score and p-value,
the reconstructed honest counterfactual, the planted inflation, and
the baseline's aggregate scores. Headline numbers: detection AUC of
the gaming score vs the baseline's AUCs, the false-positive rate on
honest logs at alpha 0.05, detection rate per subtlety, and the
honest-score recovery error of the counterfactual vs the naive
baseline of trusting the reported number.
"""

import csv
import io
import json
import os

from .baseline import baseline_scores
from .counterfactual import counterfactual_report
from .detector import audit_log
from .generate import HONEST_POLICIES, build_log

QUALITIES = (0.72, 0.80, 0.88)
COVERAGES = (0.50, 0.70, 0.85)
CONF_NOISES = (0.02, 0.05, 0.10)
SEEDS = (11, 12)
SUBTLETIES = (0.35, 0.60, 1.00)
N_CASES = 1200
N_PERM_EVAL = 399
ALPHA = 0.05
NAIVE_LIFT_THRESHOLD = 0.10

DEMO_SEED = 7
DEMO_QUALITY = 0.80
DEMO_COVERAGE = 0.85
DEMO_SUBTLETY = 0.60


def auc(positive_scores, negative_scores):
    """Mann-Whitney AUC with tie correction, pure stdlib."""
    if not positive_scores or not negative_scores:
        return None
    wins = 0.0
    for p in positive_scores:
        for q in negative_scores:
            if p > q:
                wins += 1.0
            elif p == q:
                wins += 0.5
    return wins / float(len(positive_scores) * len(negative_scores))


def _audit_one(seed, quality, coverage, policy, subtlety, n_perm,
               conf_noise=0.05):
    log, truth = build_log(seed, N_CASES, quality, policy, coverage,
                           subtlety=subtlety, conf_noise=conf_noise)
    result = audit_log(log, n_perm=n_perm, seed=seed * 7919 + 13)
    cf = counterfactual_report(log)
    base = baseline_scores(log)
    is_gaming = policy == "gaming"
    recovery_err = None
    baseline_recovery_err = None
    if cf["honest_counterfactual"] is not None:
        recovery_err = abs(cf["honest_counterfactual"]
                           - truth["true_honest_score"])
        baseline_recovery_err = abs(cf["reported_accuracy"]
                                    - truth["true_honest_score"])
    return {
        "seed": seed, "quality": quality, "coverage": coverage,
        "conf_noise": conf_noise,
        "policy": policy, "subtlety": subtlety, "is_gaming": is_gaming,
        "reported_accuracy": cf["reported_accuracy"],
        "true_honest_score": truth["true_honest_score"],
        "honest_counterfactual": cf["honest_counterfactual"],
        "planted_inflation": truth["planted_inflation"],
        "estimated_inflation": cf["inflation"],
        "gaming_gap": result.gaming_gap,
        "gaming_score": result.gaming_score,
        "p_value": result.p_value,
        "flagged": result.flagged(ALPHA),
        "baseline_accuracy": base["reported_accuracy"],
        "baseline_lift": base["lift"],
        "recovery_error": recovery_err,
        "baseline_recovery_error": baseline_recovery_err,
    }


def run_evaluation(n_perm=N_PERM_EVAL, seeds=SEEDS, qualities=QUALITIES,
                   coverages=COVERAGES, conf_noises=CONF_NOISES):
    """Run the full seeded suite; return the results payload dict."""
    runs = []
    for quality in qualities:
        for coverage in coverages:
            for conf_noise in conf_noises:
                for seed in seeds:
                    for policy in HONEST_POLICIES:
                        runs.append(_audit_one(seed, quality, coverage,
                                               policy, 0.0, n_perm,
                                               conf_noise=conf_noise))
                    for subtlety in SUBTLETIES:
                        runs.append(_audit_one(seed, quality, coverage,
                                               "gaming", subtlety, n_perm,
                                               conf_noise=conf_noise))
    honest = [r for r in runs if not r["is_gaming"]]
    gaming = [r for r in runs if r["is_gaming"]]
    per_subtlety = {}
    for subtlety in SUBTLETIES:
        cell = [r for r in gaming if r["subtlety"] == subtlety]
        per_subtlety["%.2f" % subtlety] = {
            "n": len(cell),
            "detection_rate": _mean([1.0 if r["flagged"] else 0.0
                                     for r in cell]),
            "mean_planted_inflation": _mean(
                [r["planted_inflation"] for r in cell]),
            "mean_estimated_inflation": _mean(
                [r["estimated_inflation"] for r in cell]),
        }
    headline = {
        "detector_auc": auc([r["gaming_score"] for r in gaming],
                            [r["gaming_score"] for r in honest]),
        "baseline_auc_accuracy": auc(
            [r["baseline_accuracy"] for r in gaming],
            [r["baseline_accuracy"] for r in honest]),
        "baseline_auc_lift": auc([r["baseline_lift"] for r in gaming],
                                 [r["baseline_lift"] for r in honest]),
        "honest_false_positive_rate": _mean(
            [1.0 if r["flagged"] else 0.0 for r in honest]),
        "gaming_detection_rate": _mean(
            [1.0 if r["flagged"] else 0.0 for r in gaming]),
        "mean_recovery_error": _mean([r["recovery_error"] for r in gaming]),
        "mean_baseline_recovery_error": _mean(
            [r["baseline_recovery_error"] for r in gaming]),
        "mean_planted_inflation": _mean(
            [r["planted_inflation"] for r in gaming]),
        "mean_estimated_inflation": _mean(
            [r["estimated_inflation"] for r in gaming]),
        "naive_fpr_lift010": _mean(
            [1.0 if r["baseline_lift"] > NAIVE_LIFT_THRESHOLD else 0.0
             for r in honest]),
        "naive_detection_lift010": _mean(
            [1.0 if r["baseline_lift"] > NAIVE_LIFT_THRESHOLD else 0.0
             for r in gaming]),
        "naive_detection_subtle_lift010": _mean(
            [1.0 if r["baseline_lift"] > NAIVE_LIFT_THRESHOLD else 0.0
             for r in gaming if r["subtlety"] == SUBTLETIES[0]]),
    }
    payload = {
        "seeds": list(seeds), "qualities": list(qualities),
        "coverages": list(coverages), "conf_noises": list(conf_noises),
        "subtleties": list(SUBTLETIES),
        "n_cases": N_CASES, "n_perm": n_perm, "alpha": ALPHA,
        "n_runs": len(runs), "runs": runs,
        "per_subtlety": per_subtlety, "headline": headline,
    }
    return payload


def _mean(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / float(len(values))


def headline_numbers(payload):
    """Flat headline dict (used by the drift guard)."""
    return dict(payload["headline"])


def run_demo_pair(n_perm=999):
    """Audit the demo honest log and the demo gaming log.

    Returns (honest_entry, gaming_entry); each entry is a dict with
    the log, its audit result and its counterfactual report.
    """
    entries = []
    for policy, subtlety in (("threshold", 0.0), ("gaming", DEMO_SUBTLETY)):
        log, truth = build_log(DEMO_SEED, N_CASES, DEMO_QUALITY, policy,
                               DEMO_COVERAGE, subtlety=subtlety)
        result = audit_log(log, n_perm=n_perm, seed=99)
        entries.append({"log": log, "truth": truth, "audit": result,
                        "counterfactual": counterfactual_report(log),
                        "baseline": baseline_scores(log)})
    return entries[0], entries[1]


def write_results(payload, outdir):
    """Write evaluation.json / .csv / evaluation_summary.md / HEADLINE.md."""
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "evaluation.json"), "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    runs = payload["runs"]
    if runs:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(runs[0].keys()))
        writer.writeheader()
        for row in runs:
            writer.writerow(row)
        with open(os.path.join(outdir, "evaluation.csv"), "w") as fh:
            fh.write(buf.getvalue())
    from .report import render_evaluation_summary, render_headline
    with open(os.path.join(outdir, "evaluation_summary.md"), "w") as fh:
        fh.write(render_evaluation_summary(payload))
    with open(os.path.join(outdir, "HEADLINE.md"), "w") as fh:
        fh.write(render_headline(payload))
    return outdir
