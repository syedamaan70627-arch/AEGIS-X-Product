"""
AEGIS-X API Model Service.

Manages registration, validation, and metadata retrieval for user-supplied classification models.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import UploadFile

from aegis.core.model_adapter import SklearnModelAdapter
from api.core.dependencies import (
    get_analysis_repository,
    get_dataset_repository,
    get_failure_memory_repository,
    get_fault_test_repository,
    get_governance_repository,
    get_model_repository,
    get_prediction_repository,
    get_reference_state_repository,
    get_report_repository,
    get_stress_test_repository,
)
from api.db.models import ModelRecord
from api.schemas.models import ModelDeleteResponse, ModelDependencySummary, ModelResponse
from api.services.storage_service import StorageService
from fastapi import HTTPException, status


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
        try:
            file_path, filename = await StorageService.save_uploaded_model(model_id, file, user_id=user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "MODEL_STORAGE_FAILED", "message": f"Failed to store uploaded model file: {str(e)}"},
            )

        # Validate and inspect model using SklearnModelAdapter via StorageService
        try:
            adapter = StorageService.load_model_adapter(str(file_path), user_id=user_id)
            capabilities = adapter.get_capabilities()
        except Exception as e:
            try:
                provider = get_storage_provider()
                provider.delete_file(str(file_path), user_id=user_id)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "MODEL_METADATA_INVALID", "message": f"Failed to inspect model metadata: {str(e)}"},
            )

        # Convert numpy types to native JSON-safe Python types
        n_features_in = int(capabilities["n_features_in"]) if capabilities.get("n_features_in") is not None else None
        predict_proba_supported = bool(capabilities.get("supports_predict_proba", True))

        raw_classes = capabilities.get("classes")
        classes = [c.item() if hasattr(c, "item") else c for c in raw_classes] if raw_classes is not None else None

        raw_features = capabilities.get("feature_names_in")
        feature_names = [str(f) for f in raw_features] if raw_features is not None else None

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
            predict_proba_supported=predict_proba_supported,
            n_features_in=n_features_in,
            classes=classes,
            feature_names=feature_names,
            created_at=created_at,
            status="active",
        )

        repo = get_model_repository()
        try:
            repo.create(record)
        except Exception as err:
            # DB insert failed: rollback storage artifact
            try:
                import os
                if os.path.exists(str(file_path)):
                    os.remove(str(file_path))
                provider = get_storage_provider()
                provider.delete_file(str(file_path), user_id=user_id)
            except Exception:
                pass

            err_msg = str(err)
            err_code = "MODEL_DATABASE_INSERT_FAILED"
            if "PGRST204" in err_msg or "schema" in err_msg.lower():
                err_code = "MODEL_SCHEMA_MISMATCH"
            elif "409" in err_msg or "violates" in err_msg.lower():
                err_code = "MODEL_ALREADY_EXISTS"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": err_code, "message": f"Model registration database insert failed: {err_msg}"},
            )

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
            status=record.status,
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
            status=record.status,
        )

    @classmethod
    def list_models(cls, user_id: Optional[str] = None, include_deleted: bool = False) -> List[ModelResponse]:
        """List registered models belonging to the user."""
        repo = get_model_repository()
        records = repo.list_all(owner_id=user_id, include_deleted=include_deleted)
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
                status=r.status,
            )
            for r in records
        ]

    @classmethod
    def get_model_dependencies(cls, model_id: str, user_id: str) -> ModelDependencySummary:
        """Inspect all datasets, analyses, and test artifacts linked to a model."""
        repo = get_model_repository()
        record = repo.get_by_id(model_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "MODEL_NOT_FOUND", "message": f"Model '{model_id}' not found."},
            )
        if record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "MODEL_NOT_OWNED", "message": "You do not own this model."},
            )

        dataset_repo = get_dataset_repository()
        ref_repo = get_reference_state_repository()
        analysis_repo = get_analysis_repository()
        stress_repo = get_stress_test_repository()
        fault_repo = get_fault_test_repository()
        failure_memory_repo = get_failure_memory_repository()
        prediction_repo = get_prediction_repository()
        governance_repo = get_governance_repository()
        report_repo = get_report_repository()

        datasets = len(dataset_repo.list_by_model(model_id))
        ref_state = 1 if ref_repo.get_by_model_id(model_id) else 0
        analyses = len(analysis_repo.list_by_model(model_id))
        stress_tests = len(stress_repo.list_by_model(model_id))
        fault_tests = len(fault_repo.list_by_model(model_id))
        memories = len(failure_memory_repo.list_by_model(model_id))
        predictions = len(prediction_repo.list_by_model(model_id))
        gov_evals = governance_repo.count_evaluations_by_model(model_id)
        reports = len(report_repo.list_by_model(model_id))

        return ModelDependencySummary(
            model_id=model_id,
            model_name=record.model_name,
            uploaded_datasets=datasets,
            reference_states=ref_state,
            reliability_analyses=analyses,
            stress_tests=stress_tests,
            fault_tests=fault_tests,
            failure_memory_records=memories,
            prediction_records=predictions,
            governance_evaluations=gov_evals,
            report_snapshots=reports,
        )

    @classmethod
    def delete_model(cls, model_id: str, user_id: str) -> ModelDeleteResponse:
        """Perform safe model deletion (tombstoning & executable storage removal)."""
        repo = get_model_repository()
        record = repo.get_by_id(model_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "MODEL_NOT_FOUND", "message": f"Model '{model_id}' not found."},
            )
        if record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "MODEL_NOT_OWNED", "message": "You do not own this model."},
            )

        deps = cls.get_model_dependencies(model_id=model_id, user_id=user_id)

        # Delete physical executable model file from storage if present
        if record.file_path:
            try:
                import os
                if os.path.exists(record.file_path):
                    os.remove(record.file_path)
            except Exception:
                pass

        # Update database record status to "deleted"
        updated = repo.update_status(model_id=model_id, status="deleted", owner_id=user_id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "MODEL_DELETE_FAILED", "message": f"Failed to mark model '{model_id}' as deleted."},
            )

        return ModelDeleteResponse(
            success=True,
            model_id=model_id,
            message=f"Model '{record.model_name}' deleted successfully.",
            status="deleted",
            dependency_summary=deps,
        )

