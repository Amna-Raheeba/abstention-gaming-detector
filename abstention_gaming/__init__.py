"""Abstention Gaming Detector.

Audits selective-prediction logs for label-aware abstention: a
confidence-conditional permutation test checks whether the cases a
system refused are, at the same stated confidence, disproportionately
the ones it would have got wrong - and reconstructs the honest
selective accuracy the system would have reported under a
confidence-only threshold at the same coverage.

Author: Amna Raheeba
"""

__version__ = "0.1.0"
__author__ = "Amna Raheeba"

from .models import PredictionLog, Record  # noqa: F401
from .detector import audit_log  # noqa: F401
from .counterfactual import honest_counterfactual  # noqa: F401
