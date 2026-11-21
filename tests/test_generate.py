"""Tests for the seeded generators and the abstention policies."""

import pytest

from abstention_gaming.generate import (ALL_POLICIES, apply_policy,
                                        build_log, generate_cases,
                                        n_abstain_for_coverage,
                                        true_honest_score)


def test_generate_cases_deterministic_per_seed():
    a = generate_cases(42, 200, 0.80)
    b = generate_cases(42, 200, 0.80)
    assert a == b


def test_generate_cases_differs_across_seeds():
    a = generate_cases(1, 200, 0.80)
    b = generate_cases(2, 200, 0.80)
    assert a != b


def test_generate_cases_ranges():
    cases = generate_cases(3, 500, 0.80)
    assert len(cases) == 500
    for conf, _ in cases:
        assert 0.5 <= conf <= 0.999


def test_generate_cases_quality_orders_accuracy():
    low = generate_cases(5, 2000, 0.72)
    high = generate_cases(5, 2000, 0.88)
    acc_low = sum(1 for _, ok in low if ok) / len(low)
    acc_high = sum(1 for _, ok in high if ok) / len(high)
    assert acc_high > acc_low


def test_generate_cases_rejects_bad_inputs():
    with pytest.raises(ValueError):
        generate_cases(1, 5, 0.80)
    with pytest.raises(ValueError):
        generate_cases(1, 100, 0.30)


def test_n_abstain_for_coverage_rounding():
    assert n_abstain_for_coverage(1000, 0.85) == 150
    assert n_abstain_for_coverage(1000, 0.70) == 300
    with pytest.raises(ValueError):
        n_abstain_for_coverage(1000, 1.0)


@pytest.mark.parametrize("policy", ALL_POLICIES)
def test_every_policy_hits_the_coverage_target(policy):
    subtlety = 0.6 if policy == "gaming" else 0.0
    log, _ = build_log(9, 800, 0.80, policy, 0.80, subtlety=subtlety)
    assert log.n_abstained == n_abstain_for_coverage(800, 0.80)
    assert log.coverage == pytest.approx(0.80)


def test_threshold_policy_abstains_on_lowest_confidence():
    cases = generate_cases(4, 300, 0.80)
    log = apply_policy(cases, "threshold", 0.80, seed=1)
    answered_conf = [r.confidence for r in log.records if not r.abstained]
    abstained_conf = [r.confidence for r in log.records if r.abstained]
    assert max(abstained_conf) <= min(answered_conf)


def test_gaming_abstains_on_more_errors_than_threshold():
    cases = generate_cases(7, 1200, 0.80)
    honest = apply_policy(cases, "threshold", 0.85, seed=1)
    gaming = apply_policy(cases, "gaming", 0.85, seed=1, subtlety=1.0)
    assert gaming.abstained_error_rate() > honest.abstained_error_rate()


def test_gaming_inflates_reported_accuracy_over_honest_truth():
    _, truth = build_log(7, 1200, 0.80, "gaming", 0.85, subtlety=1.0)
    assert truth["planted_inflation"] > 0.02


def test_threshold_log_has_zero_planted_inflation():
    log, truth = build_log(7, 1200, 0.80, "threshold", 0.85)
    assert truth["planted_inflation"] == pytest.approx(0.0, abs=1e-9)
    assert log.reported_accuracy() == pytest.approx(
        truth["true_honest_score"])


def test_true_honest_score_matches_threshold_policy():
    cases = generate_cases(11, 500, 0.80)
    log = apply_policy(cases, "threshold", 0.75, seed=3)
    assert true_honest_score(cases, 0.75) == pytest.approx(
        log.reported_accuracy())


def test_gaming_requires_subtlety():
    cases = generate_cases(1, 100, 0.80)
    with pytest.raises(ValueError):
        apply_policy(cases, "gaming", 0.85, seed=1, subtlety=0.0)


def test_unknown_policy_rejected():
    cases = generate_cases(1, 100, 0.80)
    with pytest.raises(ValueError):
        apply_policy(cases, "peek-everything", 0.85, seed=1)


def test_sharp_confidence_earns_honest_lift_legitimately():
    """With sharp confidence, an honest threshold policy's lift is
    large - the confound that makes raw lift useless as an audit."""
    sharp, _ = build_log(7, 2000, 0.80, "threshold", 0.85,
                         conf_noise=0.02)
    dull, _ = build_log(7, 2000, 0.80, "threshold", 0.85,
                        conf_noise=0.10)
    lift_sharp = sharp.reported_accuracy() - sharp.overall_accuracy()
    lift_dull = dull.reported_accuracy() - dull.overall_accuracy()
    assert lift_sharp > lift_dull + 0.01


def test_generate_cases_rejects_bad_conf_noise():
    with pytest.raises(ValueError):
        generate_cases(1, 100, 0.80, conf_noise=0.0)


def test_build_log_meta_records_provenance():
    log, _ = build_log(7, 400, 0.80, "noisy", 0.85)
    assert log.meta["policy"] == "noisy"
    assert log.meta["seed"] == 7
    assert log.meta["quality"] == 0.80
