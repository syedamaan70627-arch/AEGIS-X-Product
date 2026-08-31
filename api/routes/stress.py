"""
AEGIS-X API Stress Lab Endpoints.
"""

from fastapi import APIRouter, Depends, status

from api.core.auth import UserContext, get_current_user
from api.schemas.stress import StressTestListResponse, StressTestRequest, StressTestResponse
from api.services.stress_service import StressService

router = APIRouter(tags=["Stress Lab"])


@router.post(
    "/api/v1/stress-tests",
    response_model=StressTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Controlled Stress Test",
)
async def run_stress_test(request: StressTestRequest, user: UserContext = Depends(get_current_user)):
    """
    Executes controlled stress testing (Gaussian Noise, Feature Dropout, Feature Permutation, or Combined Stress)
    on a copy of evaluation data without mutating the source dataset.
    """
    return StressService.run_stress_test(request, user_id=user.user_id)


@router.get(
    "/api/v1/stress-tests/{stress_test_id}",
    summary="Get Stored Stress Test Result",
)
async def get_stress_test(stress_test_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve full saved stress test result payload by ID."""
    return StressService.get_stress_test(stress_test_id, user_id=user.user_id)


@router.get(
    "/api/v1/models/{model_id}/stress-tests",
    response_model=StressTestListResponse,
    summary="List Model Stress Tests",
)
async def list_model_stress_tests(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve list of stress test execution metadata records for a given model."""
    tests = StressService.list_stress_tests_for_model(model_id, user_id=user.user_id)
    return StressTestListResponse(total=len(tests), stress_tests=tests)
