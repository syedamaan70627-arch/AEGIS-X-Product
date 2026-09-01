"""
AEGIS-X API Analysis Service.

Executes reference fitting and operational reliability analysis using existing AEGIS-X core engines.
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from scipy.stats import spearmanr

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.contracts import TaskType
from aegis.core.data_loader import CSVDataLoader
from aegis.core.exceptions import AegisError, DatasetValidationError
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.core.validator import IntegrationValidator
from aegis.fusion.engine import OriginalFusion, StressRobustFusion
from api.core.config import settings
from api.core.dependencies import (
    get_analysis_repository,
    get_dataset_repository,
    get_model_repository,
    get_reference_state_repository,
)
from api.db.models import AnalysisRecord, ReferenceStateRecord
from api.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    DiagnosticDetail,
    FusionDetail,
    SignalDetail,
)
from api.schemas.datasets import ReferenceFitResponse
from api.services.storage_service import StorageService


class AnalysisServiceError(AegisError):
    """Raised when analysis orchestration fails."""
    pass


class AnalysisService:
    """Orchestrates reference fitting, operational analysis execution, and result retrieval."""

    @classmethod
    def fit_reference_state(
        cls, model_id: str, dataset_id: str, user_id: str = "local_dev_user"
    ) -> ReferenceFitResponse:
        """Fit reference baseline state for a model using a registered REFERENCE dataset."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()
        ref_repo = get_reference_state_repository()

        model_rec = model_repo.get_by_id(model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise AnalysisServiceError(f"Model '{model_id}' not found.")

        dataset_rec = dataset_repo.get_by_id(dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not dataset_rec:
            raise AnalysisServiceError(f"Dataset '{dataset_id}' not found.")

        if dataset_rec.model_id != model_id:
            raise DatasetValidationError(
                f"Dataset '{dataset_id}' belongs to model '{dataset_rec.model_id}', not '{model_id}'."
            )

        if dataset_rec.dataset_type != "REFERENCE":
            raise DatasetValidationError(
                f"Dataset '{dataset_id}' is of type '{dataset_rec.dataset_type}'. Reference fit requires 'REFERENCE' dataset."
            )

        try:
            # Load model and dataset via StorageService
            model_adapter = StorageService.load_model_adapter(model_rec.file_path, user_id=user_id)
            ref_dataset = StorageService.load_dataset(dataset_rec.file_path, target_column=dataset_rec.target_column, user_id=user_id)

            # Fit CoreReliabilityAnalyzer
            analyzer = CoreReliabilityAnalyzer()
            analyzer.fit_reference(
                reference_data=ref_dataset.X,
                feature_names=ref_dataset.feature_names,
                calibration_data=ref_dataset.X if ref_dataset.y is not None else None,
                calibration_labels=ref_dataset.y,
                model_adapter=model_adapter,
            )

            # Save analyzer artifact via StorageService
            sub_path = f"{model_id}/reference_analyzer.joblib"
            artifact_path = StorageService.save_joblib_artifact(sub_path, analyzer, user_id=user_id)

            fitted_at = datetime.now(timezone.utc).isoformat()
            ref_id = str(uuid.uuid4())

            ref_record = ReferenceStateRecord(
                id=ref_id,
                user_id=user_id,
                model_id=model_id,
                dataset_id=dataset_id,
                artifact_path=str(artifact_path),
                feature_names=ref_dataset.feature_names,
                num_samples=ref_dataset.num_samples,
                fitted_at=fitted_at,
            )

            ref_repo.save_or_update(ref_record)
        except AegisError:
            raise
        except Exception as exc:
            raise AnalysisServiceError(f"Reference state fit failed: {str(exc)}") from exc


        return ReferenceFitResponse(
            model_id=model_id,
            dataset_id=dataset_id,
            status="fitted",
            num_samples=ref_dataset.num_samples,
            feature_names=ref_dataset.feature_names,
            fitted_at=fitted_at,
        )

    @classmethod
    def run_analysis(cls, request: AnalysisRequest, user_id: str = "local_dev_user") -> AnalysisResponse:
        """Execute AEGIS-X operational analysis on evaluation dataset."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()
        ref_repo = get_reference_state_repository()

        model_rec = model_repo.get_by_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise AnalysisServiceError(f"Model '{request.model_id}' not found.")

        eval_dataset_rec = dataset_repo.get_by_id(request.evaluation_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not eval_dataset_rec:
            raise AnalysisServiceError(f"Evaluation dataset '{request.evaluation_dataset_id}' not found.")

        ref_state_rec = ref_repo.get_by_model_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not ref_state_rec:
            raise AnalysisServiceError(
                f"Model '{request.model_id}' has no fitted reference state. Call POST /api/v1/models/{request.model_id}/reference/{{dataset_id}}/fit first."
            )

        ref_dataset_id = request.reference_dataset_id or ref_state_rec.dataset_id
        ref_dataset_rec = dataset_repo.get_by_id(ref_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not ref_dataset_rec:
            raise AnalysisServiceError(f"Reference dataset '{ref_dataset_id}' not found.")

        # Load resources via StorageService
        model_adapter = StorageService.load_model_adapter(model_rec.file_path, user_id=user_id)
        ref_dataset = StorageService.load_dataset(ref_dataset_rec.file_path, target_column=ref_dataset_rec.target_column, user_id=user_id)
        eval_dataset = StorageService.load_dataset(eval_dataset_rec.file_path, target_column=eval_dataset_rec.target_column, user_id=user_id)

        task_type = (
            TaskType.MULTICLASS_CLASSIFICATION
            if model_rec.task_type.lower() == "multiclass_classification"
            else TaskType.BINARY_CLASSIFICATION
        )

        # Validate integration parity
        validated_input = IntegrationValidator.validate_and_build(
            model_adapter=model_adapter,
            reference_dataset=ref_dataset,
            evaluation_dataset=eval_dataset,
            task_type=task_type,
        )

        # Load fitted analyzer artifact via StorageService
        try:
            analyzer: CoreReliabilityAnalyzer = StorageService.load_joblib_artifact(ref_state_rec.artifact_path, user_id=user_id)
        except Exception:
            raise AnalysisServiceError(f"Reference state artifact missing at '{ref_state_rec.artifact_path}'. Re-fit reference state.")

        # 1. Run core operational detection (OOD, Uncertainty, Drift)
        core_result = analyzer.analyze(validated_input.X_evaluation, model_adapter=model_adapter)

        # 2. Select and run operational fusion engine
        fusion_method = request.fusion_method.lower().strip()
        if fusion_method == "original":
            fusion_engine = OriginalFusion()
        else:
            fusion_engine = StressRobustFusion()

        fusion_result = fusion_engine.fuse(core_result.ood, core_result.uncertainty, core_result.drift)

        # 3. Process label-aware retrospective diagnostics if true labels exist
        diagnostics: Optional[DiagnosticDetail] = None
        has_labels = validated_input.y_evaluation is not None

        if has_labels:
            preds = model_adapter.predict(validated_input.X_evaluation)
            y_true = validated_input.y_evaluation.to_numpy()
            is_failure = (preds != y_true).astype(int)

            num_failures = int(np.sum(is_failure))
            total_samples = len(y_true)
            accuracy = float(1.0 - (num_failures / total_samples)) if total_samples > 0 else 0.0
            error_rate = float(num_failures / total_samples) if total_samples > 0 else 0.0

            corr: Optional[float] = None
            if fusion_result.fused_risk_scores is not None and len(np.unique(is_failure)) > 1:
                rho, _ = spearmanr(fusion_result.fused_risk_scores, is_failure)
                corr = float(rho) if not np.isnan(rho) else None

            diagnostics = DiagnosticDetail(
                accuracy=round(accuracy, 4),
                error_rate=round(error_rate, 4),
                num_failures=num_failures,
                correlation_fused_risk_vs_error=round(corr, 4) if corr is not None else None,
                metrics={
                    "total_evaluation_samples": total_samples,
                    "num_failures": num_failures,
                    "model_accuracy": round(accuracy, 4),
                },
            )

        analysis_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        # Build response schema object
        ood_detail = SignalDetail(
            status=core_result.ood.status.value,
            aggregate_score=core_result.ood.aggregate_risk,
            scores=core_result.ood.risk_scores.tolist() if core_result.ood.risk_scores is not None else None,
            details={
                "method": core_result.ood.method,
                "threshold": core_result.ood.threshold,
                "detector_metadata": core_result.ood.detector_metadata,
            },
            warnings=core_result.ood.warnings,
        )

        unc_detail = SignalDetail(
            status=core_result.uncertainty.status.value,
            aggregate_score=core_result.uncertainty.aggregate_uncertainty,
            scores=core_result.uncertainty.uncertainty_scores.tolist() if core_result.uncertainty.uncertainty_scores is not None else None,
            details={
                "method": core_result.uncertainty.method,
                "is_calibrated": core_result.uncertainty.is_calibrated,
                "calibration_info": core_result.uncertainty.calibration_info,
            },
            warnings=core_result.uncertainty.warnings,
        )

        drifted_feats = [k for k, v in core_result.drift.feature_drift_flags.items() if v]
        drift_detail = SignalDetail(
            status=core_result.drift.status.value,
            aggregate_score=core_result.drift.aggregate_drift_score,
            scores=None,
            details={
                "method": core_result.drift.method,
                "drift_detected": core_result.drift.drift_detected,
                "drifted_features": drifted_feats,
                "feature_p_values": core_result.drift.feature_p_values,
            },
            warnings=core_result.drift.warnings,
        )

        fusion_detail = FusionDetail(
            status=fusion_result.status.value,
            method=fusion_result.method,
            aggregate_fused_risk=fusion_result.aggregate_fused_risk,
            fused_risk_scores=fusion_result.fused_risk_scores.tolist() if fusion_result.fused_risk_scores is not None else None,
            threshold=fusion_result.threshold,
            model_metadata=fusion_result.model_metadata,
            warnings=fusion_result.warnings,
            limitations=fusion_result.limitations,
        )

        response = AnalysisResponse(
            analysis_id=analysis_id,
            model_id=request.model_id,
            reference_dataset_id=ref_dataset_id,
            evaluation_dataset_id=request.evaluation_dataset_id,
            created_at=created_at,
            status="completed",
            model_capability_summary=core_result.capability_summary,
            ood=ood_detail,
            uncertainty=unc_detail,
            drift=drift_detail,
            fusion=fusion_detail,
            warnings=core_result.warnings,
            limitations=[
                "Individual reliability signals (OOD, Uncertainty, Drift) are preserved.",
                "Pre-label operational fusion does not use true targets.",
            ],
            diagnostics=diagnostics,
        )

        # Save result JSON payload via StorageService
        result_path = StorageService.save_analysis_result(analysis_id, response.model_dump(), user_id=user_id)

        # Save metadata record in database
        record = AnalysisRecord(
            id=analysis_id,
            user_id=user_id,
            model_id=request.model_id,
            reference_dataset_id=ref_dataset_id,
            evaluation_dataset_id=request.evaluation_dataset_id,
            status="completed",
            result_path=str(result_path),
            fusion_method=fusion_method,
            has_labels=has_labels,
            aggregate_ood_risk=ood_detail.aggregate_score,
            aggregate_uncertainty=unc_detail.aggregate_score,
            aggregate_drift_score=drift_detail.aggregate_score,
            aggregate_fused_risk=fusion_detail.aggregate_fused_risk,
            created_at=created_at,
        )

        analysis_repo = get_analysis_repository()
        analysis_repo.create(record)

        return response

    @classmethod
    def get_analysis(cls, analysis_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve stored analysis result by ID."""
        repo = get_analysis_repository()
        record = repo.get_by_id(analysis_id, owner_id=user_id)
        if not record:
            raise AnalysisServiceError(f"Analysis '{analysis_id}' not found.")

        return StorageService.load_analysis_result(record.result_path, user_id=user_id or "local_dev_user")

    @classmethod
    def list_analyses_for_model(cls, model_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List summary of analyses for a given model."""
        repo = get_analysis_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            {
                "analysis_id": r.id,
                "model_id": r.model_id,
                "reference_dataset_id": r.reference_dataset_id,
                "evaluation_dataset_id": r.evaluation_dataset_id,
                "status": r.status,
                "fusion_method": r.fusion_method,
                "has_labels": r.has_labels,
                "aggregate_ood_risk": r.aggregate_ood_risk,
                "aggregate_uncertainty": r.aggregate_uncertainty,
                "aggregate_drift_score": r.aggregate_drift_score,
                "aggregate_fused_risk": r.aggregate_fused_risk,
                "created_at": r.created_at,
            }
            for r in records
        ]
