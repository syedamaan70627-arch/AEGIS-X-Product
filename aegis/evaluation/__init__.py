"""
AEGIS-X Research Evaluation Package.
"""

from aegis.evaluation.ablation import AblationEvaluator
from aegis.evaluation.bootstrap import bootstrap_mean_ci
from aegis.evaluation.cross_domain import CrossDomainEvaluator
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture
from aegis.evaluation.metrics import EvaluationMetricsCalculator
from aegis.evaluation.multiseed import MultiSeedEvaluator
from aegis.evaluation.paired_comparison import calculate_paired_gain

__all__ = [
    "AblationEvaluator",
    "CrossDomainEvaluator",
    "EvaluationMetricsCalculator",
    "MultiSeedEvaluator",
    "bootstrap_mean_ci",
    "calculate_paired_gain",
    "load_breast_cancer_fixture",
    "load_digits_parity_fixture",
]
