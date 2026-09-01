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
from aegis.core.exceptions import AegisError, DatasetValidationError
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
    PredictionFitRequest,
    PredictionFitResponse,
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

        if eval_rec.dataset_type not in {"TEMPORAL_TRAJECTORY", "PREDICTION_TRAJECTORY"}:
            raise DatasetValidationError(
                f"Failure Prediction execution requires a TEMPORAL_TRAJECTORY dataset. "
                f"Raw '{eval_rec.dataset_type}' datasets cannot be used for failure prediction."
            )

        created_at = datetime.now(timezone.utc).isoformat()
        prediction_id = str(uuid.uuid4())

        # Check for pre-fitted predictor artifact via StorageService
        if not StorageService.has_prediction_artifact(request.model_id, user_id=user_id):
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

        # Load fitted predictor via StorageService and evaluation dataset
        predictor: FailurePredictor = StorageService.load_prediction_artifact(request.model_id, user_id=user_id)

        loaded_ds = StorageService.load_dataset(eval_rec.file_path, target_column=eval_rec.target_column, user_id=user_id)
        raw_df = loaded_ds.X.copy()
        if loaded_ds.y is not None and eval_rec.target_column:
            raw_df[eval_rec.target_column] = loaded_ds.y

        from aegis.core.temporal import validate_and_prep_trajectory_df
        clean_df = validate_and_prep_trajectory_df(raw_df, target_col="Failure_Onset_Next")
        y_onset = clean_df["Failure_Onset_Next"] if "Failure_Onset_Next" in clean_df.columns else None

        pred_result = predictor.predict(clean_df, y_true_onset=y_onset)


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

    @classmethod
    def fit_prediction_model(
        cls,
        model_id: str,
        request: PredictionFitRequest,
        user_id: str = "local_dev_user",
    ) -> PredictionFitResponse:
        """Fits FailurePredictor on a validated temporal degradation trajectory split and saves artifact via StorageService."""
        import numpy as np
        import pandas as pd

        model_repo = get_model_repository()
        model_rec = model_repo.get_by_id(model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise PredictionServiceError(f"Model '{model_id}' not found.")

        if not request.trajectory_dataset_id:
            raise DatasetValidationError(
                "Failure Prediction setup requires selecting an uploaded TEMPORAL_TRAJECTORY dataset containing "
                "temporal reliability signals ['ood_risk', 'uncertainty_risk', 'drift_risk', 'fused_risk'] "
                "and ground-truth failure labels."
            )

        dataset_repo = get_dataset_repository()
        dataset_rec = dataset_repo.get_by_id(request.trajectory_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not dataset_rec:
            raise PredictionServiceError(f"Trajectory dataset '{request.trajectory_dataset_id}' not found.")

        loaded_ds = StorageService.load_dataset(dataset_rec.file_path, target_column=dataset_rec.target_column, user_id=user_id)
        raw_df = loaded_ds.X.copy()
        if loaded_ds.y is not None and dataset_rec.target_column:
            raw_df[dataset_rec.target_column] = loaded_ds.y

        from aegis.core.temporal import split_trajectories_group_safe, validate_and_prep_trajectory_df

        # Validate temporal trajectory schema, temporal ordering (trajectory_id, step), duplicates, and target consistency
        df = validate_and_prep_trajectory_df(raw_df, target_col="Failure_Onset_Next")

        # Perform group-aware trajectory split (70% train / 30% val unique trajectory IDs)
        train_df, val_df = split_trajectories_group_safe(df, target_col="Failure_Onset_Next", train_ratio=0.70)


        predictor = FailurePredictor(
            feature_set_type=request.feature_set_type or "dynamic",
            model_type=request.model_type or "random_forest",
            random_state=request.random_state or 42,
        )

        fit_res = predictor.fit(
            train_df=train_df,
            validation_df=val_df,
            target_column="Failure_Onset_Next",
            random_state=request.random_state or 42,
        )

        # Save fitted predictor via StorageService
        StorageService.save_prediction_artifact(model_id, predictor, user_id=user_id)

        fitted_at = datetime.now(timezone.utc).isoformat()
        t_info = fit_res.threshold_info

        return PredictionFitResponse(
            model_id=model_id,
            status="fitted",
            selected_predictor=fit_res.selected_predictor,
            horizon_steps=fit_res.horizon_steps,
            horizon_unit="controlled_degradation_states",
            threshold=t_info.threshold if t_info else None,
            heldout_metrics={
                "validation_f1": t_info.validation_f1 if t_info else 0.0,
                "validation_recall": t_info.validation_recall if t_info else 0.0,
                "validation_precision": t_info.validation_precision if t_info else 0.0,
            } if t_info else None,
            fitted_at=fitted_at,
            warnings=fit_res.warnings,
            limitations=fit_res.limitations,
        )

