"""The confidence-conditional permutation test.

Idea: an honest selective-prediction system abstains on uncertainty.
Conditional on the stated confidence, its abstention decision carries
no information about the outcome. A gaming system abstains on the
label: at the *same* stated confidence, the cases it refuses are
disproportionately the ones it would have got wrong.

The test bins the log into narrow confidence bands (quantile bands).
Inside each band it compares the error rate of abstained cases with
the error rate of answered cases, and pools the gap across bands,
weighted by band size. Significance comes from a permutation null:
abstain flags are shuffled within each band (preserving each band's
abstention count), which is exactly the distribution of the statistic
under "abstention depends on confidence only". The observed gap, its
permutation z-score (the gaming score) and the permutation p-value
are reported together.
"""

import math
import random

DEFAULT_N_BANDS = 20
DEFAULT_N_PERM = 999


def make_bands(records, n_bands=DEFAULT_N_BANDS):
    """Split record indices into quantile bands of stated confidence.

    Returns a list of index lists, ordered by confidence. Bands are as
    equal in size as possible; the band count shrinks for small logs.
    """
    n = len(records)
    if n == 0:
        return []
    bands_count = max(1, min(n_bands, n // 10))
    order = sorted(range(n), key=lambda i: (records[i].confidence, i))
    bands = []
    base = n // bands_count
    extra = n % bands_count
    start = 0
    for b in range(bands_count):
        size = base + (1 if b < extra else 0)
        bands.append(order[start:start + size])
        start += size
    return bands


def band_stats(records, bands):
    """Per-band counts: sizes, abstentions and errors on both sides."""
    stats = []
    for idxs in bands:
        n_b = len(idxs)
        abst = [records[i] for i in idxs if records[i].abstained]
        ans = [records[i] for i in idxs if not records[i].abstained]
        stats.append({
            "n": n_b,
            "n_abstained": len(abst),
            "n_answered": len(ans),
            "errors_abstained": sum(1 for r in abst if not r.correct),
            "errors_answered": sum(1 for r in ans if not r.correct),
            "conf_min": min(records[i].confidence for i in idxs),
            "conf_max": max(records[i].confidence for i in idxs),
        })
    return stats


def _gap_from_counts(stats, total_n):
    """Pooled within-band error-rate gap (abstained minus answered)."""
    gap = 0.0
    for s in stats:
        if s["n_abstained"] == 0 or s["n_answered"] == 0:
            continue
        rate_abst = s["errors_abstained"] / float(s["n_abstained"])
        rate_ans = s["errors_answered"] / float(s["n_answered"])
        gap += (s["n"] / float(total_n)) * (rate_abst - rate_ans)
    return gap


def gaming_statistic(records, bands):
    """Observed pooled within-band error-rate gap for a log."""
    return _gap_from_counts(band_stats(records, bands), len(records))


def _permuted_gap(rng, records, bands, total_n):
    """One draw of the gap under within-band flag shuffling.

    Only the number of errors landing on the abstained side of each
    band is random under the null, so a replicate costs one sample
    per band instead of a full re-sort of the log.
    """
    gap = 0.0
    for idxs in bands:
        n_b = len(idxs)
        a_b = sum(1 for i in idxs if records[i].abstained)
        if a_b == 0 or a_b == n_b:
            continue
        error_positions = set(j for j, i in enumerate(idxs)
                              if not records[i].correct)
        chosen = rng.sample(range(n_b), a_b)
        err_abst = sum(1 for j in chosen if j in error_positions)
        err_ans = len(error_positions) - err_abst
        rate_abst = err_abst / float(a_b)
        rate_ans = err_ans / float(n_b - a_b)
        gap += (n_b / float(total_n)) * (rate_abst - rate_ans)
    return gap


class AuditResult(object):
    """Outcome of auditing one log with the permutation test."""

    def __init__(self, gaming_gap, gaming_score, p_value, n_perm,
                 bands, stats):
        self.gaming_gap = gaming_gap
        self.gaming_score = gaming_score
        self.p_value = p_value
        self.n_perm = n_perm
        self.bands = bands
        self.band_stats = stats

    def flagged(self, alpha=0.05):
        return self.p_value < alpha

    def to_dict(self):
        return {"gaming_gap": self.gaming_gap,
                "gaming_score": self.gaming_score,
                "p_value": self.p_value,
                "n_perm": self.n_perm,
                "n_bands": len(self.bands),
                "band_stats": self.band_stats}


def audit_log(log, n_bands=DEFAULT_N_BANDS, n_perm=DEFAULT_N_PERM,
              seed=20240521):
    """Run the permutation test on one prediction log.

    Returns an AuditResult. A log with no abstentions (or no answered
    cases) carries no abstention signal: gap 0, score 0, p-value 1.
    """
    records = log.records
    bands = make_bands(records, n_bands=n_bands)
    stats = band_stats(records, bands)
    observed = _gap_from_counts(stats, len(records))
    if log.n_abstained == 0 or log.n_answered == 0:
        return AuditResult(0.0, 0.0, 1.0, 0, bands, stats)
    rng = random.Random(seed)
    permuted = [_permuted_gap(rng, records, bands, len(records))
                for _ in range(n_perm)]
    mean_perm = sum(permuted) / float(len(permuted))
    var_perm = sum((x - mean_perm) ** 2 for x in permuted) / float(len(permuted))
    sd_perm = math.sqrt(var_perm)
    z = (observed - mean_perm) / sd_perm if sd_perm > 0 else 0.0
    exceed = sum(1 for x in permuted if x >= observed - 1e-12)
    p_value = (1 + exceed) / float(1 + n_perm)
    return AuditResult(observed, z, p_value, n_perm, bands, stats)
