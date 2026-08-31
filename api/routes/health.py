"""
AEGIS-X API Health & System Status Endpoints.
"""

from fastapi import APIRouter
from api.core.config import settings
from api.schemas.common import HealthResponse, StatusResponse

router = APIRouter(tags=["Health & Status"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def health_check():
    """Unversioned health endpoint indicating API availability."""
    return HealthResponse(
        status="ok",
        service="AEGIS-X",
        api_version=settings.API_VERSION,
        engine_available=True,
    )


@router.get("/api/v1/status", response_model=StatusResponse, summary="System Capabilities Status")
async def system_status():
    """Returns AEGIS-X engine capabilities and configured backends without exposing secrets or absolute paths."""
    return StatusResponse(
        api_status="operational",
        api_version=settings.API_VERSION,
        auth_mode="required" if settings.AUTH_REQUIRED else "disabled",
        database_backend=settings.DATABASE_BACKEND,
        storage_backend=settings.STORAGE_BACKEND,
        supported_model_formats=sorted(list(settings.ALLOWED_MODEL_EXTENSIONS)),
        supported_dataset_formats=sorted(list(settings.ALLOWED_DATASET_EXTENSIONS)),
        supported_task_types=["binary_classification", "multiclass_classification"],
        reliability_capabilities=[
            "ood_detection",
            "uncertainty_estimation",
            "drift_detection",
            "reliability_fusion",
            "stress_lab",
            "fault_injection",
            "failure_memory",
            "failure_prediction",
            "early_warning",
        ],
    )
