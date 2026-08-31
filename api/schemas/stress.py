"""
AEGIS-X API Stress Lab Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StressTestRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    evaluation_dataset_id: str = Field(..., description="ID of uploaded EVALUATION dataset")
    stress_type: str = Field(
        "Gaussian_Noise",
        description="Stress type: 'Gaussian_Noise', 'Feature_Dropout', 'Feature_Permutation', or 'Combined_Stress'",
    )
    severity: float = Field(0.2, description="Stress severity in range [0.0, 1.0]")
    random_state: Optional[int] = Field(42, description="Random seed")
    reference_dataset_id: Optional[str] = Field(None, description="Optional reference dataset ID")


class StressTestResponse(BaseModel):
    stress_test_id: str
    model_id: str
    evaluation_dataset_id: str
    stress_type: str
    severity: float
    random_state: int
    status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})

    original_risk: float
    stressed_risk: float
    risk_delta: float

    accuracy_delta: Optional[float] = None
    original_accuracy: Optional[float] = None
    stressed_accuracy: Optional[float] = None

    details: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: str


class StressTestListResponse(BaseModel):
    total: int
    stress_tests: List[Dict[str, Any]]
