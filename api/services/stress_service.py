"""
AEGIS-X API Stress Lab Service.

Orchestrates controlled stress testing without mutating evaluation data.
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
import joblib

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.data_loader import CSVDataLoader
from aegis.core.exceptions import AegisError
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.fusion.engine import StressRobustFusion
from aegis.stress.engine import ControlledStressEngine
from api.core.config import settings
from api.core.dependencies import (
    get_dataset_repository,
    get_model_repository,
    get_reference_state_repository,
    get_stress_test_repository,
)
from api.db.models import StressTestRecord
from api.schemas.stress import StressTestRequest, StressTestResponse
from api.services.storage_service import StorageService


class StressServiceError(AegisError):
    """Raised when stress lab execution fails."""
    pass


class StressService:
    """Business logic for Stress Lab API."""

    @classmethod
    def run_stress_test(cls, request: StressTestRequest, user_id: str = "local_dev_user") -> StressTestResponse:
        """Executes controlled stress test on a copy of evaluation data."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()
        ref_repo = get_reference_state_repository()

        model_rec = model_repo.get_by_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise StressServiceError(f"Model '{request.model_id}' not found.")

        eval_rec = dataset_repo.get_by_id(request.evaluation_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not eval_rec:
            raise StressServiceError(f"Evaluation dataset '{request.evaluation_dataset_id}' not found.")

        ref_state_rec = ref_repo.get_by_model_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not ref_state_rec:
            raise StressServiceError(
                f"Model '{request.model_id}' has no fitted reference state. Call POST /api/v1/models/{request.model_id}/reference/{{dataset_id}}/fit first."
            )

        # Load resources via StorageService
        model_adapter = StorageService.load_model_adapter(model_rec.file_path, user_id=user_id)
        eval_dataset = StorageService.load_dataset(eval_rec.file_path, target_column=eval_rec.target_column, user_id=user_id)

        try:
            core_analyzer: CoreReliabilityAnalyzer = StorageService.load_joblib_artifact(ref_state_rec.artifact_path, user_id=user_id)
        except Exception:
            raise StressServiceError(f"Reference state artifact missing at '{ref_state_rec.artifact_path}'. Re-fit reference state.")
        fusion_engine = StressRobustFusion()
        stress_engine = ControlledStressEngine(random_state=request.random_state or 42)

        stress_result = stress_engine.run_stress_test(
            evaluation_data=eval_dataset.X,
            stress_type=request.stress_type,
            severity=request.severity,
            model_adapter=model_adapter,
            core_analyzer=core_analyzer,
            fusion_engine=fusion_engine,
            y_true=eval_dataset.y,
            random_state=request.random_state or 42,
        )

        if stress_result.status.value == "ERROR":
            raise StressServiceError(f"Stress test execution failed: {stress_result.warnings}")

        stress_test_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        response = StressTestResponse(
            stress_test_id=stress_test_id,
            model_id=request.model_id,
            evaluation_dataset_id=request.evaluation_dataset_id,
            stress_type=stress_result.stress_type,
            severity=stress_result.severity,
            random_state=request.random_state or 42,
            status=stress_result.status.value,
            original_risk=stress_result.original_risk,
            stressed_risk=stress_result.stressed_risk,
            risk_delta=stress_result.risk_delta,
            accuracy_delta=stress_result.accuracy_delta,
            original_accuracy=stress_result.original_accuracy,
            stressed_accuracy=stress_result.stressed_accuracy,
            details=stress_result.details,
            warnings=stress_result.warnings,
            limitations=stress_result.limitations,
            created_at=created_at,
        )

        # Save result JSON via StorageService
        sub_path = f"stress/{stress_test_id}/result.json"
        result_path = StorageService.save_analysis_result(sub_path, response.model_dump(), user_id=user_id)

        # Save metadata record in database
        record = StressTestRecord(
            id=stress_test_id,
            user_id=user_id,
            model_id=request.model_id,
            evaluation_dataset_id=request.evaluation_dataset_id,
            stress_type=stress_result.stress_type,
            severity=stress_result.severity,
            status=stress_result.status.value,
            result_path=str(result_path),
            original_risk=stress_result.original_risk,
            stressed_risk=stress_result.stressed_risk,
            risk_delta=stress_result.risk_delta,
            created_at=created_at,
        )

        repo = get_stress_test_repository()
        repo.create(record)

        return response

    @classmethod
    def get_stress_test(cls, stress_test_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch stress test result payload by ID."""
        repo = get_stress_test_repository()
        rec = repo.get_by_id(stress_test_id, owner_id=user_id)
        if not rec:
            raise StressServiceError(f"Stress test '{stress_test_id}' not found.")

        return StorageService.load_analysis_result(rec.result_path, user_id=user_id or "local_dev_user")

    @classmethod
    def list_stress_tests_for_model(cls, model_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List summary of stress tests for a model."""
        repo = get_stress_test_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            {
                "stress_test_id": r.id,
                "model_id": r.model_id,
                "evaluation_dataset_id": r.evaluation_dataset_id,
                "stress_type": r.stress_type,
                "severity": r.severity,
                "status": r.status,
                "original_risk": r.original_risk,
                "stressed_risk": r.stressed_risk,
                "risk_delta": r.risk_delta,
                "created_at": r.created_at,
            }
            for r in records
        ]
