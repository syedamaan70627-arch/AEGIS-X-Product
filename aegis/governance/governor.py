"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
Product Name: Reliability Governor
Scientific Name: Evidence-Calibrated Reliability Governance (ECRG)

Main Governance Engine orchestrating operating modes, split-conformal calibrator,
anti-flapping state machine, and immutable audit decision records.
"""

import datetime
import hashlib
import json
import math
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd

from aegis.governance.artifact import ECRGCalibratorArtifact
from aegis.governance.calibrator import TrajectorySplitConformalCalibrator
from aegis.governance.schemas import (
    ECRGEvidenceContract,
    ECRGOperatingMode,
    ECRGGovernanceAction,
    ECRGDecisionRecord,
    ECRGDecisionResponse,
    ECRGCalibrationConfig,
    ECRGStateMachineConfig,
)
from aegis.governance.state_machine import ECRGStateMachine


GOVERNOR_SCHEMA_VERSION = "1.0.0"


class ReliabilityGovernor:
    """
    AEGIS-X Reliability Governor (ECRG Engine).
    Consumes frozen reliability evidence and generates auditable governance recommendations.
    """

    def __init__(
        self,
        artifact: Optional[ECRGCalibratorArtifact] = None,
        mode: ECRGOperatingMode = ECRGOperatingMode.EVIDENCE_ONLY,
        state_machine_config: Optional[ECRGStateMachineConfig] = None,
    ):
        self.artifact = artifact
        self.mode = mode
        self.state_machine = ECRGStateMachine(config=state_machine_config)

        if self.mode == ECRGOperatingMode.CALIBRATED_GOVERNANCE and self.artifact is None:
            raise ValueError("CALIBRATED_GOVERNANCE mode requires a validated ECRGCalibratorArtifact.")

    def reset_entity_state(self, entity_id: str) -> None:
        """Reset state machine state for a new engine/entity trajectory."""
        self.state_machine.reset(entity_id=entity_id)

    def acknowledge_escalation(self) -> None:
        """Acknowledge latched ESCALATE state to allow state recovery."""
        self.state_machine.acknowledge_escalation()

    def _extract_feature_dataframe(self, evidence: ECRGEvidenceContract, feature_names: List[str]) -> pd.DataFrame:
        """Extract evidence features matching calibrator schema in exact column order."""
        row_dict = {}
        for fname in feature_names:
            if hasattr(evidence, fname):
                val = getattr(evidence, fname)
            else:
                val = 0.0
            
            if val is None or math.isnan(float(val)) or math.isinf(float(val)):
                raise ValueError(f"Evidence signal '{fname}' is NaN, Infinity, or None.")
            row_dict[fname] = [float(val)]

        return pd.DataFrame(row_dict)

    def evaluate(
        self,
        evidence: ECRGEvidenceContract,
        requested_mode: Optional[ECRGOperatingMode] = None,
    ) -> ECRGDecisionRecord:
        """
        Evaluate input evidence contract and produce an immutable ECRGDecisionRecord.
        Never silently downgrades calibrated mode to evidence-only mode.
        """
        active_mode = requested_mode or self.mode

        # Compute evidence snapshot hash
        evidence_json = evidence.model_dump_json()
        snapshot_hash = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()
        decision_id = f"dec-{hashlib.sha256((evidence_json + str(datetime.datetime.now())).encode('utf-8')).hexdigest()[:16]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        entity_id = evidence.trajectory_id or evidence.model_id or "default_entity"

        # Validate basic numerical finiteness of core evidence
        core_signals = [evidence.ood_score, evidence.uncertainty_score, evidence.drift_score, evidence.fused_risk]
        if any(s is None or math.isnan(s) or math.isinf(s) for s in core_signals):
            # Critical evidence missing/corrupted -> fail safe to ESCALATE
            raw_action = ECRGGovernanceAction.ESCALATE
            effective_action, transition_reason, _ = self.state_machine.step(raw_action, evidence.state_index)
            return ECRGDecisionRecord(
                decision_id=decision_id,
                entity_id=entity_id,
                state_index=evidence.state_index,
                task_type="EVIDENCE_VALIDATION_FAILURE",
                dataset_profile="INVALID_EVIDENCE",
                operating_mode=ECRGOperatingMode.EVIDENCE_ONLY,
                target_semantic="N/A",
                horizon=evidence.prediction_horizon,
                unit="controlled_degradation_states",
                alpha=None,
                p_adverse=1.0,
                nonconformity_details={"error": "Critical evidence NaN or Inf"},
                prediction_set=[],
                raw_action=raw_action,
                previous_effective_action=self.state_machine.last_raw_action,
                effective_action=effective_action,
                transition_reason=f"Safe failure: {transition_reason}",
                reason_codes=["CRITICAL_EVIDENCE_CORRUPTED", "SAFE_ESCALATION_TRIGGERED"],
                evidence_snapshot_hash=snapshot_hash,
                calibrator_artifact_id=None,
                calibrator_artifact_sha256=None,
                schema_version=GOVERNOR_SCHEMA_VERSION,
                calibration_unit_count=None,
                guarantee_scope=None,
                calibrated=False,
                creation_timestamp=timestamp,
            )

        # ---------------------------------------------------------------------
        # MODE 1: EVIDENCE_ONLY
        # ---------------------------------------------------------------------
        if active_mode == ECRGOperatingMode.EVIDENCE_ONLY:
            # Uncalibrated advisory heuristics using frozen contract signals
            reasons = ["EVIDENCE_ONLY_MODE_ACTIVE", "ADVISORY_NON_CERTIFIED_GOVERNANCE"]
            
            if evidence.fused_risk >= 0.70 or evidence.temporal_failure_probability >= 0.70:
                raw_action = ECRGGovernanceAction.DEFER
                reasons.append("HIGH_FUSED_RISK_THRESHOLD_EXCEEDED")
            elif evidence.fused_risk >= 0.40 or evidence.ood_score >= 0.60 or evidence.uncertainty_score >= 0.60:
                raw_action = ECRGGovernanceAction.WATCH
                reasons.append("MODERATE_EVIDENCE_SIGNAL_WARNING")
            else:
                raw_action = ECRGGovernanceAction.CONTINUE
                reasons.append("ALL_EVIDENCE_SIGNALS_NOMINAL")

            effective_action, transition_reason, _ = self.state_machine.step(raw_action, evidence.state_index)

            return ECRGDecisionRecord(
                decision_id=decision_id,
                entity_id=entity_id,
                state_index=evidence.state_index,
                task_type="EVIDENCE_ONLY_EVALUATION",
                dataset_profile="UNSPECIFIED",
                operating_mode=ECRGOperatingMode.EVIDENCE_ONLY,
                target_semantic="UNSET",
                horizon=evidence.prediction_horizon,
                unit="controlled_degradation_states",
                alpha=None,
                p_adverse=float(evidence.fused_risk),
                nonconformity_details={"s_y0": float(evidence.fused_risk), "s_y1": float(1.0 - evidence.fused_risk), "quantile_q": None},
                prediction_set=[0] if raw_action == ECRGGovernanceAction.CONTINUE else ([0, 1] if raw_action == ECRGGovernanceAction.WATCH else [1]),
                raw_action=raw_action,
                previous_effective_action=self.state_machine.last_raw_action,
                effective_action=effective_action,
                transition_reason=transition_reason,
                reason_codes=reasons,
                evidence_snapshot_hash=snapshot_hash,
                calibrator_artifact_id=None,
                calibrator_artifact_sha256=None,
                schema_version=GOVERNOR_SCHEMA_VERSION,
                calibration_unit_count=None,
                guarantee_scope=None,
                calibrated=False,
                creation_timestamp=timestamp,
            )

        # ---------------------------------------------------------------------
        # MODE 2: CALIBRATED_GOVERNANCE
        # ---------------------------------------------------------------------
        elif active_mode == ECRGOperatingMode.CALIBRATED_GOVERNANCE:
            if self.artifact is None:
                raise ValueError("CALIBRATED_GOVERNANCE mode requested, but no calibrator artifact is loaded.")

            # Validate feature schema compatibility
            calibrator = self.artifact.calibrator
            feature_names = calibrator.learner.feature_names
            X_step = self._extract_feature_dataframe(evidence, feature_names)

            prediction_set, p_adverse, nonconf_details = calibrator.predict_conformal_set(X_step)
            raw_action = calibrator.map_prediction_set_to_raw_action(prediction_set)

            effective_action, transition_reason, _ = self.state_machine.step(raw_action, evidence.state_index)

            art_dict = self.artifact.to_dict()
            reasons = ["CALIBRATED_GOVERNANCE_ACTIVE", f"PREDICTION_SET_{prediction_set}"]

            guarantee_scope = (
                f"Marginal finite-sample split-conformal risk bound (1-alpha={1.0 - calibrator.target_alpha:.2f}) "
                f"over {calibrator.n_cal_units} exchangeable calibration units under {calibrator.task_type} profile."
            )

            return ECRGDecisionRecord(
                decision_id=decision_id,
                entity_id=entity_id,
                state_index=evidence.state_index,
                task_type=self.artifact.task_capability_profile,
                dataset_profile=self.artifact.task_capability_profile,
                operating_mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE,
                target_semantic=self.artifact.target_semantic,
                horizon=self.artifact.horizon,
                unit="controlled_degradation_states" if self.artifact.horizon is not None else "sample",
                alpha=calibrator.target_alpha,
                p_adverse=p_adverse,
                nonconformity_details=nonconf_details,
                prediction_set=prediction_set,
                raw_action=raw_action,
                previous_effective_action=self.state_machine.last_raw_action,
                effective_action=effective_action,
                transition_reason=transition_reason,
                reason_codes=reasons,
                evidence_snapshot_hash=snapshot_hash,
                calibrator_artifact_id=self.artifact.artifact_id,
                calibrator_artifact_sha256=art_dict["artifact_sha256"],
                schema_version=GOVERNOR_SCHEMA_VERSION,
                calibration_unit_count=calibrator.n_cal_units,
                guarantee_scope=guarantee_scope,
                calibrated=True,
                creation_timestamp=timestamp,
            )

        else:
            raise ValueError(f"Unsupported ECRG operating mode {active_mode}")
