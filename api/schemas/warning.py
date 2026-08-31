"""
AEGIS-X API Early Warning Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WarningRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    evaluation_dataset_id: str = Field(..., description="ID of uploaded EVALUATION dataset")


class WarningResponse(BaseModel):
    warning_id: str
    model_id: str
    status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})
    reason: Optional[str] = None
    warning_score: Optional[float] = None
    is_warning_triggered: Optional[bool] = None
    threshold: Optional[float] = None
    horizon_value: int = 3
    horizon_unit: str = Field("controlled_degradation_states", json_schema_extra={"example": "controlled_degradation_states"})
    signals: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: str


class WarningEvaluationRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    evaluation_dataset_id: str = Field(..., description="ID of uploaded EVALUATION dataset with trajectory history")


class WarningEvaluationResponse(BaseModel):
    warning_id: str
    model_id: str
    status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})
    horizon_value: int = 3
    horizon_unit: str = "controlled_degradation_states"
    warning_threshold: float
    state_level_metrics: Dict[str, Any] = Field(default_factory=dict)
    trajectory_level_metrics: Dict[str, Any] = Field(default_factory=dict)
    trajectory_results: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: str


class WarningListResponse(BaseModel):
    total: int
    warnings: List[Dict[str, Any]]
