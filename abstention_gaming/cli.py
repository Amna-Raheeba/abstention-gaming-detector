"""Command line interface.

Usage:
    python -m abstention_gaming demo
    python -m abstention_gaming audit [--log data/demo_log.json]
    python -m abstention_gaming evaluate [--out results]
"""

import argparse
import json
import os
import sys

from .detector import audit_log
from .counterfactual import counterfactual_report
from .baseline import baseline_scores
from .evaluate import run_demo_pair, run_evaluation, write_results
from .models import PredictionLog
from .report import render_audit_report

DEFAULT_LOG = os.path.join(os.path.dirname(__file__), "..", "data",
                           "demo_log.json")
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def _entry_for(log, n_perm=999):
    return {"log": log,
            "audit": audit_log(log, n_perm=n_perm, seed=99),
            "counterfactual": counterfactual_report(log),
            "baseline": baseline_scores(log)}


def cmd_demo(args):
    honest, gaming = run_demo_pair()
    print(render_audit_report(honest))
    print(render_audit_report(gaming))
    h_inf = honest["counterfactual"]["inflation"]
    g_inf = gaming["counterfactual"]["inflation"]
    print("Demo takeaway: the honest log's inflation is %.4f and the "
          "gaming log's is %.4f - same coverage, same underlying cases."
          % (h_inf, g_inf))
    return 0


def cmd_audit(args):
    path = args.log or DEFAULT_LOG
    with open(path) as fh:
        log = PredictionLog.from_dict(json.load(fh))
    print(render_audit_report(_entry_for(log)))
    return 0


def cmd_evaluate(args):
    payload = run_evaluation()
    outdir = args.out or DEFAULT_OUT
    write_results(payload, outdir)
    headline = payload["headline"]
    print("Evaluated %d logs. Detector AUC %.3f (baseline accuracy %.3f, "
          "lift %.3f); honest FPR %.3f; gaming detection %.3f."
          % (payload["n_runs"], headline["detector_auc"],
             headline["baseline_auc_accuracy"],
             headline["baseline_auc_lift"],
             headline["honest_false_positive_rate"],
             headline["gaming_detection_rate"]))
    print("Results written to %s" % outdir)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="abstention_gaming",
        description="Detect label-aware (gamed) abstention in "
                    "selective-prediction logs.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="audit one honest and one gaming log")
    audit_parser = sub.add_parser("audit", help="audit a stored log")
    audit_parser.add_argument("--log", default=None,
                              help="path to a JSON prediction log")
    eval_parser = sub.add_parser("evaluate", help="run the seeded suite")
    eval_parser.add_argument("--out", default=None,
                             help="output directory for results")
    args = parser.parse_args(argv)
    if args.command == "demo":
        return cmd_demo(args)
    if args.command == "audit":
        return cmd_audit(args)
    if args.command == "evaluate":
        return cmd_evaluate(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
