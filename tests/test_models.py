"""Tests for the log data types and their summary statistics."""

import pytest

from abstention_gaming.models import PredictionLog, Record


def _log(abstained_flags, correct_flags, confs=None):
    confs = confs or [0.9] * len(abstained_flags)
    records = [Record(c, a, ok)
               for c, a, ok in zip(confs, abstained_flags, correct_flags)]
    return PredictionLog(records)


def test_record_rejects_out_of_range_confidence():
    with pytest.raises(ValueError):
        Record(1.5, False, True)
    with pytest.raises(ValueError):
        Record(-0.1, False, True)


def test_empty_log_rejected():
    with pytest.raises(ValueError):
        PredictionLog([])


def test_coverage_counts():
    log = _log([True, False, False, False], [True, True, False, True])
    assert log.n == 4
    assert log.n_abstained == 1
    assert log.n_answered == 3
    assert log.coverage == 0.75


def test_reported_accuracy_uses_answered_only():
    log = _log([True, False, False], [False, True, False])
    assert log.reported_accuracy() == 0.5


def test_overall_accuracy_uses_would_be_outcomes():
    log = _log([True, False, False], [False, True, False])
    assert log.overall_accuracy() == pytest.approx(1.0 / 3.0)


def test_reported_accuracy_none_when_nothing_answered():
    log = _log([True, True], [True, False])
    assert log.reported_accuracy() is None
    assert log.coverage == 0.0


def test_error_rates_split_by_abstention():
    log = _log([True, True, False, False], [False, True, False, True])
    assert log.abstained_error_rate() == 0.5
    assert log.answered_error_rate() == 0.5


def test_error_rate_none_when_no_abstentions():
    log = _log([False, False], [True, False])
    assert log.abstained_error_rate() is None
    assert log.coverage == 1.0


def test_mean_confidence_answered_only():
    log = _log([True, False], [True, True], confs=[0.6, 0.8])
    assert log.mean_confidence() == pytest.approx(0.7)
    assert log.mean_confidence(answered_only=True) == pytest.approx(0.8)


def test_serialization_roundtrip():
    log = _log([True, False], [False, True], confs=[0.55, 0.95])
    log.meta["policy"] = "gaming"
    clone = PredictionLog.from_json(log.to_json())
    assert clone.records == log.records
    assert clone.meta["policy"] == "gaming"
    assert clone.coverage == log.coverage


def test_record_equality_and_repr():
    a = Record(0.5, True, False)
    b = Record(0.5, True, False)
    assert a == b
    assert "0.5000" in repr(a)
