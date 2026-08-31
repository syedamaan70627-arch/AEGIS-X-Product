"""
AEGIS-X API Model Capability Discovery Service.

Evaluates operational capability readiness for a registered model.
"""

from pathlib import Path
from typing import Optional

from api.core.config import settings
from api.core.dependencies import (
    get_failure_memory_repository,
    get_fault_test_repository,
    get_model_repository,
    get_reference_state_repository,
)
from api.schemas.capabilities import CapabilityStatusDetail, ModelCapabilitiesResponse
from api.services.storage_service import StorageService


class CapabilityService:
    """Evaluates readiness of AEGIS-X operational capabilities for a model."""

    @classmethod
    def get_model_capabilities(cls, model_id: str, user_id: Optional[str] = None) -> ModelCapabilitiesResponse:
        """Inspect model artifacts and repository records to return detailed capability readiness status."""
        model_repo = get_model_repository()
        ref_repo = get_reference_state_repository()
        fault_repo = get_fault_test_repository()
        memory_repo = get_failure_memory_repository()

        model_rec = model_repo.get_by_id(model_id, owner_id=user_id)
        if not model_rec:
            return ModelCapabilitiesResponse(
                model_id=model_id,
                capabilities={
                    "core_analysis": CapabilityStatusDetail(status="NOT_READY", reason=f"Model '{model_id}' not found."),
                    "stress_testing": CapabilityStatusDetail(status="NOT_READY", reason=f"Model '{model_id}' not found."),
                    "fault_testing": CapabilityStatusDetail(status="NOT_READY", reason=f"Model '{model_id}' not found."),
                    "failure_memory": CapabilityStatusDetail(status="NOT_READY", reason=f"Model '{model_id}' not found."),
                    "failure_prediction": CapabilityStatusDetail(status="NOT_READY", reason=f"Model '{model_id}' not found."),
                    "early_warning": CapabilityStatusDetail(status="NOT_READY", reason=f"Model '{model_id}' not found."),
                },
            )

        ref_state = ref_repo.get_by_model_id(model_id, owner_id=user_id)
        fault_runs = fault_repo.list_by_model(model_id, owner_id=user_id)
        memories = memory_repo.list_by_model(model_id, owner_id=user_id)

        has_ref = ref_state is not None and (Path(ref_state.artifact_path).exists() or StorageService.has_artifact(ref_state.artifact_path, user_id=user_id or "local_dev_user"))
        pred_key = f"{model_id}/prediction_model.joblib"
        has_pred = StorageService.has_artifact(pred_key, user_id=user_id or "local_dev_user")
        warn_key = f"{model_id}/warning_engine.joblib"
        has_warn = StorageService.has_artifact(warn_key, user_id=user_id or "local_dev_user")

        core_status = "READY" if has_ref else "REQUIRES_SETUP"
        core_reason = None if has_ref else "Reference state not fitted. Call POST /api/v1/models/{model_id}/reference/{dataset_id}/fit"

        stress_status = "READY" if has_ref else "REQUIRES_SETUP"
        stress_reason = None if has_ref else "Reference state not fitted."

        fault_status = "READY" if has_ref else "REQUIRES_SETUP"
        fault_reason = None if has_ref else "Reference state not fitted."

        if memories:
            mem_status = "READY"
            mem_reason = None
        elif fault_runs:
            mem_status = "REQUIRES_SETUP"
            mem_reason = "Fault test runs exist. Call POST /api/v1/failure-memory/{model_id}/build to fit signature centroids."
        else:
            mem_status = "REQUIRES_SETUP"
            mem_reason = "Requires fault injection runs before fitting failure memory."

        pred_status = "READY" if has_pred else "REQUIRES_SETUP"
        pred_reason = None if has_pred else "Prediction model artifact not fitted for this deployment."

        warn_status = "READY" if has_warn else "REQUIRES_SETUP"
        warn_reason = None if has_warn else "Early Warning engine artifact not fitted for this deployment."

        return ModelCapabilitiesResponse(
            model_id=model_id,
            capabilities={
                "core_analysis": CapabilityStatusDetail(status=core_status, reason=core_reason),
                "stress_testing": CapabilityStatusDetail(status=stress_status, reason=stress_reason),
                "fault_testing": CapabilityStatusDetail(status=fault_status, reason=fault_reason),
                "failure_memory": CapabilityStatusDetail(status=mem_status, reason=mem_reason),
                "failure_prediction": CapabilityStatusDetail(status=pred_status, reason=pred_reason),
                "early_warning": CapabilityStatusDetail(status=warn_status, reason=warn_reason),
            },
        )
