"""
AEGIS-X API Database Connection & Schema Management.

Uses Python standard library sqlite3 for lightweight, zero-dependency,
maintainable metadata persistence at storage/api/aegis.db.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from api.core.config import settings


def get_db_connection(db_path: Path = settings.DB_PATH) -> sqlite3.Connection:
    """Create and configure a SQLite connection with Row factory, WAL mode, autocommit, and busy timeout."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=60.0, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 60000;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
    return conn




@contextmanager
def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for managing SQLite connection and transaction commit/rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_user_id_column(conn: sqlite3.Connection, table_name: str) -> None:
    """Helper to ensure user_id column exists on existing SQLite tables."""
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name});")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in columns:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN user_id TEXT DEFAULT 'local_dev_user';")
    except Exception:
        pass


def init_db() -> None:
    """Initialize database tables for models, datasets, reference_states, analyses, stress, faults, memory, prediction, and warning."""
    settings.ensure_directories()
    with get_db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA journal_mode = WAL;")
        except Exception:
            pass

        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                predict_supported INTEGER NOT NULL,
                predict_proba_supported INTEGER NOT NULL,
                n_features_in INTEGER,
                classes_json TEXT,
                feature_names_json TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # Datasets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                dataset_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                target_column TEXT,
                num_samples INTEGER NOT NULL,
                num_features INTEGER NOT NULL,
                feature_names_json TEXT NOT NULL,
                has_target INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            );
        """)

        # Reference States table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reference_states (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL UNIQUE,
                dataset_id TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                feature_names_json TEXT NOT NULL,
                num_samples INTEGER NOT NULL,
                fitted_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)

        # Analyses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                reference_dataset_id TEXT NOT NULL,
                evaluation_dataset_id TEXT NOT NULL,
                status TEXT NOT NULL,
                result_path TEXT NOT NULL,
                aggregate_ood_risk REAL,
                aggregate_uncertainty REAL,
                aggregate_drift_score REAL,
                aggregate_fused_risk REAL,
                fusion_method TEXT NOT NULL,
                has_labels INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY(reference_dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
                FOREIGN KEY(evaluation_dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)

        # Stress Tests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stress_tests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                evaluation_dataset_id TEXT NOT NULL,
                stress_type TEXT NOT NULL,
                severity REAL NOT NULL,
                status TEXT NOT NULL,
                original_risk REAL,
                stressed_risk REAL,
                risk_delta REAL,
                result_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY(evaluation_dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)

        # Fault Tests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fault_tests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                evaluation_dataset_id TEXT NOT NULL,
                fault_type TEXT NOT NULL,
                severity REAL NOT NULL,
                status TEXT NOT NULL,
                result_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY(evaluation_dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)

        # Failure Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                n_signatures INTEGER NOT NULL,
                artifact_path TEXT NOT NULL,
                fitted_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            );
        """)

        # Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                status TEXT NOT NULL,
                horizon_steps INTEGER NOT NULL,
                mean_probability REAL,
                result_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            );
        """)

        # Warnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                status TEXT NOT NULL,
                warning_score REAL,
                is_warning_triggered INTEGER NOT NULL,
                threshold REAL NOT NULL,
                result_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            );
        """)

        # Governance Evaluations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_evaluations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                analysis_id TEXT,
                decision_id TEXT NOT NULL,
                state_index INTEGER NOT NULL,
                operating_mode TEXT NOT NULL,
                raw_action TEXT NOT NULL,
                effective_action TEXT NOT NULL,
                previous_effective_action TEXT,
                transition_occurred INTEGER NOT NULL DEFAULT 0,
                transition_reason TEXT,
                p_adverse REAL,
                prediction_set_json TEXT,
                reason_codes_json TEXT,
                calibrated INTEGER NOT NULL DEFAULT 0,
                calibrator_artifact_id TEXT,
                calibrator_artifact_sha256 TEXT,
                evidence_snapshot_hash TEXT NOT NULL,
                result_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            );
        """)

        # Governance Transitions Audit Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_transitions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'local_dev_user',
                model_id TEXT NOT NULL,
                evaluation_id TEXT NOT NULL,
                state_index INTEGER NOT NULL,
                previous_state TEXT,
                new_state TEXT NOT NULL,
                raw_action TEXT NOT NULL,
                transition_reason TEXT NOT NULL,
                evidence_snapshot_hash TEXT NOT NULL,
                calibrated INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY(evaluation_id) REFERENCES governance_evaluations(id) ON DELETE CASCADE
            );
        """)

        for tbl in ["models", "datasets", "reference_states", "analyses", "stress_tests", "fault_tests", "failure_memories", "predictions", "warnings", "governance_evaluations", "governance_transitions"]:
            _ensure_user_id_column(conn, tbl)
