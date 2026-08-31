"""
AEGIS-X API Fault Injection & Failure Explorer Endpoints.
"""

from fastapi import APIRouter, Depends, status

from api.core.auth import UserContext, get_current_user
from api.schemas.faults import (
    FailureExplorerResponse,
    FaultTestListResponse,
    FaultTestRequest,
    FaultTestResponse,
)
from api.services.fault_service import FaultService

router = APIRouter(tags=["Fault Injection & Failure Explorer"])


@router.post(
    "/api/v1/fault-tests",
    response_model=FaultTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Structured Fault Injection",
)
async def run_fault_test(request: FaultTestRequest, user: UserContext = Depends(get_current_user)):
    """
    Injects a structured fault family (Sensor_Bias, Gain_Error, Stuck_At, Channel_Swap, or Sign_Inversion)
    into a dataset copy and evaluates operational failure discovery without mutating the source dataset.
    """
    return FaultService.run_fault_test(request, user_id=user.user_id)


@router.get(
    "/api/v1/fault-tests/{fault_test_id}",
    summary="Get Fault Test Summary",
)
async def get_fault_test(fault_test_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve fault test execution summary by ID."""
    return FaultService.get_fault_test(fault_test_id, user_id=user.user_id)


@router.get(
    "/api/v1/fault-tests/{fault_test_id}/failures",
    response_model=FailureExplorerResponse,
    summary="Explore Failure & Reliability Events",
)
async def get_failure_explorer_data(fault_test_id: str, user: UserContext = Depends(get_current_user)):
    """
    Failure Explorer endpoint: Exposes observation-level failure events, warnings,
    and silent failure identifications. Silent failure identification requires ground-truth target labels.
    """
    return FaultService.get_failure_explorer_data(fault_test_id, user_id=user.user_id)


@router.get(
    "/api/v1/models/{model_id}/fault-tests",
    response_model=FaultTestListResponse,
    summary="List Model Fault Tests",
)
async def list_model_fault_tests(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve list of fault test execution metadata records for a given model."""
    tests = FaultService.list_fault_tests_for_model(model_id, user_id=user.user_id)
    return FaultTestListResponse(total=len(tests), fault_tests=tests)
