"""
AEGIS-X API Dataset Schemas.

Defines schemas for dataset registration and reference state fitting.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DatasetResponse(BaseModel):
    dataset_id: str
    model_id: str
    dataset_type: str = Field(..., json_schema_extra={"example": "REFERENCE"})
    filename: str
    target_column: Optional[str] = None
    num_samples: int
    num_features: int
    feature_names: List[str]
    has_target: bool
    created_at: str
    status: str = Field(..., json_schema_extra={"example": "registered"})


class DatasetListResponse(BaseModel):
    total: int
    datasets: List[DatasetResponse]


class ReferenceFitResponse(BaseModel):
    model_id: str
    dataset_id: str
    status: str = Field(..., json_schema_extra={"example": "fitted"})
    num_samples: int
    feature_names: List[str]
    fitted_at: str
