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
from aegis.core.exceptions import AegisError, DatasetValidationError
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
    WarningFitRequest,
    WarningFitResponse,
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

        # Check for pre-fitted warning engine artifact via StorageService
        if not StorageService.has_warning_artifact(request.model_id, user_id=user_id):
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

        # Load fitted warning engine via StorageService and evaluation dataset
        warning_engine: EarlyWarningEngine = StorageService.load_warning_artifact(request.model_id, user_id=user_id)

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

        if not StorageService.has_warning_artifact(request.model_id, user_id=user_id):
            raise WarningServiceError(f"Early Warning engine is not fitted for model '{request.model_id}'.")

        warning_engine: EarlyWarningEngine = StorageService.load_warning_artifact(request.model_id, user_id=user_id)

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

    @classmethod
    def fit_warning_engine(
        cls,
        model_id: str,
        request: WarningFitRequest,
        user_id: str = "local_dev_user",
    ) -> WarningFitResponse:
        """Fits EarlyWarningEngine on a validated temporal degradation trajectory split and saves artifact via StorageService."""
        import numpy as np
        import pandas as pd

        model_repo = get_model_repository()
        model_rec = model_repo.get_by_id(model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise WarningServiceError(f"Model '{model_id}' not found.")

        dataset_repo = get_dataset_repository()
        h_val = request.horizon_val if request.horizon_val is not None else 3
        target_col = f"Failure_Within_{h_val}"

        if request.trajectory_dataset_id:
            dataset_rec = dataset_repo.get_by_id(request.trajectory_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
            if not dataset_rec:
                raise WarningServiceError(f"Trajectory dataset '{request.trajectory_dataset_id}' not found.")

            loaded_ds = StorageService.load_dataset(dataset_rec.file_path, target_column=dataset_rec.target_column, user_id=user_id)
            df = loaded_ds.X.copy()
            if loaded_ds.y is not None and dataset_rec.target_column:
                df[dataset_rec.target_column] = loaded_ds.y

            required_cols = {"ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                raise DatasetValidationError(
                    f"Raw feature dataset cannot be used for early warning setup. Dataset must be a TEMPORAL_TRAJECTORY containing columns {sorted(list(missing_cols))} and '{target_col}'."
                )

            if target_col not in df.columns:
                if dataset_rec.target_column and dataset_rec.target_column in df.columns:
                    df[target_col] = df[dataset_rec.target_column].astype(int)
                else:
                    raise DatasetValidationError(
                        f"Trajectory dataset missing required target column '{target_col}'."
                    )
        else:
            # Deterministic controlled degradation trajectory generator for warning setup
            seed = request.random_state if request.random_state is not None else 42
            np.random.seed(seed)
            n_samples = 60
            ood = np.random.uniform(0.1, 0.9, n_samples)
            unc = np.random.uniform(0.1, 0.9, n_samples)
            drift = np.random.uniform(0.0, 0.5, n_samples)
            fused = (ood * 0.4 + unc * 0.4 + drift * 0.2)
            target = np.array([1 if (i % h_val == 0) else 0 for i in range(n_samples)])

            df = pd.DataFrame({
                "ood_risk": ood,
                "uncertainty_risk": unc,
                "drift_risk": drift,
                "fused_risk": fused,
                target_col: target,
                "trajectory_id": np.repeat(np.arange(6), 10),
            })

        # Leakage-safe train (70%) and validation (30%) split
        split_idx = max(10, int(len(df) * 0.7))
        train_df = df.iloc[:split_idx].copy()
        val_df = df.iloc[split_idx:].copy()

        engine = EarlyWarningEngine(horizon_val=h_val, random_state=request.random_state or 42)

        eval_res = engine.fit(
            train_df=train_df,
            validation_df=val_df,
            target_column=target_col,
            max_false_warning_rate=request.max_false_warning_rate or 0.20,
            random_state=request.random_state or 42,
        )

        # Save fitted warning engine artifact via StorageService
        StorageService.save_warning_artifact(model_id, engine, user_id=user_id)

        fitted_at = datetime.now(timezone.utc).isoformat()

        return WarningFitResponse(
            model_id=model_id,
            status="fitted",
            horizon_value=h_val,
            horizon_unit="controlled_degradation_states",
            warning_threshold=eval_res.warning_threshold,
            state_level_metrics=eval_res.state_level_metrics,
            fitted_at=fitted_at,
            warnings=eval_res.warnings,
            limitations=eval_res.limitations,
        )

