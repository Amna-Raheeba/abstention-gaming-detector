# Sample report

Real captured output of `python examples/run_audit.py` - an audit of the stored demo log (data/demo_log.json: seeded gaming abstention, subtlety 0.60, quality 0.80, coverage 0.85, 1200 cases).

```text
Abstention audit - policy gaming (seed 7, quality 0.8)
================================================================
Cases: 1200   answered: 1020   abstained: 180   coverage: 0.850
Reported selective accuracy: 0.9167
Honest counterfactual (threshold, same coverage): 0.8392
Inflation over the honest counterfactual: 0.0775
Error rate among abstained cases: 0.844
Error rate among answered cases:  0.083

Confidence-conditional permutation test (20 bands, 999 permutations)
  Pooled within-band error-rate gap: 0.8843
  Gaming score (permutation z):      24.47
  Permutation p-value:               0.0010
  Verdict: FLAGGED - abstention is label-aware at the stated confidence (alpha 0.05).

Band evidence (confidence band: abstained vs answered error rates)
  [0.500-0.537] n=  60  abst err 0.472 (n=53)  answered err 0.143 (n=7)
  [0.537-0.577] n=  60  abst err 1.000 (n=11)  answered err 0.245 (n=49)
  [0.579-0.623] n=  60  abst err 1.000 (n=12)  answered err 0.250 (n=48)
  [0.623-0.654] n=  60  abst err 1.000 (n=8)  answered err 0.173 (n=52)
  [0.656-0.698] n=  60  abst err 1.000 (n=9)  answered err 0.118 (n=51)
  [0.699-0.724] n=  60  abst err 1.000 (n=7)  answered err 0.075 (n=53)
  [0.724-0.752] n=  60  abst err 1.000 (n=9)  answered err 0.118 (n=51)
  [0.752-0.771] n=  60  abst err 1.000 (n=13)  answered err 0.085 (n=47)
  [0.772-0.787] n=  60  abst err 1.000 (n=13)  answered err 0.106 (n=47)
  [0.788-0.808] n=  60  abst err 1.000 (n=9)  answered err 0.078 (n=51)
  [0.808-0.823] n=  60  abst err 1.000 (n=4)  answered err 0.089 (n=56)
  [0.823-0.843] n=  60  abst err 1.000 (n=3)  answered err 0.070 (n=57)
  [0.843-0.861] n=  60  abst err 1.000 (n=5)  answered err 0.055 (n=55)
  [0.861-0.884] n=  60  abst err 1.000 (n=5)  answered err 0.073 (n=55)
  [0.884-0.904] n=  60  abst err 1.000 (n=6)  answered err 0.056 (n=54)
  [0.904-0.927] n=  60  abst err 1.000 (n=6)  answered err 0.019 (n=54)
  [0.928-0.954] n=  60  abst err 1.000 (n=1)  answered err 0.017 (n=59)
  [0.954-0.980] n=  60  abst err 1.000 (n=4)  answered err 0.000 (n=56)
  [0.981-0.999] n=  60  abst err 1.000 (n=1)  answered err 0.017 (n=59)
  [0.999-0.999] n=  60  abst err 1.000 (n=1)  answered err 0.000 (n=59)

Planted truth for this log: honest score 0.8392, planted inflation 0.0775.
```
