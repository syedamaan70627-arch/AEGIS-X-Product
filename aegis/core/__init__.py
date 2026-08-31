"""
AEGIS-X Core Integration Module.
Contains user contracts, model adapters, CSV data loaders, validation engine, preprocessor, reference state, and analyzer.
"""

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.contracts import (
    AnalysisRequest,
    CoreReliabilityResult,
    DatasetRegistration,
    DatasetType,
    DriftResult,
    ModelRegistration,
    OODResult,
    ReliabilityStatus,
    TaskType,
    UncertaintyResult,
    ValidatedInput,
    ValidationReport,
)
from aegis.core.data_loader import CSVDataLoader, LoadedDataset
from aegis.core.exceptions import (
    AegisError,
    DatasetValidationError,
    FeatureMismatchError,
    ModelLoadError,
    PredictionInterfaceError,
    UnsupportedModelError,
)
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.core.preprocessing import FeaturePreprocessor
from aegis.core.reference_state import ReferenceState
from aegis.core.validator import IntegrationValidator

__all__ = [
    "TaskType",
    "DatasetType",
    "ModelRegistration",
    "DatasetRegistration",
    "AnalysisRequest",
    "ValidatedInput",
    "ValidationReport",
    "ReliabilityStatus",
    "OODResult",
    "UncertaintyResult",
    "DriftResult",
    "CoreReliabilityResult",
    "AegisError",
    "ModelLoadError",
    "UnsupportedModelError",
    "DatasetValidationError",
    "FeatureMismatchError",
    "PredictionInterfaceError",
    "SklearnModelAdapter",
    "CSVDataLoader",
    "LoadedDataset",
    "IntegrationValidator",
    "FeaturePreprocessor",
    "ReferenceState",
    "CoreReliabilityAnalyzer",
]
