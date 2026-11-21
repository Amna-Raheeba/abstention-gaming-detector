"""The naive baseline: raw coverage / accuracy inspection.

This is what an auditor gets from the summary numbers alone - the
reported selective accuracy, its lift over the full-coverage
accuracy, and the coverage. It has no access to the joint
distribution of confidence, abstention and outcome, so it cannot
tell a strong honest model (high reported accuracy because the model
is good) from a mediocre gaming model (high reported accuracy
because errors were refused). The evaluation varies the underlying
model quality across logs precisely so this confound bites: at
matched coverage the baseline's ranking of logs by suspicion is
barely better than chance, while the permutation test separates the
two populations cleanly. The suite also varies confidence
sharpness: a sharp-confidence honest system earns a large lift
legitimately, so lift alone cannot indict it.
"""


def baseline_scores(log):
    """Aggregate-only scores a summary-table auditor could compute."""
    reported = log.reported_accuracy()
    overall = log.overall_accuracy()
    lift = None
    if reported is not None:
        lift = reported - overall
    return {"reported_accuracy": reported,
            "overall_accuracy": overall,
            "lift": lift,
            "coverage": log.coverage,
            "mean_confidence_answered": log.mean_confidence(answered_only=True)}


def naive_flag(log, lift_threshold=0.10):
    """Flag a log as gaming if its accuracy lift looks 'too good'.

    Any fixed threshold misfires both ways, which the evaluation
    measures: at 0.10 the rule still flags honest sharp-confidence
    systems while missing half of the subtle gaming logs; at 0.05 it
    flags over two fifths of all honest logs.
    """
    scores = baseline_scores(log)
    if scores["lift"] is None:
        return False
    return scores["lift"] > lift_threshold
