"""
AEGIS-X API Dependency Injection Module.

Provides factory functions returning repository and storage provider instances according to backend configuration.
"""

from typing import Optional
import sqlite3

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
    IGovernanceRepository,
)
from api.db.database import get_db_connection
from api.db.repositories import (
    AnalysisRepository,
    DatasetRepository,
    FailureMemoryRepository,
    FaultTestRepository,
    ModelRepository,
    PredictionRepository,
    ReferenceStateRepository,
    StressTestRepository,
    WarningRepository,
    GovernanceRepository,
)
from api.db.supabase_repositories import (
    SupabaseAnalysisRepository,
    SupabaseDatasetRepository,
    SupabaseFailureMemoryRepository,
    SupabaseFaultTestRepository,
    SupabaseModelRepository,
    SupabasePredictionRepository,
    SupabaseReferenceStateRepository,
    SupabaseStressTestRepository,
    SupabaseWarningRepository,
    SupabaseGovernanceRepository,
)
from api.storage.base import IStorageProvider
from api.storage.local_storage import LocalStorageProvider
from api.storage.supabase_storage import SupabaseStorageProvider


def get_storage_provider() -> IStorageProvider:
    """Returns storage provider based on STORAGE_BACKEND setting."""
    if settings.STORAGE_BACKEND == "supabase":
        return SupabaseStorageProvider()
    return LocalStorageProvider()


def get_model_repository(conn: Optional[sqlite3.Connection] = None) -> IModelRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseModelRepository()
    return ModelRepository(conn or get_db_connection())


def get_dataset_repository(conn: Optional[sqlite3.Connection] = None) -> IDatasetRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseDatasetRepository()
    return DatasetRepository(conn or get_db_connection())


def get_reference_state_repository(conn: Optional[sqlite3.Connection] = None) -> IReferenceStateRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseReferenceStateRepository()
    return ReferenceStateRepository(conn or get_db_connection())


def get_analysis_repository(conn: Optional[sqlite3.Connection] = None) -> IAnalysisRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseAnalysisRepository()
    return AnalysisRepository(conn or get_db_connection())


def get_stress_test_repository(conn: Optional[sqlite3.Connection] = None) -> IStressTestRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseStressTestRepository()
    return StressTestRepository(conn or get_db_connection())


def get_fault_test_repository(conn: Optional[sqlite3.Connection] = None) -> IFaultTestRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseFaultTestRepository()
    return FaultTestRepository(conn or get_db_connection())


def get_failure_memory_repository(conn: Optional[sqlite3.Connection] = None) -> IFailureMemoryRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseFailureMemoryRepository()
    return FailureMemoryRepository(conn or get_db_connection())


def get_prediction_repository(conn: Optional[sqlite3.Connection] = None) -> IPredictionRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabasePredictionRepository()
    return PredictionRepository(conn or get_db_connection())


def get_warning_repository(conn: Optional[sqlite3.Connection] = None) -> IWarningRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseWarningRepository()
    return WarningRepository(conn or get_db_connection())


def get_governance_repository(conn: Optional[sqlite3.Connection] = None) -> IGovernanceRepository:
    if settings.DATABASE_BACKEND == "supabase":
        return SupabaseGovernanceRepository()
    return GovernanceRepository(conn or get_db_connection())

