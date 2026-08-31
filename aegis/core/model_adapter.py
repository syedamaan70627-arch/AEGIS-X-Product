"""
AEGIS-X Scikit-Learn Model Adapter Module.

Provides a unified interface wrapper around user-supplied classification models.
Supports loading .joblib and .pkl files, capability inspection, and error handling.

SECURITY WARNING:
Deserializing .joblib or .pkl files uses Python pickle, which can execute arbitrary
code. Model files MUST only be loaded from trusted sources.
"""

from pathlib import Path
import pickle
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

from aegis.core.exceptions import (
    ModelLoadError,
    PredictionInterfaceError,
    UnsupportedModelError,
)


class SklearnModelAdapter:
    """
    Adapter for scikit-learn compatible classification models.

    Wraps an estimator loaded from a .joblib or .pkl file (or direct object)
    and exposes a unified, error-resilient prediction interface.
    """

    def __init__(self, raw_model: Any, source_path: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize the adapter with a pre-loaded model object.

        :param raw_model: Scikit-learn compatible model estimator.
        :param source_path: Optional file path from which the model was loaded.
        """
        self.raw_model = raw_model
        self.source_path = Path(source_path) if source_path else None

        self._verify_interface()

    @classmethod
    def load(cls, model_path: Union[str, Path]) -> "SklearnModelAdapter":
        """
        Safely load a scikit-learn model from a .joblib or .pkl file.

        SECURITY WARNING: Only load model files from trusted sources.

        :param model_path: Path to the .joblib or .pkl model file.
        :return: Initialized SklearnModelAdapter instance.
        :raises ModelLoadError: If file cannot be found, opened, or deserialized.
        :raises UnsupportedModelError: If loaded object lacks required ML interfaces.
        """
        path = Path(model_path)
        if not path.exists():
            raise ModelLoadError(f"Model file not found at path: '{path}'")

        if not path.is_file():
            raise ModelLoadError(f"Provided path is not a file: '{path}'")

        try:
            # Attempt joblib load first (handles both joblib and pickle formats)
            raw_model = joblib.load(path)
        except Exception as joblib_err:
            # Fallback to standard pickle load
            try:
                with open(path, "rb") as f:
                    raw_model = pickle.load(f)
            except Exception as pkl_err:
                raise ModelLoadError(
                    f"Failed to deserialize model file '{path}'. "
                    f"joblib error: '{joblib_err}'; pickle error: '{pkl_err}'."
                ) from pkl_err

        return cls(raw_model=raw_model, source_path=path)

    @classmethod
    def load_from_bytes(cls, content: bytes, source_name: Optional[str] = None) -> "SklearnModelAdapter":
        """
        Safely load a scikit-learn model from bytes buffer.

        SECURITY WARNING: Only load model content from trusted sources.

        :param content: Model file bytes (.joblib or .pkl format).
        :param source_name: Optional name for source tracking.
        :return: Initialized SklearnModelAdapter instance.
        :raises ModelLoadError: If bytes cannot be deserialized.
        :raises UnsupportedModelError: If loaded object lacks required ML interfaces.
        """
        import io
        buf = io.BytesIO(content)
        try:
            raw_model = joblib.load(buf)
        except Exception as joblib_err:
            buf.seek(0)
            try:
                raw_model = pickle.load(buf)
            except Exception as pkl_err:
                raise ModelLoadError(
                    f"Failed to deserialize model content. "
                    f"joblib error: '{joblib_err}'; pickle error: '{pkl_err}'."
                ) from pkl_err

        return cls(raw_model=raw_model, source_path=source_name)

    def _verify_interface(self) -> None:
        """Verify that the wrapped model satisfies AEGIS-X interface requirements."""
        if self.raw_model is None:
            raise UnsupportedModelError("Model object cannot be None.")

        if not hasattr(self.raw_model, "predict"):
            raise UnsupportedModelError(
                f"Model of type '{type(self.raw_model).__name__}' does not implement a 'predict()' method."
            )

        if not callable(getattr(self.raw_model, "predict")):
            raise UnsupportedModelError(
                f"Model attribute 'predict' on '{type(self.raw_model).__name__}' is not callable."
            )

    @property
    def supports_predict_proba(self) -> bool:
        """Check if the model supports probability estimation via predict_proba."""
        if not hasattr(self.raw_model, "predict_proba"):
            return False
        return callable(getattr(self.raw_model, "predict_proba"))

    @property
    def n_features_in(self) -> Optional[int]:
        """Return expected number of input features if exposed by the model."""
        if hasattr(self.raw_model, "n_features_in_"):
            try:
                return int(getattr(self.raw_model, "n_features_in_"))
            except (ValueError, TypeError):
                return None
        return None

    @property
    def classes(self) -> Optional[np.ndarray]:
        """Return target class labels if exposed by the model."""
        if hasattr(self.raw_model, "classes_"):
            cls_attr = getattr(self.raw_model, "classes_")
            if isinstance(cls_attr, (list, np.ndarray)):
                return np.asarray(cls_attr)
        return None

    @property
    def feature_names_in(self) -> Optional[List[str]]:
        """Return expected feature names if exposed by the model."""
        if hasattr(self.raw_model, "feature_names_in_"):
            names = getattr(self.raw_model, "feature_names_in_")
            if isinstance(names, (list, np.ndarray)):
                return [str(n) for n in names]
        return None

    def get_capabilities(self) -> Dict[str, Any]:
        """Return dictionary summarizing model capabilities and metadata."""
        return {
            "model_class": type(self.raw_model).__name__,
            "supports_predict_proba": self.supports_predict_proba,
            "n_features_in": self.n_features_in,
            "classes": self.classes.tolist() if self.classes is not None else None,
            "feature_names_in": self.feature_names_in,
            "source_path": str(self.source_path) if self.source_path else None,
        }

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Execute prediction on input feature matrix X.

        :param X: Feature matrix (numpy array or pandas DataFrame).
        :return: Predictions numpy array.
        :raises PredictionInterfaceError: If prediction call fails.
        """
        try:
            preds = self.raw_model.predict(X)
            return np.asarray(preds)
        except Exception as e:
            raise PredictionInterfaceError(
                f"Failed to execute predict() on model '{type(self.raw_model).__name__}': {e}"
            ) from e

    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Execute probability estimation on input feature matrix X.

        :param X: Feature matrix (numpy array or pandas DataFrame).
        :return: Probability matrix numpy array.
        :raises PredictionInterfaceError: If predict_proba is not supported or fails.
        """
        if not self.supports_predict_proba:
            raise PredictionInterfaceError(
                f"Model of type '{type(self.raw_model).__name__}' does not support predict_proba()."
            )

        try:
            probas = self.raw_model.predict_proba(X)
            return np.asarray(probas)
        except Exception as e:
            raise PredictionInterfaceError(
                f"Failed to execute predict_proba() on model '{type(self.raw_model).__name__}': {e}"
            ) from e
