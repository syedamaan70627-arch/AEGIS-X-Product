"""
AEGIS-X API Supabase Repositories.

Implements PostgreSQL/PostgREST repository classes matching api.db.base protocols for production deployments.
"""

import json
from typing import Any, Dict, List, Optional
import httpx

from aegis.core.exceptions import AegisError
from api.core.config import settings
from api.db.base import (
    IAnalysisRepository,
    IDatasetRepository,
    IFailureMemoryRepository,
    IFaultTestRepository,
    IModelRepository,
    IPredictionRepository,
    IReferenceStateRepository,
    IStressTestRepository,
    IWarningRepository,
)
from api.db.models import (
    AnalysisRecord,
    DatasetRecord,
    FailureMemoryRecord,
    FaultTestRecord,
    ModelRecord,
    PredictionRecord,
    ReferenceStateRecord,
    StressTestRecord,
    WarningRecord,
)


class SupabaseConfigurationError(AegisError):
    """Raised when Supabase backend is configured without required credentials."""
    pass


class BaseSupabaseRepository:
    """Base class providing HTTP REST operations against Supabase PostgREST endpoint."""

    def __init__(self, client: Optional[httpx.Client] = None) -> None:
        if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
            raise SupabaseConfigurationError(
                "DATABASE_BACKEND=supabase requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) environment variables."
            )

        self.url = f"{settings.SUPABASE_URL}/rest/v1"
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self.client = client or httpx.Client(timeout=10.0)


class SupabaseModelRepository(BaseSupabaseRepository, IModelRepository):
    def create(self, record: ModelRecord) -> ModelRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_name": record.model_name,
            "task_type": record.task_type,
            "description": record.description,
            "file_path": record.file_path,
            "filename": record.filename,
            "predict_supported": record.predict_supported,
            "predict_proba_supported": record.predict_proba_supported,
            "n_features_in": record.n_features_in,
            "classes_json": json.dumps(record.classes) if record.classes is not None else None,
            "feature_names_json": json.dumps(record.feature_names) if record.feature_names is not None else None,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/models", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, model_id: str, owner_id: Optional[str] = None) -> Optional[ModelRecord]:
        endpoint = f"{self.url}/models?id=eq.{model_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return ModelRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_name=row["model_name"],
            task_type=row["task_type"],
            description=row.get("description"),
            file_path=row["file_path"],
            filename=row["filename"],
            predict_supported=bool(row["predict_supported"]),
            predict_proba_supported=bool(row["predict_proba_supported"]),
            n_features_in=row.get("n_features_in"),
            classes=json.loads(row["classes_json"]) if row.get("classes_json") else None,
            feature_names=json.loads(row["feature_names_json"]) if row.get("feature_names_json") else None,
            created_at=row["created_at"],
        )

    def list_all(self, owner_id: Optional[str] = None) -> List[ModelRecord]:
        endpoint = f"{self.url}/models?order=created_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        models = []
        for row in res.json():
            models.append(
                ModelRecord(
                    id=row["id"],
                    user_id=row.get("user_id", "local_dev_user"),
                    model_name=row["model_name"],
                    task_type=row["task_type"],
                    description=row.get("description"),
                    file_path=row["file_path"],
                    filename=row["filename"],
                    predict_supported=bool(row["predict_supported"]),
                    predict_proba_supported=bool(row["predict_proba_supported"]),
                    n_features_in=row.get("n_features_in"),
                    classes=json.loads(row["classes_json"]) if row.get("classes_json") else None,
                    feature_names=json.loads(row["feature_names_json"]) if row.get("feature_names_json") else None,
                    created_at=row["created_at"],
                )
            )
        return models


