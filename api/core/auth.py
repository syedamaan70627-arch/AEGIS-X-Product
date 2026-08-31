"""
AEGIS-X API Authentication & Authorization Module.

Integrates Supabase Bearer token verification and resource ownership isolation.
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Header, HTTPException, Request, status
import httpx

from api.core.config import settings


@dataclass
class UserContext:
    """Represents authenticated or local development user identity."""
    user_id: str
    email: Optional[str] = None
    authenticated: bool = False


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserContext:
    """
    FastAPI dependency extracting authenticated user identity.
    In development (AUTH_REQUIRED=false), returns default local identity.
    In production (AUTH_REQUIRED=true), validates Supabase Bearer token.
    """
    if not settings.AUTH_REQUIRED:
        return UserContext(user_id="local_dev_user", email="dev@aegis.local", authenticated=False)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bearer token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token against Supabase Auth API /auth/v1/user
    if not settings.SUPABASE_URL or not (settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed: Supabase backend credentials are not configured.",
        )

    try:
        auth_url = f"{settings.SUPABASE_URL}/auth/v1/user"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {token}",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(auth_url, headers=headers)

        if res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_data = res.json()
        user_id = user_data.get("id")
        email = user_data.get("email")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation did not return a valid user identity.",
            )

        return UserContext(user_id=user_id, email=email, authenticated=True)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_resource_ownership(resource_owner_id: str, current_user: UserContext) -> None:
    """
    Enforces resource authorization ownership.
    Returns HTTP 404 if current_user does not own resource_owner_id to prevent resource existence leaking.
    """
    if settings.AUTH_REQUIRED and resource_owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )
