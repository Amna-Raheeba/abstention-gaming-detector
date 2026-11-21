# Evaluation summary

Seeded suite: 324 logs (1200 cases each), honest policies threshold / noisy / random and gaming at subtlety 0.35 / 0.60 / 1.00, model quality 0.72 / 0.80 / 0.88, confidence noise 0.02 / 0.05 / 0.10, coverage 0.50 / 0.70 / 0.85, seeds [11, 12]. Permutations per audit: 399.

## Headline numbers

| Metric | Value |
| --- | --- |
| Detection AUC, permutation gaming score | 1.000 |
| Detection AUC, baseline reported accuracy | 0.882 |
| Detection AUC, baseline accuracy lift | 0.976 |
| False-positive rate on honest logs (alpha 0.05) | 0.012 |
| Detection rate on gaming logs | 1.000 |
| Mean planted inflation (gaming logs) | 0.0754 |
| Mean estimated inflation (counterfactual) | 0.0754 |
| Mean honest-score recovery error, detector | 0.0000 |
| Mean honest-score recovery error, trust-the-report baseline | 0.0754 |
| Naive rule (flag if lift > 0.10): false-positive rate | 0.056 |
| Naive rule (flag if lift > 0.10): detection rate, all gaming | 0.796 |
| Naive rule (flag if lift > 0.10): detection rate, subtlety 0.35 | 0.500 |

## Detection by gaming subtlety

| Subtlety | Logs | Detection rate | Planted inflation | Estimated inflation |
| --- | --- | --- | --- | --- |
| 0.35 | 54 | 1.000 | 0.0409 | 0.0409 |
| 0.60 | 54 | 1.000 | 0.0688 | 0.0688 |
| 1.00 | 54 | 1.000 | 0.1165 | 0.1165 |
