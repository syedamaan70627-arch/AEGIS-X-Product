"""
AEGIS-X API Fault Injection & Failure Explorer Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FaultTestRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    evaluation_dataset_id: str = Field(..., description="ID of uploaded EVALUATION dataset")
    fault_type: str = Field(
        ...,
        description="Fault family: 'Sensor_Bias', 'Gain_Error', 'Stuck_At', 'Channel_Swap', or 'Sign_Inversion'",
    )
    severity: float = Field(0.2, description="Fault severity in range [0.0, 1.0]")
    affected_features: Optional[List[str]] = Field(None, description="Optional target feature names")
    stuck_value: Optional[float] = Field(None, description="Optional stuck value for Stuck_At fault")
    feature_pair: Optional[List[str]] = Field(None, description="Optional feature pair for Channel_Swap fault")
    random_state: Optional[int] = Field(42, description="Random seed")
    reference_dataset_id: Optional[str] = Field(None, description="Optional reference dataset ID")


class FaultTestResponse(BaseModel):
    fault_test_id: str
    model_id: str
    evaluation_dataset_id: str
    fault_type: str
    severity: float
    affected_features: List[str]
    status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})

    transformation_metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: str


class FailureEventDetail(BaseModel):
    sample_id: Any
    ood_risk: float
    uncertainty_risk: float
    drift_risk: float
    fused_risk: float
    is_high_risk_warning: bool
    fault_type: Optional[str] = None
    severity: Optional[float] = None
    has_actual_failure: Optional[bool] = None
    is_silent_failure: Optional[bool] = None


class FailureExplorerResponse(BaseModel):
    fault_test_id: str
    is_label_aware: bool
    total_samples: int
    total_warnings: int
    total_failures: Optional[int] = None
    silent_failures: Optional[int] = None
    silent_failure_rate: Optional[float] = None
    silent_failure_status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})
    failure_events: List[FailureEventDetail] = Field(default_factory=list)
    summary_by_fault: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class FaultTestListResponse(BaseModel):
    total: int
    fault_tests: List[Dict[str, Any]]
