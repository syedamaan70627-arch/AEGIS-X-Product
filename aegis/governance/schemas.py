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
