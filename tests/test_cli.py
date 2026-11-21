"""Tests for the command line interface."""

import json
import os

from abstention_gaming.cli import main

ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_cli_demo_runs(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Abstention audit" in out
    assert "Demo takeaway" in out


def test_cli_audit_demo_log(capsys):
    assert main(["audit", "--log",
                 os.path.join(ROOT, "data", "demo_log.json")]) == 0
    out = capsys.readouterr().out
    assert "Abstention audit" in out
    assert "FLAGGED" in out


def test_cli_evaluate_writes_results(tmp_path):
    outdir = str(tmp_path / "results")
    assert main(["evaluate", "--out", outdir]) == 0
    for name in ("evaluation.json", "evaluation.csv",
                 "evaluation_summary.md", "HEADLINE.md"):
        assert os.path.isfile(os.path.join(outdir, name)), name
    with open(os.path.join(outdir, "evaluation.json")) as fh:
        payload = json.load(fh)
    assert payload["n_runs"] == 324


def test_cli_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()
