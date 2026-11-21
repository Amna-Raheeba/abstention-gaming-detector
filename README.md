# Abstention Gaming Detector

*Did it abstain because it was unsure, or because it was wrong?*

An offline audit tool for selective-prediction logs. It detects when a
reported "accuracy with abstention" is gamed - when the system refused
cases it would have got wrong, in a way its stated confidence cannot
explain - and reconstructs the honest selective accuracy the system
would have reported under a confidence-only threshold at the same
coverage.

Author: Amna Raheeba · MIT License · Pure Python stdlib (Streamlit
dashboard optional)

## 1. The problem

Selective prediction lets a system answer only when confident and
abstain otherwise, reporting accuracy on the answered subset. The
reported number is gameable in a specific way: abstain not on
*uncertainty* but on *the label* - peek at which cases would be
errors and refuse exactly those. Coverage stays plausible, the
accuracy looks excellent, and nothing in the summary table
(coverage, reported accuracy, even accuracy lift over full coverage)
can convict it, because an honest system with sharp confidence or a
better model produces the same summary numbers.

This tool audits the log itself, where the gaming leaves a trace:
at the *same stated confidence*, the refused cases are
disproportionately the would-be errors.

## 2. The instrument

### 2.1 Input: a prediction log

One record per case: stated `confidence`, `abstained` flag, and the
would-be `correct` outcome. Would-be outcomes for abstained cases
exist in the settings this audits - benchmark replays, internal
evaluation runs, regulatory audits where the full scoring run was
logged before the abstention decision was applied.

### 2.2 The confidence-conditional permutation test

1. Bin the log into 20 narrow quantile bands of stated confidence.
2. In each band, compare the error rate of abstained cases with the
   error rate of answered cases. Pool the gap across bands, weighted
   by band size. Under honest (confidence-only) abstention the
   decision is uninformative about the outcome *given* confidence,
   so the gap hovers at zero. Under gaming it is systematically
   positive.
