# Changelog

## 0.1.0 - 2026-11-22

- Initial release.
- Confidence-conditional permutation test for label-aware abstention:
  quantile confidence bands, pooled within-band error-rate gap,
  within-band flag-shuffle null with p-value and z-score.
- Honest counterfactual reconstruction at matched coverage and
  inflation estimate per log.
- Aggregate-only baseline (reported accuracy / lift) for comparison.
- Seeded evaluation suite: honest threshold / noisy / random
  abstainers vs gaming abstainers at subtlety 0.35 / 0.60 / 1.00,
  model quality and coverage varied, planted ground truth throughout.
- Streamlit dashboard (audit explorer, band evidence, evaluation),
  CLI (`demo`, `audit`, `evaluate`), notebooks and examples.
