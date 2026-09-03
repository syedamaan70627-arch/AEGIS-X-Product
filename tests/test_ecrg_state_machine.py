"""
AEGIS-X Module 14 — Anti-Flapping Governance State Machine Unit Test Suite.
Tests Requirements 19-25 from Section 12.
"""

import pytest
from aegis.governance.schemas import ECRGGovernanceAction, ECRGStateMachineConfig
from aegis.governance.state_machine import ECRGStateMachine


def test_19_immediate_upward_state_transition():
    """Test 19: Upward safety transitions occur immediately."""
    sm = ECRGStateMachine()
    
    # Step 0: CONTINUE
    eff0, _, _ = sm.step(ECRGGovernanceAction.CONTINUE, state_index=0)
    assert eff0 == ECRGGovernanceAction.CONTINUE

    # Step 1: Raw DEFER -> Immediate upward transition to DEFER
    eff1, reason, trans = sm.step(ECRGGovernanceAction.DEFER, state_index=1)
    assert eff1 == ECRGGovernanceAction.DEFER
    assert trans is True
    assert "Immediate upward" in reason


def test_20_hysteretic_cooldown_recovery():
    """Test 20: Downward recovery requires consecutive lower states + cooldown."""
    config = ECRGStateMachineConfig(recovery_consecutive_states=3, cooldown_steps=2)
    sm = ECRGStateMachine(config=config)

    # Elevate to WATCH
    sm.step(ECRGGovernanceAction.WATCH, state_index=0)
    assert sm.current_effective_action == ECRGGovernanceAction.WATCH

    # Lower raw action CONTINUE for step 1 & 2 -> Below recovery threshold (3)
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=1)
    assert sm.current_effective_action == ECRGGovernanceAction.WATCH
    
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=2)
    assert sm.current_effective_action == ECRGGovernanceAction.WATCH

    # Step 3: Hits 3 consecutive lower steps -> enters cooldown (cooldown_remaining = 2 -> 1)
    eff3, _, _ = sm.step(ECRGGovernanceAction.CONTINUE, state_index=3)
    assert eff3 == ECRGGovernanceAction.WATCH  # In cooldown

    # Step 4: Cooldown step 2 (cooldown_remaining = 1 -> 0)
    eff4, _, _ = sm.step(ECRGGovernanceAction.CONTINUE, state_index=4)
    assert eff4 == ECRGGovernanceAction.WATCH

    # Step 5: Cooldown complete -> step down to CONTINUE
    eff5, _, _ = sm.step(ECRGGovernanceAction.CONTINUE, state_index=5)
    assert eff5 == ECRGGovernanceAction.CONTINUE


def test_21_persistent_defer_escalation():
    """Test 21: Repeated DEFER raw actions transition to ESCALATE after persistence threshold (3)."""
    config = ECRGStateMachineConfig(defer_persistence_threshold=3)
    sm = ECRGStateMachine(config=config)

    # 1st DEFER -> DEFER
    eff1, _, _ = sm.step(ECRGGovernanceAction.DEFER, state_index=0)
    assert eff1 == ECRGGovernanceAction.DEFER

    # 2nd DEFER -> DEFER
    eff2, _, _ = sm.step(ECRGGovernanceAction.DEFER, state_index=1)
    assert eff2 == ECRGGovernanceAction.DEFER

    # 3rd DEFER -> Trigger persistent DEFER escalation to ESCALATE
    eff3, reason, _ = sm.step(ECRGGovernanceAction.DEFER, state_index=2)
    assert eff3 == ECRGGovernanceAction.ESCALATE
    assert "Persistent DEFER" in reason


def test_22_latched_escalate_acknowledgement():
    """Test 22: ESCALATE remains latched by default until explicit acknowledgement."""
    config = ECRGStateMachineConfig(latch_escalate=True, recovery_consecutive_states=1, cooldown_steps=0)
    sm = ECRGStateMachine(config=config)

    # Trigger ESCALATE
    sm.step(ECRGGovernanceAction.ESCALATE, state_index=0)
    assert sm.current_effective_action == ECRGGovernanceAction.ESCALATE

    # Subsequent CONTINUE raw actions will NOT clear latched ESCALATE
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=1)
    assert sm.current_effective_action == ECRGGovernanceAction.ESCALATE
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=2)
    assert sm.current_effective_action == ECRGGovernanceAction.ESCALATE

    # Explicit acknowledgement allows state recovery
    sm.acknowledge_escalation()
    # Step-down progression: ESCALATE (3) -> DEFER (2) -> WATCH (1) -> CONTINUE (0)
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=3)  # -> DEFER
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=4)  # -> WATCH
    eff5, _, _ = sm.step(ECRGGovernanceAction.CONTINUE, state_index=5)  # -> CONTINUE
    assert eff5 == ECRGGovernanceAction.CONTINUE


def test_23_per_engine_state_reset():
    """Test 23: State resets cleanly at start of every new engine/entity trajectory."""
    sm = ECRGStateMachine()
    sm.step(ECRGGovernanceAction.ESCALATE, state_index=0)
    assert sm.current_effective_action == ECRGGovernanceAction.ESCALATE

    # Reset for new engine
    sm.reset(entity_id="engine_002")
    assert sm.current_effective_action == ECRGGovernanceAction.CONTINUE
    assert sm.last_state_index is None
    assert sm.consecutive_defer_count == 0


def test_24_out_of_order_state_rejection():
    """Test 24: Rejects duplicate, backward, or non-monotonic state indices."""
    sm = ECRGStateMachine()
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=10)
    
    # Duplicate state_index 10
    with pytest.raises(ValueError) as exc1:
        sm.step(ECRGGovernanceAction.CONTINUE, state_index=10)
    assert "Out-of-order or duplicate state_index" in str(exc1.value)

    # Backward state_index 5
    with pytest.raises(ValueError) as exc2:
        sm.step(ECRGGovernanceAction.CONTINUE, state_index=5)
    assert "Out-of-order or duplicate state_index" in str(exc2.value)


def test_25_deterministic_repeated_execution():
    """Test 25: Deterministic repeated execution yields identical state transitions."""
    actions = [ECRGGovernanceAction.CONTINUE, ECRGGovernanceAction.WATCH, ECRGGovernanceAction.DEFER, ECRGGovernanceAction.CONTINUE]
    
    run1_res = []
    sm1 = ECRGStateMachine()
    for idx, act in enumerate(actions):
        eff, _, _ = sm1.step(act, state_index=idx)
        run1_res.append(eff)

    run2_res = []
    sm2 = ECRGStateMachine()
    for idx, act in enumerate(actions):
        eff, _, _ = sm2.step(act, state_index=idx)
        run2_res.append(eff)

    assert run1_res == run2_res
