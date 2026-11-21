"""Streamlit dashboard for the Abstention Gaming Detector.

Three tabs:
1. Audit explorer - build a seeded log (honest or gaming abstention,
   chosen quality / coverage / subtlety) and audit it live: gaming
   score, permutation p-value, reported vs counterfactual accuracy.
2. Band evidence - the per-confidence-band error rates, abstained vs
   answered, that the permutation test pools.
3. Evaluation - the stored multi-seed headline results (from
   results/evaluation.json): detection AUC vs the aggregate-only
   baseline, false-positive rate, detection by subtlety, and
   honest-score recovery error.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from abstention_gaming.baseline import baseline_scores
from abstention_gaming.counterfactual import counterfactual_report
from abstention_gaming.detector import audit_log
from abstention_gaming.evaluate import N_CASES
from abstention_gaming.generate import build_log

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "results", "evaluation.json")


@st.cache_data(show_spinner=False)
def load_audit(policy, subtlety, quality, coverage, seed):
    log, truth = build_log(seed, N_CASES, quality, policy, coverage,
                           subtlety=subtlety)
    audit = audit_log(log, n_perm=399, seed=99)
    return {"meta": log.meta,
            "coverage": log.coverage,
            "abstained_error_rate": log.abstained_error_rate(),
            "answered_error_rate": log.answered_error_rate(),
            "audit": audit.to_dict(),
            "counterfactual": counterfactual_report(log),
            "baseline": baseline_scores(log),
            "truth": truth}


@st.cache_data(show_spinner=False)
def load_results():
    if not os.path.isfile(RESULTS):
        return None
    with open(RESULTS) as fh:
        return json.load(fh)


st.set_page_config(page_title="Abstention Gaming Detector", layout="wide")
st.title("Abstention Gaming Detector")
st.write("Did the system abstain because it was unsure, or because it "
         "was wrong? A confidence-conditional permutation test audits "
         "the log; a matched-coverage counterfactual prices the claim.")

tab_audit, tab_bands, tab_eval = st.tabs(
    ["Audit explorer", "Band evidence", "Evaluation"])

with tab_audit:
    col1, col2, col3 = st.columns(3)
    policy = col1.selectbox("Abstention policy",
                            ["threshold", "noisy", "random", "gaming"])
    quality = col2.selectbox("Model quality", [0.72, 0.80, 0.88],
                             index=1)
    coverage = col3.selectbox("Coverage", [0.50, 0.70, 0.85], index=2)
    col4, col5 = st.columns(2)
    subtlety = col4.slider("Gaming subtlety (gaming policy only)",
                           0.05, 1.0, 0.60, 0.05)
    seed = col5.number_input("Seed", min_value=1, max_value=9999,
                             value=7)
    data = load_audit(policy, subtlety if policy == "gaming" else 0.0,
                      quality, coverage, int(seed))
    cf = data["counterfactual"]
    audit = data["audit"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Reported accuracy", "%.4f" % cf["reported_accuracy"])
    m2.metric("Honest counterfactual",
              "%.4f" % cf["honest_counterfactual"])
    m3.metric("Inflation", "%.4f" % cf["inflation"])
    m4.metric("Permutation p-value", "%.4f" % audit["p_value"])
    st.write("Gaming score (permutation z): **%.2f** - pooled "
             "within-band error-rate gap **%.4f** over %d bands."
             % (audit["gaming_score"], audit["gaming_gap"],
                audit["n_bands"]))
    if audit["p_value"] < 0.05:
        st.error("FLAGGED: abstention is label-aware at the stated "
                 "confidence (alpha 0.05).")
    else:
        st.success("Not flagged: abstention is consistent with "
                   "confidence-only selective prediction.")
    st.write("Planted truth for this seeded log: honest score %.4f, "
             "planted inflation %.4f."
             % (data["truth"]["true_honest_score"],
                data["truth"]["planted_inflation"]))

with tab_bands:
    st.write("Per-band error rates for the log selected in the Audit "
             "explorer tab. Under honest abstention the two rates "
             "track each other inside every band; gaming pulls the "
             "abstained rate up and the answered rate down.")
    rows = []
    chart = {"band": [], "abstained err": [], "answered err": []}
    for idx, s in enumerate(data["audit"]["band_stats"]):
        if s["n_abstained"] == 0 or s["n_answered"] == 0:
            continue
        rate_a = s["errors_abstained"] / float(s["n_abstained"])
        rate_r = s["errors_answered"] / float(s["n_answered"])
        rows.append({"band": idx,
                     "conf_min": round(s["conf_min"], 3),
                     "conf_max": round(s["conf_max"], 3),
                     "n": s["n"],
                     "abstained_err_rate": round(rate_a, 3),
                     "answered_err_rate": round(rate_r, 3)})
        chart["band"].append(idx)
        chart["abstained err"].append(rate_a)
        chart["answered err"].append(rate_r)
    st.dataframe(rows)
    st.bar_chart(chart, x="band", y=["abstained err", "answered err"])

with tab_eval:
    payload = load_results()
    if payload is None:
        st.write("No stored results yet. Run: python -m "
                 "abstention_gaming evaluate")
    else:
        h = payload["headline"]
        st.write("Seeded suite: %d logs, %d cases each."
                 % (payload["n_runs"], payload["n_cases"]))
        e1, e2, e3 = st.columns(3)
        e1.metric("Detector AUC", "%.3f" % h["detector_auc"])
        e2.metric("Baseline AUC (accuracy)",
                  "%.3f" % h["baseline_auc_accuracy"])
        e3.metric("Baseline AUC (lift)", "%.3f" % h["baseline_auc_lift"])
        e4, e5, e6 = st.columns(3)
        e4.metric("Honest false-positive rate",
                  "%.3f" % h["honest_false_positive_rate"])
        e5.metric("Gaming detection rate",
                  "%.3f" % h["gaming_detection_rate"])
        e6.metric("Mean recovery error",
                  "%.4f" % h["mean_recovery_error"])
        st.write("Detection by gaming subtlety:")
        rows = []
        for key in sorted(payload["per_subtlety"]):
            cell = payload["per_subtlety"][key]
            rows.append({"subtlety": key, "logs": cell["n"],
                         "detection_rate": round(cell["detection_rate"], 3),
                         "planted_inflation": round(
                             cell["mean_planted_inflation"], 4),
                         "estimated_inflation": round(
                             cell["mean_estimated_inflation"], 4)})
        st.dataframe(rows)
