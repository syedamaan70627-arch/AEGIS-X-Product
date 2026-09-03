"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG) Schemas.
Typed Pydantic contracts for inputs, governance actions, operating modes, and outputs.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ECRGOperatingMode(str, Enum):
    """ECRG Operating Modes."""
    EVIDENCE_ONLY = "EVIDENCE_ONLY"
    CALIBRATED_GOVERNANCE = "CALIBRATED_GOVERNANCE"


class ECRGGovernanceAction(str, Enum):
    """ECRG Governance Decision Actions."""
    CONTINUE = "CONTINUE"
    WATCH = "WATCH"
    DEFER = "DEFER"
    ESCALATE = "ESCALATE"


class ECRGEvidenceContract(BaseModel):
    """
    Typed Evidence Input Contract for Module 14.
    Aggregates reliability signals, anomaly signatures, and temporal hazard estimates from Modules 1-13.
    """
    # Identifiers & Provenance
    model_id: str = Field(..., description="Target model identifier")
    dataset_id: str = Field(..., description="Evaluated dataset identifier")
    trajectory_id: Optional[str] = Field(None, description="Operational trajectory/unit ID")
    state_index: int = Field(..., ge=0, description="Sequential state step index within trajectory")
    timestamp: str = Field(..., description="ISO-8601 evaluation timestamp")
    source_analysis_id: Optional[str] = Field(None, description="Upstream analysis execution ID")

    # Label-Free Production Signals (Modules 1-4)
    ood_score: float = Field(..., ge=0.0, le=1.0, description="Module 1: Pre-label OOD risk score")
    uncertainty_score: float = Field(..., ge=0.0, le=1.0, description="Module 2: Predictive uncertainty score")
    drift_score: float = Field(..., ge=0.0, le=1.0, description="Module 3: Feature drift score")
    fused_risk: float = Field(..., ge=0.0, le=1.0, description="Module 4: StressRobustFusion risk score")

    # Detector Diagnostics & Interactions
    signal_disagreement: float = Field(0.0, ge=0.0, le=1.0, description="Variance across OOD, uncertainty, and drift")
    ood_drift_redundancy: float = Field(0.0, ge=0.0, le=1.0, description="Covariance between OOD and Feature Drift signals")
    stress_robustness: float = Field(1.0, ge=0.0, le=1.0, description="Module 5: Evaluated model robustness factor")
    fault_sensitivity: float = Field(0.0, ge=0.0, le=1.0, description="Module 6: Evaluated fault sensitivity factor")

    # Advanced Intelligence Evidence (Modules 11-13)
    memory_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Module 11: Failure Memory k-NN similarity score")
    temporal_failure_probability: float = Field(0.0, ge=0.0, le=1.0, description="Module 12: Hazard model failure probability")
    early_warning_state: str = Field("NORMAL", description="Module 13: Degradation lead state (NORMAL/DEGRADED/CRITICAL)")
    prediction_horizon: int = Field(5, ge=1, description="Controlled degradation lead step horizon K")

    # Ground-Truth / Outcome Data (Labeled Calibration & Retrospective Evaluation ONLY)
    eventual_failure: Optional[bool] = Field(None, description="True trajectory outcome (None in label-free production)")
    failure_within_horizon: Optional[bool] = Field(None, description="True failure within horizon K (None in production)")


class ECRGCalibrationConfig(BaseModel):
    """Conformal Risk Control Configuration for CALIBRATED_GOVERNANCE mode."""
    target_risk_alpha: float = Field(..., gt=0.0, lt=1.0, description="Target upper bound on unsafe automatic acceptance risk alpha")
    calibration_set_size: int = Field(0, ge=0, description="Number of trajectories/units in calibration split")
    calibrated_quantile_threshold: Optional[float] = Field(None, description="Computed q_hat quantile threshold")
    calibration_method: str = Field("Split_Conformal_Risk_Control", description="Conformal calibration algorithm")
    risk_quantity_controlled: str = Field("Population_Unsafe_Acceptance_Risk", description="Controlled risk metric (Population vs Selective)")
    stated_assumptions: List[str] = Field(
        default_factory=lambda: [
            "Exchangeable/i.i.d. trajectory sampling between calibration and test sets",
            "Group-aware trajectory split isolation",
            "Bounded loss function for unsafe automatic acceptance",
        ],
        description="Formal statistical assumptions for risk bounds",
    )


