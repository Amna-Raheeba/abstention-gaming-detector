"""Notebook 01 - demo run.

Audits two logs built from the SAME underlying cases at the SAME
coverage: one honest threshold abstainer and one gaming abstainer
(subtlety 0.60). The gaming log reports the higher selective
accuracy; the permutation test and the honest counterfactual show
what that number cost. Runnable as a plain script:
python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstention_gaming.evaluate import run_demo_pair
from abstention_gaming.report import render_audit_report


def main():
    honest, gaming = run_demo_pair()
    print(render_audit_report(honest))
    print(render_audit_report(gaming))
    print("Planted truth: honest log inflation %.4f, gaming log "
          "inflation %.4f (the counterfactual recovers both from the "
          "logs alone)."
          % (honest["truth"]["planted_inflation"],
             gaming["truth"]["planted_inflation"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
