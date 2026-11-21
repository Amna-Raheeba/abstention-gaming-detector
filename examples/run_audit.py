"""Example: audit the stored demo log and print the report.

The demo log (data/demo_log.json) is a seeded gaming log: the system
abstained on visible would-be errors with subtlety 0.60 at coverage
0.85. The audit flags it and prices the inflation.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstention_gaming.baseline import baseline_scores
from abstention_gaming.counterfactual import counterfactual_report
from abstention_gaming.detector import audit_log
from abstention_gaming.models import PredictionLog
from abstention_gaming.report import render_audit_report

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data",
                        "demo_log.json")


def main():
    with open(LOG_PATH) as fh:
        payload = json.load(fh)
    log = PredictionLog.from_dict(payload)
    entry = {"log": log,
             "audit": audit_log(log, n_perm=999, seed=99),
             "counterfactual": counterfactual_report(log),
             "baseline": baseline_scores(log)}
    print(render_audit_report(entry))
    truth = payload.get("truth") or {}
    if truth:
        print("Planted truth for this log: honest score %.4f, planted "
              "inflation %.4f."
              % (truth["true_honest_score"], truth["planted_inflation"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
