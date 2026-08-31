"""
AEGIS-X API Failure Prediction Service.

Executes next-step onset-aware failure prediction when pre-fitted predictor artifacts exist.
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
import joblib

from aegis.core.data_loader import CSVDataLoader
from aegis.core.exceptions import AegisError
from aegis.prediction.engine import FailurePredictor
from api.core.config import settings
from api.core.dependencies import (
    get_dataset_repository,
    get_model_repository,
    get_prediction_repository,
)
from api.db.models import PredictionRecord
from api.schemas.prediction import (
    PredictionEventDetail,
    PredictionRequest,
    PredictionResponse,
)
from api.services.storage_service import StorageService


class PredictionServiceError(AegisError):
    """Raised when prediction execution fails."""
    pass


class PredictionService:
    """Business logic for Failure Prediction API."""

    @classmethod
    def run_prediction(cls, request: PredictionRequest, user_id: str = "local_dev_user") -> PredictionResponse:
        """Executes failure prediction using a pre-fitted FailurePredictor artifact if available."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()

        model_rec = model_repo.get_by_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise PredictionServiceError(f"Model '{request.model_id}' not found.")

        eval_rec = dataset_repo.get_by_id(request.evaluation_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not eval_rec:
            raise PredictionServiceError(f"Evaluation dataset '{request.evaluation_dataset_id}' not found.")

        created_at = datetime.now(timezone.utc).isoformat()
        prediction_id = str(uuid.uuid4())

        # Check for pre-fitted predictor artifact under storage/artifacts/<model_id>/prediction_model.joblib
        artifact_path = settings.ARTIFACTS_DIR / request.model_id / "prediction_model.joblib"
        if not artifact_path.exists():
            response = PredictionResponse(
                prediction_id=prediction_id,
                model_id=request.model_id,
                status="NOT_AVAILABLE",
                reason="Failure prediction model is not fitted for this deployment/setup.",
                horizon_steps=1,
                horizon_unit="controlled_degradation_states",
                warnings=["Failure prediction model is not fitted for this deployment/setup."],
                limitations=[
                    "Failure prediction requires pre-fitted degradation trajectory models.",
                    "Untrained deployments return ReliabilityStatus.NOT_AVAILABLE.",
                ],
                created_at=created_at,
            )

            record = PredictionRecord(
                id=prediction_id,
                user_id=user_id,
                model_id=request.model_id,
                status="NOT_AVAILABLE",
                horizon_steps=1,
                result_path="",
                mean_probability=None,
                created_at=created_at,
            )
            pred_repo = get_prediction_repository()
            pred_repo.create(record)

            return response

        # Load fitted predictor and evaluation dataset
        predictor: FailurePredictor = joblib.load(artifact_path)
        eval_dataset = CSVDataLoader.load(eval_rec.file_path, target_column=eval_rec.target_column)

        pred_result = predictor.predict(eval_dataset.X, y_true_onset=eval_dataset.y)

        events_detail = [
            PredictionEventDetail(
                sample_id=ev.sample_id,
                predicted_failure_prob=ev.predicted_failure_prob,
                is_failure_warning=ev.is_failure_warning,
                threshold=ev.threshold,
                actual_failure_onset=ev.actual_failure_onset,
            )
            for ev in pred_result.predictions
        ]

        response = PredictionResponse(
            prediction_id=prediction_id,
            model_id=request.model_id,
            status=pred_result.status.value,
            reason=None,
            horizon_steps=pred_result.horizon_steps,
            horizon_unit="controlled_degradation_states",
            selected_predictor=pred_result.selected_predictor,
            threshold=pred_result.threshold_info.threshold if pred_result.threshold_info else None,
            aggregate_onset_warning_rate=pred_result.aggregate_onset_warning_rate,
            mean_predicted_probability=pred_result.mean_predicted_probability,
            predictions=events_detail,
            heldout_metrics=pred_result.heldout_metrics,
            warnings=pred_result.warnings,
            limitations=pred_result.limitations,
            created_at=created_at,
        )

        sub_path = f"predictions/{prediction_id}/result.json"
        result_path = StorageService.save_analysis_result(sub_path, response.model_dump(), user_id=user_id)

        record = PredictionRecord(
            id=prediction_id,
            user_id=user_id,
            model_id=request.model_id,
            status=pred_result.status.value,
            horizon_steps=pred_result.horizon_steps,
            result_path=str(result_path),
            mean_probability=pred_result.mean_predicted_probability,
            created_at=created_at,
        )

        pred_repo = get_prediction_repository()
        pred_repo.create(record)

        return response

    @classmethod
    def get_prediction(cls, prediction_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch prediction result payload by ID."""
        repo = get_prediction_repository()
        rec = repo.get_by_id(prediction_id, owner_id=user_id)
        if not rec:
            raise PredictionServiceError(f"Prediction '{prediction_id}' not found.")

        if not rec.result_path:
            return {
                "prediction_id": rec.id,
                "model_id": rec.model_id,
                "status": rec.status,
                "created_at": rec.created_at,
            }
        return StorageService.load_analysis_result(rec.result_path, user_id=user_id or "local_dev_user")

    @classmethod
    def list_predictions_for_model(cls, model_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List predictions for a model."""
        repo = get_prediction_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            {
                "prediction_id": r.id,
                "model_id": r.model_id,
                "status": r.status,
                "horizon_steps": r.horizon_steps,
                "mean_probability": r.mean_probability,
                "created_at": r.created_at,
            }
            for r in records
        ]
