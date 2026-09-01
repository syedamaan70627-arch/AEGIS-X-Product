"""
AEGIS-X API Failure Prediction Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    evaluation_dataset_id: str = Field(..., description="ID of uploaded EVALUATION dataset")


class PredictionEventDetail(BaseModel):
    sample_id: Any
    predicted_failure_prob: float
    is_failure_warning: bool
    threshold: float
    actual_failure_onset: Optional[bool] = None


class PredictionResponse(BaseModel):
    prediction_id: str
    model_id: str
    status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})
    reason: Optional[str] = None
    horizon_steps: int = 1
    horizon_unit: str = Field("controlled_degradation_states", json_schema_extra={"example": "controlled_degradation_states"})
    selected_predictor: Optional[str] = None
    threshold: Optional[float] = None
    aggregate_onset_warning_rate: Optional[float] = None
    mean_predicted_probability: Optional[float] = None
    predictions: Optional[List[PredictionEventDetail]] = None
    heldout_metrics: Optional[Dict[str, float]] = None
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: str


class PredictionListResponse(BaseModel):
    total: int
    predictions: List[Dict[str, Any]]


class PredictionFitRequest(BaseModel):
    trajectory_dataset_id: Optional[str] = Field(None, description="Optional ID of uploaded TEMPORAL_TRAJECTORY dataset")
    feature_set_type: str = Field("dynamic", description="Feature set type: dynamic or static")
    model_type: str = Field("random_forest", description="Predictor model type: random_forest or gradient_boosting")
    random_state: Optional[int] = Field(42, description="Random seed")


class PredictionFitResponse(BaseModel):
    model_id: str
    status: str = "fitted"
    selected_predictor: str
    horizon_steps: int = 1
    horizon_unit: str = "controlled_degradation_states"
    threshold: Optional[float] = None
    heldout_metrics: Optional[Dict[str, float]] = None
    fitted_at: str
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

