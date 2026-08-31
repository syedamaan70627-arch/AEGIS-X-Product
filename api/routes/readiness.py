"""
AEGIS-X API Readiness Probe Endpoint.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

from api.core.config import settings
from api.db.database import get_db_session

router = APIRouter(tags=["Health & Readiness"])


class ReadinessResponse(BaseModel):
    status: str
    database: str
    storage: str
    auth: str


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def get_readiness():
    """
    Readiness probe verifying API initialization, database connection, and storage availability.
    """
    db_status = "HEALTHY"
    if settings.DATABASE_BACKEND == "sqlite":
        try:
            with get_db_session() as conn:
                conn.execute("SELECT 1;")
        except Exception as exc:
            db_status = f"UNHEALTHY: {str(exc)}"
    elif settings.DATABASE_BACKEND == "supabase":
        if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
            db_status = "UNCONFIGURED: Missing SUPABASE_URL or keys."

    storage_status = "HEALTHY"
    if settings.STORAGE_BACKEND == "supabase":
        if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
            storage_status = "UNCONFIGURED: Missing SUPABASE_URL or keys."

    auth_status = "REQUIRED" if settings.AUTH_REQUIRED else "DISABLED"

    overall = "OK" if "UNHEALTHY" not in db_status and "UNCONFIGURED" not in db_status else "DEGRADED"

    return ReadinessResponse(
        status=overall,
        database=db_status,
        storage=storage_status,
        auth=auth_status,
    )
