"""
AEGIS-X API Governance Schemas.

Pydantic models for ECRG evaluation requests, responses, status, and history endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aegis.governance.schemas import ECRGOperatingMode, ECRGGovernanceAction


class GovernanceEvaluationRequest(BaseModel):
    """Input payload for evaluating reliability governance."""
    model_id: str = Field(..., description="Target model identifier")
    dataset_id: str = Field(..., description="Evaluated dataset identifier")
    trajectory_id: Optional[str] = Field(None, description="Operational trajectory/unit ID")
    state_index: int = Field(0, ge=0, description="Sequential state step index within trajectory")
    timestamp: Optional[str] = Field(None, description="ISO-8601 evaluation timestamp")
    source_analysis_id: Optional[str] = Field(None, description="Upstream analysis execution ID")

    # Reliability signals (Modules 1-4)
    ood_score: float = Field(..., ge=0.0, le=1.0, description="Module 1: Pre-label OOD risk score")
    uncertainty_score: float = Field(..., ge=0.0, le=1.0, description="Module 2: Predictive uncertainty score")
    drift_score: float = Field(..., ge=0.0, le=1.0, description="Module 3: Feature drift score")
    fused_risk: float = Field(..., ge=0.0, le=1.0, description="Module 4: Fused risk score")

    # Detector diagnostics (Modules 5-6)
    signal_disagreement: float = Field(0.0, ge=0.0, le=1.0, description="Variance across signals")
    ood_drift_redundancy: float = Field(0.0, ge=0.0, le=1.0, description="Covariance between OOD and drift")
    stress_robustness: float = Field(1.0, ge=0.0, le=1.0, description="Evaluated model robustness factor")
    fault_sensitivity: float = Field(0.0, ge=0.0, le=1.0, description="Evaluated fault sensitivity factor")

    # Advanced signals (Modules 11-13)
    memory_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Failure Memory k-NN similarity score")
    temporal_failure_probability: float = Field(0.0, ge=0.0, le=1.0, description="Hazard failure probability")
    early_warning_state: str = Field("NORMAL", description="Degradation lead state (NORMAL/DEGRADED/CRITICAL)")
    prediction_horizon: int = Field(5, ge=1, description="Controlled degradation lead step horizon K")

    # Optional outcome labels
    eventual_failure: Optional[bool] = Field(None, description="True trajectory outcome")
    failure_within_horizon: Optional[bool] = Field(None, description="True failure within horizon K")

    # Operating parameters
    mode: ECRGOperatingMode = Field(ECRGOperatingMode.EVIDENCE_ONLY, description="ECRG operating mode")
    target_risk_alpha: float = Field(0.05, gt=0.0, lt=1.0, description="Target risk alpha for conformal calibration")


class GovernanceEvaluationResponse(BaseModel):
    """Output payload for a governance evaluation decision."""
    evaluation_id: str = Field(..., description="Unique evaluation decision ID")
    model_id: str = Field(..., description="Target model ID")
    user_id: str = Field(..., description="Owner user ID")
    dataset_id: str = Field(..., description="Evaluated dataset ID")
    mode: ECRGOperatingMode = Field(..., description="Operating mode used")
    action: ECRGGovernanceAction = Field(..., description="Effective governance decision action")
    warning_severity: str = Field("LOW", description="Warning severity (LOW/MODERATE/HIGH/CRITICAL)")
    certification_banner: str = Field(..., description="UI banner text")
    calibrated: bool = Field(False, description="Whether formal conformal guarantees apply")
    primary_supporting_signal: str = Field(..., description="Main driving signal")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting evidence details")
    contradictory_evidence: List[str] = Field(default_factory=list, description="Contradictory evidence details")
    signal_disagreement_index: float = Field(0.0, description="Measured signal variance")
    consecutive_state_count: int = Field(1, description="Consecutive steps in current state")
    in_cooldown: bool = Field(False, description="De-escalation cooldown active status")
    state_transition_occurred: bool = Field(False, description="Whether state transitioned on this step")
    evidence_snapshot_hash: str = Field(..., description="SHA-256 hash of input evidence snapshot")
    p_adverse: float = Field(0.0, description="Estimated adverse probability")
    transition_reason: str = Field(..., description="Transition rationale")
    reason_codes: List[str] = Field(default_factory=list, description="Machine-readable reason codes")
    result_json_path: Optional[str] = Field(None, description="Artifact storage location")
    created_at: str = Field(..., description="ISO-8601 timestamp")


class GovernanceStatusResponse(BaseModel):
    """Current governance status for a specific model."""
    model_id: str = Field(..., description="Target model ID")
    latest_action: ECRGGovernanceAction = Field(..., description="Latest governance decision action")
    mode: ECRGOperatingMode = Field(..., description="Latest operating mode")
    warning_severity: str = Field("LOW", description="Current warning severity")
    consecutive_state_count: int = Field(1, description="Consecutive state count")
    in_cooldown: bool = Field(False, description="Cooldown active status")
    last_evaluated_at: str = Field(..., description="ISO-8601 timestamp of last evaluation")
    total_evaluations: int = Field(0, description="Total evaluations run")
    total_transitions: int = Field(0, description="Total state transitions recorded")


class GovernanceTransitionResponse(BaseModel):
    """Recorded governance state transition."""
    transition_id: str = Field(..., description="Unique transition ID")
    model_id: str = Field(..., description="Target model ID")
    from_action: Optional[ECRGGovernanceAction] = Field(None, description="Previous action")
    to_action: ECRGGovernanceAction = Field(..., description="New action")
    transition_reason: str = Field(..., description="Transition rationale")
    reason_codes: List[str] = Field(default_factory=list, description="Reason codes")
    in_cooldown: bool = Field(False, description="Cooldown active status")
    timestamp: str = Field(..., description="ISO-8601 timestamp")


class GovernanceHistoryResponse(BaseModel):
    """Paginated governance evaluation history."""
    model_id: str = Field(..., description="Target model ID")
    total: int = Field(..., description="Total available records")
    limit: int = Field(..., description="Page limit")
    offset: int = Field(..., description="Page offset")
    evaluations: List[GovernanceEvaluationResponse] = Field(..., description="Evaluation records")
