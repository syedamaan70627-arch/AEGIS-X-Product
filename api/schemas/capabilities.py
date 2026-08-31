"""
AEGIS-X API Model Capabilities Schemas.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class CapabilityStatusDetail(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "READY"})
    reason: Optional[str] = None


class ModelCapabilitiesResponse(BaseModel):
    model_id: str
    capabilities: Dict[str, CapabilityStatusDetail]
