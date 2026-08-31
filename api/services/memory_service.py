"""
AEGIS-X API Failure Memory Service.

Orchestrates unsupervised failure signature clustering and non-leakage centroid query matching.
"""

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
import joblib
import pandas as pd

from aegis.core.contracts import FailureEvent
from aegis.core.exceptions import AegisError, DatasetValidationError
from aegis.failure_memory.matcher import FailureMemoryMatcher
from aegis.failure_memory.memory import FailureMemory
from aegis.failure_memory.signatures import ConditionProfileExtractor
from api.core.config import settings
from api.core.dependencies import (
    get_failure_memory_repository,
    get_fault_test_repository,
    get_model_repository,
)
from api.db.models import FailureMemoryRecord
from api.schemas.memory import (
    MemoryBuildRequest,
    MemoryBuildResponse,
    MemoryListResponse,
    MemoryMatchRequest,
    MemoryMatchResponse,
    SignatureDetail,
)
from api.services.storage_service import StorageService


class MemoryServiceError(AegisError):
    """Raised when Failure Memory operation fails."""
    pass


class MemoryService:
    """Business logic for Failure Memory API."""

    @classmethod
    def build_failure_memory(
        cls, model_id: str, request: MemoryBuildRequest, user_id: str = "local_dev_user"
    ) -> MemoryBuildResponse:
        """Builds unsupervised Failure Memory signature centroids from historical fault/stress condition profiles."""
        model_repo = get_model_repository()
        model_rec = model_repo.get_by_id(model_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not model_rec:
            raise MemoryServiceError(f"Model '{model_id}' not found.")

        fault_repo = get_fault_test_repository()
        if request.fault_test_ids:
            fault_records = [
                fault_repo.get_by_id(fid, owner_id=user_id if user_id != "local_dev_user" else None)
                for fid in request.fault_test_ids
                if fault_repo.get_by_id(fid, owner_id=user_id if user_id != "local_dev_user" else None)
            ]
        else:
            fault_records = fault_repo.list_by_model(model_id, owner_id=user_id if user_id != "local_dev_user" else None)

        if not fault_records:
            raise DatasetValidationError(
                f"No fault injection test runs found for model '{model_id}'. Run POST /api/v1/fault-tests first to generate condition profile events."
            )

        # Collect FailureEvent objects from stored result JSON payloads
        all_events: List[FailureEvent] = []
        for frec in fault_records:
            payload = StorageService.load_analysis_result(frec.result_path, user_id=user_id)
            events_raw = payload.get("failure_explorer", {}).get("failure_events", [])
            for ev_dict in events_raw:
                all_events.append(
                    FailureEvent(
                        sample_id=ev_dict["sample_id"],
                        ood_risk=ev_dict["ood_risk"],
                        uncertainty_risk=ev_dict["uncertainty_risk"],
                        drift_risk=ev_dict["drift_risk"],
                        fused_risk=ev_dict["fused_risk"],
                        is_high_risk_warning=ev_dict["is_high_risk_warning"],
                        fault_type=ev_dict.get("fault_type", frec.fault_type),
                        severity=ev_dict.get("severity", frec.severity),
                        has_actual_failure=ev_dict.get("has_actual_failure"),
                        is_silent_failure=ev_dict.get("is_silent_failure"),
                    )
                )

        if not all_events:
            raise DatasetValidationError("Collected fault runs contain 0 failure events.")

        # Extract aggregated condition profiles
        profiles_df = ConditionProfileExtractor.extract_profiles_from_events(all_events)

        if len(profiles_df) < request.n_clusters:
            n_clusters = max(1, len(profiles_df))
        else:
            n_clusters = request.n_clusters

        # Fit FailureMemory
        memory = FailureMemory(random_state=request.random_state or 42)
        fit_result = memory.fit(profiles_df, n_clusters=n_clusters, random_state=request.random_state or 42)

        memory_id = str(uuid.uuid4())
        fitted_at = datetime.now(timezone.utc).isoformat()

        # Save fitted FailureMemory artifact via StorageService
        sub_path = f"{model_id}/failure_memory/memory_{memory_id}.joblib"
        artifact_path = StorageService.save_joblib_artifact(sub_path, memory, user_id=user_id)

        signatures_detail = [
            SignatureDetail(
                signature_id=sig.signature_id,
                centroid_profile=sig.centroid_profile,
                feature_names=sig.feature_names,
                sample_count=sig.sample_count,
                distance_threshold=sig.distance_threshold,
                confidence=sig.confidence,
            )
            for sig in fit_result.signatures
        ]

        response = MemoryBuildResponse(
            memory_id=memory_id,
            model_id=model_id,
            status=fit_result.status.value,
            n_signatures=fit_result.n_signatures,
            signatures=signatures_detail,
            silhouette_score=fit_result.silhouette_score,
            stability_ari=fit_result.stability_ari,
            quality_summary=fit_result.quality_summary,
            warnings=fit_result.warnings,
            limitations=fit_result.limitations,
            fitted_at=fitted_at,
        )

        # Save metadata record in database
        record = FailureMemoryRecord(
            id=memory_id,
            user_id=user_id,
            model_id=model_id,
            n_signatures=fit_result.n_signatures,
            artifact_path=str(artifact_path),
            fitted_at=fitted_at,
        )

        repo = get_failure_memory_repository()
        repo.save_or_update(record)

        return response

    @classmethod
    def match_query_profile(
        cls, memory_id: str, request: MemoryMatchRequest, user_id: str = "local_dev_user"
    ) -> MemoryMatchResponse:
        """Matches a query condition profile against pre-fitted Failure Memory centroids."""
        repo = get_failure_memory_repository()
        rec = repo.get_by_id(memory_id, owner_id=user_id if user_id != "local_dev_user" else None)
        if not rec:
            raise MemoryServiceError(f"Failure Memory '{memory_id}' not found.")

        try:
            memory: FailureMemory = StorageService.load_joblib_artifact(rec.artifact_path, user_id=user_id)
        except Exception:
            raise MemoryServiceError(f"Failure Memory artifact missing at '{rec.artifact_path}'.")

        match_res = FailureMemoryMatcher.match(request.query_profile, memory)

        return MemoryMatchResponse(
            matched_signature_id=match_res.signature_id,
            signature_distance=match_res.signature_distance,
            distance_threshold=match_res.distance_threshold,
            is_known_pattern=match_res.is_known_pattern,
            centroid_profile=match_res.centroid_profile,
            associated_fault_distribution=match_res.associated_fault_distribution,
            warnings=match_res.warnings,
            limitations=match_res.limitations,
        )

    @classmethod
    def get_memory_details(cls, memory_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve details of a fitted Failure Memory."""
        repo = get_failure_memory_repository()
        rec = repo.get_by_id(memory_id, owner_id=user_id)
        if not rec:
            raise MemoryServiceError(f"Failure Memory '{memory_id}' not found.")

        try:
            memory: FailureMemory = StorageService.load_joblib_artifact(rec.artifact_path, user_id=user_id or "local_dev_user")
        except Exception:
            raise MemoryServiceError(f"Failure Memory artifact missing at '{rec.artifact_path}'.")
        return {
            "memory_id": rec.id,
            "model_id": rec.model_id,
            "n_signatures": rec.n_signatures,
            "feature_names": memory.feature_names,
            "distance_thresholds": memory.distance_thresholds,
            "signatures": [
                {
                    "signature_id": sig.signature_id,
                    "centroid_profile": sig.centroid_profile,
                    "sample_count": sig.sample_count,
                    "distance_threshold": sig.distance_threshold,
                }
                for sig in memory.signatures
            ],
            "fitted_at": rec.fitted_at,
        }

    @classmethod
    def list_memories_for_model(cls, model_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List failure memories for a model."""
        repo = get_failure_memory_repository()
        records = repo.list_by_model(model_id, owner_id=user_id)
        return [
            {
                "memory_id": r.id,
                "model_id": r.model_id,
                "n_signatures": r.n_signatures,
                "fitted_at": r.fitted_at,
            }
            for r in records
        ]