class SupabaseDatasetRepository(BaseSupabaseRepository, IDatasetRepository):
    def create(self, record: DatasetRecord) -> DatasetRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "dataset_type": record.dataset_type,
            "file_path": record.file_path,
            "filename": record.filename,
            "target_column": record.target_column,
            "num_samples": record.num_samples,
            "num_features": record.num_features,
            "feature_names_json": json.dumps(record.feature_names),
            "has_target": record.has_target,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/datasets", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, dataset_id: str, owner_id: Optional[str] = None) -> Optional[DatasetRecord]:
        endpoint = f"{self.url}/datasets?id=eq.{dataset_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return DatasetRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            dataset_type=row["dataset_type"],
            file_path=row["file_path"],
            filename=row["filename"],
            target_column=row.get("target_column"),
            num_samples=row["num_samples"],
            num_features=row["num_features"],
            feature_names=json.loads(row["feature_names_json"]),
            has_target=bool(row["has_target"]),
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: Optional[str] = None, owner_id: Optional[str] = None) -> List[DatasetRecord]:
        endpoint = f"{self.url}/datasets?order=created_at.desc"
        if model_id:
            endpoint += f"&model_id=eq.{model_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        datasets = []
        for row in res.json():
            datasets.append(
                DatasetRecord(
                    id=row["id"],
                    user_id=row.get("user_id", "local_dev_user"),
                    model_id=row["model_id"],
                    dataset_type=row["dataset_type"],
                    file_path=row["file_path"],
                    filename=row["filename"],
                    target_column=row.get("target_column"),
                    num_samples=row["num_samples"],
                    num_features=row["num_features"],
                    feature_names=json.loads(row["feature_names_json"]),
                    has_target=bool(row["has_target"]),
                    created_at=row["created_at"],
                )
            )
        return datasets


class SupabaseReferenceStateRepository(BaseSupabaseRepository, IReferenceStateRepository):
    def save_or_update(self, record: ReferenceStateRecord) -> ReferenceStateRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "dataset_id": record.dataset_id,
            "artifact_path": record.artifact_path,
            "feature_names_json": json.dumps(record.feature_names),
            "num_samples": record.num_samples,
            "fitted_at": record.fitted_at,
        }
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates"}
        res = self.client.post(f"{self.url}/reference_states", headers=headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_model_id(self, model_id: str, owner_id: Optional[str] = None) -> Optional[ReferenceStateRecord]:
        endpoint = f"{self.url}/reference_states?model_id=eq.{model_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return ReferenceStateRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            dataset_id=row["dataset_id"],
            artifact_path=row["artifact_path"],
            feature_names=json.loads(row["feature_names_json"]),
            num_samples=row["num_samples"],
            fitted_at=row["fitted_at"],
        )


class SupabaseAnalysisRepository(BaseSupabaseRepository, IAnalysisRepository):
    def create(self, record: AnalysisRecord) -> AnalysisRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "reference_dataset_id": record.reference_dataset_id,
            "evaluation_dataset_id": record.evaluation_dataset_id,
            "status": record.status,
            "result_path": record.result_path,
            "aggregate_ood_risk": record.aggregate_ood_risk,
            "aggregate_uncertainty": record.aggregate_uncertainty,
            "aggregate_drift_score": record.aggregate_drift_score,
            "aggregate_fused_risk": record.aggregate_fused_risk,
            "fusion_method": record.fusion_method,
            "has_labels": record.has_labels,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/analyses", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, analysis_id: str, owner_id: Optional[str] = None) -> Optional[AnalysisRecord]:
        endpoint = f"{self.url}/analyses?id=eq.{analysis_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return AnalysisRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            reference_dataset_id=row["reference_dataset_id"],
            evaluation_dataset_id=row["evaluation_dataset_id"],
            status=row["status"],
            result_path=row["result_path"],
            aggregate_ood_risk=row.get("aggregate_ood_risk"),
            aggregate_uncertainty=row.get("aggregate_uncertainty"),
            aggregate_drift_score=row.get("aggregate_drift_score"),
            aggregate_fused_risk=row.get("aggregate_fused_risk"),
            fusion_method=row["fusion_method"],
            has_labels=bool(row["has_labels"]),
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[AnalysisRecord]:
        endpoint = f"{self.url}/analyses?model_id=eq.{model_id}&order=created_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        analyses = []
        for row in res.json():
            analyses.append(
                AnalysisRecord(
                    id=row["id"],
                    user_id=row.get("user_id", "local_dev_user"),
                    model_id=row["model_id"],
                    reference_dataset_id=row["reference_dataset_id"],
                    evaluation_dataset_id=row["evaluation_dataset_id"],
                    status=row["status"],
                    result_path=row["result_path"],
                    aggregate_ood_risk=row.get("aggregate_ood_risk"),
                    aggregate_uncertainty=row.get("aggregate_uncertainty"),
                    aggregate_drift_score=row.get("aggregate_drift_score"),
                    aggregate_fused_risk=row.get("aggregate_fused_risk"),
                    fusion_method=row["fusion_method"],
                    has_labels=bool(row["has_labels"]),
                    created_at=row["created_at"],
                )
            )
        return analyses


