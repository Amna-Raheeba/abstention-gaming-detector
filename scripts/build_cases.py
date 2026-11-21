"""Build the stored data fixtures.

Writes:
- data/demo_log.json: the seeded gaming demo log (seed 7, quality
  0.80, coverage 0.85, subtlety 0.60) that `audit` and the examples
  run against.
- data/scenarios.json: the evaluation suite definition.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstention_gaming.evaluate import (CONF_NOISES, COVERAGES,
                                        DEMO_COVERAGE, DEMO_QUALITY,
                                        DEMO_SEED, DEMO_SUBTLETY, N_CASES,
                                        QUALITIES, SEEDS, SUBTLETIES)
from abstention_gaming.generate import HONEST_POLICIES, build_log

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def main():
    log, truth = build_log(DEMO_SEED, N_CASES, DEMO_QUALITY, "gaming",
                           DEMO_COVERAGE, subtlety=DEMO_SUBTLETY)
    payload = log.to_dict()
    payload["truth"] = truth
    with open(os.path.join(DATA, "demo_log.json"), "w") as fh:
        json.dump(payload, fh, indent=1)
    scenarios = {
        "honest_policies": list(HONEST_POLICIES),
        "gaming_subtleties": list(SUBTLETIES),
        "qualities": list(QUALITIES),
        "coverages": list(COVERAGES),
        "conf_noises": list(CONF_NOISES),
        "seeds": list(SEEDS),
        "n_cases": N_CASES,
        "demo": {"seed": DEMO_SEED, "quality": DEMO_QUALITY,
                 "coverage": DEMO_COVERAGE, "subtlety": DEMO_SUBTLETY},
    }
    with open(os.path.join(DATA, "scenarios.json"), "w") as fh:
        json.dump(scenarios, fh, indent=2, sort_keys=True)
    print("Wrote data/demo_log.json (%d records) and data/scenarios.json"
          % log.n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
