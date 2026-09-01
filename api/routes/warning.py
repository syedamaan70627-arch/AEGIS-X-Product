"""
AEGIS-X API Early Warning Endpoints.
"""

from fastapi import APIRouter, Depends, status

from api.core.auth import UserContext, get_current_user
from api.schemas.warning import (
    WarningEvaluationRequest,
    WarningEvaluationResponse,
    WarningFitRequest,
    WarningFitResponse,
    WarningListResponse,
    WarningRequest,
    WarningResponse,
)
from api.services.warning_service import WarningService

router = APIRouter(tags=["Early Warning Engine"])


@router.post(
    "/api/v1/early-warning/{model_id}/fit",
    response_model=WarningFitResponse,
    status_code=status.HTTP_200_OK,
    summary="Fit Early Warning Engine",
)
async def fit_early_warning(
    model_id: str,
    request: WarningFitRequest = WarningFitRequest(),
    user: UserContext = Depends(get_current_user),
):
    """
    Fits EarlyWarningEngine on a temporal degradation trajectory split and saves artifact to persistent storage.
    """
    return WarningService.fit_warning_engine(model_id, request, user_id=user.user_id)



@router.post(
    "/api/v1/warnings",
    response_model=WarningResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Early Warning Status",
)
async def query_warning(request: WarningRequest, user: UserContext = Depends(get_current_user)):
    """
    Executes dynamic multi-signal temporal warning query when pre-fitted warning artifacts exist.
    If no pre-fitted warning artifact is available, returns status = NOT_AVAILABLE.
    Horizon unit is strictly measured in controlled_degradation_states.
    """
    return WarningService.query_warning(request, user_id=user.user_id)


@router.post(
    "/api/v1/warnings/evaluate",
    response_model=WarningEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Trajectory Lead Times",
)
async def evaluate_warning_trajectories(request: WarningEvaluationRequest, user: UserContext = Depends(get_current_user)):
    """
    Evaluates full held-out trajectory lead times, early warning rates, and false warning caps
    using a pre-fitted Early Warning engine.
    """
    return WarningService.evaluate_trajectories(request, user_id=user.user_id)


@router.get(
    "/api/v1/warnings/{warning_id}",
    summary="Get Stored Warning Result",
)
async def get_warning(warning_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve full saved warning result payload by ID."""
    return WarningService.get_warning(warning_id, user_id=user.user_id)


@router.get(
    "/api/v1/models/{model_id}/warnings",
    response_model=WarningListResponse,
    summary="List Model Warnings",
)
async def list_model_warnings(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve list of warning execution records for a model."""
    warnings_list = WarningService.list_warnings_for_model(model_id, user_id=user.user_id)
    return WarningListResponse(total=len(warnings_list), warnings=warnings_list)
