"""
AEGIS-X API Fault Injection & Failure Explorer Service.

Orchestrates structured fault injection and failure discovery without mutating evaluation data.
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
import joblib

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.data_loader import CSVDataLoader
from aegis.core.exceptions import AegisError, DatasetValidationError
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.faults.failure_discovery import FailureDiscoveryEngine
from aegis.faults.transformations import FaultInjector
from aegis.fusion.engine import StressRobustFusion
from api.core.config import settings
from api.core.dependencies import (
    get_dataset_repository,
    get_fault_test_repository,
    get_model_repository,
    get_reference_state_repository,
)
from api.db.models import FaultTestRecord
from api.schemas.faults import (
    FailureEventDetail,
    FailureExplorerResponse,
    FaultTestRequest,
    FaultTestResponse,
)
from api.services.storage_service import StorageService


class FaultServiceError(AegisError):
    """Raised when fault injection execution fails."""
    pass


class FaultService:
    """Business logic for Fault Injection and Failure Explorer APIs."""

    @classmethod
    def run_fault_test(cls, request: FaultTestRequest, user_id: str = "local_dev_user") -> FaultTestResponse:
        """Injects structured fault into a copy of evaluation data and runs failure discovery."""
        model_repo = get_model_repository()
        dataset_repo = get_dataset_repository()
        ref_repo = get_reference_state_repository()

        model_rec = model_repo.get_by_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise FaultServiceError(f"Model '{request.model_id}' not found.")

        eval_rec = dataset_repo.get_by_id(request.evaluation_dataset_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not eval_rec:
            raise FaultServiceError(f"Evaluation dataset '{request.evaluation_dataset_id}' not found.")

        ref_state_rec = ref_repo.get_by_model_id(request.model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not ref_state_rec:
            raise FaultServiceError(
                f"Model '{request.model_id}' has no fitted reference state. Call POST /api/v1/models/{request.model_id}/reference/{{dataset_id}}/fit first."
            )

        # Load resources via StorageService
        model_adapter = StorageService.load_model_adapter(model_rec.file_path, user_id=user_id)
        eval_dataset = StorageService.load_dataset(eval_rec.file_path, target_column=eval_rec.target_column, user_id=user_id)

        # Validate affected features exist in dataset if specified
        if request.affected_features:
            missing = set(request.affected_features) - set(eval_dataset.feature_names)
            if missing:
                raise DatasetValidationError(
                    f"Specified affected_features {sorted(list(missing))} do not exist in evaluation dataset features {eval_dataset.feature_names}."
                )

        if request.feature_pair:
            missing = set(request.feature_pair) - set(eval_dataset.feature_names)
            if missing:
                raise DatasetValidationError(
                    f"Specified feature_pair {sorted(list(missing))} do not exist in evaluation dataset features {eval_dataset.feature_names}."
                )

        try:
            core_analyzer: CoreReliabilityAnalyzer = StorageService.load_joblib_artifact(ref_state_rec.artifact_path, user_id=user_id)
        except Exception:
            raise FaultServiceError(f"Reference state artifact missing at '{ref_state_rec.artifact_path}'. Re-fit reference state.")
        fusion_engine = StressRobustFusion()
        seed = request.random_state or 42

        # 1. Inject fault into a copy of data using FaultInjector
        kwargs: Dict[str, Any] = {}
        if request.stuck_value is not None:
            kwargs["stuck_value"] = request.stuck_value
        if request.feature_pair:
            kwargs["feature_pair"] = (request.feature_pair[0], request.feature_pair[1])

        faulted_data, fault_inj_res = FaultInjector.inject(
            data=eval_dataset.X,
            fault_type=request.fault_type,
            severity=request.severity,
            feature_names=request.affected_features,
            seed=seed,
            **kwargs,
        )

        # 2. Execute Failure Discovery Engine
        discovery_engine = FailureDiscoveryEngine()
        discovery_res = discovery_engine.discover_failures(
            faulted_data=faulted_data,
            original_data=eval_dataset.X,
            y_true=eval_dataset.y,
            model_adapter=model_adapter,
            core_analyzer=core_analyzer,
            fusion_engine=fusion_engine,
            fault_type=request.fault_type,
            severity=request.severity,
        )

        fault_test_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        response = FaultTestResponse(
            fault_test_id=fault_test_id,
            model_id=request.model_id,
            evaluation_dataset_id=request.evaluation_dataset_id,
            fault_type=fault_inj_res.fault_type,
            severity=fault_inj_res.severity,
            affected_features=fault_inj_res.affected_features,
            status=fault_inj_res.status.value,
            transformation_metadata=fault_inj_res.transformation_metadata,
            warnings=fault_inj_res.warnings + discovery_res.warnings,
            limitations=fault_inj_res.limitations + discovery_res.limitations,
            created_at=created_at,
        )

        # Format failure explorer payload
        events_list = []
        for ev in discovery_res.failure_events:
            events_list.append(
                FailureEventDetail(
                    sample_id=ev.sample_id,
                    ood_risk=ev.ood_risk,
                    uncertainty_risk=ev.uncertainty_risk,
                    drift_risk=ev.drift_risk,
                    fused_risk=ev.fused_risk,
                    is_high_risk_warning=ev.is_high_risk_warning,
                    fault_type=ev.fault_type,
                    severity=ev.severity,
                    has_actual_failure=ev.has_actual_failure,
                    is_silent_failure=ev.is_silent_failure,
                ).model_dump()
            )

        explorer_payload = {
            "fault_test_id": fault_test_id,
            "is_label_aware": discovery_res.is_label_aware,
            "total_samples": discovery_res.total_samples,
            "total_warnings": discovery_res.total_warnings,
            "total_failures": discovery_res.total_failures,
            "silent_failures": discovery_res.silent_failures,
            "silent_failure_rate": discovery_res.silent_failure_rate,
            "silent_failure_status": "AVAILABLE" if discovery_res.is_label_aware else "NOT_AVAILABLE",
            "failure_events": events_list,
            "summary_by_fault": discovery_res.summary_by_fault,
            "warnings": discovery_res.warnings,
            "limitations": discovery_res.limitations,
        }

        payload_to_store = {
            "test_summary": response.model_dump(),
            "failure_explorer": explorer_payload,
        }

        sub_path = f"faults/{fault_test_id}/result.json"
        result_path = StorageService.save_analysis_result(sub_path, payload_to_store, user_id=user_id)

        # Save metadata record in database
        record = FaultTestRecord(
            id=fault_test_id,
            user_id=user_id,
            model_id=request.model_id,
            evaluation_dataset_id=request.evaluation_dataset_id,
            fault_type=fault_inj_res.fault_type,
            severity=fault_inj_res.severity,
            status=fault_inj_res.status.value,
            result_path=str(result_path),
            created_at=created_at,
        )

        repo = get_fault_test_repository()
        repo.create(record)

        return response

    @classmethod
    def get_fault_test(cls, fault_test_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch fault test result payload by ID."""
        repo = get_fault_test_repository()
        rec = repo.get_by_id(fault_test_id, owner_id=user_id)
        if not rec:
            raise FaultServiceError(f"Fault test '{fault_test_id}' not found.")

        payload = StorageService.load_analysis_result(rec.result_path, user_id=user_id or "local_dev_user")
        return payload["test_summary"]

    @classmethod
    def get_failure_explorer_data(cls, fault_test_id: str, user_id: Optional[str] = None) -> FailureExplorerResponse:
        """Fetch failure explorer payload for a fault test run."""
        repo = get_fault_test_repository()
        rec = repo.get_by_id(fault_test_id, owner_id=user_id)
        if not rec:
            raise FaultServiceError(f"Fault test '{fault_test_id}' not found.")

        full_payload = StorageService.load_analysis_result(rec.result_path, user_id=user_id or "local_dev_user")
        fe_dict = full_payload["failure_explorer"]
        return FailureExplorerResponse(**fe_dict)

    @classmethod
    def list_fault_tests_for_model(cls, model_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List summary of fault tests for a model."""
        repo = get_fault_test_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            {
                "fault_test_id": r.id,
                "model_id": r.model_id,
                "evaluation_dataset_id": r.evaluation_dataset_id,
                "fault_type": r.fault_type,
                "severity": r.severity,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in records
        ]