3. Significance from a permutation null: abstain flags are shuffled
   within each band (preserving each band's abstention count), which
   is exactly the statistic's distribution under "abstention depends
   on confidence only". Outputs: the pooled gap, a gaming score
   (permutation z), and a permutation p-value.

### 2.3 The honest counterfactual

Rank the log's own cases by stated confidence, answer exactly as
many as the system chose to answer, and score those. The difference
between the reported accuracy and this counterfactual is the
inflation: accuracy bought by choosing refusals with information
beyond the stated confidence.

### 2.4 The baseline it is compared against

Raw coverage / accuracy inspection - the aggregate scores from the
summary table (reported accuracy, and lift over full-coverage
accuracy), including the naive decision rule "flag any log whose
lift exceeds a threshold". This is what an auditor without the
joint distribution of confidence, abstention and outcome can do.

## 3. Measured results

Seeded evaluation, planted ground truth throughout: 324 logs of
1200 cases each. Honest policies (threshold, noisy, random) and a
gaming policy at subtlety 0.35 / 0.60 / 1.00 (the fraction of
would-be errors the policy can see), crossed with model quality
0.72 / 0.80 / 0.88, confidence noise 0.02 / 0.05 / 0.10 and coverage
0.50 / 0.70 / 0.85, two seeds per cell. All policies are
coverage-matched within a cell.

| Metric | Value |
| --- | --- |
| Detection AUC, permutation gaming score | 1.000 |
| Detection AUC, baseline reported accuracy | 0.882 |
| Detection AUC, baseline accuracy lift | 0.976 |
| False-positive rate on honest logs (alpha 0.05) | 0.012 (2 of 162) |
| Detection rate on gaming logs | 1.000 at every subtlety |
| Mean planted inflation (gaming logs) | 0.075 |
| Mean honest-score recovery error, detector | 0.0000 |
| Mean honest-score recovery error, trust-the-report | 0.075 |

Planted inflation by subtlety: 0.041 (0.35), 0.069 (0.60),
0.116 (1.00) - the counterfactual recovers each exactly.

The baseline as a *decision rule* fails in both directions, which is
the operational point. "Flag if lift > 0.10" still falsely flags
5.6% of honest logs while missing 50.0% of the subtle (0.35) gaming
logs; loosening the threshold to 0.05 catches the gamers but flags
42.0% of all honest logs. No threshold separates the populations,
because sharp-confidence honest systems earn large lifts
legitimately (honest lifts span -0.024 to 0.114; subtle gaming lifts
start at 0.066). The permutation test, conditioning on confidence,
holds its calibrated false-positive rate (0.012 observed at nominal
0.05) and detects every gaming log in the suite.

Demo (seed 7, same cases, coverage 0.85): the honest log reports
0.8392 with counterfactual 0.8392 and p = 1.000; the gaming log
(subtlety 0.60) reports 0.9167 against a counterfactual of 0.8392 -
inflation 0.0775 - with pooled within-band gap 0.884 and
p = 0.001.

## 4. Honest limits

- **Synthetic logs, planted mechanisms.** The numbers validate the
  instrument against known ground truth; they are not a claim about
  any real vendor's log. Real gaming could be subtler in structure
  (e.g. abstaining on errors only inside one confidence region -
  the band table would show it, and per-band evidence is reported
  precisely so a human can look).
- **Detection is exact at n = 1200 partly because the signal is
  strong there.** The subtlety-0.35 gamer still removes about 4
  points of planted inflation, which 1200 cases make visible.
  Smaller logs and weaker gaming will degrade power; the p-value,
  not the verdict, is the output to trust at the margin.
- **The counterfactual's zero recovery error is by construction**
  in this audit setting: the log carries would-be outcomes for
  abstained cases, so the matched-coverage threshold score is
  computed, not estimated. Where would-be outcomes do not exist,
  the counterfactual would need band-level imputation and would
  carry real error; the permutation test also relies on those
  outcomes. Logs without them are out of scope.
- **Bands are quantile bins of stated confidence.** A system that
  *lies about its confidence* (reports confidence engineered to
  hide the selection) attacks the conditioning itself; detecting
  miscalibrated confidence is a different audit.
- The honest false-positive rate came in below nominal (0.012 vs
  0.05): the test is slightly conservative on these generators,
  reported as measured.

## 5. Usage

```bash
python -m abstention_gaming demo       # audit an honest vs a gaming log
python -m abstention_gaming audit      # audit data/demo_log.json
python -m abstention_gaming evaluate   # rerun the full seeded suite
streamlit run app.py                   # dashboard
python notebooks/01_demo_run.py
python notebooks/02_evaluation_experiment.py
python scripts/reproduce_results.py    # drift guard on headline numbers
```

## 6. Project structure

```text
abstention_gaming/
  models.py         prediction log types and summary statistics
  generate.py       seeded case generator + honest/gaming policies
  detector.py       confidence bands + permutation test
  counterfactual.py honest score reconstruction at matched coverage
  baseline.py       aggregate-only scores and the naive rule
  evaluate.py       the seeded suite, AUCs, headline numbers
  report.py         text / Markdown renderers
  cli.py            demo / audit / evaluate commands
data/               demo log fixture + suite definition
results/            evaluation.json / .csv, summary, HEADLINE.md
notebooks/          runnable demo + evaluation notebooks
examples/           stored-log audit + captured sample report
tests/              pytest suite (70+ tests)
```

## 7. Prior art and differentiator

Selective classification (Geifman & El-Yaniv; conformal selective
prediction) *builds* abstention policies and reports risk-coverage
curves; strategic-classification gaming papers model users gaming a
classifier. Neither audits a third party's abstention log for
label-aware abstention, and neither reconstructs the honest
counterfactual score at matched coverage. This tool does both, from
the log alone, with a permutation test whose null is exactly the
honest-abstention hypothesis.

**Paper angle:** "Did it abstain because it was unsure, or because
it was wrong? A permutation audit of selective-prediction claims."

## 8. License

MIT - see `LICENSE`.
