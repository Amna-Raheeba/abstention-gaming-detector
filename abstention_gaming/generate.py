"""Seeded generators for prediction logs with planted ground truth.

Cases are generated first (a stated confidence and a would-be outcome
per case, from a latent per-case skill). An abstention policy is then
applied to the frozen cases. Because the cases never change, the honest
counterfactual for any log is known exactly: the accuracy a pure
confidence-threshold policy would have reported on the same cases at
the same coverage. That planted truth is what the evaluation scores
the detector against.

Policies
--------
Honest (abstention depends on confidence, never on the outcome):
- ``threshold``: abstain on the lowest-confidence cases.
- ``noisy``: abstain on a confidence-plus-independent-noise ranking.
- ``random``: abstain uniformly at random (honest but useless).

Gaming (abstention peeks at the outcome):
- ``gaming``: each would-be error is "visible" to the policy with
  probability ``subtlety``; visible errors are abstained first
  (lowest confidence first, so the log still looks threshold-like),
  and any remaining abstention budget is filled with the
  lowest-confidence remaining cases. Subtlety 1.0 is blatant
  (every error the budget can hold is removed); 0.35 is subtle.
"""

import random

from .models import PredictionLog, Record

HONEST_POLICIES = ("threshold", "noisy", "random")
GAMING_POLICY = "gaming"
ALL_POLICIES = HONEST_POLICIES + (GAMING_POLICY,)

NOISE_SCALE = 0.35

# Spread of per-case latent skill around the mean quality. Wide
# enough that cases genuinely differ in difficulty and confidence
# (which tracks skill) can earn an honest threshold policy a large
# accuracy lift - the confound the audit must see through.
SKILL_SPREAD = 0.16


def generate_cases(seed, n_cases, quality, conf_noise=0.05):
    """Return a list of (confidence, correct) pairs, fully seeded.

    ``quality`` is the mean latent skill of the underlying predictor
    (roughly its full-coverage accuracy). Confidence is the latent
    skill plus independent noise of scale ``conf_noise``, so
    confidence is informative but imperfectly calibrated - as in real
    logs. Small ``conf_noise`` means sharp confidence: an honest
    threshold policy on such a system earns a large accuracy lift
    legitimately, which is exactly what makes raw lift uninformative
    about gaming.
    """
    if n_cases < 10:
        raise ValueError("n_cases must be at least 10")
    if not 0.5 < quality < 0.99:
        raise ValueError("quality must lie in (0.5, 0.99)")
    if conf_noise <= 0:
        raise ValueError("conf_noise must be positive")
    rng = random.Random(seed)
    cases = []
    for _ in range(n_cases):
        skill = quality + rng.gauss(0.0, SKILL_SPREAD)
        skill = min(0.985, max(0.52, skill))
        confidence = skill + rng.gauss(0.0, conf_noise)
        confidence = min(0.999, max(0.5, confidence))
        correct = rng.random() < skill
        cases.append((confidence, correct))
    return cases


def n_abstain_for_coverage(n_cases, coverage):
    if not 0.0 < coverage < 1.0:
        raise ValueError("coverage must lie in (0, 1)")
    return int(round((1.0 - coverage) * n_cases))


def true_honest_score(cases, coverage):
    """Accuracy of a pure confidence-threshold policy on these cases.

    This is the planted ground truth: what an honest system with the
    same underlying predictions would have reported at this coverage.
    """
    n = len(cases)
    n_abstain = n_abstain_for_coverage(n, coverage)
    ranked = sorted(range(n), key=lambda i: (-cases[i][0], i))
    answered = ranked[:n - n_abstain]
    if not answered:
        return None
    return sum(1 for i in answered if cases[i][1]) / float(len(answered))


def apply_policy(cases, policy, coverage, seed, subtlety=0.0):
    """Apply an abstention policy to frozen cases; return a log."""
    n = len(cases)
    n_abstain = n_abstain_for_coverage(n, coverage)
    rng = random.Random(seed)
    abstained = set()
    if policy == "threshold":
        ranked = sorted(range(n), key=lambda i: (cases[i][0], i))
        abstained = set(ranked[:n_abstain])
    elif policy == "noisy":
        keys = {}
        for i in range(n):
            keys[i] = (1.0 - cases[i][0]) + NOISE_SCALE * rng.random()
        ranked = sorted(range(n), key=lambda i: (-keys[i], i))
        abstained = set(ranked[:n_abstain])
    elif policy == "random":
        abstained = set(rng.sample(range(n), n_abstain))
    elif policy == GAMING_POLICY:
        if not 0.0 < subtlety <= 1.0:
            raise ValueError("gaming subtlety must lie in (0, 1]")
        visible_errors = [i for i in range(n)
                          if not cases[i][1] and rng.random() < subtlety]
        visible_errors.sort(key=lambda i: (cases[i][0], i))
        chosen = visible_errors[:n_abstain]
        abstained = set(chosen)
        if len(abstained) < n_abstain:
            rest = [i for i in range(n) if i not in abstained]
            rest.sort(key=lambda i: (cases[i][0], i))
            for i in rest[:n_abstain - len(abstained)]:
                abstained.add(i)
    else:
        raise ValueError("unknown policy: %s" % policy)
    records = [Record(conf, i in abstained, corr)
               for i, (conf, corr) in enumerate(cases)]
    meta = {"policy": policy, "coverage_target": coverage,
            "subtlety": subtlety if policy == GAMING_POLICY else 0.0}
    return PredictionLog(records, meta=meta)


def build_log(seed, n_cases, quality, policy, coverage, subtlety=0.0,
              conf_noise=0.05):
    """Generate cases and a log; return (log, truth) with planted truth.

    ``truth`` carries the exact honest counterfactual for the same
    cases and the planted inflation of the log's reported accuracy
    over that counterfactual.
    """
    cases = generate_cases(seed, n_cases, quality, conf_noise=conf_noise)
    log = apply_policy(cases, policy, coverage, seed + 1000003,
                       subtlety=subtlety)
    log.meta.update({"seed": seed, "n_cases": n_cases, "quality": quality,
                     "conf_noise": conf_noise})
    honest = true_honest_score(cases, coverage)
    reported = log.reported_accuracy()
    truth = {"true_honest_score": honest,
             "planted_inflation": (reported - honest) if reported is not None
             else None}
    return log, truth
