"""
AEGIS-X Module 14 Phase 6 Service Unit Tests.

Tests for GovernanceService including model ownership verification, ECRG decision evaluation,
state machine transition recording, fail-safe handling, and persistence in DB.
"""

import uuid
import pytest
from aegis.governance.schemas import ECRGGovernanceAction, ECRGOperatingMode
from api.db.models import ModelRecord
from api.core.dependencies import get_model_repository
from api.schemas.governance import GovernanceEvaluationRequest
from api.services.governance_service import GovernanceService


@pytest.fixture
def registered_model():
    """Register a model record in the DB repo."""
    repo = get_model_repository()
    model_id = f"gov_service_test_model_{uuid.uuid4()}"
    user_id = "test_owner_user"

    record = ModelRecord(
        id=model_id,
        user_id=user_id,
        model_name="Gov Test Model",
        task_type="binary_classification",
        description="Governance test model",
        file_path="storage/models/test.joblib",
        filename="test.joblib",
        predict_supported=True,
        predict_proba_supported=True,
        n_features_in=4,
        classes=[0, 1],
        feature_names=["f1", "f2", "f3", "f4"],
        created_at="2026-09-04T12:00:00Z",
    )
    repo.create(record)
    return {"model_id": model_id, "user_id": user_id}


def test_governance_service_evaluate_success(registered_model):
    """Test successful governance evaluation for an existing model."""
    res = registered_model
    req = GovernanceEvaluationRequest(
        model_id=res["model_id"],
        dataset_id="dataset_123",
        trajectory_id="traj_1",
        state_index=0,
        ood_score=0.1,
        uncertainty_score=0.1,
        drift_score=0.05,
        fused_risk=0.1,
        mode=ECRGOperatingMode.EVIDENCE_ONLY,
    )
    resp = GovernanceService.evaluate_governance(req, user_id=res["user_id"])

    assert resp.model_id == res["model_id"]
    assert resp.user_id == res["user_id"]
    assert resp.action in [ECRGGovernanceAction.CONTINUE, ECRGGovernanceAction.WATCH, ECRGGovernanceAction.DEFER, ECRGGovernanceAction.ESCALATE]
    assert resp.evaluation_id is not None
    assert resp.evidence_snapshot_hash is not None


def test_governance_service_access_denied(registered_model):
    """Test that evaluating governance for a model owned by another user raises ValueError."""
    res = registered_model
    req = GovernanceEvaluationRequest(
        model_id=res["model_id"],
        dataset_id="dataset_123",
        ood_score=0.1,
        uncertainty_score=0.1,
        drift_score=0.05,
        fused_risk=0.1,
    )
    with pytest.raises(ValueError, match="not found or access denied"):
        GovernanceService.evaluate_governance(req, user_id="unauthorized_user")


def test_governance_service_status_and_history(registered_model):
    """Test status and history queries after multiple evaluations."""
    res = registered_model

    # Initial status (empty)
    status_initial = GovernanceService.get_status(res["model_id"], user_id=res["user_id"])
    assert status_initial.total_evaluations == 0

    # Run evaluation 1
    req1 = GovernanceEvaluationRequest(
        model_id=res["model_id"],
        dataset_id="dataset_123",
        state_index=0,
        ood_score=0.1,
        uncertainty_score=0.1,
        drift_score=0.05,
        fused_risk=0.1,
    )
    GovernanceService.evaluate_governance(req1, user_id=res["user_id"])

    # Run evaluation 2
    req2 = GovernanceEvaluationRequest(
        model_id=res["model_id"],
        dataset_id="dataset_123",
        state_index=1,
        ood_score=0.8,
        uncertainty_score=0.8,
        drift_score=0.8,
        fused_risk=0.85,
    )
    GovernanceService.evaluate_governance(req2, user_id=res["user_id"])

    status = GovernanceService.get_status(res["model_id"], user_id=res["user_id"])
    assert status.total_evaluations == 2

    history = GovernanceService.get_history(res["model_id"], user_id=res["user_id"], limit=10, offset=0)
    assert history.total == 2
    assert len(history.evaluations) == 2


def test_governance_service_failsafe_on_exception(registered_model, monkeypatch):
    """Test that invalid/corrupted evidence evaluation falls back to safe ESCALATE response."""
    res = registered_model

    req = GovernanceEvaluationRequest(
        model_id=res["model_id"],
        dataset_id="dataset_123",
        ood_score=0.1,
        uncertainty_score=0.1,
        drift_score=0.05,
        fused_risk=0.1,
    )

    def mock_eval_raise(*args, **kwargs):
        raise ValueError("Corrupted array computation")

    monkeypatch.setattr("aegis.governance.governor.ReliabilityGovernor.evaluate", mock_eval_raise)

    resp = GovernanceService.evaluate_governance(req, user_id=res["user_id"])
    assert resp.action == ECRGGovernanceAction.ESCALATE
    assert "SAFE_ESCALATION_TRIGGERED" in resp.reason_codes
    assert "CRITICAL_EVIDENCE_CORRUPTED" in resp.reason_codes


def test_governance_persistence_id_separation(registered_model):
    """Test that GovernanceEvaluationRecord.id is a valid UUID while decision_id is dec- string."""
    from api.core.dependencies import get_governance_repository
    res = registered_model
    req = GovernanceEvaluationRequest(
        model_id=res["model_id"],
        dataset_id="dataset_uuid_test",
        state_index=0,
        ood_score=0.1,
        uncertainty_score=0.1,
        drift_score=0.05,
        fused_risk=0.1,
    )
    resp = GovernanceService.evaluate_governance(req, user_id=res["user_id"])

    gov_repo = get_governance_repository()
    evals = gov_repo.list_evaluations(res["model_id"], owner_id=res["user_id"])
    assert len(evals) == 1
    eval_rec = evals[0]

    # Verify rec.id is a valid UUID
    parsed_uuid = uuid.UUID(eval_rec.id)
    assert str(parsed_uuid) == eval_rec.id

    # Verify rec.decision_id is a dec- string
    assert eval_rec.decision_id.startswith("dec-")
    assert resp.evaluation_id.startswith("dec-")

