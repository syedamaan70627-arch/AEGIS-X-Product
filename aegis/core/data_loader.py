"""
AEGIS-X CSV Data Loader Module.

Provides robust loading and schema validation for CSV tabular datasets.
Ensures numeric feature integrity, column name uniqueness, target separation,
and domain-agnostic feature preservation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError


@dataclass
class LoadedDataset:
    """Container holding loaded feature matrix, optional target vector, and dataset metadata."""
    X: pd.DataFrame
    y: Optional[pd.Series]
    feature_names: List[str]
    target_column: Optional[str]
    num_samples: int
    num_features: int
    dtypes: Dict[str, str] = field(default_factory=dict)
    source_path: Optional[str] = None

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata summary for registration records."""
        return {
            "num_samples": self.num_samples,
            "num_features": self.num_features,
            "feature_names": self.feature_names,
            "has_target": self.y is not None,
            "target_column": self.target_column,
            "dtypes": self.dtypes,
            "source_path": self.source_path,
        }


class CSVDataLoader:
    """
    DataLoader for tabular CSV files in AEGIS-X Version 1.

    Loads CSV datasets, enforces feature preservation, separates target columns,
    validates numerical feature dtypes, and rejects empty or malformed files.
    """

    @classmethod
    def load(
        cls,
        csv_path: Union[str, Path],
        target_column: Optional[str] = None,
    ) -> LoadedDataset:
        """
        Load and validate a CSV dataset.

        :param csv_path: Path to the CSV file.
        :param target_column: Optional name of the label/target column.
        :return: LoadedDataset instance containing features X, target y, and metadata.
        :raises DatasetValidationError: If file is missing, empty, or contains non-numeric features.
        """
        path = Path(csv_path)

        if not path.exists():
            raise DatasetValidationError(f"Dataset CSV file not found at path: '{path}'")

        if not path.is_file():
            raise DatasetValidationError(f"Provided dataset path is not a file: '{path}'")

        try:
            # Read first line to inspect exact CSV header before pandas auto-mangles duplicate columns
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                first_line = f.readline().strip()

            if not first_line:
                raise DatasetValidationError(f"Dataset CSV '{path}' is empty (0 rows or 0 columns).")

            import csv
            import io
            header_cols = next(csv.reader(io.StringIO(first_line)))
            seen = set()
            duplicates = set()
            for col in header_cols:
                if col in seen:
                    duplicates.add(col)
                seen.add(col)

            if duplicates:
                raise DatasetValidationError(
                    f"Dataset CSV '{path}' contains duplicate column names in header: {sorted(list(duplicates))}"
                )

            df = pd.read_csv(path)
        except DatasetValidationError:
            raise
        except Exception as e:
            raise DatasetValidationError(f"Failed to parse CSV file '{path}': {e}") from e

        # Handle target column separation if specified
        y: Optional[pd.Series] = None
        if target_column is not None:
            if target_column not in df.columns:
                raise DatasetValidationError(
                    f"Specified target column '{target_column}' not found in CSV columns: {list(df.columns)}"
                )
            y = df[target_column].copy()
            X = df.drop(columns=[target_column]).copy()
        else:
            X = df.copy()

        if X.shape[1] == 0:
            raise DatasetValidationError(
                f"Dataset CSV '{path}' contains no feature columns after removing target '{target_column}'."
            )

        feature_names = list(X.columns)

        # Validate non-numeric feature types for V1 tabular requirement
        non_numeric_cols = []
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                non_numeric_cols.append(col)

        if non_numeric_cols:
            raise DatasetValidationError(
                f"AEGIS-X Version 1 requires strictly numeric features. "
                f"The following feature columns in '{path}' contain non-numeric types: {non_numeric_cols}"
            )

        dtypes = {col: str(dtype) for col, dtype in X.dtypes.items()}

        return LoadedDataset(
            X=X,
            y=y,
            feature_names=feature_names,
            target_column=target_column,
            num_samples=len(X),
            num_features=len(feature_names),
            dtypes=dtypes,
            source_path=str(path),
        )

    @classmethod
    def load_from_bytes(
        cls,
        content: bytes,
        target_column: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> LoadedDataset:
        """
        Load and validate a CSV dataset from raw bytes.

        :param content: CSV file content as bytes.
        :param target_column: Optional name of the label/target column.
        :param source_name: Optional name for source tracking.
        :return: LoadedDataset instance containing features X, target y, and metadata.
        :raises DatasetValidationError: If file content is empty or contains non-numeric features.
        """
        import io
        import csv

        if not content:
            raise DatasetValidationError("Dataset CSV content is empty.")

        text_content = content.decode("utf-8", errors="replace")
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        if not lines:
            raise DatasetValidationError("Dataset CSV content contains 0 non-empty lines.")

        first_line = lines[0]
        header_cols = next(csv.reader(io.StringIO(first_line)))
        seen = set()
        duplicates = set()
        for col in header_cols:
            if col in seen:
                duplicates.add(col)
            seen.add(col)

        if duplicates:
            raise DatasetValidationError(
                f"Dataset CSV contains duplicate column names in header: {sorted(list(duplicates))}"
            )

        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise DatasetValidationError(f"Failed to parse CSV bytes: {e}") from e

        # Handle target column separation if specified
        y: Optional[pd.Series] = None
        if target_column is not None:
            if target_column not in df.columns:
                raise DatasetValidationError(
                    f"Specified target column '{target_column}' not found in CSV columns: {list(df.columns)}"
                )
            y = df[target_column].copy()
            X = df.drop(columns=[target_column]).copy()
        else:
            X = df.copy()

        if X.shape[1] == 0:
            raise DatasetValidationError(
                f"Dataset CSV contains no feature columns after removing target '{target_column}'."
            )

        feature_names = list(X.columns)

        # Validate non-numeric feature types
        non_numeric_cols = []
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                non_numeric_cols.append(col)

        if non_numeric_cols:
            raise DatasetValidationError(
                f"AEGIS-X Version 1 requires strictly numeric features. "
                f"The following feature columns contain non-numeric types: {non_numeric_cols}"
            )

        dtypes = {col: str(dtype) for col, dtype in X.dtypes.items()}

        return LoadedDataset(
            X=X,
            y=y,
            feature_names=feature_names,
            target_column=target_column,
            num_samples=len(X),
            num_features=len(feature_names),
            dtypes=dtypes,
            source_path=source_name,
        )
