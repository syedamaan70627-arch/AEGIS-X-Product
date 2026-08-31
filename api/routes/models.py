"""
AEGIS-X API Model Registry Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.core.auth import UserContext, get_current_user
from api.schemas.capabilities import ModelCapabilitiesResponse
from api.schemas.datasets import ReferenceFitResponse
from api.schemas.models import ModelListResponse, ModelResponse
from api.services.analysis_service import AnalysisService
from api.services.capability_service import CapabilityService
from api.services.model_service import ModelService

router = APIRouter(prefix="/api/v1/models", tags=["Model Registry"])


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED, summary="Register Model File")
async def register_model(
    model_name: str = Form(..., description="Name of the model"),
    task_type: str = Form("binary_classification", description="Task type: binary_classification or multiclass_classification"),
    description: Optional[str] = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="Model file (.joblib or .pkl)"),
    user: UserContext = Depends(get_current_user),
):
    """
    Register an existing sklearn-compatible classification model file (.joblib or .pkl).
    
    SECURITY WARNING: Deserializing pickle/joblib files can execute arbitrary code. Uploaded files MUST be from trusted sources.
    """
    return await ModelService.register_model(
        model_name=model_name,
        task_type=task_type,
        file=file,
        description=description,
        user_id=user.user_id,
    )


@router.get("", response_model=ModelListResponse, summary="List Registered Models")
async def list_models(user: UserContext = Depends(get_current_user)):
    """List all registered models belonging to the authenticated user."""
    models = ModelService.list_models(user_id=user.user_id)
    return ModelListResponse(total=len(models), models=models)


@router.get("/{model_id}", response_model=ModelResponse, summary="Get Model Details")
async def get_model(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve model metadata by ID."""
    model = ModelService.get_model(model_id, user_id=user.user_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model '{model_id}' not found.")
    return model


@router.get("/{model_id}/capabilities", response_model=ModelCapabilitiesResponse, summary="Get Model Reliability Capabilities")
async def get_model_capabilities(model_id: str, user: UserContext = Depends(get_current_user)):
    """
    Returns operational readiness capabilities for a model across core analysis, stress testing,
    fault testing, failure memory, failure prediction, and early warning modules.
    """
    return CapabilityService.get_model_capabilities(model_id, user_id=user.user_id)


@router.post(
    "/{model_id}/reference/{dataset_id}/fit",
    response_model=ReferenceFitResponse,
    summary="Fit Model Reference State",
)
async def fit_reference_state(model_id: str, dataset_id: str, user: UserContext = Depends(get_current_user)):
    """
    Fits the AEGIS-X baseline reference state (OOD, Drift, and Calibration) for a model
    using a registered REFERENCE dataset.
    """
    return AnalysisService.fit_reference_state(model_id=model_id, dataset_id=dataset_id, user_id=user.user_id)
