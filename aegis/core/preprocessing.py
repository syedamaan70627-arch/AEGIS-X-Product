"""
AEGIS-X Preprocessing Module.

Provides input-copy safe feature normalization and realignment utilities for
AEGIS-X reliability engines.
"""

from typing import List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from aegis.core.exceptions import DatasetValidationError


class FeaturePreprocessor:
    """
    Standardizes feature vectors and enforces schema consistency without mutating
    input data structures.
    """

    def __init__(self, feature_names: Optional[List[str]] = None) -> None:
        self.feature_names: Optional[List[str]] = feature_names
        self.scaler: StandardScaler = StandardScaler()
        self.is_fitted: bool = False

    def _to_numpy_copy(
        self, data: Union[pd.DataFrame, np.ndarray]
    ) -> Tuple[np.ndarray, List[str]]:
        """Converts input data structure into a copy of numpy ndarray and extracts feature names."""
        if isinstance(data, pd.DataFrame):
            df_copy = data.copy(deep=True)
            cols = list(df_copy.columns)
            if self.feature_names is not None:
                # Validate and reorder if needed
                missing = set(self.feature_names) - set(cols)
                if missing:
                    raise DatasetValidationError(
                        f"Input DataFrame is missing required features: {sorted(list(missing))}"
                    )
                df_copy = df_copy[self.feature_names]
                cols = self.feature_names
            return df_copy.to_numpy(dtype=np.float64, copy=True), cols
        elif isinstance(data, np.ndarray):
            arr_copy = np.array(data, dtype=np.float64, copy=True)
            if arr_copy.ndim == 1:
                arr_copy = arr_copy.reshape(1, -1)
            cols = (
                self.feature_names
                if self.feature_names is not None
                else [f"feature_{i}" for i in range(arr_copy.shape[1])]
            )
            return arr_copy, cols
        else:
            raise DatasetValidationError(
                f"Unsupported data type for feature preprocessing: {type(data)}"
            )

    def fit(self, data: Union[pd.DataFrame, np.ndarray]) -> "FeaturePreprocessor":
        """Fits the StandardScaler on reference feature data without modifying input."""
        X_copy, cols = self._to_numpy_copy(data)
        if self.feature_names is None:
            self.feature_names = cols

        if X_copy.shape[0] == 0:
            raise DatasetValidationError("Cannot fit preprocessor on an empty feature array.")

        self.scaler.fit(X_copy)
        self.is_fitted = True
        return self

    def transform(self, data: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Transforms evaluation data using the fitted scaler."""
        if not self.is_fitted:
            raise DatasetValidationError("FeaturePreprocessor must be fitted before calling transform().")

        X_copy, cols = self._to_numpy_copy(data)
        if X_copy.shape[1] != self.scaler.n_features_in_:
            raise DatasetValidationError(
                f"Feature dimension mismatch: expected {self.scaler.n_features_in_} features, "
                f"got {X_copy.shape[1]}."
            )

        return self.scaler.transform(X_copy)

    def fit_transform(self, data: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Fits preprocessor and returns transformed data array."""
        self.fit(data)
        return self.transform(data)
