"""
AEGIS-X API Governance Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.core.auth import UserContext, get_current_user
from api.schemas.governance import (
    GovernanceEvaluationRequest,
    GovernanceEvaluationResponse,
    GovernanceHistoryResponse,
    GovernanceStatusResponse,
)
from api.services.governance_service import GovernanceService

router = APIRouter(prefix="/api/v1/governance", tags=["Evidence Governance"])


@router.post(
    "/evaluate",
    response_model=GovernanceEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Reliability Governance",
)
async def evaluate_governance(
    request: GovernanceEvaluationRequest,
    user: UserContext = Depends(get_current_user),
):
    """
    Evaluate evidence-calibrated reliability governance for a model.
    Enforces RLS model ownership and state machine anti-flapping transitions.
    """
    try:
        return GovernanceService.evaluate_governance(request, user_id=user.user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.get(
    "/{model_id}/status",
    response_model=GovernanceStatusResponse,
    summary="Get Governance Status",
)
async def get_governance_status(
    model_id: str,
    user: UserContext = Depends(get_current_user),
):
    """Retrieve current governance state, active action, and state transition counts for a model."""
    try:
        return GovernanceService.get_status(model_id, user_id=user.user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.get(
    "/{model_id}/history",
    response_model=GovernanceHistoryResponse,
    summary="Get Governance History",
)
async def get_governance_history(
    model_id: str,
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    user: UserContext = Depends(get_current_user),
):
    """Retrieve paginated governance evaluation audit history for a model."""
    try:
        return GovernanceService.get_history(model_id, user_id=user.user_id, limit=limit, offset=offset)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))
