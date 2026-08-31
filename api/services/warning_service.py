"""
AEGIS-X API Early Warning Service.

Executes dynamic multi-signal temporal warning and trajectory lead evaluation when fitted warning artifacts exist.
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
import joblib

from aegis.core.data_loader import CSVDataLoader
from aegis.core.exceptions import AegisError
from aegis.warning.engine import EarlyWarningEngine
from api.core.config import settings
from api.core.dependencies import (
    get_dataset_repository,
    get_model_repository,
    get_warning_repository,
)
from api.db.models import WarningRecord
from api.schemas.warning import (
    WarningEvaluationRequest,
    WarningEvaluationResponse,
    WarningRequest,
    WarningResponse,
)
from api.services.storage_service import StorageService


class WarningServiceError(AegisError):
    """Raised when early warning execution fails."""
    pass


class WarningService:
    """Business logic for Early Warning API."""

    @classmethod
    def query_warning(cls, request: WarningRequest, user_id: str = "local_dev_user") -> WarningResponse:
        """Executes operational early warning query using a pre-fitted EarlyWarningEngine artifact if available."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()

        model_rec = model_repo.get_by_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise WarningServiceError(f"Model '{request.model_id}' not found.")

        eval_rec = dataset_repo.get_by_id(request.evaluation_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not eval_rec:
            raise WarningServiceError(f"Evaluation dataset '{request.evaluation_dataset_id}' not found.")

        created_at = datetime.now(timezone.utc).isoformat()
        warning_id = str(uuid.uuid4())

        # Check for pre-fitted warning engine artifact under storage/artifacts/<model_id>/warning_engine.joblib
        artifact_path = settings.ARTIFACTS_DIR / request.model_id / "warning_engine.joblib"
        if not artifact_path.exists():
            response = WarningResponse(
                warning_id=warning_id,
                model_id=request.model_id,
                status="NOT_AVAILABLE",
                reason="Early Warning engine is not fitted for this deployment/setup.",
                horizon_value=3,
                horizon_unit="controlled_degradation_states",
                warnings=["Early Warning engine is not fitted for this deployment/setup."],
                limitations=[
                    "Early Warning requires pre-fitted degradation trajectory models.",
                    "Untrained deployments return ReliabilityStatus.NOT_AVAILABLE.",
                ],
                created_at=created_at,
            )

            record = WarningRecord(
                id=warning_id,
                user_id=user_id,
                model_id=request.model_id,
                status="NOT_AVAILABLE",
                is_warning_triggered=False,
                threshold=0.46,
                result_path="",
                warning_score=None,
                created_at=created_at,
            )
            warn_repo = get_warning_repository()
            warn_repo.create(record)

            return response

        # Load fitted warning engine and evaluation dataset
        warning_engine: EarlyWarningEngine = joblib.load(artifact_path)
        eval_dataset = CSVDataLoader.load(eval_rec.file_path, target_column=eval_rec.target_column)

        warning_res = warning_engine.predict_warning(eval_dataset.X)

        response = WarningResponse(
            warning_id=warning_id,
            model_id=request.model_id,
            status=warning_res.status.value,
            reason=None,
            warning_score=warning_res.warning_score,
            is_warning_triggered=warning_res.is_warning_triggered,
            threshold=warning_res.threshold,
            horizon_value=warning_res.horizon.value if warning_res.horizon else 3,
            horizon_unit="controlled_degradation_states",
            signals=warning_res.signals,
            warnings=warning_res.warnings,
            limitations=warning_res.limitations,
            created_at=created_at,
        )

        sub_path = f"warnings/{warning_id}/result.json"
        result_path = StorageService.save_analysis_result(sub_path, response.model_dump(), user_id=user_id)

        record = WarningRecord(
            id=warning_id,
            user_id=user_id,
            model_id=request.model_id,
            status=warning_res.status.value,
            is_warning_triggered=warning_res.is_warning_triggered,
            threshold=warning_res.threshold,
            result_path=str(result_path),
            warning_score=warning_res.warning_score,
            created_at=created_at,
        )

        warn_repo = get_warning_repository()
        warn_repo.create(record)

        return response

    @classmethod
    def evaluate_trajectories(
        cls, request: WarningEvaluationRequest, user_id: str = "local_dev_user"
    ) -> WarningEvaluationResponse:
        """Evaluates full historical trajectory lead times and false warning rates using pre-fitted warning engine."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()

        model_rec = model_repo.get_by_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise WarningServiceError(f"Model '{request.model_id}' not found.")

        eval_rec = dataset_repo.get_by_id(request.evaluation_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not eval_rec:
            raise WarningServiceError(f"Evaluation dataset '{request.evaluation_dataset_id}' not found.")

        artifact_path = settings.ARTIFACTS_DIR / request.model_id / "warning_engine.joblib"
        if not artifact_path.exists():
            raise WarningServiceError(f"Early Warning engine is not fitted for model '{request.model_id}'.")

        warning_engine: EarlyWarningEngine = joblib.load(artifact_path)
        eval_dataset = CSVDataLoader.load(eval_rec.file_path, target_column=eval_rec.target_column)

        eval_res = warning_engine.evaluate_trajectories(eval_dataset.X)

        warning_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        response = WarningEvaluationResponse(
            warning_id=warning_id,
            model_id=request.model_id,
            status=eval_res.status.value,
            horizon_value=eval_res.selected_horizon.value if eval_res.selected_horizon else 3,
            horizon_unit="controlled_degradation_states",
            warning_threshold=eval_res.warning_threshold,
            state_level_metrics=eval_res.state_level_metrics,
            trajectory_level_metrics=eval_res.trajectory_level_metrics,
            trajectory_results=[r.to_dict() if hasattr(r, "to_dict") else str(r) for r in eval_res.trajectory_results],
            warnings=eval_res.warnings,
            limitations=eval_res.limitations,
            created_at=created_at,
        )

        return response

    @classmethod
    def get_warning(cls, warning_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch warning result payload by ID."""
        repo = get_warning_repository()
        rec = repo.get_by_id(warning_id, owner_id=user_id)
        if not rec:
            raise WarningServiceError(f"Warning '{warning_id}' not found.")

        if not rec.result_path:
            return {
                "warning_id": rec.id,
                "model_id": rec.model_id,
                "status": rec.status,
                "created_at": rec.created_at,
            }
        return StorageService.load_analysis_result(rec.result_path, user_id=user_id or "local_dev_user")

    @classmethod
    def list_warnings_for_model(cls, model_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List warnings for a model."""
        repo = get_warning_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            {
                "warning_id": r.id,
                "model_id": r.model_id,
                "status": r.status,
                "warning_score": r.warning_score,
                "is_warning_triggered": r.is_warning_triggered,
                "threshold": r.threshold,
                "created_at": r.created_at,
            }
            for r in records
        ]
