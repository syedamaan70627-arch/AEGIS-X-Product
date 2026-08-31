"""
AEGIS-X Failure Memory Matcher Module.

Matches new incoming condition profiles against pre-fitted Failure Memory centroids
without re-fitting or query-time leakage.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from aegis.core.contracts import SignatureMatchResult
from aegis.core.exceptions import DatasetValidationError
from aegis.failure_memory.memory import FailureMemory


class FailureMemoryMatcher:
    """
    Matcher Engine for querying pre-fitted Failure Memory centroids with incoming reliability profiles.
    """

    @staticmethod
    def match(
        query_profile: Union[pd.DataFrame, pd.Series, Dict[str, float], np.ndarray],
        memory: FailureMemory,
    ) -> SignatureMatchResult:
        """
        Matches a query profile against pre-fitted Failure Memory centroids.
        Never refits memory or mutates memory state during query.
        """
        if not memory.is_fitted or memory.kmeans is None:
            raise DatasetValidationError("Cannot match against an un-fitted FailureMemory instance.")

        feature_names = memory.feature_names

        # Convert query profile to 2D numpy array with correct feature order
        if isinstance(query_profile, dict):
            q_vec = np.array([[query_profile.get(fn, 0.0) for fn in feature_names]], dtype=np.float64)
        elif isinstance(query_profile, pd.Series):
            q_vec = np.array([[query_profile.get(fn, 0.0) for fn in feature_names]], dtype=np.float64)
        elif isinstance(query_profile, pd.DataFrame):
            # Ensure correct column ordering
            q_vec = query_profile[feature_names].to_numpy(copy=True)
            if len(q_vec) > 1:
                q_vec = np.mean(q_vec, axis=0, keepdims=True)
        elif isinstance(query_profile, np.ndarray):
            q_vec = np.atleast_2d(np.array(query_profile, copy=True, dtype=np.float64))
            if q_vec.shape[1] != len(feature_names):
                raise DatasetValidationError(
                    f"Query feature dimension mismatch: expected {len(feature_names)}, got {q_vec.shape[1]}."
                )
        else:
            raise DatasetValidationError(f"Unsupported query profile type: {type(query_profile)}")

        # 1. Apply pre-fitted scaler (NO query-time re-fitting / leakage!)
        q_scaled = memory.scaler.transform(q_vec)

        # 2. Compute Euclidean distances to all centroids
        distances = memory.kmeans.transform(q_scaled)[0]

        # 3. Find closest signature centroid
        sig_id = int(np.argmin(distances))
        dist_val = float(distances[sig_id])

        # 4. Check distance threshold
        thresh = float(memory.distance_thresholds.get(sig_id, 1.0))
        is_known = bool(dist_val <= thresh)

        # Find matching signature metadata
        sig_obj = next((s for s in memory.signatures if s.signature_id == sig_id), None)
        centroid_dict = sig_obj.centroid_profile if sig_obj else {}
        fault_dist = sig_obj.associated_fault_distribution if sig_obj else {}

        warnings_list: List[str] = []
        if not is_known:
            warnings_list.append(
                f"Query profile distance ({dist_val:.4f}) exceeds cluster threshold ({thresh:.4f}); flagged as novel/unmatched pattern."
            )

        return SignatureMatchResult(
            signature_id=sig_id,
            signature_distance=dist_val,
            distance_threshold=thresh,
            is_known_pattern=is_known,
            centroid_profile=centroid_dict,
            associated_fault_distribution=fault_dist,
            warnings=warnings_list,
            limitations=[
                "Failure Memory matching compares empirical Euclidean distance to pre-fitted cluster centroids.",
                "Signature matching identifies recurring reliability profiles; it does NOT confirm a causal root cause.",
            ],
        )
