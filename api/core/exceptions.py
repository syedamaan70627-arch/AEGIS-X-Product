"""
AEGIS-X API Exception Handler Middleware.

Translates framework exceptions into standard, structured JSON error responses.
Guarantees CORS headers exist on all error responses even during unexpected failures.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import httpx

from aegis.core.exceptions import (
    AegisError,
    DatasetValidationError,
    FeatureMismatchError,
    ModelLoadError,
    PredictionInterfaceError,
    UnsupportedModelError,
)
from api.schemas.common import ErrorDetail, ErrorResponse
from api.services.analysis_service import AnalysisServiceError
from api.services.storage_service import StorageError

logger = logging.getLogger("aegis.exceptions")


def _build_error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    headers = {}
    origin = request.headers.get("origin")
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=code,
                message=message,
            )
        ).model_dump(),
        headers=headers if headers else None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI application instance."""

    @app.exception_handler(ModelLoadError)
    async def model_load_error_handler(request: Request, exc: ModelLoadError):
        logger.warning(f"ModelLoadError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_400_BAD_REQUEST, "MODEL_LOAD_ERROR", str(exc))

    @app.exception_handler(UnsupportedModelError)
    async def unsupported_model_error_handler(request: Request, exc: UnsupportedModelError):
        logger.warning(f"UnsupportedModelError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, "UNSUPPORTED_MODEL", str(exc))

    @app.exception_handler(DatasetValidationError)
    async def dataset_validation_error_handler(request: Request, exc: DatasetValidationError):
        logger.warning(f"DatasetValidationError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_400_BAD_REQUEST, "DATASET_VALIDATION_ERROR", str(exc))

    @app.exception_handler(FeatureMismatchError)
    async def feature_mismatch_error_handler(request: Request, exc: FeatureMismatchError):
        logger.warning(f"FeatureMismatchError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_400_BAD_REQUEST, "FEATURE_MISMATCH", str(exc))

    @app.exception_handler(PredictionInterfaceError)
    async def prediction_interface_error_handler(request: Request, exc: PredictionInterfaceError):
        logger.warning(f"PredictionInterfaceError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_400_BAD_REQUEST, "PREDICTION_INTERFACE_ERROR", str(exc))

    @app.exception_handler(StorageError)
    async def storage_error_handler(request: Request, exc: StorageError):
        logger.warning(f"StorageError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_400_BAD_REQUEST, "STORAGE_ERROR", str(exc))

    @app.exception_handler(AnalysisServiceError)
    async def analysis_service_error_handler(request: Request, exc: AnalysisServiceError):
        logger.warning(f"AnalysisServiceError on {request.url.path}: {exc}")
        msg = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
        return _build_error_response(request, status_code, "ANALYSIS_ERROR", msg)

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_error_handler(request: Request, exc: FileNotFoundError):
        logger.warning(f"FileNotFoundError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_404_NOT_FOUND, "FILE_NOT_FOUND", str(exc))

    @app.exception_handler(httpx.HTTPError)
    async def httpx_error_handler(request: Request, exc: httpx.HTTPError):
        logger.error(f"Upstream HTTP error on {request.url.path}: {exc}", exc_info=True)
        return _build_error_response(
            request,
            status.HTTP_502_BAD_GATEWAY,
            "UPSTREAM_SERVICE_ERROR",
            f"Storage or database service communication failure. {str(exc)}",
        )

    @app.exception_handler(AegisError)
    async def aegis_base_error_handler(request: Request, exc: AegisError):
        logger.warning(f"AegisError on {request.url.path}: {exc}")
        return _build_error_response(request, status.HTTP_400_BAD_REQUEST, "AEGIS_ERROR", str(exc))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        return _build_error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_SERVER_ERROR",
            f"An internal error occurred: {str(exc)}",
        )
