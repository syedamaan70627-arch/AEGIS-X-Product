"""
AEGIS-X API Dataset Service.

Manages CSV dataset uploads, schema validation, model compatibility checking, and metadata registration.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import UploadFile

from aegis.core.data_loader import CSVDataLoader
from aegis.core.exceptions import DatasetValidationError, FeatureMismatchError
from api.core.dependencies import get_dataset_repository, get_model_repository
from api.db.models import DatasetRecord
from api.schemas.datasets import DatasetResponse
from api.services.storage_service import StorageService


class DatasetService:
    """Business logic for Dataset Registry API."""

    @classmethod
    async def register_dataset(
        cls,
        model_id: str,
        dataset_type: str,
        file: UploadFile,
        target_column: Optional[str] = None,
        user_id: str = "local_dev_user",
    ) -> DatasetResponse:
        """Upload, validate CSV, check model feature compatibility, and persist dataset record."""
        upper_type = dataset_type.upper().strip()
        if upper_type not in {"REFERENCE", "EVALUATION"}:
            raise DatasetValidationError(
                f"Invalid dataset_type '{dataset_type}'. Must be 'REFERENCE' or 'EVALUATION'."
            )

        # Verify model exists and belongs to user
        model_repo = get_model_repository()
        model_rec = model_repo.get_by_id(model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise DatasetValidationError(f"Model ID '{model_id}' not found.")

        dataset_id = str(uuid.uuid4())

        # Save dataset file safely
        file_path, filename = await StorageService.save_uploaded_dataset(dataset_id, file, user_id=user_id)

        # Validate CSV using StorageService
        loaded_ds = StorageService.load_dataset(str(file_path), target_column=target_column, user_id=user_id)

        # Verify feature count compatibility with model if n_features_in is known
        if model_rec.n_features_in is not None and model_rec.n_features_in != loaded_ds.num_features:
            raise FeatureMismatchError(
                f"Dataset feature count ({loaded_ds.num_features}) does not match model expected features ({model_rec.n_features_in})."
            )

        # Verify feature names compatibility with model if feature_names_in is known
        if model_rec.feature_names:
            model_feat_set = set(model_rec.feature_names)
            ds_feat_set = set(loaded_ds.feature_names)
            missing = model_feat_set - ds_feat_set
            if missing:
                raise FeatureMismatchError(
                    f"Dataset is missing required model features: {sorted(list(missing))}."
                )

        created_at = datetime.now(timezone.utc).isoformat()

        record = DatasetRecord(
            id=dataset_id,
            user_id=user_id,
            model_id=model_id,
            dataset_type=upper_type,
            file_path=str(file_path),
            filename=filename,
            target_column=target_column,
            num_samples=loaded_ds.num_samples,
            num_features=loaded_ds.num_features,
            feature_names=loaded_ds.feature_names,
            has_target=loaded_ds.y is not None,
            created_at=created_at,
        )

        dataset_repo = get_dataset_repository()
        dataset_repo.create(record)

        return DatasetResponse(
            dataset_id=record.id,
            model_id=record.model_id,
            dataset_type=record.dataset_type,
            filename=record.filename,
            target_column=record.target_column,
            num_samples=record.num_samples,
            num_features=record.num_features,
            feature_names=record.feature_names,
            has_target=record.has_target,
            created_at=record.created_at,
            status="registered",
        )

    @classmethod
    def get_dataset(cls, dataset_id: str, user_id: Optional[str] = None) -> Optional[DatasetResponse]:
        """Fetch dataset metadata by ID."""
        repo = get_dataset_repository()
        record = repo.get_by_id(dataset_id, owner_id=user_id)
        if not record:
            return None
        return DatasetResponse(
            dataset_id=record.id,
            model_id=record.model_id,
            dataset_type=record.dataset_type,
            filename=record.filename,
            target_column=record.target_column,
            num_samples=record.num_samples,
            num_features=record.num_features,
            feature_names=record.feature_names,
            has_target=record.has_target,
            created_at=record.created_at,
            status="registered",
        )

    @classmethod
    def list_datasets(cls, model_id: Optional[str] = None, user_id: Optional[str] = None) -> List[DatasetResponse]:
        """List datasets, optionally filtering by model ID and user ID."""
        repo = get_dataset_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            DatasetResponse(
                dataset_id=r.id,
                model_id=r.model_id,
                dataset_type=r.dataset_type,
                filename=r.filename,
                target_column=r.target_column,
                num_samples=r.num_samples,
                num_features=r.num_features,
                feature_names=r.feature_names,
                has_target=r.has_target,
                created_at=r.created_at,
                status="registered",
            )
            for r in records
        ]

    @classmethod
    def delete_dataset(cls, dataset_id: str, user_id: str = "local_dev_user") -> bool:
        """Delete dataset metadata record and remove file from storage."""
        repo = get_dataset_repository()
        owner = user_id if user_id != "local_dev_user" else None
        record = repo.get_by_id(dataset_id, owner_id=owner)
        if not record:
            raise DatasetValidationError(f"Dataset '{dataset_id}' not found.")

        try:
            from api.core.dependencies import get_storage_provider
            provider = get_storage_provider()
            provider.delete_file(record.file_path, user_id=user_id)
        except Exception:
            pass

        return repo.delete(dataset_id, owner_id=owner)

