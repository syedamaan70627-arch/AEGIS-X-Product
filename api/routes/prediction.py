"""
AEGIS-X API Failure Prediction Endpoints.
"""

from fastapi import APIRouter, Depends, status

from api.core.auth import UserContext, get_current_user
from api.schemas.prediction import (
    PredictionListResponse,
    PredictionRequest,
    PredictionResponse,
)
from api.services.prediction_service import PredictionService

router = APIRouter(tags=["Failure Prediction"])


@router.post(
    "/api/v1/predictions/failure",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Failure Prediction",
)
async def run_failure_prediction(request: PredictionRequest, user: UserContext = Depends(get_current_user)):
    """
    Executes next-step onset-aware failure prediction when pre-fitted predictor artifacts exist.
    If no pre-fitted predictor artifact is available for the model deployment, returns status = NOT_AVAILABLE.
    """
    return PredictionService.run_prediction(request, user_id=user.user_id)


@router.get(
    "/api/v1/predictions/{prediction_id}",
    summary="Get Stored Prediction Result",
)
async def get_prediction(prediction_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve full saved prediction result payload by ID."""
    return PredictionService.get_prediction(prediction_id, user_id=user.user_id)


@router.get(
    "/api/v1/models/{model_id}/predictions",
    response_model=PredictionListResponse,
    summary="List Model Predictions",
)
async def list_model_predictions(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve list of prediction execution records for a model."""
    preds = PredictionService.list_predictions_for_model(model_id, user_id=user.user_id)
    return PredictionListResponse(total=len(preds), predictions=preds)
