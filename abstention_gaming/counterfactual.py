"""The honest counterfactual: what the log would have reported
under a confidence-only threshold at the same coverage.

The reconstruction needs no model of the system. Take the log's own
cases, rank them by stated confidence, answer exactly as many as the
system chose to answer, and score those. Any accuracy the reported
number has above this counterfactual was bought by choosing *which*
cases to refuse with information beyond the stated confidence - in
the planted-truth generators, exactly the inflation the gaming
policy inserted.
"""


def honest_counterfactual(log):
    """Return (score, threshold) for the matched-coverage threshold.

    ``score`` is the accuracy over the ``n_answered`` highest-
    confidence cases of the log itself; ``threshold`` is the lowest
    confidence among them. Returns (None, None) if nothing was
    answered.
    """
    k = log.n_answered
    if k == 0:
        return None, None
    ranked = sorted(log.records, key=lambda r: (-r.confidence,))
    answered = ranked[:k]
    score = sum(1 for r in answered if r.correct) / float(k)
    threshold = answered[-1].confidence
    return score, threshold


def counterfactual_report(log):
    """Reported vs counterfactual accuracy and the inflation gap."""
    reported = log.reported_accuracy()
    honest, threshold = honest_counterfactual(log)
    inflation = None
    if reported is not None and honest is not None:
        inflation = reported - honest
    return {"reported_accuracy": reported,
            "honest_counterfactual": honest,
            "inflation": inflation,
            "threshold": threshold,
            "coverage": log.coverage}
