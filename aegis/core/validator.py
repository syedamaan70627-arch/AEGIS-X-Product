"""
AEGIS-X Integration Validator Engine Module.

Verifies strict compatibility between user classification models, reference datasets,
and evaluation datasets without altering scientific data values.
"""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from aegis.core.contracts import (
    DatasetRegistration,
    ModelRegistration,
    TaskType,
    ValidatedInput,
    ValidationReport,
)
from aegis.core.data_loader import LoadedDataset
from aegis.core.exceptions import (
    DatasetValidationError,
    FeatureMismatchError,
    PredictionInterfaceError,
)
from aegis.core.model_adapter import SklearnModelAdapter


class IntegrationValidator:
    """
    Validation engine that enforces compatibility contracts across Model,
    Reference Dataset, and Evaluation Dataset for AEGIS-X.
    """

    @classmethod
    def validate(
        cls,
        model_adapter: SklearnModelAdapter,
        reference_dataset: LoadedDataset,
        evaluation_dataset: LoadedDataset,
        task_type: TaskType = TaskType.BINARY_CLASSIFICATION,
    ) -> ValidationReport:
        """
        Validate model adapter and datasets against AEGIS-X compatibility requirements.

        :param model_adapter: Initialized SklearnModelAdapter.
        :param reference_dataset: LoadedDataset for baseline reference data.
        :param evaluation_dataset: LoadedDataset for new evaluation data.
        :param task_type: Expected TaskType (BINARY or MULTICLASS).
        :return: Structured ValidationReport object.
        """
        errors: List[str] = []
        warnings: List[str] = []
        details: dict = {}

        # 1. Check feature count parity between reference and evaluation
        if reference_dataset.num_features != evaluation_dataset.num_features:
            errors.append(
                f"Feature count mismatch: reference dataset has {reference_dataset.num_features} features, "
                f"but evaluation dataset has {evaluation_dataset.num_features} features."
            )

        # 2. Check feature names parity
        ref_features = reference_dataset.feature_names
        eval_features = evaluation_dataset.feature_names

        ref_set = set(ref_features)
        eval_set = set(eval_features)

        if ref_set != eval_set:
            missing_in_eval = list(ref_set - eval_set)
            missing_in_ref = list(eval_set - ref_set)
            errors.append(
                f"Feature schema mismatch between reference and evaluation datasets. "
                f"Missing in evaluation: {missing_in_eval}; Missing in reference: {missing_in_ref}."
            )

        # 3. Check feature ordering alignment
        if ref_set == eval_set and ref_features != eval_features:
            warnings.append(
                "Evaluation dataset column order differs from reference dataset. "
                "Feature columns will be aligned to reference ordering."
            )

        # 4. Check model expected feature count (if available on model)
        if model_adapter.n_features_in is not None:
            if model_adapter.n_features_in != reference_dataset.num_features:
                errors.append(
                    f"Model expects {model_adapter.n_features_in} features (n_features_in_), "
                    f"but dataset provides {reference_dataset.num_features} features."
                )

        # 5. Check model expected feature names (if available on model)
        if model_adapter.feature_names_in is not None:
            model_feat_set = set(model_adapter.feature_names_in)
            missing_model_feats = list(model_feat_set - ref_set)
            if missing_model_feats:
                errors.append(
                    f"Model requires features {missing_model_feats} which are missing from input dataset."
                )

        # 6. Check evaluation dataset is non-empty
        if evaluation_dataset.num_samples == 0:
            errors.append("Evaluation dataset is empty (0 samples).")

        if reference_dataset.num_samples == 0:
            errors.append("Reference dataset is empty (0 samples).")

        # 7. Optional target column handling
        if reference_dataset.y is None:
            warnings.append("Reference dataset has no target label column. Operating in label-free mode.")
        if evaluation_dataset.y is None:
            warnings.append("Evaluation dataset has no target label column. Operating in label-free mode.")

        # If errors present up to this point, skip execution smoke test
        if errors:
            return ValidationReport(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                details=details,
            )

        # Align evaluation feature order to reference dataset feature order
        X_ref = reference_dataset.X
        X_eval = evaluation_dataset.X[ref_features]

        # 8. Smoke test predict() on a tiny validated sample
        sample_size = min(5, len(X_ref))
        tiny_sample = X_ref.iloc[:sample_size]

        try:
            sample_preds = model_adapter.predict(tiny_sample)
            details["sample_predictions_head"] = sample_preds.tolist()
        except Exception as e:
            errors.append(f"Model predict() smoke test failed on validated data sample: {e}")

        # 9. Smoke test predict_proba() when supported
        if model_adapter.supports_predict_proba:
            try:
                sample_probas = model_adapter.predict_proba(tiny_sample)
                details["supports_predict_proba"] = True
                details["proba_shape"] = list(sample_probas.shape)

                if model_adapter.classes is not None:
                    if sample_probas.shape[1] != len(model_adapter.classes):
                        errors.append(
                            f"predict_proba output column count ({sample_probas.shape[1]}) "
                            f"does not match model classes count ({len(model_adapter.classes)})."
                        )
            except Exception as e:
                errors.append(f"Model predict_proba() smoke test failed: {e}")
        else:
            details["supports_predict_proba"] = False
            warnings.append("Model does not support predict_proba(). Confidence-based analysis will be restricted.")

        # 10. Check binary/multiclass task type consistency
        if model_adapter.classes is not None:
            num_classes = len(model_adapter.classes)
            details["num_classes"] = num_classes
            if task_type == TaskType.BINARY_CLASSIFICATION and num_classes > 2:
                errors.append(
                    f"TaskType specified as BINARY_CLASSIFICATION, but model contains {num_classes} classes."
                )
            elif task_type == TaskType.MULTICLASS_CLASSIFICATION and num_classes <= 2:
                warnings.append(
                    f"TaskType specified as MULTICLASS_CLASSIFICATION, but model contains only {num_classes} classes."
                )

        is_valid = len(errors) == 0
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            details=details,
        )

    @classmethod
    def validate_and_build(
        cls,
        model_adapter: SklearnModelAdapter,
        reference_dataset: LoadedDataset,
        evaluation_dataset: LoadedDataset,
        task_type: TaskType = TaskType.BINARY_CLASSIFICATION,
    ) -> ValidatedInput:
        """
        Validate input compatibility and return a ready ValidatedInput container.

        :raises FeatureMismatchError: If feature schemas or counts mismatch.
        :raises DatasetValidationError: If validation fails for other dataset/model reasons.
        """
        report = cls.validate(
            model_adapter=model_adapter,
            reference_dataset=reference_dataset,
            evaluation_dataset=evaluation_dataset,
            task_type=task_type,
        )

        if not report.is_valid:
            error_str = " | ".join(report.errors)
            if "Feature" in error_str:
                raise FeatureMismatchError(f"Integration validation failed due to feature mismatch: {error_str}")
            raise DatasetValidationError(f"Integration validation failed: {error_str}")

        # Safely align feature column ordering of evaluation matrix to reference feature order
        X_ref = reference_dataset.X
        X_eval = evaluation_dataset.X[reference_dataset.feature_names]

        return ValidatedInput(
            model_adapter=model_adapter,
            X_reference=X_ref,
            y_reference=reference_dataset.y,
            X_evaluation=X_eval,
            y_evaluation=evaluation_dataset.y,
            feature_names=reference_dataset.feature_names,
            task_type=task_type,
            report=report,
        )
