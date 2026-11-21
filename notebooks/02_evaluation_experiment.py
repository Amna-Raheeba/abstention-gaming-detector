"""Notebook 02 - the headline evaluation experiment.

Runs the full seeded suite (honest threshold / noisy / random
abstainers vs gaming abstainers at three subtlety levels, model
quality and coverage varied) and prints the evaluation summary:
detection AUC of the permutation test vs the aggregate-only
baseline, false-positive rate on honest logs, detection rate per
subtlety, and honest-score recovery error. Runnable as a plain
script: python notebooks/02_evaluation_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstention_gaming.evaluate import run_evaluation
from abstention_gaming.report import render_evaluation_summary


def main():
    payload = run_evaluation()
    print(render_evaluation_summary(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
