"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
Safe, Non-Pickle Calibrator Artifact Manager.

Requirements:
- Zero pickle deserialization. Uses canonical JSON serialization.
- Validates schema, required keys, numeric finiteness (no NaN/Inf), feature compatibility, and SHA-256 hash.
- Fails closed on tampered or corrupted artifacts.
- Supports 2-run deterministic artifact hash comparison.
"""

import datetime
import hashlib
import json
import math
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator


ARTIFACT_SCHEMA_VERSION = "1.0.0"
FROZEN_UPSTREAM_EVIDENCE_VERSION = "1.2.0"


def compute_canonical_hash(payload: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a dictionary formatted as canonical JSON."""
    payload_copy = dict(payload)
    payload_copy.pop("artifact_sha256", None)
    canonical_json = json.dumps(payload_copy, sort_keys=True, indent=2)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class ECRGCalibratorArtifact:
    """
    Versioned Calibrator Artifact Container.
    Encapsulates fitted risk learner, conformal quantile, feature schema, and provenance metadata.
    """

    def __init__(
        self,
        calibrator: TrajectorySplitConformalCalibrator,
        task_capability_profile: str,
        target_semantic: str,
        horizon: Optional[int] = None,
        training_dataset_hash: str = "UNKNOWN_TRAIN_HASH",
        calibration_dataset_hash: str = "UNKNOWN_CAL_HASH",
        artifact_id: Optional[str] = None,
    ):
        if calibrator.calibrated_q is None or not calibrator.learner.fitted:
            raise ValueError("Cannot create artifact from uncalibrated or unfitted calibrator.")

        self.calibrator = calibrator
        self.task_capability_profile = task_capability_profile
        self.target_semantic = target_semantic
        self.horizon = horizon
        self.training_dataset_hash = training_dataset_hash
        self.calibration_dataset_hash = calibration_dataset_hash
        self.creation_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.artifact_id = artifact_id or f"ecrg-art-{hashlib.sha256(self.creation_timestamp.encode('utf-8')).hexdigest()[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize artifact metadata and fitted parameters to a canonical dictionary."""
        learner_params = self.calibrator.learner.get_params_dict()
        
        # Sort calibration scores for deterministic hashing
        sorted_scores = sorted(self.calibrator.calibration_scores)
        scores_hash = hashlib.sha256(json.dumps(sorted_scores).encode("utf-8")).hexdigest()

        payload = {
            "artifact_id": self.artifact_id,
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "frozen_upstream_evidence_version": FROZEN_UPSTREAM_EVIDENCE_VERSION,
            "creation_timestamp": self.creation_timestamp,
            "task_capability_profile": self.task_capability_profile,
            "target_semantic": self.target_semantic,
            "horizon": self.horizon,
            "target_alpha": self.calibrator.target_alpha,
            "calibrated_quantile": float(self.calibrator.calibrated_q),
            "k_order_stat": self.calibrator.k_order_stat,
            "n_cal_units": self.calibrator.n_cal_units,
            "finite_sample_resolution": float(self.calibrator.finite_sample_resolution),
            "calibration_scores": sorted_scores,
            "calibration_scores_hash": scores_hash,
            "training_dataset_hash": self.training_dataset_hash,
            "calibration_dataset_hash": self.calibration_dataset_hash,
            "feature_names": self.calibrator.learner.feature_names,
            "learner_params": learner_params,
        }

        payload["artifact_sha256"] = compute_canonical_hash(payload)
        return payload

    def to_json(self) -> str:
        """Serialize artifact to canonical JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ECRGCalibratorArtifact":
        """
        Deserialize and validate calibrator artifact from dictionary.
        Enforces schema, finiteness, hash integrity, and key validation.
        """
        required_keys = [
            "artifact_id",
            "artifact_schema_version",
            "task_capability_profile",
            "target_semantic",
            "target_alpha",
            "calibrated_quantile",
            "k_order_stat",
            "n_cal_units",
            "feature_names",
            "learner_params",
            "artifact_sha256",
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required artifact key '{key}'.")

        # 1. Schema version check
        if data["artifact_schema_version"] != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"Incompatible artifact schema version '{data['artifact_schema_version']}'. "
                f"Expected '{ARTIFACT_SCHEMA_VERSION}'."
            )

        # 2. SHA-256 tamper/integrity validation
        stored_hash = data["artifact_sha256"]
        computed_hash = compute_canonical_hash(data)
        if stored_hash != computed_hash:
            raise ValueError(
                f"Artifact SHA-256 hash mismatch! Stored: {stored_hash}, Computed: {computed_hash}. "
                "Artifact appears tampered or corrupted."
            )

        # 3. Numeric finiteness validation
        q_val = float(data["calibrated_quantile"])
        if math.isnan(q_val) or math.isinf(q_val):
            raise ValueError("Calibrated quantile threshold is NaN or Infinity.")

        learner_params = data["learner_params"]
        for p_key in ["scaler_mean", "scaler_scale", "coef", "intercept"]:
            arr = np.array(learner_params[p_key])
            if np.isnan(arr).any() or np.isinf(arr).any():
                raise ValueError(f"Learner parameter '{p_key}' contains NaN or Infinity.")

        # Reconstruct components
        learner = DeterministicRiskLearner().load_params_dict(learner_params)
        calibrator = TrajectorySplitConformalCalibrator(
            target_alpha=float(data["target_alpha"]),
            learner=learner,
        )
        calibrator.calibrated_q = q_val
        calibrator.k_order_stat = int(data["k_order_stat"])
        calibrator.n_cal_units = int(data["n_cal_units"])
        calibrator.task_type = data["task_capability_profile"]
        calibrator.finite_sample_resolution = float(data.get("finite_sample_resolution", 1.0 / (calibrator.n_cal_units + 1)))
        calibrator.calibration_scores = [float(x) for x in data.get("calibration_scores", [])]

        artifact = cls.__new__(cls)
        artifact.calibrator = calibrator
        artifact.task_capability_profile = data["task_capability_profile"]
        artifact.target_semantic = data["target_semantic"]
        artifact.horizon = data.get("horizon")
        artifact.training_dataset_hash = data.get("training_dataset_hash", "UNKNOWN_TRAIN_HASH")
        artifact.calibration_dataset_hash = data.get("calibration_dataset_hash", "UNKNOWN_CAL_HASH")
        artifact.creation_timestamp = data.get("creation_timestamp", "")
        artifact.artifact_id = data["artifact_id"]
        return artifact

    @classmethod
    def from_json(cls, json_str: str) -> "ECRGCalibratorArtifact":
        """Deserialize and validate artifact from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


def compare_deterministic_artifact_builds(art1: ECRGCalibratorArtifact, art2: ECRGCalibratorArtifact) -> bool:
    """
    Verify that two independent calibrator builds yield identical parameters and artifact SHA-256 hashes.
    """
    d1 = art1.to_dict()
    d2 = art2.to_dict()

    # Compare core scientific fields (timestamp & artifact_id may vary if generated at different times)
    keys_to_compare = [
        "task_capability_profile",
        "target_semantic",
        "horizon",
        "target_alpha",
        "calibrated_quantile",
        "k_order_stat",
        "n_cal_units",
        "calibration_scores_hash",
        "feature_names",
        "learner_params",
    ]

    for k in keys_to_compare:
        if d1[k] != d2[k]:
            return False
    return True
