"""
AEGIS-X API Common Schemas.

Defines schemas for health checks, system capability status, and structured error responses.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    service: str = Field(..., json_schema_extra={"example": "AEGIS-X"})
    api_version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    engine_available: bool = Field(..., json_schema_extra={"example": True})


class RootResponse(BaseModel):
    service: str = Field(..., json_schema_extra={"example": "AEGIS-X API"})
    status: str = Field(..., json_schema_extra={"example": "online"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    health: str = Field(..., json_schema_extra={"example": "/health"})
    readiness: str = Field(..., json_schema_extra={"example": "/ready"})
    docs: str = Field(..., json_schema_extra={"example": "/docs"})


class StatusResponse(BaseModel):
    api_status: str = Field(..., json_schema_extra={"example": "operational"})
    api_version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    auth_mode: str = Field(..., json_schema_extra={"example": "disabled"})
    database_backend: str = Field(..., json_schema_extra={"example": "sqlite"})
    storage_backend: str = Field(..., json_schema_extra={"example": "local"})
    supported_model_formats: List[str] = Field(..., json_schema_extra={"example": [".joblib", ".pkl"]})
    supported_dataset_formats: List[str] = Field(..., json_schema_extra={"example": [".csv"]})
    supported_task_types: List[str] = Field(
        ..., json_schema_extra={"example": ["binary_classification", "multiclass_classification"]}
    )
    reliability_capabilities: List[str] = Field(
        ..., json_schema_extra={"example": ["ood_detection", "uncertainty_estimation", "drift_detection", "reliability_fusion"]}
    )


class ErrorDetail(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "FEATURE_MISMATCH"})
    message: str = Field(..., json_schema_extra={"example": "Feature schema mismatch between model and evaluation dataset."})
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
