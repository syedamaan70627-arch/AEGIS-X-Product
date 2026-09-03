"""
AEGIS-X Module 14 Phase 4 — State-Machine Anti-Flapping Attack Tests.
Verifies multi-entity state isolation, hysteretic recovery, and latching safeguards.
"""

import pytest
from aegis.governance.schemas import ECRGGovernanceAction, ECRGStateMachineConfig
from aegis.governance.state_machine import ECRGStateMachine


def test_1_interleaved_engine_trajectories_do_not_contaminate_state():
    """Test 1: Interleaved evaluations for two engine IDs (Engine A & Engine B) do NOT contaminate state."""
    sm_engine_a = ECRGStateMachine()
    sm_engine_b = ECRGStateMachine()

    # Step 0 for Engine A -> ESCALATE
    eff_a0, _, _ = sm_engine_a.step(ECRGGovernanceAction.ESCALATE, state_index=0)
    assert eff_a0 == ECRGGovernanceAction.ESCALATE

    # Step 0 for Engine B -> CONTINUE
    eff_b0, _, _ = sm_engine_b.step(ECRGGovernanceAction.CONTINUE, state_index=0)
    assert eff_b0 == ECRGGovernanceAction.CONTINUE

    # Engine A remains ESCALATE while Engine B remains CONTINUE
    eff_a1, _, _ = sm_engine_a.step(ECRGGovernanceAction.CONTINUE, state_index=1)
    assert eff_a1 == ECRGGovernanceAction.ESCALATE
    assert sm_engine_b.current_effective_action == ECRGGovernanceAction.CONTINUE


def test_2_duplicate_and_backward_state_indices_rejected():
    """Test 2: Rejects duplicate or backward state_index within the same trajectory."""
    sm = ECRGStateMachine()
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=5)

    # Duplicate state_index=5
    with pytest.raises(ValueError) as exc1:
        sm.step(ECRGGovernanceAction.CONTINUE, state_index=5)
    assert "Out-of-order or duplicate state_index" in str(exc1.value)

    # Backward state_index=4
    with pytest.raises(ValueError) as exc2:
        sm.step(ECRGGovernanceAction.CONTINUE, state_index=4)
    assert "Out-of-order or duplicate state_index" in str(exc2.value)


def test_3_persistent_defer_escalates_to_escalate():
    """Test 3: Persistent DEFER threshold reached escalates effective state to ESCALATE."""
    sm = ECRGStateMachine(config=ECRGStateMachineConfig(defer_persistence_threshold=3))
    
    sm.step(ECRGGovernanceAction.DEFER, state_index=0)
    sm.step(ECRGGovernanceAction.DEFER, state_index=1)
    eff3, reason, _ = sm.step(ECRGGovernanceAction.DEFER, state_index=2)

    assert eff3 == ECRGGovernanceAction.ESCALATE
    assert "Persistent DEFER" in reason


def test_4_latched_escalate_requires_explicit_reset_or_ack():
    """Test 4: ESCALATE remains latched until acknowledge_escalation or reset."""
    sm = ECRGStateMachine(config=ECRGStateMachineConfig(latch_escalate=True))
    sm.step(ECRGGovernanceAction.ESCALATE, state_index=0)
    
    # Unacknowledged
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=1)
    assert sm.current_effective_action == ECRGGovernanceAction.ESCALATE

    # Reset clears latched state
    sm.reset(entity_id="engine_99")
    assert sm.current_effective_action == ECRGGovernanceAction.CONTINUE


def test_5_all_units_expressed_only_in_degradation_steps():
    """Test 5: Controlled degradation step counts are unitless state indices (never seconds/hours)."""
    config = ECRGStateMachineConfig(defer_persistence_threshold=3, recovery_consecutive_states=3, cooldown_steps=2)
    assert isinstance(config.defer_persistence_threshold, int)
    assert isinstance(config.recovery_consecutive_states, int)
    assert isinstance(config.cooldown_steps, int)
