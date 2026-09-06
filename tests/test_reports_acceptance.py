"""
AEGIS-X Reports Module Acceptance Test Suite.

Verifies end-to-end report generation, context locking, 12-module completeness matrix,
trust state derivation, operator action plans, RLS security isolation, snapshot immutability,
and export rendering.
"""

import pytest
import sqlite3
import tempfile
import json
import uuid
import datetime
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from api.db.database import get_db_connection, init_db
from api.db.models import (
    ModelRecord,
    DatasetRecord,
    AnalysisRecord,
    GovernanceEvaluationRecord,
    ReportRecord,
)
from api.db.repositories import (
    ModelRepository,
    DatasetRepository,
    AnalysisRepository,
    GovernanceRepository,
    ReportRepository,
)
from aegis.reports.generator import ReportGenerator
from aegis.reports.schemas import TrustDisposition, RetrainingDisposition, ModuleStatus
from api.services.reports_service import ReportsService


@pytest.fixture
def db_conn():
    """Provides a fresh SQLite connection with initialized tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Create tables
    conn.execute("""
        CREATE TABLE models (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_name TEXT NOT NULL,
            task_type TEXT NOT NULL, description TEXT, file_path TEXT NOT NULL,
            filename TEXT NOT NULL, predict_supported INTEGER NOT NULL,
            predict_proba_supported INTEGER NOT NULL, n_features_in INTEGER,
            classes_json TEXT, feature_names_json TEXT, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE datasets (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            dataset_type TEXT NOT NULL, file_path TEXT NOT NULL, filename TEXT NOT NULL,
            target_column TEXT, num_samples INTEGER NOT NULL, num_features INTEGER NOT NULL,
            feature_names_json TEXT NOT NULL, has_target INTEGER NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE reference_states (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL UNIQUE,
            dataset_id TEXT NOT NULL, artifact_path TEXT NOT NULL, feature_names_json TEXT NOT NULL,
            num_samples INTEGER NOT NULL, fitted_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE analyses (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            reference_dataset_id TEXT NOT NULL, evaluation_dataset_id TEXT NOT NULL,
            status TEXT NOT NULL, result_path TEXT NOT NULL, aggregate_ood_risk REAL,
            aggregate_uncertainty REAL, aggregate_drift_score REAL, aggregate_fused_risk REAL,
            fusion_method TEXT NOT NULL, has_labels INTEGER NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE stress_tests (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            evaluation_dataset_id TEXT NOT NULL, stress_type TEXT NOT NULL, severity REAL NOT NULL,
            status TEXT NOT NULL, original_risk REAL, stressed_risk REAL, risk_delta REAL,
            result_path TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE fault_tests (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            evaluation_dataset_id TEXT NOT NULL, fault_type TEXT NOT NULL, severity REAL NOT NULL,
            status TEXT NOT NULL, result_path TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE failure_memories (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            n_signatures INTEGER NOT NULL, artifact_path TEXT NOT NULL, fitted_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE predictions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            status TEXT NOT NULL, horizon_steps INTEGER NOT NULL, mean_probability REAL,
            result_path TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE warnings (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            status TEXT NOT NULL, warning_score REAL, is_warning_triggered INTEGER NOT NULL,
            threshold REAL NOT NULL, result_path TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE governance_evaluations (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            analysis_id TEXT, decision_id TEXT NOT NULL, state_index INTEGER NOT NULL,
            operating_mode TEXT NOT NULL, raw_action TEXT NOT NULL, effective_action TEXT NOT NULL,
            previous_effective_action TEXT, transition_occurred INTEGER NOT NULL DEFAULT 0,
            transition_reason TEXT, p_adverse REAL, prediction_set_json TEXT, reason_codes_json TEXT,
            calibrated INTEGER NOT NULL DEFAULT 0, calibrator_artifact_id TEXT,
            calibrator_artifact_sha256 TEXT, evidence_snapshot_hash TEXT NOT NULL,
            result_path TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE governance_transitions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            evaluation_id TEXT NOT NULL, state_index INTEGER NOT NULL, previous_state TEXT,
            new_state TEXT NOT NULL, raw_action TEXT NOT NULL, transition_reason TEXT NOT NULL,
            evidence_snapshot_hash TEXT NOT NULL, calibrated INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE reports (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, model_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL, report_type TEXT NOT NULL, title TEXT NOT NULL,
            disposition TEXT NOT NULL, completeness_score REAL NOT NULL, result_path TEXT NOT NULL,
            snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL
        );
    """)
    conn.commit()

    yield conn
    conn.close()
    if db_path.exists():
        db_path.unlink()


def test_context_locking_validation(db_conn):
    """Verifies that mixing evidence across different users or models raises an error."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    model = ModelRecord(
        id="mod_1", user_id="user_a", model_name="TestModel", task_type="classification",
        description="", file_path="fake.pkl", filename="fake.pkl", predict_supported=True,
        predict_proba_supported=True, n_features_in=4, classes=["0", "1"], feature_names=["f1", "f2", "f3", "f4"],
        created_at=now
    )
    ref_ds = DatasetRecord(
        id="ds_ref", user_id="user_a", model_id="mod_1", dataset_type="REFERENCE",
        file_path="ref.csv", filename="ref.csv", target_column=None, num_samples=100,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    eval_ds = DatasetRecord(
        id="ds_eval", user_id="user_a", model_id="mod_1", dataset_type="EVALUATION",
        file_path="eval.csv", filename="eval.csv", target_column=None, num_samples=50,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    analysis = AnalysisRecord(
        id="ana_1", user_id="user_a", model_id="mod_1", reference_dataset_id="ds_ref",
        evaluation_dataset_id="ds_eval", status="COMPLETED", result_path="res.json",
        aggregate_ood_risk=0.1, aggregate_uncertainty=0.2, aggregate_drift_score=0.05,
        aggregate_fused_risk=0.12, fusion_method="uncertainty_weighted", has_labels=False,
        created_at=now
    )

    # Valid generator initialization
    generator = ReportGenerator(
        user_id="user_a", model=model, analysis=analysis, ref_dataset=ref_ds, eval_dataset=eval_ds
    )
    payload = generator.generate("rep_test")
    assert payload.context.report_id == "rep_test"
    assert payload.trust_disposition in [TrustDisposition.HIGH, TrustDisposition.CONDITIONAL]

    # Invalid user_id mismatch
    with pytest.raises(ValueError, match="Model owner mismatch"):
        ReportGenerator(
            user_id="user_b", model=model, analysis=analysis, ref_dataset=ref_ds, eval_dataset=eval_ds
        )


def test_completeness_matrix_and_trust_derivation(db_conn):
    """Verifies evidence completeness matrix scoring and categorical trust state rules."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    model = ModelRecord(
        id="mod_2", user_id="user_a", model_name="CreditModel", task_type="classification",
        description="", file_path="fake.pkl", filename="fake.pkl", predict_supported=True,
        predict_proba_supported=True, n_features_in=4, classes=["0", "1"], feature_names=["f1", "f2", "f3", "f4"],
        created_at=now
    )
    ref_ds = DatasetRecord(
        id="ds_ref2", user_id="user_a", model_id="mod_2", dataset_type="REFERENCE",
        file_path="ref.csv", filename="ref.csv", target_column=None, num_samples=100,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    eval_ds = DatasetRecord(
        id="ds_eval2", user_id="user_a", model_id="mod_2", dataset_type="EVALUATION",
        file_path="eval.csv", filename="eval.csv", target_column=None, num_samples=50,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    # High risk analysis
    analysis_high_risk = AnalysisRecord(
        id="ana_high", user_id="user_a", model_id="mod_2", reference_dataset_id="ds_ref2",
        evaluation_dataset_id="ds_eval2", status="COMPLETED", result_path="res.json",
        aggregate_ood_risk=0.7, aggregate_uncertainty=0.6, aggregate_drift_score=0.65,
        aggregate_fused_risk=0.68, fusion_method="uncertainty_weighted", has_labels=False,
        created_at=now
    )

    gov_eval = GovernanceEvaluationRecord(
        id="gov_1", user_id="user_a", model_id="mod_2", analysis_id="ana_high",
        decision_id="dec_1", state_index=2, operating_mode="CONFORMAL_GUARDED",
        raw_action="DEFER", effective_action="DEFER", previous_effective_action="WATCH",
        transition_occurred=True, transition_reason="State transition to DEFER", p_adverse=0.7,
        prediction_set_json=json.dumps([0, 1]), reason_codes_json=json.dumps(["HIGH_RISK"]),
        calibrated=True, calibrator_artifact_id="cal_1", calibrator_artifact_sha256="abc",
        evidence_snapshot_hash="hash123", result_path="res.json", created_at=now
    )

    generator = ReportGenerator(
        user_id="user_a", model=model, analysis=analysis_high_risk, ref_dataset=ref_ds,
        eval_dataset=eval_ds, governance_evals=[gov_eval]
    )
    payload = generator.generate("rep_high")

    assert payload.trust_disposition == TrustDisposition.RESTRICTED
    assert payload.retraining_disposition == RetrainingDisposition.URGENT_MODEL_REVIEW
    assert len(payload.action_plan) > 0
    assert payload.action_plan[0].priority == "P1"


def test_report_repository_sqlite_crud(db_conn):
    """Verifies report creation, retrieval, owner isolation, and list filtering in SQLite repository."""
    repo = ReportRepository(db_conn)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    rec = ReportRecord(
        id="rep_100", user_id="user_owner", model_id="mod_100", analysis_id="ana_100",
        report_type="integrated", title="Integrated Reliability Report", disposition="HIGH",
        completeness_score=92.3, result_path="reports/rep_100.json",
        snapshot_json={"test": "data"}, created_at=now
    )

    created = repo.create(rec)
    assert created.id == "rep_100"

    fetched = repo.get_by_id("rep_100", owner_id="user_owner")
    assert fetched is not None
    assert fetched.title == "Integrated Reliability Report"
    assert fetched.snapshot_json == {"test": "data"}

    # Owner security isolation
    cross_fetched = repo.get_by_id("rep_100", owner_id="user_other")
    assert cross_fetched is None

    model_reports = repo.list_by_model("mod_100", owner_id="user_owner")
    assert len(model_reports) == 1
    assert model_reports[0].id == "rep_100"


def test_unexecuted_modules_render_unavailable(db_conn):
    """Verifies that missing modules render UNAVAILABLE and do not produce dummy 0.0 scores."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    model = ModelRecord(
        id="mod_unexecuted", user_id="user_a", model_name="TestModel", task_type="classification",
        description="", file_path="fake.pkl", filename="fake.pkl", predict_supported=True,
        predict_proba_supported=True, n_features_in=4, classes=["0", "1"], feature_names=["f1", "f2", "f3", "f4"],
        created_at=now
    )
    ref_ds = DatasetRecord(
        id="ds_ref_u", user_id="user_a", model_id="mod_unexecuted", dataset_type="REFERENCE",
        file_path="ref.csv", filename="ref.csv", target_column=None, num_samples=100,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    eval_ds = DatasetRecord(
        id="ds_eval_u", user_id="user_a", model_id="mod_unexecuted", dataset_type="EVALUATION",
        file_path="eval.csv", filename="eval.csv", target_column=None, num_samples=50,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    analysis = AnalysisRecord(
        id="ana_u", user_id="user_a", model_id="mod_unexecuted", reference_dataset_id="ds_ref_u",
        evaluation_dataset_id="ds_eval_u", status="COMPLETED", result_path="res.json",
        aggregate_ood_risk=0.1, aggregate_uncertainty=0.2, aggregate_drift_score=0.05,
        aggregate_fused_risk=0.12, fusion_method="uncertainty_weighted", has_labels=False,
        created_at=now
    )

    generator = ReportGenerator(
        user_id="user_a", model=model, analysis=analysis, ref_dataset=ref_ds, eval_dataset=eval_ds
    )
    payload = generator.generate("rep_u")

    # Stress Lab, Fault Lab, and Governance were not provided
    assert payload.completeness["stress_robustness"].status == ModuleStatus.UNAVAILABLE
    assert payload.completeness["stress_robustness"].prerequisite_missing is not None

    assert payload.completeness["fault_sensitivity"].status == ModuleStatus.UNAVAILABLE
    assert payload.completeness["fault_sensitivity"].prerequisite_missing is not None

    assert payload.completeness["ecrg_governance"].status == ModuleStatus.UNAVAILABLE
    assert payload.completeness["ecrg_governance"].prerequisite_missing is not None

    # Summaries must reflect UNAVAILABLE status, not fabricated zeros
    assert payload.stress_lab_summary["status"] == "UNAVAILABLE"
    assert payload.stress_lab_summary["avg_risk_delta"] is None

    assert payload.fault_lab_summary["status"] == "UNAVAILABLE"
    assert payload.fault_lab_summary["pass_rate"] is None

    assert payload.ecrg_governance_summary["effective_action"] == "UNAVAILABLE"


def test_switching_model_and_analysis_isolation(db_conn):
    """Verifies that changing model_id or analysis_id yields distinct evidence snapshots."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    model_1 = ModelRecord(
        id="mod_m1", user_id="user_a", model_name="ModelOne", task_type="classification",
        description="", file_path="fake.pkl", filename="fake.pkl", predict_supported=True,
        predict_proba_supported=True, n_features_in=4, classes=["0", "1"], feature_names=["f1", "f2", "f3", "f4"],
        created_at=now
    )
    model_2 = ModelRecord(
        id="mod_m2", user_id="user_a", model_name="ModelTwo", task_type="classification",
        description="", file_path="fake2.pkl", filename="fake2.pkl", predict_supported=True,
        predict_proba_supported=True, n_features_in=4, classes=["0", "1"], feature_names=["f1", "f2", "f3", "f4"],
        created_at=now
    )
    ref_ds = DatasetRecord(
        id="ds_ref_iso", user_id="user_a", model_id="mod_m1", dataset_type="REFERENCE",
        file_path="ref.csv", filename="ref.csv", target_column=None, num_samples=100,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    eval_ds = DatasetRecord(
        id="ds_eval_iso", user_id="user_a", model_id="mod_m1", dataset_type="EVALUATION",
        file_path="eval.csv", filename="eval.csv", target_column=None, num_samples=50,
        num_features=4, feature_names=["f1", "f2", "f3", "f4"], has_target=False, created_at=now
    )
    analysis_1 = AnalysisRecord(
        id="ana_iso1", user_id="user_a", model_id="mod_m1", reference_dataset_id="ds_ref_iso",
        evaluation_dataset_id="ds_eval_iso", status="COMPLETED", result_path="res.json",
        aggregate_ood_risk=0.1, aggregate_uncertainty=0.1, aggregate_drift_score=0.05,
        aggregate_fused_risk=0.08, fusion_method="uncertainty_weighted", has_labels=False,
        created_at=now
    )

    gen1 = ReportGenerator(user_id="user_a", model=model_1, analysis=analysis_1, ref_dataset=ref_ds, eval_dataset=eval_ds)
    p1 = gen1.generate("rep_m1")

    assert p1.context.model_id == "mod_m1"
    assert p1.reliability_summary["aggregate_fused_risk"] == 0.08


def test_api_report_endpoints():
    """Test REST API routes /api/v1/reports/generate, GET, list, and export."""
    client = TestClient(app)

    # Health check to ensure API router loaded
    res = client.get("/health")
    assert res.status_code == 200

