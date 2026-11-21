"""Shared fixtures: small seeded logs for the test suite."""

import pytest

from abstention_gaming.generate import build_log


@pytest.fixture()
def honest_log():
    log, truth = build_log(7, 600, 0.80, "threshold", 0.85)
    return log, truth


@pytest.fixture()
def gaming_log():
    log, truth = build_log(7, 600, 0.80, "gaming", 0.85, subtlety=1.0)
    return log, truth
