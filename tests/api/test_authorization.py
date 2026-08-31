"""
Tests for AEGIS-X Multi-User Authorization & Ownership Isolation.
"""

import io
import joblib
from unittest.mock import patch
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.core.auth import UserContext, get_current_user
from api.core.config import settings
from api.main import app

client = TestClient(app)


def test_user_authorization_isolation():
    """Test that User B cannot access or view resources owned by User A."""
    clf = LogisticRegression()
    clf.fit([[1, 2, 3], [4, 5, 6]], [0, 1])
    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    user_a = UserContext(user_id="user_A", email="usera@example.com", authenticated=True)
    user_b = UserContext(user_id="user_B", email="userb@example.com", authenticated=True)

    try:
        # 1. User A registers a model
        app.dependency_overrides[get_current_user] = lambda: user_a
        with patch.object(settings, "AUTH_REQUIRED", True):
            res_m = client.post(
                "/api/v1/models",
                data={"model_name": "User A Private Model", "task_type": "binary_classification"},
                files={"file": ("model.joblib", buf, "application/octet-stream")},
            )
            assert res_m.status_code == 201
            model_a_id = res_m.json()["model_id"]

        # 2. User B tries to fetch User A's model -> 404 Not Found
        app.dependency_overrides[get_current_user] = lambda: user_b
        with patch.object(settings, "AUTH_REQUIRED", True):
            res_get = client.get(f"/api/v1/models/{model_a_id}")
            assert res_get.status_code == 404

            # User B lists models -> User A model must NOT appear
            res_list = client.get("/api/v1/models")
            assert res_list.status_code == 200
            user_b_models = res_list.json()["models"]
            assert all(m["model_id"] != model_a_id for m in user_b_models)
    finally:
        app.dependency_overrides.clear()
