"""
AEGIS-X API Analysis Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.core.auth import UserContext, get_current_user
from api.schemas.analysis import AnalysisListResponse, AnalysisRequest, AnalysisResponse
from api.services.analysis_service import AnalysisService

router = APIRouter(tags=["Analysis Engine"])


@router.post(
    "/api/v1/analysis",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Core AEGIS-X Analysis",
)
async def run_analysis(request: AnalysisRequest, user: UserContext = Depends(get_current_user)):
    """
    Executes operational AEGIS-X reliability analysis (OOD, Uncertainty, Drift, and Fusion)
    on an EVALUATION dataset using the model's fitted REFERENCE state.
    
    Operates label-free when target labels are absent, and includes retrospective diagnostics
    when true target labels are present. Preserves individual OOD, Uncertainty, Drift, and Fusion signals.
    """
    return AnalysisService.run_analysis(request, user_id=user.user_id)


@router.get(
    "/api/v1/analysis/{analysis_id}",
    summary="Get Stored Analysis Result Payload",
)
async def get_analysis(analysis_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve full saved analysis result payload by ID."""
    return AnalysisService.get_analysis(analysis_id, user_id=user.user_id)


@router.get(
    "/api/v1/models/{model_id}/analyses",
    response_model=AnalysisListResponse,
    summary="List Model Analyses",
)
async def list_model_analyses(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve list of analysis execution metadata records for a given model."""
    analyses = AnalysisService.list_analyses_for_model(model_id, user_id=user.user_id)
    return AnalysisListResponse(total=len(analyses), analyses=analyses)
