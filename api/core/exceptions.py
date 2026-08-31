"""
AEGIS-X API Exception Handler Middleware.

Translates framework exceptions into standard, structured JSON error responses.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

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


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI application instance."""

    @app.exception_handler(ModelLoadError)
    async def model_load_error_handler(request: Request, exc: ModelLoadError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="MODEL_LOAD_ERROR",
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(UnsupportedModelError)
    async def unsupported_model_error_handler(request: Request, exc: UnsupportedModelError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="UNSUPPORTED_MODEL",
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(DatasetValidationError)
    async def dataset_validation_error_handler(request: Request, exc: DatasetValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DATASET_VALIDATION_ERROR",
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(FeatureMismatchError)
    async def feature_mismatch_error_handler(request: Request, exc: FeatureMismatchError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="FEATURE_MISMATCH",
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(PredictionInterfaceError)
    async def prediction_interface_error_handler(request: Request, exc: PredictionInterfaceError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="PREDICTION_INTERFACE_ERROR",
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(StorageError)
    async def storage_error_handler(request: Request, exc: StorageError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="STORAGE_ERROR",
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(AnalysisServiceError)
    async def analysis_service_error_handler(request: Request, exc: AnalysisServiceError):
        msg = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="ANALYSIS_ERROR",
                    message=msg,
                )
            ).model_dump(),
        )

    @app.exception_handler(AegisError)
    async def aegis_base_error_handler(request: Request, exc: AegisError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="AEGIS_ERROR",
                    message=str(exc),
                )
            ).model_dump(),
        )
