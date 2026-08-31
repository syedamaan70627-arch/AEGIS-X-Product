"""
AEGIS-X API Failure Memory Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryBuildRequest(BaseModel):
    model_id: str = Field(..., description="ID of registered model")
    fault_test_ids: Optional[List[str]] = Field(None, description="Optional list of fault test IDs to include")
    stress_test_ids: Optional[List[str]] = Field(None, description="Optional list of stress test IDs to include")
    n_clusters: int = Field(3, description="Number of failure signature centroids to fit")
    random_state: Optional[int] = Field(42, description="Random seed")


class SignatureDetail(BaseModel):
    signature_id: int
    centroid_profile: Dict[str, float]
    feature_names: List[str]
    sample_count: int
    distance_threshold: float
    confidence: float


class MemoryBuildResponse(BaseModel):
    memory_id: str
    model_id: str
    status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})
    n_signatures: int
    signatures: List[SignatureDetail] = Field(default_factory=list)
    silhouette_score: Optional[float] = None
    stability_ari: Optional[float] = None
    quality_summary: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    fitted_at: str


class MemoryMatchRequest(BaseModel):
    query_profile: Dict[str, float] = Field(
        ...,
        description="Query condition profile mapping feature names (e.g. mean_ood_risk, mean_uncertainty) to float values",
    )


class MemoryMatchResponse(BaseModel):
    matched_signature_id: int
    signature_distance: float
    distance_threshold: float
    is_known_pattern: bool
    centroid_profile: Dict[str, float] = Field(default_factory=dict)
    associated_fault_distribution: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class MemoryListResponse(BaseModel):
    total: int
    memories: List[Dict[str, Any]]
