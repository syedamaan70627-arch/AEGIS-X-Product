"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
Anti-Flapping Governance State Machine.

Requirements:
- State Severity: CONTINUE (0) < WATCH (1) < DEFER (2) < ESCALATE (3).
- Upward safety transitions occur immediately.
- Persistent DEFER: repeated DEFER raw actions trigger transition to ESCALATE after defer_persistence_threshold.
- Downward recovery requires recovery_consecutive_states consecutive lower-risk steps and cooldown_steps degradation states.
- Latching: ESCALATE remains latched until explicit acknowledge_escalation() or reset().
- Per-entity isolation: reset() clears all history and state.
- Monotonicity: rejects duplicate, backward, or non-monotonic state indices.
- All horizons/cooldowns expressed exclusively in controlled_degradation_states.
"""

from typing import Dict, List, Optional, Tuple, Any
from aegis.governance.schemas import ECRGGovernanceAction, ECRGStateMachineConfig


ACTION_SEVERITY: Dict[ECRGGovernanceAction, int] = {
    ECRGGovernanceAction.CONTINUE: 0,
    ECRGGovernanceAction.WATCH: 1,
    ECRGGovernanceAction.DEFER: 2,
    ECRGGovernanceAction.ESCALATE: 3,
}

SEVERITY_ACTION: Dict[int, ECRGGovernanceAction] = {
    0: ECRGGovernanceAction.CONTINUE,
    1: ECRGGovernanceAction.WATCH,
    2: ECRGGovernanceAction.DEFER,
    3: ECRGGovernanceAction.ESCALATE,
}


class ECRGStateMachine:
    """
    Per-Entity Anti-Flapping Governance State Machine.
    """

    def __init__(self, config: Optional[ECRGStateMachineConfig] = None):
        self.config = config or ECRGStateMachineConfig()
        self.current_effective_action: ECRGGovernanceAction = ECRGGovernanceAction.CONTINUE
        self.last_raw_action: Optional[ECRGGovernanceAction] = None
        self.last_state_index: Optional[int] = None
        self.consecutive_defer_count: int = 0
        self.consecutive_lower_count: int = 0
        self.in_cooldown: bool = False
        self.cooldown_remaining: int = 0
        self.escalation_latched: bool = False
        self.escalation_acknowledged: bool = False
        self.consecutive_state_count: int = 1
        self.entity_id: Optional[str] = None

    def reset(self, entity_id: Optional[str] = None) -> None:
        """Reset state machine for a new engine/entity trajectory."""
        self.current_effective_action = ECRGGovernanceAction.CONTINUE
        self.last_raw_action = None
        self.last_state_index = None
        self.consecutive_defer_count = 0
        self.consecutive_lower_count = 0
        self.in_cooldown = False
        self.cooldown_remaining = 0
        self.escalation_latched = False
        self.escalation_acknowledged = False
        self.consecutive_state_count = 1
        self.entity_id = entity_id

    def acknowledge_escalation(self) -> None:
        """Acknowledge latched ESCALATE state to allow recovery."""
        self.escalation_acknowledged = True
        self.escalation_latched = False

    def step(self, raw_action: ECRGGovernanceAction, state_index: int) -> Tuple[ECRGGovernanceAction, str, bool]:
        """
        Process a single step in the trajectory.
        Returns Tuple[effective_action, transition_reason, transition_occurred].
        """
        # Monotonicity validation
        if self.last_state_index is not None and state_index <= self.last_state_index:
            raise ValueError(
                f"Out-of-order or duplicate state_index {state_index} received. "
                f"Previous state_index was {self.last_state_index}."
            )

        self.last_state_index = state_index
        prev_effective = self.current_effective_action
        raw_sev = ACTION_SEVERITY[raw_action]
        curr_sev = ACTION_SEVERITY[self.current_effective_action]

        # Track persistent DEFER count
        if raw_action == ECRGGovernanceAction.DEFER:
            self.consecutive_defer_count += 1
        else:
            self.consecutive_defer_count = 0

        # Case 1: Persistent DEFER escalation
        if (
            self.consecutive_defer_count >= self.config.defer_persistence_threshold
            and raw_action == ECRGGovernanceAction.DEFER
        ):
            new_effective = ECRGGovernanceAction.ESCALATE
            reason = f"Persistent DEFER for {self.consecutive_defer_count} consecutive steps; escalating to ESCALATE."
            if self.config.latch_escalate:
                self.escalation_latched = True
                self.escalation_acknowledged = False

        # Case 2: Active latched ESCALATE state
        elif self.current_effective_action == ECRGGovernanceAction.ESCALATE and self.escalation_latched and not self.escalation_acknowledged:
            new_effective = ECRGGovernanceAction.ESCALATE
            reason = "ESCALATE state latched until explicit acknowledgement or trajectory reset."

        # Case 3: Immediate upward transition
        elif raw_sev > curr_sev:
            new_effective = raw_action
            reason = f"Immediate upward safety transition from {prev_effective.value} to {raw_action.value}."
            self.consecutive_lower_count = 0
            self.cooldown_remaining = 0
            if raw_action == ECRGGovernanceAction.ESCALATE and self.config.latch_escalate:
                self.escalation_latched = True
                self.escalation_acknowledged = False

        # Case 4: Downward recovery evaluation
        elif raw_sev < curr_sev:
            self.consecutive_lower_count += 1
            
            # Check if lower state persistence condition is met
            if self.consecutive_lower_count >= self.config.recovery_consecutive_states:
                if self.cooldown_remaining > 0:
                    self.cooldown_remaining -= 1
                    new_effective = self.current_effective_action
                    reason = f"In de-escalation cooldown. {self.cooldown_remaining + 1} controlled degradation steps remaining."
                elif not self.in_cooldown and self.config.cooldown_steps > 0:
                    self.in_cooldown = True
                    self.cooldown_remaining = self.config.cooldown_steps - 1
                    new_effective = self.current_effective_action
                    reason = f"Required {self.config.recovery_consecutive_states} consecutive lower steps reached. Starting de-escalation cooldown ({self.config.cooldown_steps} steps)."
                else:
                    # De-escalate state by 1 step or to target raw severity
                    target_sev = max(raw_sev, curr_sev - 1)
                    new_effective = SEVERITY_ACTION[target_sev]
                    reason = (
                        f"De-escalated from {prev_effective.value} to {new_effective.value} "
                        f"after {self.consecutive_lower_count} consecutive lower-risk steps."
                    )
                    self.consecutive_lower_count = 0
                    self.in_cooldown = False
                    self.cooldown_remaining = 0
            else:
                new_effective = self.current_effective_action
                reason = (
                    f"Lower raw action {raw_action.value} observed ({self.consecutive_lower_count}/"
                    f"{self.config.recovery_consecutive_states} required consecutive lower steps)."
                )

        # Case 5: Same severity raw action
        else:
            new_effective = self.current_effective_action
            reason = f"Maintaining current governance state {self.current_effective_action.value}."
            self.consecutive_lower_count = 0

        # Update state tracking
        transition_occurred = (new_effective != prev_effective)
        if transition_occurred:
            self.current_effective_action = new_effective
            self.consecutive_state_count = 1
        else:
            self.consecutive_state_count += 1

        self.last_raw_action = raw_action
        return new_effective, reason, transition_occurred
