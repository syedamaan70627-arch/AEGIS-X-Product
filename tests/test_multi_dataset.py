"""
Tests for Multi-Dataset upload, per-file schema validation, duplicate filenames, and Batch Monitor listing.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def sample_model(tmp_path):
    """Creates and registers a 3-feature test model."""
    clf = LogisticRegression()
    clf.fit([[0, 0, 0], [1, 1, 1], [0, 1, 0], [1, 0, 1]], [0, 1, 0, 1])
    model_path = tmp_path / "multi_test_model.joblib"
    joblib.dump(clf, model_path)

    with open(model_path, "rb") as f:
        res = client.post(
            "/api/v1/models",
            data={"model_name": "Multi-Dataset Test Model", "task_type": "binary_classification"},
            files={"file": ("model.joblib", f, "application/octet-stream")},
        )
    return res.json()["model_id"]


def test_multi_dataset_independent_records(sample_model):
    """Test uploading 5 evaluation datasets creates 5 independent records without concatenation."""
    filenames = [
        "evaluation_00pct_ood.csv",
        "evaluation_10pct_ood.csv",
        "evaluation_25pct_ood.csv",
        "evaluation_50pct_ood.csv",
        "evaluation_100pct_ood.csv",
    ]

    dataset_ids = []
    for fn in filenames:
        csv_content = b"f1,f2,f3\n0.1,0.2,0.3\n0.4,0.5,0.6\n"
        res = client.post(
            "/api/v1/datasets",
            data={"model_id": sample_model, "dataset_type": "EVALUATION"},
            files={"file": (fn, io.BytesIO(csv_content), "text/csv")},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["filename"] == fn
        assert data["num_features"] == 3
        dataset_ids.append(data["dataset_id"])

    # Verify all 5 dataset IDs are distinct
    assert len(set(dataset_ids)) == 5

    # Verify GET /api/v1/datasets returns all 5 datasets
    res_list = client.get(f"/api/v1/datasets?model_id={sample_model}")
    assert res_list.status_code == 200
    listed_datasets = res_list.json()["datasets"]
    assert len(listed_datasets) == 5


def test_schema_mismatch_validation(sample_model):
    """Test uploading a dataset with incorrect feature count returns feature mismatch error."""
    # Model expects 3 features, provide 2
    bad_csv = b"f1,f2\n0.1,0.2\n0.3,0.4\n"
    res = client.post(
        "/api/v1/datasets",
        data={"model_id": sample_model, "dataset_type": "EVALUATION"},
        files={"file": ("invalid_features.csv", io.BytesIO(bad_csv), "text/csv")},
    )
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "FEATURE_MISMATCH"
    assert "model expected features (3)" in data["error"]["message"]


def test_duplicate_filenames_supported(sample_model):
    """Test uploading two datasets with identical filenames creates distinct records."""
    csv1 = b"f1,f2,f3\n0.1,0.2,0.3\n"
    csv2 = b"f1,f2,f3\n0.7,0.8,0.9\n"

    res1 = client.post(
        "/api/v1/datasets",
        data={"model_id": sample_model, "dataset_type": "EVALUATION"},
        files={"file": ("evaluation.csv", io.BytesIO(csv1), "text/csv")},
    )
    res2 = client.post(
        "/api/v1/datasets",
        data={"model_id": sample_model, "dataset_type": "EVALUATION"},
        files={"file": ("evaluation.csv", io.BytesIO(csv2), "text/csv")},
    )

    assert res1.status_code == 201
    assert res2.status_code == 201

    d1 = res1.json()
    d2 = res2.json()

    assert d1["dataset_id"] != d2["dataset_id"]
    assert d1["filename"] == "evaluation.csv"
    assert d2["filename"] == "evaluation.csv"
