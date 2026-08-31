"""
AEGIS-X Integration Contract Automated Test Suite.

NOTE ON TEST FIXTURES:
`sklearn.datasets.make_classification` is used ONLY as a temporary software test fixture
to generate dummy model artifacts during automated software testing. It is strictly a testing
utility and MUST NOT be interpreted or described as a new AEGIS-X research dataset.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pickle
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier

from aegis.core.contracts import (
    DatasetRegistration,
    DatasetType,
    ModelRegistration,
    TaskType,
)
from aegis.core.data_loader import CSVDataLoader, LoadedDataset
from aegis.core.exceptions import (
    DatasetValidationError,
    FeatureMismatchError,
    ModelLoadError,
    PredictionInterfaceError,
    UnsupportedModelError,
)
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.core.validator import IntegrationValidator


class DummyNonPredictModel:
    """Class lacking predict() for testing interface verification."""
    pass


class DummyCallablePredictModel:
    """Minimal model implementing predict but not predict_proba."""
    def predict(self, X):
        return np.zeros(len(X))


class TestAEGISXIntegrationContract(unittest.TestCase):
    """Test suite verifying ModelAdapter, CSVDataLoader, and IntegrationValidator."""

    def setUp(self) -> None:
        """Create temporary directory for isolated test artifacts."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Generate temporary classification data fixture for software test setup
        X_mat, y_vec = make_classification(
            n_samples=100,
            n_features=5,
            n_informative=3,
            n_classes=2,
            random_state=42,
        )
        self.feature_names = [f"feature_{i}" for i in range(5)]
        self.df = pd.DataFrame(X_mat, columns=self.feature_names)
        self.df["target"] = y_vec

        # Train a sample model for test loading (using DataFrame to preserve feature names)
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.model.fit(self.df[self.feature_names], y_vec)

        # Save model in joblib and pkl formats
        self.joblib_model_path = self.temp_path / "model.joblib"
        self.pkl_model_path = self.temp_path / "model.pkl"
        joblib.dump(self.model, self.joblib_model_path)
        with open(self.pkl_model_path, "wb") as f:
            pickle.dump(self.model, f)

        # Save reference and evaluation CSV files
        self.ref_csv_path = self.temp_path / "reference.csv"
        self.eval_csv_path = self.temp_path / "evaluation.csv"
        self.df.to_csv(self.ref_csv_path, index=False)
        self.df.drop(columns=["target"]).to_csv(self.eval_csv_path, index=False)

    def tearDown(self) -> None:
        """Clean up temporary directory after each test."""
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # ModelAdapter Tests
    # -------------------------------------------------------------------------

    def test_valid_model_loading_joblib(self) -> None:
        """Test loading model from valid .joblib file."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        self.assertIsNotNone(adapter.raw_model)
        self.assertTrue(adapter.supports_predict_proba)
        self.assertEqual(adapter.n_features_in, 5)

    def test_valid_model_loading_pkl(self) -> None:
        """Test loading model from valid .pkl file."""
        adapter = SklearnModelAdapter.load(self.pkl_model_path)
        self.assertIsNotNone(adapter.raw_model)
        self.assertTrue(adapter.supports_predict_proba)

    def test_invalid_model_path(self) -> None:
        """Test error handling when loading model from non-existent path."""
        non_existent = self.temp_path / "non_existent_model.joblib"
        with self.assertRaises(ModelLoadError):
            SklearnModelAdapter.load(non_existent)

    def test_invalid_model_file_content(self) -> None:
        """Test error handling when model file is corrupted/invalid."""
        corrupted_path = self.temp_path / "corrupted.joblib"
        with open(corrupted_path, "w") as f:
            f.write("not a binary model file")

        with self.assertRaises(ModelLoadError):
            SklearnModelAdapter.load(corrupted_path)

    def test_unsupported_model_interface(self) -> None:
        """Test that objects lacking predict() raise UnsupportedModelError."""
        dummy_obj = DummyNonPredictModel()
        with self.assertRaises(UnsupportedModelError):
            SklearnModelAdapter(raw_model=dummy_obj)

    def test_predict_capability(self) -> None:
        """Test model predict() method execution."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        preds = adapter.predict(self.df[self.feature_names])
        self.assertEqual(len(preds), 100)
        self.assertTrue(set(np.unique(preds)).issubset({0, 1}))

    def test_predict_proba_detection_and_execution(self) -> None:
        """Test detection and execution of predict_proba()."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        self.assertTrue(adapter.supports_predict_proba)

        probas = adapter.predict_proba(self.df[self.feature_names])
        self.assertEqual(probas.shape, (100, 2))

    def test_unsupported_predict_proba(self) -> None:
        """Test adapter behavior when wrapped model lacks predict_proba."""
        dummy_model = DummyCallablePredictModel()
        adapter = SklearnModelAdapter(raw_model=dummy_model)

        self.assertFalse(adapter.supports_predict_proba)
        with self.assertRaises(PredictionInterfaceError):
            adapter.predict_proba(self.df[self.feature_names])

    # -------------------------------------------------------------------------
    # DataLoader Tests
    # -------------------------------------------------------------------------

    def test_csv_loading_with_target(self) -> None:
        """Test loading CSV dataset with target column specified."""
        loaded = CSVDataLoader.load(self.ref_csv_path, target_column="target")
        self.assertEqual(loaded.num_samples, 100)
        self.assertEqual(loaded.num_features, 5)
        self.assertListEqual(loaded.feature_names, self.feature_names)
        self.assertIsNotNone(loaded.y)
        self.assertEqual(len(loaded.y), 100)

    def test_csv_loading_without_target(self) -> None:
        """Test loading CSV dataset in label-free mode (no target column)."""
        loaded = CSVDataLoader.load(self.eval_csv_path, target_column=None)
        self.assertEqual(loaded.num_samples, 100)
        self.assertEqual(loaded.num_features, 5)
        self.assertIsNone(loaded.y)

    def test_invalid_csv_path(self) -> None:
        """Test error handling when dataset file path does not exist."""
        non_existent = self.temp_path / "non_existent.csv"
        with self.assertRaises(DatasetValidationError):
            CSVDataLoader.load(non_existent)

    def test_empty_csv_file(self) -> None:
        """Test error handling when loading an empty CSV file."""
        empty_csv = self.temp_path / "empty.csv"
        with open(empty_csv, "w") as f:
            f.write("")

        with self.assertRaises(DatasetValidationError):
            CSVDataLoader.load(empty_csv)

    def test_missing_target_column_raises_error(self) -> None:
        """Test error when specified target column does not exist in CSV."""
        with self.assertRaises(DatasetValidationError):
            CSVDataLoader.load(self.ref_csv_path, target_column="non_existent_target")

    def test_duplicate_column_names_raises_error(self) -> None:
        """Test error when CSV header contains duplicate column names."""
        dup_df = pd.DataFrame([[1, 2, 3]], columns=["f1", "f1", "f2"])
        dup_csv = self.temp_path / "duplicate_cols.csv"
        dup_df.to_csv(dup_csv, index=False)

        with self.assertRaises(DatasetValidationError):
            CSVDataLoader.load(dup_csv)

    def test_non_numeric_features_raises_error(self) -> None:
        """Test that non-numeric columns in feature matrix trigger DatasetValidationError."""
        bad_df = self.df.copy()
        bad_df["feature_0"] = "categorical_string_value"
        bad_csv = self.temp_path / "non_numeric.csv"
        bad_df.to_csv(bad_csv, index=False)

        with self.assertRaises(DatasetValidationError):
            CSVDataLoader.load(bad_csv)

    # -------------------------------------------------------------------------
    # IntegrationValidator Tests
    # -------------------------------------------------------------------------

    def test_successful_integration_validation(self) -> None:
        """Test end-to-end validation of compatible model, ref, and eval datasets."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        ref_ds = CSVDataLoader.load(self.ref_csv_path, target_column="target")
        eval_ds = CSVDataLoader.load(self.eval_csv_path, target_column=None)

        report = IntegrationValidator.validate(
            model_adapter=adapter,
            reference_dataset=ref_ds,
            evaluation_dataset=eval_ds,
            task_type=TaskType.BINARY_CLASSIFICATION,
        )

        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.errors), 0)

        # Validate build container creation
        validated_input = IntegrationValidator.validate_and_build(
            model_adapter=adapter,
            reference_dataset=ref_ds,
            evaluation_dataset=eval_ds,
            task_type=TaskType.BINARY_CLASSIFICATION,
        )
        self.assertEqual(validated_input.X_reference.shape, (100, 5))
        self.assertEqual(validated_input.X_evaluation.shape, (100, 5))

    def test_feature_count_mismatch_validation(self) -> None:
        """Test validator detection when feature counts mismatch."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        ref_ds = CSVDataLoader.load(self.ref_csv_path, target_column="target")

        # Create evaluation dataset with 4 features instead of 5
        eval_4_df = self.df.drop(columns=["target", "feature_4"])
        eval_4_csv = self.temp_path / "eval_4.csv"
        eval_4_df.to_csv(eval_4_csv, index=False)
        eval_ds = CSVDataLoader.load(eval_4_csv)

        report = IntegrationValidator.validate(
            model_adapter=adapter,
            reference_dataset=ref_ds,
            evaluation_dataset=eval_ds,
        )

        self.assertFalse(report.is_valid)
        self.assertTrue(any("Feature count mismatch" in err for err in report.errors))

        with self.assertRaises(FeatureMismatchError):
            IntegrationValidator.validate_and_build(
                model_adapter=adapter,
                reference_dataset=ref_ds,
                evaluation_dataset=eval_ds,
            )

    def test_feature_name_mismatch_validation(self) -> None:
        """Test validator detection when feature names mismatch."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        ref_ds = CSVDataLoader.load(self.ref_csv_path, target_column="target")

        # Create evaluation dataset with a renamed feature
        eval_renamed_df = self.df.drop(columns=["target"]).rename(columns={"feature_0": "different_name"})
        eval_renamed_csv = self.temp_path / "eval_renamed.csv"
        eval_renamed_df.to_csv(eval_renamed_csv, index=False)
        eval_ds = CSVDataLoader.load(eval_renamed_csv)

        report = IntegrationValidator.validate(
            model_adapter=adapter,
            reference_dataset=ref_ds,
            evaluation_dataset=eval_ds,
        )

        self.assertFalse(report.is_valid)
        self.assertTrue(any("Feature schema mismatch" in err for err in report.errors))

    def test_feature_ordering_realignment(self) -> None:
        """Test that validator aligns evaluation feature ordering when names match."""
        adapter = SklearnModelAdapter.load(self.joblib_model_path)
        ref_ds = CSVDataLoader.load(self.ref_csv_path, target_column="target")

        # Reorder evaluation columns
        reordered_cols = ["feature_4", "feature_0", "feature_2", "feature_1", "feature_3"]
        eval_reordered_df = self.df[reordered_cols].copy()
        eval_reordered_csv = self.temp_path / "eval_reordered.csv"
        eval_reordered_df.to_csv(eval_reordered_csv, index=False)
        eval_ds = CSVDataLoader.load(eval_reordered_csv)

        validated_input = IntegrationValidator.validate_and_build(
            model_adapter=adapter,
            reference_dataset=ref_ds,
            evaluation_dataset=eval_ds,
        )

        # Confirm evaluation columns aligned to reference ordering
        self.assertListEqual(list(validated_input.X_evaluation.columns), self.feature_names)


if __name__ == "__main__":
    unittest.main()
