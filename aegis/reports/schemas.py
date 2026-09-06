"""
AEGIS-X Reports Schemas & Data Models.

Defines strict type models for report context, completeness matrix, trust states,
decision rationales, operator action plans, and complete report payloads.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TrustDisposition(str, Enum):
    HIGH = "HIGH"
    CONDITIONAL = "CONDITIONAL"
    LOW = "LOW"
    RESTRICTED = "RESTRICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"


class RetrainingDisposition(str, Enum):
    NOT_INDICATED = "NOT INDICATED"
    MONITOR = "MONITOR"
    RECALIBRATION_ADVISED = "RECALIBRATION ADVISED"
    RETRAINING_ADVISED = "RETRAINING ADVISED"
    URGENT_MODEL_REVIEW = "URGENT MODEL REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"


class ModuleStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT APPLICABLE"


class ModuleCompleteness(BaseModel):
    name: str
    status: ModuleStatus
    evidence_count: int = 0
    last_verified_at: Optional[str] = None
    prerequisite_missing: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ReportContext(BaseModel):
    report_id: str
    user_id: str
    model_id: str
    model_name: str
    analysis_id: str
    generated_at: str
    reference_dataset_id: str
    reference_dataset_name: Optional[str] = None
    evaluation_dataset_id: str
    evaluation_dataset_name: Optional[str] = None
    task_type: str = "classification"
    filename: Optional[str] = None
    n_features_in: Optional[int] = None
    predict_supported: Optional[bool] = None
    predict_proba_supported: Optional[bool] = None


class WhyThisDecisionEntry(BaseModel):
    factor: str
    impact: str  # "POSITIVE" | "NEUTRAL" | "NEGATIVE" | "CRITICAL"
    description: str
    evidence_link: str


class ActionItem(BaseModel):
    priority: str  # "P1" | "P2" | "P3" | "P4"
    title: str
    rationale: str
    trigger_condition: str
    target_component: str


class RiskDriver(BaseModel):
    category: str
    driver_name: str
    severity_score: float
    impact_description: str


class ReportPayload(BaseModel):
    context: ReportContext
    report_type: str = "integrated"  # "reliability" | "model_trust" | "governance" | "integrated"
    trust_disposition: TrustDisposition
    trust_rationale: str
    completeness: Dict[str, ModuleCompleteness]
    overall_completeness_pct: float
    reliability_summary: Dict[str, Any]
    stress_lab_summary: Dict[str, Any]
    fault_lab_summary: Dict[str, Any]
    failure_explorer_summary: Dict[str, Any]
    temporal_intelligence_summary: Dict[str, Any]
    ecrg_governance_summary: Dict[str, Any]
    why_this_decision: List[WhyThisDecisionEntry]
    action_plan: List[ActionItem]
    retraining_disposition: RetrainingDisposition
    retraining_rationale: str
    deployment_suitability: Dict[str, Any]
    trend_comparison: Dict[str, Any]
    top_risk_drivers: List[RiskDriver]
    scientific_limitations: List[str]
