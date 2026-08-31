"""
Unit tests for AEGIS-X Failure Memory and Failure Memory Matcher.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.core.exceptions import DatasetValidationError
from aegis.failure_memory.matcher import FailureMemoryMatcher
from aegis.failure_memory.memory import FailureMemory
from aegis.failure_memory.signatures import ConditionProfileExtractor


@pytest.fixture
def sample_profiles():
    np.random.seed(42)
    rows = []
    groups = ["Sensor_Bias", "Gain_Error", "Stuck_At", "Channel_Swap", "Sign_Inversion"]
    for i in range(15):
        rows.append({
            "group_key": groups[i % len(groups)],
            "mean_ood_risk": float(np.random.uniform(0.1, 0.9)),
            "mean_uncertainty": float(np.random.uniform(0.1, 0.9)),
            "mean_drift_score": float(np.random.uniform(0.0, 0.5)),
            "mean_fused_risk": float(np.random.uniform(0.1, 0.9)),
            "failure_rate": float(np.random.uniform(0.0, 0.5)),
            "silent_failure_rate": float(np.random.uniform(0.0, 0.2)),
        })
    return pd.DataFrame(rows)


def test_failure_memory_fit(sample_profiles):
    memory = FailureMemory(random_state=42)
    res = memory.fit(sample_profiles, n_clusters=3)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.n_signatures == 3
    assert memory.is_fitted
    assert len(memory.signatures) == 3
    assert memory.quality_summary["stability_ari"] >= 0.0


def test_failure_memory_matcher(sample_profiles):
    memory = FailureMemory(random_state=42)
    memory.fit(sample_profiles, n_clusters=3)

    # Query matching known profile
    query = sample_profiles.iloc[0].to_dict()
    match_res = FailureMemoryMatcher.match(query, memory)

    assert 0 <= match_res.signature_id < 3
    assert match_res.signature_distance >= 0.0
    assert match_res.is_known_pattern is True

    # Memory state must remain unchanged (no re-fitting during query!)
    assert memory.n_clusters == 3


def test_failure_memory_matcher_distant_query(sample_profiles):
    memory = FailureMemory(random_state=42)
    memory.fit(sample_profiles, n_clusters=3)

    # Extreme distant outlier query
    distant_query = {
        "mean_ood_risk": 50.0,
        "mean_uncertainty": 50.0,
        "mean_drift_score": 50.0,
        "mean_fused_risk": 50.0,
        "failure_rate": 10.0,
        "silent_failure_rate": 10.0,
    }

    match_res = FailureMemoryMatcher.match(distant_query, memory)
    assert match_res.is_known_pattern is False
    assert any("exceeds cluster threshold" in w for w in match_res.warnings)


def test_failure_memory_serialization(sample_profiles, tmp_path):
    memory = FailureMemory(random_state=42)
    memory.fit(sample_profiles, n_clusters=3)

    save_dir = tmp_path / "failure_memory_artifact"
    memory.save_artifact(save_dir)

    loaded_memory = FailureMemory().load_artifact(save_dir)
    assert loaded_memory.is_fitted
    assert loaded_memory.n_clusters == 3

    # Match query using loaded memory
    query = sample_profiles.iloc[0].to_dict()
    res1 = FailureMemoryMatcher.match(query, memory)
    res2 = FailureMemoryMatcher.match(query, loaded_memory)

    assert res1.signature_id == res2.signature_id
    np.testing.assert_allclose(res1.signature_distance, res2.signature_distance)


def test_unfitted_matcher_raises():
    memory = FailureMemory()
    with pytest.raises(DatasetValidationError):
        FailureMemoryMatcher.match({"mean_ood_risk": 0.5}, memory)
