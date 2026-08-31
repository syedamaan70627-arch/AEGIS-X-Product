"""
AEGIS-X API Storage Service.

Handles safe filesystem/cloud storage operations, filename sanitization, path traversal defense,
file size limit enforcement, and user-scoped storage abstraction via IStorageProvider.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from fastapi import UploadFile

from aegis.core.exceptions import AegisError
from api.core.config import settings
from api.core.dependencies import get_storage_provider


class StorageError(AegisError):
    """Raised when filesystem or upload validation fails."""
    pass


class StorageService:
    """Safe storage manager for uploaded models, datasets, reference state artifacts, and analysis results."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        if not filename:
            raise StorageError("Filename cannot be empty.")
        clean_name = Path(filename).name
        # Prevent hidden files or path traversal constructs
        if clean_name.startswith(".") or ".." in clean_name or "/" in clean_name or "\\" in clean_name:
            raise StorageError(f"Invalid or unsafe filename: '{filename}'.")
        return clean_name

    @classmethod
    async def save_uploaded_model(
        cls, model_id: str, upload_file: UploadFile, user_id: str = "local_dev_user"
    ) -> Tuple[Path, str]:
        """Validate extension, sanitize filename, enforce size limit, and store model file via StorageProvider."""
        orig_filename = upload_file.filename or "model.joblib"
        clean_filename = cls.sanitize_filename(orig_filename)

        ext = Path(clean_filename).suffix.lower()
        if ext not in settings.ALLOWED_MODEL_EXTENSIONS:
            raise StorageError(
                f"Unsupported model file extension '{ext}'. Allowed extensions: {sorted(list(settings.ALLOWED_MODEL_EXTENSIONS))}"
            )

        content = await upload_file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise StorageError(
                f"File size ({len(content)} bytes) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes."
            )

        provider = get_storage_provider()
        relative_key = f"models/{model_id}/{clean_filename}"
        saved_path_str = provider.save_file(relative_key, content, user_id=user_id)

        return Path(saved_path_str), clean_filename

    @classmethod
    async def save_uploaded_dataset(
        cls, dataset_id: str, upload_file: UploadFile, user_id: str = "local_dev_user"
    ) -> Tuple[Path, str]:
        """Validate CSV extension, sanitize filename, enforce size limit, and store dataset file via StorageProvider."""
        orig_filename = upload_file.filename or "dataset.csv"
        clean_filename = cls.sanitize_filename(orig_filename)

        ext = Path(clean_filename).suffix.lower()
        if ext not in settings.ALLOWED_DATASET_EXTENSIONS:
            raise StorageError(
                f"Unsupported dataset file extension '{ext}'. Allowed extensions: {sorted(list(settings.ALLOWED_DATASET_EXTENSIONS))}"
            )

        content = await upload_file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise StorageError(
                f"File size ({len(content)} bytes) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes."
            )

        provider = get_storage_provider()
        relative_key = f"datasets/{dataset_id}/{clean_filename}"
        saved_path_str = provider.save_file(relative_key, content, user_id=user_id)

        return Path(saved_path_str), clean_filename

    @classmethod
    def save_analysis_result(cls, sub_path: str, data: Dict[str, Any], user_id: str = "local_dev_user") -> Path:
        """Store full analysis result JSON payload via StorageProvider."""
        provider = get_storage_provider()
        relative_key = f"results/{sub_path.lstrip('/')}"
        saved_path_str = provider.save_json(relative_key, data, user_id=user_id)
        return Path(saved_path_str)

    @classmethod
    def load_analysis_result(cls, result_path_str: str, user_id: str = "local_dev_user") -> Dict[str, Any]:
        """Load stored analysis result JSON payload via StorageProvider."""
        provider = get_storage_provider()
        try:
            return provider.load_json(result_path_str, user_id=user_id)
        except Exception:
            # Fallback to direct path load if given absolute file path
            path = Path(result_path_str)
            if not path.exists():
                raise StorageError(f"Analysis result file not found at '{path}'.")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    @classmethod
    def load_model_adapter(cls, file_path_str: str, user_id: str = "local_dev_user"):
        """Load SklearnModelAdapter via StorageProvider (works for local files and Supabase Storage keys)."""
        from aegis.core.model_adapter import SklearnModelAdapter

        local_path = Path(file_path_str)
        if local_path.exists() and local_path.is_file():
            return SklearnModelAdapter.load(local_path)

        provider = get_storage_provider()
        content = provider.load_file(file_path_str, user_id=user_id)
        return SklearnModelAdapter.load_from_bytes(content, source_name=file_path_str)

    @classmethod
    def load_dataset(cls, file_path_str: str, target_column: Optional[str] = None, user_id: str = "local_dev_user"):
        """Load LoadedDataset via StorageProvider (works for local CSV files and Supabase Storage keys)."""
        from aegis.core.data_loader import CSVDataLoader

        local_path = Path(file_path_str)
        if local_path.exists() and local_path.is_file():
            return CSVDataLoader.load(local_path, target_column=target_column)

        provider = get_storage_provider()
        content = provider.load_file(file_path_str, user_id=user_id)
        return CSVDataLoader.load_from_bytes(content, target_column=target_column, source_name=file_path_str)

    @classmethod
    def save_joblib_artifact(cls, sub_path: str, obj: Any, user_id: str = "local_dev_user") -> Path:
        """Serialize and save a joblib artifact via StorageProvider."""
        import io
        import joblib

        buf = io.BytesIO()
        joblib.dump(obj, buf)
        buf.seek(0)

        provider = get_storage_provider()
        relative_key = f"artifacts/{sub_path.lstrip('/')}"
        saved_path_str = provider.save_file(relative_key, buf.getvalue(), user_id=user_id)
        return Path(saved_path_str)

    @classmethod
    def load_joblib_artifact(cls, artifact_path_str: str, user_id: str = "local_dev_user") -> Any:
        """Load joblib artifact via StorageProvider."""
        import io
        import joblib

        local_path = Path(artifact_path_str)
        if local_path.exists() and local_path.is_file():
            return joblib.load(local_path)

        provider = get_storage_provider()
        content = provider.load_file(artifact_path_str, user_id=user_id)
        return joblib.load(io.BytesIO(content))

    @classmethod
    def has_artifact(cls, sub_path_str: str, user_id: str = "local_dev_user") -> bool:
        """Check if artifact exists in local storage or cloud storage provider."""
        local_path = Path(sub_path_str)
        if local_path.exists():
            return True
        local_art_path = settings.ARTIFACTS_DIR / sub_path_str.lstrip("/")
        if local_art_path.exists():
            return True
        try:
            provider = get_storage_provider()
            provider.load_file(sub_path_str, user_id=user_id)
            return True
        except Exception:
            return False
