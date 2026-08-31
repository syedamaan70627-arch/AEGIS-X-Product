"""
AEGIS-X Integration Contracts Module.

Defines domain-agnostic dataclasses, enums, and type definitions for model and
dataset registration, analysis requests, validation reports, and validated inputs.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class ModelType(str, Enum):
    """Supported model file format types for Version 1."""
    SKLEARN_JOBLIB = "sklearn_joblib"
    SKLEARN_PKL = "sklearn_pkl"
    GENERIC_SKLEARN = "generic_sklearn"


class TaskType(str, Enum):
    """Supported machine learning task types for Version 1."""
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"


class DatasetType(str, Enum):
    """Dataset role within the AEGIS-X reliability engine."""
    REFERENCE = "reference"
    EVALUATION = "evaluation"


@dataclass
class ModelRegistration:
    """User registration record for an existing trained ML model."""
    model_id: str
    model_name: str
    model_path: Union[str, Path]
    task_type: TaskType
    feature_names: List[str] = field(default_factory=list)
    target_column: Optional[str] = None
    probability_supported: bool = False
    model_type: ModelType = ModelType.GENERIC_SKLEARN
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.model_path, str):
            self.model_path = Path(self.model_path)
        if isinstance(self.task_type, str):
            self.task_type = TaskType(self.task_type)
        if isinstance(self.model_type, str):
            self.model_type = ModelType(self.model_type)


@dataclass
class DatasetRegistration:
    """User registration record for a dataset (reference or evaluation)."""
    dataset_id: str
    dataset_name: str
    dataset_path: Union[str, Path]
    dataset_type: DatasetType
    feature_names: List[str] = field(default_factory=list)
    target_column: Optional[str] = None
    num_samples: int = 0
    num_features: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.dataset_path, str):
            self.dataset_path = Path(self.dataset_path)
        if isinstance(self.dataset_type, str):
            self.dataset_type = DatasetType(self.dataset_type)


@dataclass
class AnalysisRequest:
    """Request payload encapsulating model and dataset parameters for reliability analysis."""
    request_id: str
    model_registration: ModelRegistration
    reference_dataset_registration: DatasetRegistration
    evaluation_dataset_registration: DatasetRegistration
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Structured report produced by the AEGIS-X IntegrationValidator."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidatedInput:
    """Container holding fully validated model adapter, feature schema, and data matrices."""
    model_adapter: Any
    X_reference: Any
    y_reference: Optional[Any]
    X_evaluation: Any
    y_evaluation: Optional[Any]
    feature_names: List[str]
    task_type: TaskType
    report: ValidationReport


class ReliabilityStatus(str, Enum):
    """Execution status for reliability modules and results."""
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


@dataclass
class OODResult:
    """Structured result produced by the Out-of-Distribution (OOD) Detector."""
    status: ReliabilityStatus
    method: str
    scores: Optional[Any] = None
    risk_scores: Optional[Any] = None
    aggregate_risk: float = 0.0
    threshold: Optional[float] = None
    reference_stats: Dict[str, Any] = field(default_factory=dict)
    detector_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class UncertaintyResult:
    """Structured result produced by the Uncertainty Estimator."""
    status: ReliabilityStatus
    method: str
    probabilities: Optional[Any] = None
    uncertainty_scores: Optional[Any] = None
    aggregate_uncertainty: float = 0.0
    is_calibrated: bool = False
    calibration_info: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class DriftResult:
    """Structured result produced by the Concept/Distribution Drift Detector."""
    status: ReliabilityStatus
    method: str
    feature_drift_flags: Dict[str, bool] = field(default_factory=dict)
    feature_p_values: Dict[str, float] = field(default_factory=dict)
    feature_statistics: Dict[str, float] = field(default_factory=dict)
    aggregate_drift_score: float = 0.0
    drift_detected: bool = False
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class CoreReliabilityResult:
    """Aggregated result holding output signals from OOD, Uncertainty, and Drift detectors."""
    ood: OODResult
    uncertainty: UncertaintyResult
    drift: DriftResult
    warnings: List[str] = field(default_factory=list)
    capability_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusionResult:
    """Structured result produced by the Reliability Fusion Engine."""
    status: ReliabilityStatus
    method: str
    ood_signal: Optional[Any] = None
    uncertainty_signal: Optional[Any] = None
    drift_signal: Optional[Any] = None
    fused_risk_scores: Optional[Any] = None
    aggregate_fused_risk: float = 0.0
    threshold: Optional[float] = None
    model_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class StressTestResult:
    """Structured result produced by the Controlled Stress Testing Engine."""
    status: ReliabilityStatus
    stress_type: str
    severity: float
    original_risk: float
    stressed_risk: float
    risk_delta: float
    accuracy_delta: Optional[float] = None
    original_accuracy: Optional[float] = None
    stressed_accuracy: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


class FaultType(str, Enum):
    """Supported structured fault injection types (Module 7)."""
    SENSOR_BIAS = "Sensor_Bias"
    GAIN_ERROR = "Gain_Error"
    STUCK_AT = "Stuck_At"
    CHANNEL_SWAP = "Channel_Swap"
    SIGN_INVERSION = "Sign_Inversion"


@dataclass
class FaultConfiguration:
    """Configuration specification for structured fault injection."""
    fault_type: Union[FaultType, str]
    severity: float
    affected_features: List[str] = field(default_factory=list)
    random_state: int = 42
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FaultInjectionResult:
    """Structured result produced by the FaultInjector engine."""
    status: ReliabilityStatus
    fault_type: str
    severity: float
    affected_features: List[str]
    transformation_metadata: Dict[str, Any] = field(default_factory=dict)
    random_state: int = 42
    original_shape: Optional[Tuple[int, int]] = None
    transformed_shape: Optional[Tuple[int, int]] = None
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class FailureEvent:
    """Individual observation failure event detail."""
    sample_id: Union[int, str]
    ood_risk: float
    uncertainty_risk: float
    drift_risk: float
    fused_risk: float
    is_high_risk_warning: bool
    fault_type: Optional[str] = None
    severity: Optional[float] = None
    has_actual_failure: Optional[bool] = None  # None if label-free
    is_silent_failure: Optional[bool] = None   # None if label-free
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureDiscoveryResult:
    """Structured summary report produced by the FailureDiscoveryEngine."""
    status: ReliabilityStatus
    is_label_aware: bool
    total_samples: int
    total_warnings: int
    total_failures: Optional[int] = None
    silent_failures: Optional[int] = None
    silent_failure_rate: Optional[float] = None
    failure_events: List[FailureEvent] = field(default_factory=list)
    summary_by_fault: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class FailureSignature:
    """Discovered failure signature profile centroid representation (Module 8R)."""
    signature_id: int
    centroid_profile: Dict[str, float]
    feature_names: List[str]
    sample_count: int = 0
    distance_threshold: float = 0.0
    associated_fault_distribution: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class SignatureMatchResult:
    """Structured result of matching a query reliability profile against Failure Memory."""
    signature_id: int
    signature_distance: float
    distance_threshold: float
    is_known_pattern: bool
    centroid_profile: Dict[str, float] = field(default_factory=dict)
    associated_fault_distribution: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class FailureMemoryResult:
    """Structured result of building or querying Failure Memory."""
    status: ReliabilityStatus
    n_signatures: int
    signatures: List[FailureSignature] = field(default_factory=list)
    silhouette_score: Optional[float] = None
    stability_ari: Optional[float] = None
    quality_summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class PredictionThresholdInfo:
    """Metadata detailing validation-only threshold selection (Module 9R)."""
    threshold: float
    selection_metric: str = "f1"
    selection_split: str = "validation"
    validation_f1: float = 0.0
    validation_recall: float = 0.0
    validation_precision: float = 0.0


@dataclass
class FailurePredictionEvent:
    """Individual prediction event detail."""
    sample_id: Union[int, str]
    predicted_failure_prob: float
    is_failure_warning: bool
    threshold: float
    actual_future_failure: Optional[bool] = None  # None if label-free / operational
    actual_failure_onset: Optional[bool] = None   # None if label-free / operational
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailurePredictionResult:
    """Structured summary report produced by FailurePredictor."""
    status: ReliabilityStatus
    horizon_steps: int
    selected_predictor: str
    threshold_info: Optional[PredictionThresholdInfo] = None
    predictions: List[FailurePredictionEvent] = field(default_factory=list)
    aggregate_onset_warning_rate: float = 0.0
    mean_predicted_probability: float = 0.0
    heldout_metrics: Optional[Dict[str, float]] = None
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class WarningHorizon:
    """Multi-state warning horizon representation (Module 10)."""
    value: int = 3
    unit: str = "controlled_degradation_states"


@dataclass
class WarningEvent:
    """Individual state early warning event detail."""
    state_id: Union[int, str]
    trajectory_id: Union[int, str]
    warning_score: float
    is_warning_triggered: bool
    threshold: float
    horizon: WarningHorizon
    actual_failure_within_horizon: Optional[bool] = None  # None if operational / label-free
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrajectoryWarningResult:
    """Trajectory-level warning lead time evaluation result."""
    trajectory_id: Union[int, str]
    eventually_fails: bool
    first_warning_state_index: Optional[int] = None
    failure_state_index: Optional[int] = None
    lead_steps: Optional[int] = None  # (failure_index - first_warning_index)
    is_early_warning: bool = False
    is_false_trajectory_warning: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WarningResult:
    """Operational query warning result for a single observation or state."""
    status: ReliabilityStatus
    warning_score: float
    is_warning_triggered: bool
    threshold: float
    horizon: WarningHorizon
    signals: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class EarlyWarningEvaluation:
    """Structured summary report produced by EarlyWarningEngine."""
    status: ReliabilityStatus
    selected_horizon: WarningHorizon
    warning_threshold: float
    state_level_metrics: Dict[str, float] = field(default_factory=dict)
    trajectory_level_metrics: Dict[str, Any] = field(default_factory=dict)
    trajectory_results: List[TrajectoryWarningResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class AblationConfiguration:
    """Configuration description for an ablation run."""
    name: str
    description: str
    included_signals: List[str]
    feature_names: List[str]


@dataclass
class AblationMetrics:
    """State-level evaluation metrics for an ablated model."""
    auroc: float
    aupr: float
    precision: float
    recall: float
    f1: float
    threshold: float


@dataclass
class ComponentContribution:
    """Evaluated contribution and signed delta for a specific ablated component (Module 11)."""
    component_name: str
    config_name: str
    metrics: AblationMetrics
    delta_auroc: float  # (ablated - full)
    delta_aupr: float   # (ablated - full)
    delta_f1: float     # (ablated - full)
    is_performance_sensitive: bool = False


@dataclass
class AblationStudyResult:
    """Structured summary report produced by AblationEvaluator."""
    status: ReliabilityStatus
    horizon_steps: int
    full_metrics: AblationMetrics
    component_contributions: Dict[str, ComponentContribution] = field(default_factory=dict)
    static_vs_dynamic: Dict[str, float] = field(default_factory=dict)
    most_sensitive_component: str = ""
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class DomainEvaluationResult:
    """Evaluation result for a single real tabular research domain (Module 12)."""
    domain_name: str
    sample_count: int
    feature_count: int
    baseline_accuracy: float
    fusion_auroc: float
    best_individual_signal: str
    best_individual_auroc: float
    fusion_beats_individual: bool
    spearman_correlation: float
    unseen_family_auroc: float
    warning_lead_summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class CrossDomainResult:
    """Structured summary report for Module 12 real cross-domain validation."""
    status: ReliabilityStatus
    domain_results: Dict[str, DomainEvaluationResult] = field(default_factory=dict)
    mean_fusion_auroc: float = 0.0
    mean_spearman_correlation: float = 0.0
    mean_unseen_family_auroc: float = 0.0
    fusion_win_count: int = 0
    total_domains: int = 0
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class BootstrapInterval:
    """Bootstrap confidence interval representation (Module 13)."""
    estimate: float
    lower: float
    upper: float
    confidence_level: float = 0.95


@dataclass
class SeedDomainRunResult:
    """Evaluation result for a single (seed, domain) run in Module 13."""
    seed: int
    domain_name: str
    fusion_auroc: float
    fusion_aupr: float
    best_individual_signal: str
    best_individual_aupr: float
    paired_aupr_gain: float  # (fusion_aupr - best_individual_aupr)
    is_fusion_win: bool
    spearman_correlation: float
    unseen_family_auroc: float
    warning_status: str = ""


@dataclass
class MultiSeedAggregateResult:
    """Aggregate multi-seed evaluation metrics across all runs (Module 13)."""
    mean_fusion_auroc: float
    fusion_auroc_ci: BootstrapInterval
    mean_spearman_correlation: float
    spearman_ci: BootstrapInterval
    mean_unseen_family_auroc: float
    unseen_family_ci: BootstrapInterval
    mean_paired_gain: float
    paired_gain_ci: BootstrapInterval
    fusion_win_rate: float
    fusion_win_count: int
    total_runs: int
    domain_gains: Dict[str, float] = field(default_factory=dict)


@dataclass
class EarlyWarningReproducibilityResult:
    """Summary of cross-seed early warning reproducibility (Module 13)."""
    total_measurable_boundaries: int
    positive_lead_count: int
    positive_lead_rate: float
    late_warning_count: int
    late_warning_rate: float


@dataclass
class FinalResearchValidationSummary:
    """Final structured scientific research validation summary produced by Module 13."""
    status: ReliabilityStatus
    seeds_evaluated: List[int]
    domains_evaluated: List[str]
    total_requested_experiments: int
    completed_experiments: int
    failed_experiments: int
    aggregate_results: MultiSeedAggregateResult
    early_warning_reproducibility: EarlyWarningReproducibilityResult
    verdict: str = "ROBUST FRAMEWORK / MIXED FUSION EVIDENCE"
    is_fusion_superiority_established: bool = False
    defensible_claim: str = ""
    preserved_negative_findings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)









