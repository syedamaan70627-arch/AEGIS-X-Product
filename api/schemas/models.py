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
