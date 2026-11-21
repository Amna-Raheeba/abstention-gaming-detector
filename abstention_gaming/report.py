"""Plain-text and Markdown rendering of audits and evaluations."""


def _fmt(value, digits=4):
    if value is None:
        return "n/a"
    return "%.*f" % (digits, value)


def render_audit_report(entry):
    """Render one audited log (dict with log/audit/counterfactual)."""
    log = entry["log"]
    audit = entry["audit"]
    cf = entry["counterfactual"]
    meta = log.meta
    lines = []
    lines.append("Abstention audit - policy %s (seed %s, quality %s)"
                 % (meta.get("policy"), meta.get("seed"),
                    meta.get("quality")))
    lines.append("=" * 64)
    lines.append("Cases: %d   answered: %d   abstained: %d   coverage: %s"
                 % (log.n, log.n_answered, log.n_abstained,
                    _fmt(log.coverage, 3)))
    lines.append("Reported selective accuracy: %s"
                 % _fmt(cf["reported_accuracy"]))
    lines.append("Honest counterfactual (threshold, same coverage): %s"
                 % _fmt(cf["honest_counterfactual"]))
    lines.append("Inflation over the honest counterfactual: %s"
                 % _fmt(cf["inflation"]))
    lines.append("Error rate among abstained cases: %s"
                 % _fmt(log.abstained_error_rate(), 3))
    lines.append("Error rate among answered cases:  %s"
                 % _fmt(log.answered_error_rate(), 3))
    lines.append("")
    lines.append("Confidence-conditional permutation test (%d bands, "
                 "%d permutations)" % (len(audit.bands), audit.n_perm))
    lines.append("  Pooled within-band error-rate gap: %s"
                 % _fmt(audit.gaming_gap))
    lines.append("  Gaming score (permutation z):      %s"
                 % _fmt(audit.gaming_score, 2))
    lines.append("  Permutation p-value:               %s"
                 % _fmt(audit.p_value))
    if audit.flagged():
        lines.append("  Verdict: FLAGGED - abstention is label-aware at "
                     "the stated confidence (alpha 0.05).")
    else:
        lines.append("  Verdict: not flagged - abstention is consistent "
                     "with confidence-only selective prediction.")
    lines.append("")
    lines.append("Band evidence (confidence band: abstained vs answered "
                 "error rates)")
    for s in audit.band_stats:
        if s["n_abstained"] == 0 or s["n_answered"] == 0:
            continue
        rate_a = s["errors_abstained"] / float(s["n_abstained"])
        rate_r = s["errors_answered"] / float(s["n_answered"])
        lines.append("  [%.3f-%.3f] n=%4d  abst err %.3f (n=%d)  "
                     "answered err %.3f (n=%d)"
                     % (s["conf_min"], s["conf_max"], s["n"], rate_a,
                        s["n_abstained"], rate_r, s["n_answered"]))
    return "\n".join(lines) + "\n"


def render_evaluation_summary(payload):
    """Markdown summary of the full seeded evaluation."""
    h = payload["headline"]
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append("Seeded suite: %d logs (%d cases each), honest policies "
                 "threshold / noisy / random and gaming at subtlety "
                 "0.35 / 0.60 / 1.00, model quality 0.72 / 0.80 / 0.88, "
                 "confidence noise 0.02 / 0.05 / 0.10, coverage 0.50 / "
                 "0.70 / 0.85, seeds %s. Permutations per audit: %d."
                 % (payload["n_runs"], payload["n_cases"],
                    payload["seeds"], payload["n_perm"]))
    lines.append("")
    lines.append("## Headline numbers")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append("| Detection AUC, permutation gaming score | %s |"
                 % _fmt(h["detector_auc"], 3))
    lines.append("| Detection AUC, baseline reported accuracy | %s |"
                 % _fmt(h["baseline_auc_accuracy"], 3))
    lines.append("| Detection AUC, baseline accuracy lift | %s |"
                 % _fmt(h["baseline_auc_lift"], 3))
    lines.append("| False-positive rate on honest logs (alpha 0.05) | %s |"
                 % _fmt(h["honest_false_positive_rate"], 3))
    lines.append("| Detection rate on gaming logs | %s |"
                 % _fmt(h["gaming_detection_rate"], 3))
    lines.append("| Mean planted inflation (gaming logs) | %s |"
                 % _fmt(h["mean_planted_inflation"]))
    lines.append("| Mean estimated inflation (counterfactual) | %s |"
                 % _fmt(h["mean_estimated_inflation"]))
    lines.append("| Mean honest-score recovery error, detector | %s |"
                 % _fmt(h["mean_recovery_error"]))
    lines.append("| Mean honest-score recovery error, trust-the-report "
                 "baseline | %s |" % _fmt(h["mean_baseline_recovery_error"]))
    lines.append("| Naive rule (flag if lift > 0.10): false-positive "
                 "rate | %s |" % _fmt(h["naive_fpr_lift010"], 3))
    lines.append("| Naive rule (flag if lift > 0.10): detection rate, "
                 "all gaming | %s |" % _fmt(h["naive_detection_lift010"], 3))
    lines.append("| Naive rule (flag if lift > 0.10): detection rate, "
                 "subtlety 0.35 | %s |"
                 % _fmt(h["naive_detection_subtle_lift010"], 3))
    lines.append("")
    lines.append("## Detection by gaming subtlety")
    lines.append("")
    lines.append("| Subtlety | Logs | Detection rate | Planted inflation "
                 "| Estimated inflation |")
    lines.append("| --- | --- | --- | --- | --- |")
    for key in sorted(payload["per_subtlety"]):
        cell = payload["per_subtlety"][key]
        lines.append("| %s | %d | %s | %s | %s |"
                     % (key, cell["n"], _fmt(cell["detection_rate"], 3),
                        _fmt(cell["mean_planted_inflation"]),
                        _fmt(cell["mean_estimated_inflation"])))
    lines.append("")
    return "\n".join(lines)


def render_headline(payload):
    """One-paragraph headline for results/HEADLINE.md."""
    h = payload["headline"]
    return (
        "# Headline results\n\n"
        "Across %d seeded logs (honest threshold / noisy / random "
        "abstainers and gaming abstainers at subtlety 0.35-1.00, model "
        "quality and coverage varied, all coverage-matched), the "
        "confidence-conditional permutation test separates gaming from "
        "honest abstention with AUC %s, against %s for raw reported "
        "accuracy and %s for accuracy lift - the aggregate numbers an "
        "auditor gets from a summary table. The false-positive rate on "
        "honest logs is %s at alpha 0.05. As a decision rule the "
        "baseline fails both ways: flagging every log whose accuracy "
        "lift exceeds 0.10 still falsely flags %s of honest logs while "
        "missing %s of the subtle (0.35) gaming logs. Gaming logs "
        "overstate their selective accuracy by %s on average; the "
        "reconstructed honest counterfactual recovers the true honest "
        "score with mean error %s, versus %s for trusting the "
        "reported number.\n"
        % (payload["n_runs"], _fmt(h["detector_auc"], 3),
           _fmt(h["baseline_auc_accuracy"], 3),
           _fmt(h["baseline_auc_lift"], 3),
           _fmt(h["honest_false_positive_rate"], 3),
           _fmt(h["naive_fpr_lift010"], 3),
           _fmt(1.0 - h["naive_detection_subtle_lift010"], 3),
           _fmt(h["mean_planted_inflation"], 3),
           _fmt(h["mean_recovery_error"], 4),
           _fmt(h["mean_baseline_recovery_error"], 3)))
