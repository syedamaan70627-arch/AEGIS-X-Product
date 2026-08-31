"""
AEGIS-X API User Identity Endpoint.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.core.auth import UserContext, get_current_user

router = APIRouter(prefix="/api/v1", tags=["Authentication"])


class UserMeResponse(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"})
    email: str = Field(..., json_schema_extra={"example": "user@example.com"})
    authenticated: bool = Field(..., json_schema_extra={"example": True})


@router.get("/me", response_model=UserMeResponse, summary="Get Authenticated Identity Summary")
async def get_user_me(user: UserContext = Depends(get_current_user)):
    """
    Returns summary of current user identity.
    In local development (AUTH_REQUIRED=false), returns development identity.
    In production (AUTH_REQUIRED=true), returns authenticated Supabase user identity.
    """
    return UserMeResponse(
        user_id=user.user_id,
        email=user.email or "dev@aegis.local",
        authenticated=user.authenticated,
    )
