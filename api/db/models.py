"""
AEGIS-X API Database Entity Models.

Provides Python dataclasses mapping directly to SQLite/PostgreSQL database rows.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ModelRecord:
    id: str
    model_name: str
    task_type: str
    file_path: str
    filename: str
    predict_supported: bool
    predict_proba_supported: bool
    created_at: str
    user_id: str = "local_dev_user"
    description: Optional[str] = None
    n_features_in: Optional[int] = None
    classes: Optional[List[Any]] = field(default_factory=list)
    feature_names: Optional[List[str]] = field(default_factory=list)


@dataclass
class DatasetRecord:
    id: str
    model_id: str
    dataset_type: str
    file_path: str
    filename: str
    num_samples: int
    num_features: int
    feature_names: List[str]
    has_target: bool
    created_at: str
    user_id: str = "local_dev_user"
    target_column: Optional[str] = None


@dataclass
class ReferenceStateRecord:
    id: str
    model_id: str
    dataset_id: str
    artifact_path: str
    feature_names: List[str]
    num_samples: int
    fitted_at: str
    user_id: str = "local_dev_user"


@dataclass
class AnalysisRecord:
    id: str
    model_id: str
    reference_dataset_id: str
    evaluation_dataset_id: str
    status: str
    result_path: str
    fusion_method: str
    has_labels: bool
    created_at: str
    user_id: str = "local_dev_user"
    aggregate_ood_risk: Optional[float] = None
    aggregate_uncertainty: Optional[float] = None
    aggregate_drift_score: Optional[float] = None
    aggregate_fused_risk: Optional[float] = None


@dataclass
class StressTestRecord:
    id: str
    model_id: str
    evaluation_dataset_id: str
    stress_type: str
    severity: float
    status: str
    result_path: str
    created_at: str
    user_id: str = "local_dev_user"
    original_risk: Optional[float] = None
    stressed_risk: Optional[float] = None
    risk_delta: Optional[float] = None


@dataclass
class FaultTestRecord:
    id: str
    model_id: str
    evaluation_dataset_id: str
    fault_type: str
    severity: float
    status: str
    result_path: str
    created_at: str
    user_id: str = "local_dev_user"


@dataclass
class FailureMemoryRecord:
    id: str
    model_id: str
    n_signatures: int
    artifact_path: str
    fitted_at: str
    user_id: str = "local_dev_user"


@dataclass
class PredictionRecord:
    id: str
    model_id: str
    status: str
    horizon_steps: int
    result_path: str
    created_at: str
    user_id: str = "local_dev_user"
    mean_probability: Optional[float] = None


@dataclass
class WarningRecord:
    id: str
    model_id: str
    status: str
    is_warning_triggered: bool
    threshold: float
    result_path: str
    created_at: str
    user_id: str = "local_dev_user"
    warning_score: Optional[float] = None


@dataclass
class GovernanceEvaluationRecord:
    id: str
    model_id: str
    decision_id: str
    state_index: int
    operating_mode: str
    raw_action: str
    effective_action: str
    transition_occurred: bool
    evidence_snapshot_hash: str
    result_path: str
    created_at: str
    user_id: str = "local_dev_user"
    analysis_id: Optional[str] = None
    previous_effective_action: Optional[str] = None
    transition_reason: Optional[str] = None
    p_adverse: Optional[float] = None
    prediction_set_json: Optional[str] = None
    reason_codes_json: Optional[str] = None
    calibrated: bool = False
    calibrator_artifact_id: Optional[str] = None
    calibrator_artifact_sha256: Optional[str] = None


@dataclass
class GovernanceTransitionRecord:
    id: str
    model_id: str
    evaluation_id: str
    state_index: int
    new_state: str
    raw_action: str
    transition_reason: str
    evidence_snapshot_hash: str
    created_at: str
    user_id: str = "local_dev_user"
    previous_state: Optional[str] = None
    calibrated: bool = False
