"""
AEGIS-X Failure Memory Module.

Provides unsupervised failure signature clustering (Module 8R) and serializable memory artifacts.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from aegis.core.contracts import (
    FailureMemoryResult,
    FailureSignature,
    ReliabilityStatus,
)
from aegis.core.exceptions import DatasetValidationError
from aegis.failure_memory.signatures import ConditionProfileExtractor


class FailureMemory:
    """
    Failure Memory Engine for learning recurring reliability signature centroids
    and storing serialized memory artifacts.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state: int = random_state
        self.scaler: StandardScaler = StandardScaler()
        self.kmeans: Optional[KMeans] = None
        self.n_clusters: int = 3
        self.feature_names: List[str] = ConditionProfileExtractor.SIGNATURE_FEATURES
        self.distance_thresholds: Dict[int, float] = {}
        self.signatures: List[FailureSignature] = []
        self.is_fitted: bool = False
        self.quality_summary: Dict[str, Any] = {}

    def fit(
        self,
        profiles_df: pd.DataFrame,
        n_clusters: int = 3,
        random_state: Optional[int] = None,
    ) -> FailureMemoryResult:
        """
        Fits StandardScaler and KMeans on numerical condition profiles without using fault labels as inputs.
        """
        seed = random_state if random_state is not None else self.random_state
        self.n_clusters = n_clusters

        missing_cols = [col for col in self.feature_names if col not in profiles_df.columns]
        if missing_cols:
            raise DatasetValidationError(f"Condition profiles DataFrame missing required features: {missing_cols}")

        if len(profiles_df) < n_clusters:
            raise DatasetValidationError(
                f"Cannot fit FailureMemory with {len(profiles_df)} profiles for n_clusters={n_clusters}."
            )

        X_raw = profiles_df[self.feature_names].to_numpy(copy=True)

        # 1. Fit scaler & transform
        X_scaled = self.scaler.fit_transform(X_raw)

        # 2. Fit KMeans model
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
        cluster_labels = self.kmeans.fit_predict(X_scaled)

        # 3. Calculate distance thresholds per cluster (95th percentile)
        distances_to_centroids = self.kmeans.transform(X_scaled)
        self.distance_thresholds = {}
        for cid in range(n_clusters):
            mask = (cluster_labels == cid)
            if np.any(mask):
                cid_dists = distances_to_centroids[mask, cid]
                thresh = float(np.percentile(cid_dists, 95)) if len(cid_dists) > 1 else float(np.max(cid_dists) * 1.2 + 1e-5)
                self.distance_thresholds[cid] = thresh
            else:
                self.distance_thresholds[cid] = 1.0

        # 4. Calculate clustering quality metrics
        sil_score: Optional[float] = None
        if len(np.unique(cluster_labels)) > 1 and len(X_scaled) > n_clusters:
            sil_score = float(silhouette_score(X_scaled, cluster_labels))

        # Calculate stability ARI across 10 random seeds
        ari_scores = []
        for s_idx in range(10):
            test_km = KMeans(n_clusters=n_clusters, random_state=seed + s_idx + 1, n_init=5)
            t_labels = test_km.fit_predict(X_scaled)
            ari_scores.append(float(adjusted_rand_score(cluster_labels, t_labels)))
        stability_ari = float(np.mean(ari_scores))

        # 5. Construct FailureSignature objects
        self.signatures = []
        centroids_scaled = self.kmeans.cluster_centers_
        centroids_unscaled = self.scaler.inverse_transform(centroids_scaled)

        group_keys = profiles_df["group_key"].to_numpy() if "group_key" in profiles_df.columns else None

        for cid in range(n_clusters):
            cnt = int(np.sum(cluster_labels == cid))
            centroid_dict = {
                fname: float(centroids_unscaled[cid, f_idx])
                for f_idx, fname in enumerate(self.feature_names)
            }

            fault_dist: Dict[str, float] = {}
            if group_keys is not None:
                c_groups = group_keys[cluster_labels == cid]
                if len(c_groups) > 0:
                    unique_g, g_counts = np.unique(c_groups, return_counts=True)
                    fault_dist = {str(g): float(c / len(c_groups)) for g, c in zip(unique_g, g_counts)}

            sig = FailureSignature(
                signature_id=cid,
                centroid_profile=centroid_dict,
                feature_names=self.feature_names,
                sample_count=cnt,
                distance_threshold=self.distance_thresholds.get(cid, 1.0),
                associated_fault_distribution=fault_dist,
                confidence=float(cnt / len(profiles_df)),
                warnings=[],
                limitations=[
                    "Failure signatures represent unsupervised reliability profiles.",
                    "Signatures are recurring empirical patterns, NOT confirmed causal root causes.",
                ],
            )
            self.signatures.append(sig)

        self.is_fitted = True
        self.quality_summary = {
            "n_clusters": n_clusters,
            "n_profiles": len(profiles_df),
            "silhouette_score": sil_score,
            "stability_ari": stability_ari,
            "feature_names": self.feature_names,
        }

        return FailureMemoryResult(
            status=ReliabilityStatus.AVAILABLE,
            n_signatures=n_clusters,
            signatures=self.signatures,
            silhouette_score=sil_score,
            stability_ari=stability_ari,
            quality_summary=self.quality_summary,
            warnings=[],
            limitations=[
                "Failure Memory clusters recurring condition profiles without fault label inputs.",
                "Root-cause claims are strictly avoided; signatures represent associative reliability patterns.",
            ],
        )

    def save_artifact(self, directory_path: Union[str, Path]) -> None:
        """Saves fitted memory models and metadata to target directory."""
        if not self.is_fitted or self.kmeans is None:
            raise DatasetValidationError("Cannot save un-fitted FailureMemory.")

        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.scaler, dir_path / "failure_signature_scaler_refined.pkl")
        joblib.dump(self.kmeans, dir_path / "failure_signature_model_refined.pkl")

        metadata = {
            "n_clusters": self.n_clusters,
            "feature_names": self.feature_names,
            "distance_thresholds": self.distance_thresholds,
            "quality_summary": self.quality_summary,
            "signatures": [
                {
                    "signature_id": sig.signature_id,
                    "centroid_profile": sig.centroid_profile,
                    "sample_count": sig.sample_count,
                    "distance_threshold": sig.distance_threshold,
                    "associated_fault_distribution": sig.associated_fault_distribution,
                }
                for sig in self.signatures
            ],
        }

        with open(dir_path / "failure_memory_refined.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_artifact(self, directory_path: Union[str, Path]) -> "FailureMemory":
        """Loads pre-fitted memory models and metadata from target directory."""
        dir_path = Path(directory_path)

        scaler_path = dir_path / "failure_signature_scaler_refined.pkl"
        kmeans_path = dir_path / "failure_signature_model_refined.pkl"
        json_path = dir_path / "failure_memory_refined.json"

        if not (scaler_path.exists() and kmeans_path.exists() and json_path.exists()):
            raise DatasetValidationError(f"Missing required FailureMemory artifacts in {dir_path}")

        self.scaler = joblib.load(scaler_path)
        self.kmeans = joblib.load(kmeans_path)

        with open(json_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.n_clusters = metadata["n_clusters"]
        self.feature_names = metadata["feature_names"]
        self.distance_thresholds = {int(k): float(v) for k, v in metadata["distance_thresholds"].items()}
        self.quality_summary = metadata.get("quality_summary", {})

        self.signatures = []
        for s_data in metadata.get("signatures", []):
            sig = FailureSignature(
                signature_id=s_data["signature_id"],
                centroid_profile=s_data["centroid_profile"],
                feature_names=self.feature_names,
                sample_count=s_data["sample_count"],
                distance_threshold=s_data["distance_threshold"],
                associated_fault_distribution=s_data.get("associated_fault_distribution", {}),
                limitations=[
                    "Failure signatures represent unsupervised reliability profiles.",
                    "Signatures are recurring empirical patterns, NOT confirmed causal root causes.",
                ],
            )
            self.signatures.append(sig)

        self.is_fitted = True
        return self
