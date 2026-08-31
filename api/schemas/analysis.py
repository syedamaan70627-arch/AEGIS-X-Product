"""
AEGIS-X API Analysis Schemas.

Defines request and response contracts for core reliability analysis,
preserving individual OOD, Uncertainty, Drift, and Fusion signals.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    evaluation_dataset_id: str = Field(..., description="ID of uploaded EVALUATION dataset")
    reference_dataset_id: Optional[str] = Field(
        None, description="Optional ID of REFERENCE dataset (defaults to active reference state)"
    )
    fusion_method: str = Field(
        "stress_robust", description="Fusion method to apply: 'stress_robust' or 'original'"
    )


class SignalDetail(BaseModel):
    status: str
    aggregate_score: Optional[float] = None
    scores: Optional[List[float]] = None
    details: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)


class FusionDetail(BaseModel):
    status: str
    method: str
    aggregate_fused_risk: Optional[float] = None
    fused_risk_scores: Optional[List[float]] = None
    threshold: float = 0.5
    model_metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class DiagnosticDetail(BaseModel):
    accuracy: Optional[float] = None
    error_rate: Optional[float] = None
    num_failures: Optional[int] = None
    correlation_fused_risk_vs_error: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    model_id: str
    reference_dataset_id: str
    evaluation_dataset_id: str
    created_at: str
    status: str = Field(..., json_schema_extra={"example": "completed"})

    model_capability_summary: Dict[str, Any]

    ood: SignalDetail
    uncertainty: SignalDetail
    drift: SignalDetail
    fusion: FusionDetail

    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    diagnostics: Optional[DiagnosticDetail] = None


class AnalysisListResponse(BaseModel):
    total: int
    analyses: List[Dict[str, Any]]
