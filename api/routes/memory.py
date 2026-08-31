"""
AEGIS-X API Failure Memory Endpoints.
"""

from fastapi import APIRouter, Depends, status

from api.core.auth import UserContext, get_current_user
from api.schemas.memory import (
    MemoryBuildRequest,
    MemoryBuildResponse,
    MemoryListResponse,
    MemoryMatchRequest,
    MemoryMatchResponse,
)
from api.services.memory_service import MemoryService

router = APIRouter(tags=["Failure Memory"])


@router.post(
    "/api/v1/failure-memory/{model_id}/build",
    response_model=MemoryBuildResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Build Failure Signature Memory",
)
async def build_failure_memory(model_id: str, request: MemoryBuildRequest, user: UserContext = Depends(get_current_user)):
    """
    Fits unsupervised Failure Memory signature centroids from aggregated numerical condition profiles.
    Does NOT use fault family labels during clustering.
    """
    return MemoryService.build_failure_memory(model_id=model_id, request=request, user_id=user.user_id)


@router.get(
    "/api/v1/failure-memory/{memory_id}",
    summary="Get Failure Memory Details",
)
async def get_failure_memory(memory_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve signature centroids and cluster quality metrics for a fitted Failure Memory."""
    return MemoryService.get_memory_details(memory_id, user_id=user.user_id)


@router.post(
    "/api/v1/failure-memory/{memory_id}/match",
    response_model=MemoryMatchResponse,
    summary="Match Query Condition Profile",
)
async def match_query_profile(memory_id: str, request: MemoryMatchRequest, user: UserContext = Depends(get_current_user)):
    """
    Matches a new incoming condition profile against pre-fitted Failure Memory centroids.
    Never refits memory state or mutates centroids during query.
    """
    return MemoryService.match_query_profile(memory_id=memory_id, request=request, user_id=user.user_id)


@router.get(
    "/api/v1/models/{model_id}/failure-memory",
    response_model=MemoryListResponse,
    summary="List Model Failure Memories",
)
async def list_model_failure_memories(model_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve list of failure memory records for a given model."""
    memories = MemoryService.list_memories_for_model(model_id, user_id=user.user_id)
    return MemoryListResponse(total=len(memories), memories=memories)
