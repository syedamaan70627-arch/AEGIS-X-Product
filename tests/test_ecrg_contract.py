"""
AEGIS-X Module 14 — ECRG Contract & Schema Validation Unit Tests.
"""

import pytest
from aegis.governance.schemas import (
    ECRGEvidenceContract,
    ECRGOperatingMode,
    ECRGGovernanceAction,
    ECRGDecisionResponse,
    ECRGCalibrationConfig,
)


def test_ecrg_evidence_contract_validation():
    """Verify that ECRGEvidenceContract initializes and validates bounds properly."""
    evidence = ECRGEvidenceContract(
        model_id="test-model-123",
        dataset_id="test-ds-456",
        trajectory_id="unit_001",
        state_index=12,
        timestamp="2026-09-02T20:30:00Z",
        ood_score=0.15,
        uncertainty_score=0.22,
        drift_score=0.18,
        fused_risk=0.20,
        signal_disagreement=0.04,
        memory_similarity=0.35,
        temporal_failure_probability=0.10,
        early_warning_state="NORMAL",
        prediction_horizon=5,
    )
    
    assert evidence.model_id == "test-model-123"
    assert evidence.fused_risk == 0.20
    assert evidence.eventual_failure is None  # Label-free production default


def test_ecrg_decision_response_structure():
    """Verify ECRGDecisionResponse structure and enum values."""
    response = ECRGDecisionResponse(
        decision_id="dec-789",
        mode=ECRGOperatingMode.EVIDENCE_ONLY,
        action=ECRGGovernanceAction.CONTINUE,
        warning_severity="LOW",
        certification_banner="LABEL-FREE / NON-CERTIFIED",
        calibrated=False,
        primary_supporting_signal="fused_risk",
        supporting_evidence=["Fused risk 0.20 is below warning threshold 0.35"],
        contradictory_evidence=[],
        signal_disagreement_index=0.04,
        consecutive_state_count=5,
        in_cooldown=False,
        state_transition_occurred=False,
    )

    assert response.mode == ECRGOperatingMode.EVIDENCE_ONLY
    assert response.action == ECRGGovernanceAction.CONTINUE
    assert response.certification_banner == "LABEL-FREE / NON-CERTIFIED"
    assert response.calibrated is False


def test_ecrg_calibrated_governance_mode():
    """Verify CALIBRATED_GOVERNANCE config structure."""
    config = ECRGCalibrationConfig(
        target_risk_alpha=0.05,
        calibration_set_size=100,
        calibrated_quantile_threshold=0.38,
        calibration_method="Split_Conformal_Risk_Control",
    )
    
    assert config.target_risk_alpha == 0.05
    assert len(config.stated_assumptions) > 0
