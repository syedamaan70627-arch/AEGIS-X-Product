"""
AEGIS-X API SQLite Repositories.

Implements SQLite repository CRUD methods conforming to api.db.base protocols with owner filtering.
"""

import json
import sqlite3
from typing import List, Optional

from api.db.base import (
    IAnalysisRepository,
    IDatasetRepository,
    IFailureMemoryRepository,
    IFaultTestRepository,
    IGovernanceRepository,
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
    GovernanceEvaluationRecord,
    GovernanceTransitionRecord,
    ModelRecord,
    PredictionRecord,
    ReferenceStateRecord,
    StressTestRecord,
    WarningRecord,
)


class ModelRepository(IModelRepository):
    """SQLite repository for managing Model records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: ModelRecord) -> ModelRecord:
        query = """
            INSERT INTO models (
                id, user_id, model_name, task_type, description, file_path, filename,
                predict_supported, predict_proba_supported, n_features_in,
                classes_json, feature_names_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_name,
                record.task_type,
                record.description,
                record.file_path,
                record.filename,
                1 if record.predict_supported else 0,
                1 if record.predict_proba_supported else 0,
                record.n_features_in,
                json.dumps(record.classes) if record.classes is not None else None,
                json.dumps(record.feature_names) if record.feature_names is not None else None,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, model_id: str, owner_id: Optional[str] = None) -> Optional[ModelRecord]:
        if owner_id:
            query = "SELECT * FROM models WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM models WHERE id = ?;"
            cursor = self.conn.execute(query, (model_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return ModelRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_name=row["model_name"],
            task_type=row["task_type"],
            description=row["description"],
            file_path=row["file_path"],
            filename=row["filename"],
            predict_supported=bool(row["predict_supported"]),
            predict_proba_supported=bool(row["predict_proba_supported"]),
            n_features_in=row["n_features_in"],
            classes=json.loads(row["classes_json"]) if row["classes_json"] else None,
            feature_names=json.loads(row["feature_names_json"]) if row["feature_names_json"] else None,
            created_at=row["created_at"],
        )

    def list_all(self, owner_id: Optional[str] = None) -> List[ModelRecord]:
        if owner_id:
            query = "SELECT * FROM models WHERE user_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (owner_id,))
        else:
            query = "SELECT * FROM models ORDER BY created_at DESC;"
            cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        models = []
        for row in rows:
            models.append(
                ModelRecord(
                    id=row["id"],
                    user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                    model_name=row["model_name"],
                    task_type=row["task_type"],
                    description=row["description"],
                    file_path=row["file_path"],
                    filename=row["filename"],
                    predict_supported=bool(row["predict_supported"]),
                    predict_proba_supported=bool(row["predict_proba_supported"]),
                    n_features_in=row["n_features_in"],
                    classes=json.loads(row["classes_json"]) if row["classes_json"] else None,
                    feature_names=json.loads(row["feature_names_json"]) if row["feature_names_json"] else None,
                    created_at=row["created_at"],
                )
            )
        return models


class DatasetRepository(IDatasetRepository):
    """SQLite repository for managing Dataset records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: DatasetRecord) -> DatasetRecord:
        query = """
            INSERT INTO datasets (
                id, user_id, model_id, dataset_type, file_path, filename, target_column,
                num_samples, num_features, feature_names_json, has_target, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.dataset_type,
                record.file_path,
                record.filename,
                record.target_column,
                record.num_samples,
                record.num_features,
                json.dumps(record.feature_names),
                1 if record.has_target else 0,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, dataset_id: str, owner_id: Optional[str] = None) -> Optional[DatasetRecord]:
        if owner_id:
            query = "SELECT * FROM datasets WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (dataset_id, owner_id))
        else:
            query = "SELECT * FROM datasets WHERE id = ?;"
            cursor = self.conn.execute(query, (dataset_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return DatasetRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            dataset_type=row["dataset_type"],
            file_path=row["file_path"],
            filename=row["filename"],
            target_column=row["target_column"],
            num_samples=row["num_samples"],
            num_features=row["num_features"],
            feature_names=json.loads(row["feature_names_json"]),
            has_target=bool(row["has_target"]),
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: Optional[str] = None, owner_id: Optional[str] = None) -> List[DatasetRecord]:
        params = []
        conditions = []
        if model_id:
            conditions.append("model_id = ?")
            params.append(model_id)
        if owner_id:
            conditions.append("user_id = ?")
            params.append(owner_id)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM datasets{where_clause} ORDER BY created_at DESC;"
        cursor = self.conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        datasets = []
        for row in rows:
            datasets.append(
                DatasetRecord(
                    id=row["id"],
                    user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                    model_id=row["model_id"],
                    dataset_type=row["dataset_type"],
                    file_path=row["file_path"],
                    filename=row["filename"],
                    target_column=row["target_column"],
                    num_samples=row["num_samples"],
                    num_features=row["num_features"],
                    feature_names=json.loads(row["feature_names_json"]),
                    has_target=bool(row["has_target"]),
                    created_at=row["created_at"],
                )
            )
        return datasets

    def delete(self, dataset_id: str, owner_id: Optional[str] = None) -> bool:
        if owner_id:
            query = "DELETE FROM datasets WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (dataset_id, owner_id))
        else:
            query = "DELETE FROM datasets WHERE id = ?;"
            cursor = self.conn.execute(query, (dataset_id,))
        self.conn.commit()
        return cursor.rowcount > 0


class ReferenceStateRepository(IReferenceStateRepository):
    """SQLite repository for managing Reference State records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save_or_update(self, record: ReferenceStateRecord) -> ReferenceStateRecord:
        query = """
            INSERT INTO reference_states (
                id, user_id, model_id, dataset_id, artifact_path, feature_names_json, num_samples, fitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model_id) DO UPDATE SET
                id = excluded.id,
                user_id = excluded.user_id,
                dataset_id = excluded.dataset_id,
                artifact_path = excluded.artifact_path,
                feature_names_json = excluded.feature_names_json,
                num_samples = excluded.num_samples,
                fitted_at = excluded.fitted_at;
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.dataset_id,
                record.artifact_path,
                json.dumps(record.feature_names),
                record.num_samples,
                record.fitted_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_model_id(self, model_id: str, owner_id: Optional[str] = None) -> Optional[ReferenceStateRecord]:
        if owner_id:
            query = "SELECT * FROM reference_states WHERE model_id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM reference_states WHERE model_id = ?;"
            cursor = self.conn.execute(query, (model_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return ReferenceStateRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            dataset_id=row["dataset_id"],
            artifact_path=row["artifact_path"],
            feature_names=json.loads(row["feature_names_json"]),
            num_samples=row["num_samples"],
            fitted_at=row["fitted_at"],
        )


class AnalysisRepository(IAnalysisRepository):
    """SQLite repository for managing Analysis records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: AnalysisRecord) -> AnalysisRecord:
        query = """
            INSERT INTO analyses (
                id, user_id, model_id, reference_dataset_id, evaluation_dataset_id,
                status, result_path, aggregate_ood_risk, aggregate_uncertainty,
                aggregate_drift_score, aggregate_fused_risk, fusion_method,
                has_labels, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.reference_dataset_id,
                record.evaluation_dataset_id,
                record.status,
                record.result_path,
                record.aggregate_ood_risk,
                record.aggregate_uncertainty,
                record.aggregate_drift_score,
                record.aggregate_fused_risk,
                record.fusion_method,
                1 if record.has_labels else 0,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, analysis_id: str, owner_id: Optional[str] = None) -> Optional[AnalysisRecord]:
        if owner_id:
            query = "SELECT * FROM analyses WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (analysis_id, owner_id))
        else:
            query = "SELECT * FROM analyses WHERE id = ?;"
            cursor = self.conn.execute(query, (analysis_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return AnalysisRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            reference_dataset_id=row["reference_dataset_id"],
            evaluation_dataset_id=row["evaluation_dataset_id"],
            status=row["status"],
            result_path=row["result_path"],
            aggregate_ood_risk=row["aggregate_ood_risk"],
            aggregate_uncertainty=row["aggregate_uncertainty"],
            aggregate_drift_score=row["aggregate_drift_score"],
            aggregate_fused_risk=row["aggregate_fused_risk"],
            fusion_method=row["fusion_method"],
            has_labels=bool(row["has_labels"]),
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[AnalysisRecord]:
        if owner_id:
            query = "SELECT * FROM analyses WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM analyses WHERE model_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id,))
        rows = cursor.fetchall()
        analyses = []
        for row in rows:
            analyses.append(
                AnalysisRecord(
                    id=row["id"],
                    user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                    model_id=row["model_id"],
                    reference_dataset_id=row["reference_dataset_id"],
                    evaluation_dataset_id=row["evaluation_dataset_id"],
                    status=row["status"],
                    result_path=row["result_path"],
                    aggregate_ood_risk=row["aggregate_ood_risk"],
                    aggregate_uncertainty=row["aggregate_uncertainty"],
                    aggregate_drift_score=row["aggregate_drift_score"],
                    aggregate_fused_risk=row["aggregate_fused_risk"],
                    fusion_method=row["fusion_method"],
                    has_labels=bool(row["has_labels"]),
                    created_at=row["created_at"],
                )
            )
        return analyses


class StressTestRepository(IStressTestRepository):
    """SQLite repository for managing Stress Test records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: StressTestRecord) -> StressTestRecord:
        query = """
            INSERT INTO stress_tests (
                id, user_id, model_id, evaluation_dataset_id, stress_type, severity,
                status, original_risk, stressed_risk, risk_delta, result_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.evaluation_dataset_id,
                record.stress_type,
                record.severity,
                record.status,
                record.original_risk,
                record.stressed_risk,
                record.risk_delta,
                record.result_path,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, stress_test_id: str, owner_id: Optional[str] = None) -> Optional[StressTestRecord]:
        if owner_id:
            query = "SELECT * FROM stress_tests WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (stress_test_id, owner_id))
        else:
            query = "SELECT * FROM stress_tests WHERE id = ?;"
            cursor = self.conn.execute(query, (stress_test_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return StressTestRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            evaluation_dataset_id=row["evaluation_dataset_id"],
            stress_type=row["stress_type"],
            severity=row["severity"],
            status=row["status"],
            result_path=row["result_path"],
            created_at=row["created_at"],
            original_risk=row["original_risk"],
            stressed_risk=row["stressed_risk"],
            risk_delta=row["risk_delta"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[StressTestRecord]:
        if owner_id:
            query = "SELECT * FROM stress_tests WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM stress_tests WHERE model_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id,))
        rows = cursor.fetchall()
        return [
            StressTestRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                evaluation_dataset_id=row["evaluation_dataset_id"],
                stress_type=row["stress_type"],
                severity=row["severity"],
                status=row["status"],
                result_path=row["result_path"],
                created_at=row["created_at"],
                original_risk=row["original_risk"],
                stressed_risk=row["stressed_risk"],
                risk_delta=row["risk_delta"],
            )
            for row in rows
        ]


class FaultTestRepository(IFaultTestRepository):
    """SQLite repository for managing Fault Test records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: FaultTestRecord) -> FaultTestRecord:
        query = """
            INSERT INTO fault_tests (
                id, user_id, model_id, evaluation_dataset_id, fault_type, severity,
                status, result_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.evaluation_dataset_id,
                record.fault_type,
                record.severity,
                record.status,
                record.result_path,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, fault_test_id: str, owner_id: Optional[str] = None) -> Optional[FaultTestRecord]:
        if owner_id:
            query = "SELECT * FROM fault_tests WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (fault_test_id, owner_id))
        else:
            query = "SELECT * FROM fault_tests WHERE id = ?;"
            cursor = self.conn.execute(query, (fault_test_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return FaultTestRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            evaluation_dataset_id=row["evaluation_dataset_id"],
            fault_type=row["fault_type"],
            severity=row["severity"],
            status=row["status"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[FaultTestRecord]:
        if owner_id:
            query = "SELECT * FROM fault_tests WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM fault_tests WHERE model_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id,))
        rows = cursor.fetchall()
        return [
            FaultTestRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                evaluation_dataset_id=row["evaluation_dataset_id"],
                fault_type=row["fault_type"],
                severity=row["severity"],
                status=row["status"],
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class FailureMemoryRepository(IFailureMemoryRepository):
    """SQLite repository for managing Failure Memory records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save_or_update(self, record: FailureMemoryRecord) -> FailureMemoryRecord:
        query = """
            INSERT INTO failure_memories (id, user_id, model_id, n_signatures, artifact_path, fitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                n_signatures = excluded.n_signatures,
                artifact_path = excluded.artifact_path,
                fitted_at = excluded.fitted_at;
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.n_signatures,
                record.artifact_path,
                record.fitted_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, memory_id: str, owner_id: Optional[str] = None) -> Optional[FailureMemoryRecord]:
        if owner_id:
            query = "SELECT * FROM failure_memories WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (memory_id, owner_id))
        else:
            query = "SELECT * FROM failure_memories WHERE id = ?;"
            cursor = self.conn.execute(query, (memory_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return FailureMemoryRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            n_signatures=row["n_signatures"],
            artifact_path=row["artifact_path"],
            fitted_at=row["fitted_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[FailureMemoryRecord]:
        if owner_id:
            query = "SELECT * FROM failure_memories WHERE model_id = ? AND user_id = ? ORDER BY fitted_at DESC;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM failure_memories WHERE model_id = ? ORDER BY fitted_at DESC;"
            cursor = self.conn.execute(query, (model_id,))
        rows = cursor.fetchall()
        return [
            FailureMemoryRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                n_signatures=row["n_signatures"],
                artifact_path=row["artifact_path"],
                fitted_at=row["fitted_at"],
            )
            for row in rows
        ]


class PredictionRepository(IPredictionRepository):
    """SQLite repository for managing Failure Prediction records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: PredictionRecord) -> PredictionRecord:
        query = """
            INSERT INTO predictions (id, user_id, model_id, status, horizon_steps, mean_probability, result_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.status,
                record.horizon_steps,
                record.mean_probability,
                record.result_path,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, prediction_id: str, owner_id: Optional[str] = None) -> Optional[PredictionRecord]:
        if owner_id:
            query = "SELECT * FROM predictions WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (prediction_id, owner_id))
        else:
            query = "SELECT * FROM predictions WHERE id = ?;"
            cursor = self.conn.execute(query, (prediction_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return PredictionRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            status=row["status"],
            horizon_steps=row["horizon_steps"],
            mean_probability=row["mean_probability"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[PredictionRecord]:
        if owner_id:
            query = "SELECT * FROM predictions WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM predictions WHERE model_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id,))
        rows = cursor.fetchall()
        return [
            PredictionRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                status=row["status"],
                horizon_steps=row["horizon_steps"],
                mean_probability=row["mean_probability"],
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class WarningRepository(IWarningRepository):
    """SQLite repository for managing Early Warning records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, record: WarningRecord) -> WarningRecord:
        query = """
            INSERT INTO warnings (id, user_id, model_id, status, warning_score, is_warning_triggered, threshold, result_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.status,
                record.warning_score,
                1 if record.is_warning_triggered else 0,
                record.threshold,
                record.result_path,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_by_id(self, warning_id: str, owner_id: Optional[str] = None) -> Optional[WarningRecord]:
        if owner_id:
            query = "SELECT * FROM warnings WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (warning_id, owner_id))
        else:
            query = "SELECT * FROM warnings WHERE id = ?;"
            cursor = self.conn.execute(query, (warning_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return WarningRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            status=row["status"],
            warning_score=row["warning_score"],
            is_warning_triggered=bool(row["is_warning_triggered"]),
            threshold=row["threshold"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_by_model(self, model_id: str, owner_id: Optional[str] = None) -> List[WarningRecord]:
        if owner_id:
            query = "SELECT * FROM warnings WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM warnings WHERE model_id = ? ORDER BY created_at DESC;"
            cursor = self.conn.execute(query, (model_id,))
        return [
            WarningRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                status=row["status"],
                warning_score=row["warning_score"],
                is_warning_triggered=bool(row["is_warning_triggered"]),
                threshold=row["threshold"],
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class GovernanceRepository(IGovernanceRepository):
    """SQLite repository for managing Governance Evaluation and Transition records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_evaluation(self, record: GovernanceEvaluationRecord) -> GovernanceEvaluationRecord:
        query = """
            INSERT INTO governance_evaluations (
                id, user_id, model_id, analysis_id, decision_id, state_index, operating_mode,
                raw_action, effective_action, previous_effective_action, transition_occurred,
                transition_reason, p_adverse, prediction_set_json, reason_codes_json,
                calibrated, calibrator_artifact_id, calibrator_artifact_sha256,
                evidence_snapshot_hash, result_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.analysis_id,
                record.decision_id,
                record.state_index,
                record.operating_mode,
                record.raw_action,
                record.effective_action,
                record.previous_effective_action,
                1 if record.transition_occurred else 0,
                record.transition_reason,
                record.p_adverse,
                record.prediction_set_json,
                record.reason_codes_json,
                1 if record.calibrated else 0,
                record.calibrator_artifact_id,
                record.calibrator_artifact_sha256,
                record.evidence_snapshot_hash,
                record.result_path,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def create_transition(self, record: GovernanceTransitionRecord) -> GovernanceTransitionRecord:
        query = """
            INSERT INTO governance_transitions (
                id, user_id, model_id, evaluation_id, state_index, previous_state,
                new_state, raw_action, transition_reason, evidence_snapshot_hash,
                calibrated, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.conn.execute(
            query,
            (
                record.id,
                record.user_id,
                record.model_id,
                record.evaluation_id,
                record.state_index,
                record.previous_state,
                record.new_state,
                record.raw_action,
                record.transition_reason,
                record.evidence_snapshot_hash,
                1 if record.calibrated else 0,
                record.created_at,
            ),
        )
        self.conn.commit()
        return record

    def get_evaluation_by_id(self, evaluation_id: str, owner_id: Optional[str] = None) -> Optional[GovernanceEvaluationRecord]:
        if owner_id:
            query = "SELECT * FROM governance_evaluations WHERE id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (evaluation_id, owner_id))
        else:
            query = "SELECT * FROM governance_evaluations WHERE id = ?;"
            cursor = self.conn.execute(query, (evaluation_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return GovernanceEvaluationRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            analysis_id=row["analysis_id"],
            decision_id=row["decision_id"],
            state_index=row["state_index"],
            operating_mode=row["operating_mode"],
            raw_action=row["raw_action"],
            effective_action=row["effective_action"],
            previous_effective_action=row["previous_effective_action"],
            transition_occurred=bool(row["transition_occurred"]),
            transition_reason=row["transition_reason"],
            p_adverse=row["p_adverse"],
            prediction_set_json=row["prediction_set_json"],
            reason_codes_json=row["reason_codes_json"],
            calibrated=bool(row["calibrated"]),
            calibrator_artifact_id=row["calibrator_artifact_id"],
            calibrator_artifact_sha256=row["calibrator_artifact_sha256"],
            evidence_snapshot_hash=row["evidence_snapshot_hash"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def get_latest_evaluation(self, model_id: str, owner_id: Optional[str] = None) -> Optional[GovernanceEvaluationRecord]:
        if owner_id:
            query = "SELECT * FROM governance_evaluations WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT * FROM governance_evaluations WHERE model_id = ? ORDER BY created_at DESC LIMIT 1;"
            cursor = self.conn.execute(query, (model_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return GovernanceEvaluationRecord(
            id=row["id"],
            user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
            model_id=row["model_id"],
            analysis_id=row["analysis_id"],
            decision_id=row["decision_id"],
            state_index=row["state_index"],
            operating_mode=row["operating_mode"],
            raw_action=row["raw_action"],
            effective_action=row["effective_action"],
            previous_effective_action=row["previous_effective_action"],
            transition_occurred=bool(row["transition_occurred"]),
            transition_reason=row["transition_reason"],
            p_adverse=row["p_adverse"],
            prediction_set_json=row["prediction_set_json"],
            reason_codes_json=row["reason_codes_json"],
            calibrated=bool(row["calibrated"]),
            calibrator_artifact_id=row["calibrator_artifact_id"],
            calibrator_artifact_sha256=row["calibrator_artifact_sha256"],
            evidence_snapshot_hash=row["evidence_snapshot_hash"],
            result_path=row["result_path"],
            created_at=row["created_at"],
        )

    def list_evaluations(self, model_id: str, owner_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[GovernanceEvaluationRecord]:
        if owner_id:
            query = "SELECT * FROM governance_evaluations WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?;"
            cursor = self.conn.execute(query, (model_id, owner_id, limit, offset))
        else:
            query = "SELECT * FROM governance_evaluations WHERE model_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?;"
            cursor = self.conn.execute(query, (model_id, limit, offset))
        rows = cursor.fetchall()
        return [
            GovernanceEvaluationRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                analysis_id=row["analysis_id"],
                decision_id=row["decision_id"],
                state_index=row["state_index"],
                operating_mode=row["operating_mode"],
                raw_action=row["raw_action"],
                effective_action=row["effective_action"],
                previous_effective_action=row["previous_effective_action"],
                transition_occurred=bool(row["transition_occurred"]),
                transition_reason=row["transition_reason"],
                p_adverse=row["p_adverse"],
                prediction_set_json=row["prediction_set_json"],
                reason_codes_json=row["reason_codes_json"],
                calibrated=bool(row["calibrated"]),
                calibrator_artifact_id=row["calibrator_artifact_id"],
                calibrator_artifact_sha256=row["calibrator_artifact_sha256"],
                evidence_snapshot_hash=row["evidence_snapshot_hash"],
                result_path=row["result_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    list_evaluations_by_model = list_evaluations

    def list_transitions(self, model_id: str, owner_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[GovernanceTransitionRecord]:
        if owner_id:
            query = "SELECT * FROM governance_transitions WHERE model_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?;"
            cursor = self.conn.execute(query, (model_id, owner_id, limit, offset))
        else:
            query = "SELECT * FROM governance_transitions WHERE model_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?;"
            cursor = self.conn.execute(query, (model_id, limit, offset))
        rows = cursor.fetchall()
        return [
            GovernanceTransitionRecord(
                id=row["id"],
                user_id=row["user_id"] if "user_id" in row.keys() else "local_dev_user",
                model_id=row["model_id"],
                evaluation_id=row["evaluation_id"],
                state_index=row["state_index"],
                previous_state=row["previous_state"],
                new_state=row["new_state"],
                raw_action=row["raw_action"],
                transition_reason=row["transition_reason"],
                evidence_snapshot_hash=row["evidence_snapshot_hash"],
                calibrated=bool(row["calibrated"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    list_transitions_by_model = list_transitions


    def count_evaluations_by_model(self, model_id: str, owner_id: Optional[str] = None) -> int:
        if owner_id:
            query = "SELECT COUNT(*) as cnt FROM governance_evaluations WHERE model_id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT COUNT(*) as cnt FROM governance_evaluations WHERE model_id = ?;"
            cursor = self.conn.execute(query, (model_id,))
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def count_transitions_by_model(self, model_id: str, owner_id: Optional[str] = None) -> int:
        if owner_id:
            query = "SELECT COUNT(*) as cnt FROM governance_transitions WHERE model_id = ? AND user_id = ?;"
            cursor = self.conn.execute(query, (model_id, owner_id))
        else:
            query = "SELECT COUNT(*) as cnt FROM governance_transitions WHERE model_id = ?;"
            cursor = self.conn.execute(query, (model_id,))
        row = cursor.fetchone()
        return row["cnt"] if row else 0