class ECRGDecisionResponse(BaseModel):
    """Typed Governance Decision Output for Module 14."""
    decision_id: str = Field(..., description="Unique governance decision ID")
    mode: ECRGOperatingMode = Field(..., description="Active operating mode")
    action: ECRGGovernanceAction = Field(..., description="Recommended governance decision action")
    warning_severity: str = Field("LOW", description="Warning severity (LOW/MODERATE/HIGH/CRITICAL)")
    
    # Mode-specific Banner & Status
    certification_banner: str = Field(..., description="UI banner text (e.g. LABEL-FREE / NON-CERTIFIED)")
    calibrated: bool = Field(False, description="Whether formal conformal calibration guarantees apply")
    
    # Calibration Telemetry (populated in CALIBRATED_GOVERNANCE mode)
    calibration_config: Optional[ECRGCalibrationConfig] = Field(None, description="Conformal calibration details")
    population_risk: Optional[float] = Field(None, description="E[1(action==CONTINUE) * failure_within_horizon]")
    selective_risk: Optional[float] = Field(None, description="P(failure_within_horizon=1 | action==CONTINUE)")
    coverage: Optional[float] = Field(None, description="P(action==CONTINUE)")

    # Non-Causal Evidence Attribution
    primary_supporting_signal: str = Field(..., description="Main reliability detector driving decision")
    supporting_evidence: List[str] = Field(default_factory=list, description="List of supporting evidence descriptions")
    contradictory_evidence: List[str] = Field(default_factory=list, description="List of contradictory evidence descriptions")
    signal_disagreement_index: float = Field(0.0, ge=0.0, le=1.0, description="Measured signal variance")
    
    # State-Machine Anti-Flapping Status
    consecutive_state_count: int = Field(1, ge=1, description="Consecutive steps in current governance state")
    in_cooldown: bool = Field(False, description="Whether de-escalation cooldown is currently active")
    state_transition_occurred: bool = Field(False, description="Whether state changed on this evaluation step")


class ECRGStateMachineConfig(BaseModel):
    """Versioned configuration for Anti-Flapping Governance State Machine."""
    defer_persistence_threshold: int = Field(3, ge=1, description="Consecutive DEFER actions required to trigger ESCALATE")
    recovery_consecutive_states: int = Field(3, ge=1, description="Consecutive lower-risk states required for de-escalation")
    cooldown_steps: int = Field(3, ge=0, description="Cooldown controlled degradation steps enforced after de-escalation")
    latch_escalate: bool = Field(True, description="Whether ESCALATE state remains latched until explicit reset/acknowledgement")
    version: str = Field("1.0.0", description="State machine configuration schema version")


class ECRGDecisionRecord(BaseModel):
    """
    Immutable Governance Decision Record as required by Section 9.
    Contains complete audit trail, evidence snapshot hash, calibrator metadata, and state machine transition details.
    """
    decision_id: str = Field(..., description="Unique decision ID")
    entity_id: str = Field(..., description="Entity/engine/trajectory ID")
    state_index: int = Field(..., ge=0, description="Sequential state index within trajectory")
    task_type: str = Field(..., description="Task type (STATIC_SELECTIVE_RISK / TEMPORAL_GOVERNANCE / AUXILIARY_SIMULATED_SEQUENCE)")
    dataset_profile: str = Field(..., description="Capability/dataset profile identifier")
    operating_mode: ECRGOperatingMode = Field(..., description="Operating mode")
    target_semantic: str = Field(..., description="Target semantic (e.g. SAMPLE_PREDICTION_ERROR / FAILURE_WITHIN_HORIZON)")
    horizon: Optional[int] = Field(None, description="Prediction horizon K")
    unit: str = Field("controlled_degradation_states", description="Horizon/state unit representation")
    alpha: Optional[float] = Field(None, description="Target risk alpha")
    p_adverse: float = Field(..., ge=0.0, le=1.0, description="Estimated adverse outcome probability P(Y=1|x)")
    nonconformity_details: Dict[str, Any] = Field(..., description="Nonconformity scores s(x,0), s(x,1), and quantile q")
    prediction_set: List[int] = Field(..., description="Conformal prediction set (subset of {0, 1})")
    raw_action: ECRGGovernanceAction = Field(..., description="Instantaneous raw governance action from prediction set")
    previous_effective_action: Optional[ECRGGovernanceAction] = Field(None, description="Previous step effective action")
    effective_action: ECRGGovernanceAction = Field(..., description="Final anti-flapping effective governance action")
    transition_reason: str = Field(..., description="Explanation of state machine transition decision")
    reason_codes: List[str] = Field(default_factory=list, description="Machine-readable decision reason codes")
    evidence_snapshot_hash: str = Field(..., description="SHA-256 hash of input evidence vector/snapshot")
    calibrator_artifact_id: Optional[str] = Field(None, description="Calibrator artifact ID")
    calibrator_artifact_sha256: Optional[str] = Field(None, description="Calibrator artifact SHA-256 hash")
    schema_version: str = Field("1.0.0", description="Decision record schema version")
    calibration_unit_count: Optional[int] = Field(None, description="Number of independent calibration units (e.g. 20)")
    guarantee_scope: Optional[str] = Field(None, description="Formal scope description of conformal coverage guarantee")
    calibrated: bool = Field(False, description="Whether decision is formally calibrated")
    creation_timestamp: str = Field(..., description="ISO-8601 creation timestamp")

