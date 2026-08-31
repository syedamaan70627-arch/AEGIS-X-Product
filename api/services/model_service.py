"""
AEGIS-X API Model Service.

Manages registration, validation, and metadata retrieval for user-supplied classification models.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import UploadFile

from aegis.core.model_adapter import SklearnModelAdapter
from api.core.dependencies import get_model_repository
from api.db.models import ModelRecord
from api.schemas.models import ModelResponse
from api.services.storage_service import StorageService


class ModelService:
    """Business logic for Model Registry API."""

    @classmethod
    async def register_model(
        cls,
        model_name: str,
        task_type: str,
        file: UploadFile,
        description: Optional[str] = None,
        user_id: str = "local_dev_user",
    ) -> ModelResponse:
        """Register, inspect, and persist a scikit-learn compatible classification model."""
        model_id = str(uuid.uuid4())

        # Save model file safely via StorageService
        file_path, filename = await StorageService.save_uploaded_model(model_id, file, user_id=user_id)

        # Validate and inspect model using SklearnModelAdapter via StorageService
        adapter = StorageService.load_model_adapter(str(file_path), user_id=user_id)
        capabilities = adapter.get_capabilities()

        created_at = datetime.now(timezone.utc).isoformat()

        record = ModelRecord(
            id=model_id,
            user_id=user_id,
            model_name=model_name,
            task_type=task_type,
            description=description,
            file_path=str(file_path),
            filename=filename,
            predict_supported=True,
            predict_proba_supported=capabilities["supports_predict_proba"],
            n_features_in=capabilities["n_features_in"],
            classes=capabilities["classes"],
            feature_names=capabilities["feature_names_in"],
            created_at=created_at,
        )

        repo = get_model_repository()
        repo.create(record)

        return ModelResponse(
            model_id=record.id,
            model_name=record.model_name,
            task_type=record.task_type,
            description=record.description,
            filename=record.filename,
            predict_supported=record.predict_supported,
            predict_proba_supported=record.predict_proba_supported,
            n_features_in=record.n_features_in,
            classes=record.classes,
            feature_names=record.feature_names,
            created_at=record.created_at,
            status="registered",
        )

    @classmethod
    def get_model(cls, model_id: str, user_id: Optional[str] = None) -> Optional[ModelResponse]:
        """Fetch model metadata by ID."""
        repo = get_model_repository()
        record = repo.get_by_id(model_id, owner_id=user_id)
        if not record:
            return None
        return ModelResponse(
            model_id=record.id,
            model_name=record.model_name,
            task_type=record.task_type,
            description=record.description,
            filename=record.filename,
            predict_supported=record.predict_supported,
            predict_proba_supported=record.predict_proba_supported,
            n_features_in=record.n_features_in,
            classes=record.classes,
            feature_names=record.feature_names,
            created_at=record.created_at,
            status="registered",
        )

    @classmethod
    def list_models(cls, user_id: Optional[str] = None) -> List[ModelResponse]:
        """List registered models belonging to the user."""
        repo = get_model_repository()
        records = repo.list_all(owner_id=user_id)
        return [
            ModelResponse(
                model_id=r.id,
                model_name=r.model_name,
                task_type=r.task_type,
                description=r.description,
                filename=r.filename,
                predict_supported=r.predict_supported,
                predict_proba_supported=r.predict_proba_supported,
                n_features_in=r.n_features_in,
                classes=r.classes,
                feature_names=r.feature_names,
                created_at=r.created_at,
                status="registered",
            )
            for r in records
        ]
