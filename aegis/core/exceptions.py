"""
AEGIS-X Custom Exceptions Module.

Defines human-readable exception types for model loading, dataset validation,
feature schema checking, and prediction interface compatibility.
"""


class AegisError(Exception):
    """Base exception class for all AEGIS-X framework errors."""
    pass


class ModelLoadError(AegisError):
    """Raised when a user model file (.joblib or .pkl) cannot be found, opened, or deserialized."""
    pass


class UnsupportedModelError(AegisError):
    """Raised when a model object does not conform to expected V1 scikit-learn interfaces."""
    pass


class DatasetValidationError(AegisError):
    """Raised when a dataset CSV violates schema, format, missing column, or numerical requirements."""
    pass


class FeatureMismatchError(AegisError):
    """Raised when feature counts, names, or ordering mismatch between model, reference, or evaluation data."""
    pass


class PredictionInterfaceError(AegisError):
    """Raised when calling model predict() or predict_proba() fails or returns incompatible shapes."""
    pass
