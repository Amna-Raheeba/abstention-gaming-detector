"""Tests for the confidence-conditional permutation test."""

import pytest

from abstention_gaming.detector import (audit_log, band_stats,
                                        gaming_statistic, make_bands)
from abstention_gaming.generate import build_log
from abstention_gaming.models import PredictionLog, Record


def _crafted_log(abstained_errors, answered_errors, per_band=40):
    """Two confidence bands; per-band error counts planted exactly."""
    records = []
    for band_conf, a_err, r_err in zip((0.6, 0.9), abstained_errors,
                                       answered_errors):
        half = per_band // 2
        for j in range(half):
            records.append(Record(band_conf, True, j >= a_err))
        for j in range(half):
            records.append(Record(band_conf, False, j >= r_err))
    return PredictionLog(records)


def test_make_bands_partitions_all_records():
    log, _ = build_log(3, 500, 0.80, "threshold", 0.85)
    bands = make_bands(log.records, n_bands=10)
    flat = sorted(i for band in bands for i in band)
    assert flat == list(range(500))
    assert len(bands) == 10


def test_make_bands_are_confidence_ordered():
    log, _ = build_log(3, 500, 0.80, "threshold", 0.85)
    bands = make_bands(log.records, n_bands=10)
    maxima = [max(log.records[i].confidence for i in band)
              for band in bands]
    assert maxima == sorted(maxima)


def test_make_bands_shrinks_for_small_logs():
    records = [Record(0.5 + 0.01 * i, False, True) for i in range(30)]
    bands = make_bands(records, n_bands=20)
    assert len(bands) == 3


def test_band_stats_counts():
    log = _crafted_log((10, 2), (2, 10))
    bands = make_bands(log.records, n_bands=2)
    stats = band_stats(log.records, bands)
    assert stats[0]["errors_abstained"] == 10
    assert stats[0]["errors_answered"] == 2
    assert stats[1]["errors_abstained"] == 2
    assert stats[1]["errors_answered"] == 10


def test_statistic_positive_for_label_aware_abstention():
    log = _crafted_log((16, 16), (2, 2))
    bands = make_bands(log.records, n_bands=2)
    assert gaming_statistic(log.records, bands) > 0.3


def test_statistic_near_zero_for_confidence_only_abstention():
    log = _crafted_log((6, 6), (6, 6))
    bands = make_bands(log.records, n_bands=2)
    assert gaming_statistic(log.records, bands) == pytest.approx(0.0)


def test_audit_flags_blatant_gaming(gaming_log):
    log, _ = gaming_log
    result = audit_log(log, n_perm=199, seed=5)
    assert result.p_value < 0.05
    assert result.flagged()
    assert result.gaming_gap > 0.05


def test_audit_does_not_flag_threshold_honest(honest_log):
    log, _ = honest_log
    result = audit_log(log, n_perm=199, seed=5)
    assert result.p_value > 0.05
    assert not result.flagged()


def test_audit_p_value_floor_and_determinism(honest_log):
    log, _ = honest_log
    first = audit_log(log, n_perm=99, seed=5)
    second = audit_log(log, n_perm=99, seed=5)
    assert first.p_value == second.p_value
    assert first.gaming_score == second.gaming_score
    assert first.p_value >= 1.0 / 100.0


def test_audit_no_abstentions_is_clean():
    log, _ = build_log(3, 300, 0.80, "threshold", 0.85)
    records = [Record(r.confidence, False, r.correct) for r in log.records]
    clean = PredictionLog(records)
    result = audit_log(clean, n_perm=99, seed=5)
    assert result.p_value == 1.0
    assert result.gaming_gap == 0.0


def test_audit_all_abstained_is_clean():
    records = [Record(0.9, True, i % 2 == 0) for i in range(100)]
    result = audit_log(PredictionLog(records), n_perm=99, seed=5)
    assert result.p_value == 1.0


def test_audit_result_to_dict_shape(honest_log):
    log, _ = honest_log
    result = audit_log(log, n_perm=49, seed=5)
    payload = result.to_dict()
    for key in ("gaming_gap", "gaming_score", "p_value", "n_perm",
                "n_bands", "band_stats"):
        assert key in payload
    assert payload["n_bands"] == len(result.bands)