class SupabaseStressTestRepository(BaseSupabaseRepository, IStressTestRepository):
    def create(self, record: StressTestRecord) -> StressTestRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "evaluation_dataset_id": record.evaluation_dataset_id,
            "stress_type": record.stress_type,
            "severity": record.severity,
            "status": record.status,
            "original_risk": record.original_risk,
            "stressed_risk": record.stressed_risk,
            "risk_delta": record.risk_delta,
            "result_path": record.result_path,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/stress_tests", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, stress_test_id: str, owner_id: Optional[str] = None) -> Optional[StressTestRecord]:
        endpoint = f"{self.url}/stress_tests?id=eq.{stress_test_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return StressTestRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            evaluation_dataset_id=row["evaluation_dataset_id"],
            stress_type=row["stress_type"],
            severity=row["severity"],
            status=row["status"],
            result_path=row["result_path"],
            created_at=row["created_at"],
            original_risk=row.get("original_risk"),
            stressed_risk=row.get("stressed_risk"),
            risk_delta=row.get("risk_delta"),
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[StressTestRecord]:
        endpoint = f"{self.url}/stress_tests?model_id=eq.{model_id}&order=created_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        return [
            StressTestRecord(
                id=row["id"],
                user_id=row.get("user_id", "local_dev_user"),
                model_id=row["model_id"],
                evaluation_dataset_id=row["evaluation_dataset_id"],
                stress_type=row["stress_type"],
                severity=row["severity"],
                status=row["status"],
                result_path=row["result_path"],
                created_at=row["created_at"],
                original_risk=row.get("original_risk"),
                stressed_risk=row.get("stressed_risk"),
                risk_delta=row.get("risk_delta"),
            )
            for row in res.json()
        ]


class SupabaseFaultTestRepository(BaseSupabaseRepository, IFaultTestRepository):
    def create(self, record: FaultTestRecord) -> FaultTestRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "evaluation_dataset_id": record.evaluation_dataset_id,
            "fault_type": record.fault_type,
            "severity": record.severity,
            "status": record.status,
            "result_path": record.result_path,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/fault_tests", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, fault_test_id: str, owner_id: Optional[str] = None) -> Optional[FaultTestRecord]:
        endpoint = f"{self.url}/fault_tests?id=eq.{fault_test_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return FaultTestRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            evaluation_dataset_id=row["evaluation_dataset_id"],
            fault_type=row["fault_type"],
            severity=row["severity"],
            status=row["status"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[FaultTestRecord]:
        endpoint = f"{self.url}/fault_tests?model_id=eq.{model_id}&order=created_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        return [
            FaultTestRecord(
                id=row["id"],
                user_id=row.get("user_id", "local_dev_user"),
                model_id=row["model_id"],
                evaluation_dataset_id=row["evaluation_dataset_id"],
                fault_type=row["fault_type"],
                severity=row["severity"],
                status=row["status"],
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in res.json()
        ]


class SupabaseFailureMemoryRepository(BaseSupabaseRepository, IFailureMemoryRepository):
    def save_or_update(self, record: FailureMemoryRecord) -> FailureMemoryRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "n_signatures": record.n_signatures,
            "artifact_path": record.artifact_path,
            "fitted_at": record.fitted_at,
        }
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates"}
        res = self.client.post(f"{self.url}/failure_memories", headers=headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, memory_id: str, owner_id: Optional[str] = None) -> Optional[FailureMemoryRecord]:
        endpoint = f"{self.url}/failure_memories?id=eq.{memory_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return FailureMemoryRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            n_signatures=row["n_signatures"],
            artifact_path=row["artifact_path"],
            fitted_at=row["fitted_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[FailureMemoryRecord]:
        endpoint = f"{self.url}/failure_memories?model_id=eq.{model_id}&order=fitted_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        return [
            FailureMemoryRecord(
                id=row["id"],
                user_id=row.get("user_id", "local_dev_user"),
                model_id=row["model_id"],
                n_signatures=row["n_signatures"],
                artifact_path=row["artifact_path"],
                fitted_at=row["fitted_at"],
            )
            for row in res.json()
        ]


