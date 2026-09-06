"""
AEGIS-X API Model Schemas.

Defines request metadata and response representations for the Model Registry.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    model_id: str
    model_name: str
    task_type: str
    description: Optional[str] = None
    filename: str
    predict_supported: bool
    predict_proba_supported: bool
    n_features_in: Optional[int] = None
    classes: Optional[List[Any]] = None
    feature_names: Optional[List[str]] = None
    created_at: str
    status: str = Field(..., json_schema_extra={"example": "registered"})


class ModelListResponse(BaseModel):
    total: int
    models: List[ModelResponse]


class ModelDependencySummary(BaseModel):
    model_id: str
    model_name: str
    uploaded_datasets: int = 0
    reference_states: int = 0
    reliability_analyses: int = 0
    stress_tests: int = 0
    fault_tests: int = 0
    failure_memory_records: int = 0
    prediction_records: int = 0
    governance_evaluations: int = 0
    report_snapshots: int = 0


class ModelDeleteResponse(BaseModel):
    success: bool
    model_id: str
    message: str
    status: str = "deleted"
    dependency_summary: Optional[ModelDependencySummary] = None

