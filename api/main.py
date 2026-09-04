"""
AEGIS-X Production REST API Application Entry Point.

Exposes the production-grade AEGIS-X AI reliability engine through a clean, secure, model-agnostic REST API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.core.exceptions import register_exception_handlers
from api.core.middleware import RequestIDMiddleware
from api.db.database import init_db
from api.routes import (
    analysis,
    auth,
    datasets,
    faults,
    health,
    memory,
    models,
    prediction,
    readiness,
    stress,
    warning,
    governance,
)

# Ensure storage directories and database tables exist on module import
settings.ensure_directories()
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to perform startup initialization and cleanup."""
    settings.ensure_directories()
    init_db()
    yield


app = FastAPI(
    title=settings.API_TITLE,
    description=(
        "Model-Agnostic AI Reliability Analysis API.\n\n"
        "Exposes AEGIS-X operational capabilities:\n"
        "- Core Reliability Analysis (OOD, Uncertainty, Drift, Fusion)\n"
        "- Stress Lab (Controlled Noise, Dropout, Permutation)\n"
        "- Fault Injection & Failure Explorer (Sensor Bias, Gain Error, Stuck-At, Channel Swap, Sign Inversion)\n"
        "- Failure Memory (Unsupervised Failure Signature Centroids & Matcher)\n"
        "- Failure Prediction (Onset-Aware Next-Step Prediction)\n"
        "- Early Warning (Multi-Signal Temporal Lead Evaluation)\n"
        "- Evidence-Calibrated Reliability Governance (ECRG Conformal Risk Control & Anti-Flapping)\n\n"
        "SECURITY WARNING: Uploaded model files (.joblib or .pkl) are deserialized using Python pickle. "
        "Model files MUST only be uploaded from trusted sources."
    ),
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# CORS Middleware (configurable allowed origins, explicit credentials handling, and Vercel preview regex)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_origin_regex=settings.CORS_ALLOWED_ORIGIN_REGEX if settings.CORS_ALLOWED_ORIGIN_REGEX else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID Middleware
app.add_middleware(RequestIDMiddleware)

# Register custom exception handlers
register_exception_handlers(app)

# Include API Routers
app.include_router(health.router)
app.include_router(readiness.router)
app.include_router(auth.router)
app.include_router(models.router)
app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(stress.router)
app.include_router(faults.router)
app.include_router(memory.router)
app.include_router(prediction.router)
app.include_router(warning.router)
app.include_router(governance.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