class SupabasePredictionRepository(BaseSupabaseRepository, IPredictionRepository):
    def create(self, record: PredictionRecord) -> PredictionRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "status": record.status,
            "horizon_steps": record.horizon_steps,
            "mean_probability": record.mean_probability,
            "result_path": record.result_path,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/predictions", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, prediction_id: str, owner_id: Optional[str] = None) -> Optional[PredictionRecord]:
        endpoint = f"{self.url}/predictions?id=eq.{prediction_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return PredictionRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            status=row["status"],
            horizon_steps=row["horizon_steps"],
            mean_probability=row.get("mean_probability"),
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[PredictionRecord]:
        endpoint = f"{self.url}/predictions?model_id=eq.{model_id}&order=created_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        return [
            PredictionRecord(
                id=row["id"],
                user_id=row.get("user_id", "local_dev_user"),
                model_id=row["model_id"],
                status=row["status"],
                horizon_steps=row["horizon_steps"],
                mean_probability=row.get("mean_probability"),
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in res.json()
        ]


class SupabaseWarningRepository(BaseSupabaseRepository, IWarningRepository):
    def create(self, record: WarningRecord) -> WarningRecord:
        payload = {
            "id": record.id,
            "user_id": record.user_id,
            "model_id": record.model_id,
            "status": record.status,
            "warning_score": record.warning_score,
            "is_warning_triggered": record.is_warning_triggered,
            "threshold": record.threshold,
            "result_path": record.result_path,
            "created_at": record.created_at,
        }
        res = self.client.post(f"{self.url}/warnings", headers=self.headers, json=payload)
        res.raise_for_status()
        return record

    def get_by_id(self, warning_id: str, owner_id: Optional[str] = None) -> Optional[WarningRecord]:
        endpoint = f"{self.url}/warnings?id=eq.{warning_id}"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200 or not res.json():
            return None
        row = res.json()[0]
        return WarningRecord(
            id=row["id"],
            user_id=row.get("user_id", "local_dev_user"),
            model_id=row["model_id"],
            status=row["status"],
            warning_score=row.get("warning_score"),
            is_warning_triggered=bool(row["is_warning_triggered"]),
            threshold=row["threshold"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[WarningRecord]:
        endpoint = f"{self.url}/warnings?model_id=eq.{model_id}&order=created_at.desc"
        if owner_id:
            endpoint += f"&user_id=eq.{owner_id}"
        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            return []
        return [
            WarningRecord(
                id=row["id"],
                user_id=row.get("user_id", "local_dev_user"),
                model_id=row["model_id"],
                status=row["status"],
                warning_score=row.get("warning_score"),
                is_warning_triggered=bool(row["is_warning_triggered"]),
                threshold=row["threshold"],
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in res.json()
        ]
