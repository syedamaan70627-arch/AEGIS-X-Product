"""
AEGIS-X API Governance Service.

Provides business logic for Evidence-Calibrated Reliability Governance (ECRG).
Enforces model ownership isolation, invokes ReliabilityGovernor, persists evaluation
and transition records, and saves artifacts to storage.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import List, Optional
import uuid

from aegis.governance.governor import ReliabilityGovernor
from aegis.governance.schemas import (
    ECRGEvidenceContract,
    ECRGGovernanceAction,
    ECRGOperatingMode,
)
from api.core.dependencies import get_governance_repository, get_model_repository
from api.services.storage_service import StorageService


from api.db.models import GovernanceEvaluationRecord, GovernanceTransitionRecord
from api.schemas.governance import (
    GovernanceEvaluationRequest,
    GovernanceEvaluationResponse,
    GovernanceHistoryResponse,
    GovernanceStatusResponse,
)

logger = logging.getLogger(__name__)


class GovernanceService:
    """Business logic for ECRG Governance API."""

    @classmethod
    def evaluate_governance(
        cls,
        request: GovernanceEvaluationRequest,
        user_id: str,
    ) -> GovernanceEvaluationResponse:
        """
        Evaluate reliability governance for a model owned by user_id.

        Raises:
            ValueError: If model is not found or not owned by user_id.
        """
        model_repo = get_model_repository()
        model = model_repo.get_by_id(request.model_id, owner_id=user_id)
        if not model:
            raise ValueError(f"Model '{request.model_id}' not found or access denied.")

        gov_repo = get_governance_repository()
        latest_eval = gov_repo.get_latest_evaluation(request.model_id, owner_id=user_id)

        previous_effective_action: Optional[ECRGGovernanceAction] = None
        if latest_eval and latest_eval.effective_action:
            try:
                previous_effective_action = ECRGGovernanceAction(latest_eval.effective_action)
            except ValueError:
                previous_effective_action = None

        timestamp = request.timestamp or datetime.now(timezone.utc).isoformat()

        # Build ECRGEvidenceContract with fail-safe check
        try:
            evidence = ECRGEvidenceContract(
                model_id=request.model_id,
                dataset_id=request.dataset_id,
                trajectory_id=request.trajectory_id,
                state_index=request.state_index,
                timestamp=timestamp,
                source_analysis_id=request.source_analysis_id,
                ood_score=request.ood_score,
                uncertainty_score=request.uncertainty_score,
                drift_score=request.drift_score,
                fused_risk=request.fused_risk,
                signal_disagreement=request.signal_disagreement,
                ood_drift_redundancy=request.ood_drift_redundancy,
                stress_robustness=request.stress_robustness,
                fault_sensitivity=request.fault_sensitivity,
                memory_similarity=request.memory_similarity,
                temporal_failure_probability=request.temporal_failure_probability,
                early_warning_state=request.early_warning_state,
                prediction_horizon=request.prediction_horizon,
                eventual_failure=request.eventual_failure,
                failure_within_horizon=request.failure_within_horizon,
            )

            governor = ReliabilityGovernor()
            decision_record = governor.evaluate(
                evidence=evidence,
                requested_mode=request.mode,
            )

        except Exception as err:
            logger.error(f"Error during ECRG governance evaluation: {err}", exc_info=True)
            return cls._build_failsafe_response(request, user_id, timestamp, str(err))

        eval_id = decision_record.decision_id
        created_at = decision_record.creation_timestamp

        # Save result JSON via StorageService (serverless & cloud storage safe)
        json_path = StorageService.save_analysis_result(
            f"governance/{request.model_id}/{eval_id}.json",
            decision_record.model_dump(),
            user_id=user_id,
        )


        transition_occurred = previous_effective_action != decision_record.effective_action if previous_effective_action else False

        # Save evaluation record to DB
        eval_record = GovernanceEvaluationRecord(
            id=eval_id,
            user_id=user_id,
            model_id=request.model_id,
            decision_id=decision_record.decision_id,
            state_index=request.state_index,
            operating_mode=decision_record.operating_mode.value,
            raw_action=decision_record.raw_action.value,
            effective_action=decision_record.effective_action.value,
            transition_occurred=transition_occurred,
            evidence_snapshot_hash=decision_record.evidence_snapshot_hash,
            result_path=str(json_path),
            created_at=created_at,
            analysis_id=request.source_analysis_id,
            previous_effective_action=previous_effective_action.value if previous_effective_action else None,
            transition_reason=decision_record.transition_reason,
            p_adverse=decision_record.p_adverse,
            prediction_set_json=json.dumps(decision_record.prediction_set),
            reason_codes_json=json.dumps(decision_record.reason_codes),
            calibrated=decision_record.calibrated,
            calibrator_artifact_id=decision_record.calibrator_artifact_id,
            calibrator_artifact_sha256=decision_record.calibrator_artifact_sha256,
        )
        gov_repo.create_evaluation(eval_record)

        # Record transition if action changed
        if transition_occurred:
            trans_record = GovernanceTransitionRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                model_id=request.model_id,
                evaluation_id=eval_id,
                state_index=request.state_index,
                previous_state=previous_effective_action.value if previous_effective_action else None,
                new_state=decision_record.effective_action.value,
                raw_action=decision_record.raw_action.value,
                transition_reason=decision_record.transition_reason,
                evidence_snapshot_hash=decision_record.evidence_snapshot_hash,
                calibrated=decision_record.calibrated,
                created_at=created_at,
            )
            gov_repo.create_transition(trans_record)

        return cls._record_to_response(eval_record, request.dataset_id, request.signal_disagreement)

    @classmethod
    def get_status(cls, model_id: str, user_id: str) -> GovernanceStatusResponse:
        """
        Retrieve current governance status for a model.

        Raises:
            ValueError: If model is not found or not owned by user_id.
        """
        model_repo = get_model_repository()
        model = model_repo.get_by_id(model_id, owner_id=user_id)
        if not model:
            raise ValueError(f"Model '{model_id}' not found or access denied.")

        gov_repo = get_governance_repository()
        latest_eval = gov_repo.get_latest_evaluation(model_id, owner_id=user_id)

        evaluations = gov_repo.list_evaluations(model_id, owner_id=user_id, limit=1000)
        transitions = gov_repo.list_transitions(model_id, owner_id=user_id, limit=1000)

        if not latest_eval:
            return GovernanceStatusResponse(
                model_id=model_id,
                latest_action=ECRGGovernanceAction.CONTINUE,
                mode=ECRGOperatingMode.EVIDENCE_ONLY,
                warning_severity="LOW",
                consecutive_state_count=0,
                in_cooldown=False,
                last_evaluated_at="",
                total_evaluations=0,
                total_transitions=0,
            )

        eff_action = ECRGGovernanceAction(latest_eval.effective_action)
        warning_severity = (
            "CRITICAL" if eff_action == ECRGGovernanceAction.ESCALATE
            else "HIGH" if eff_action == ECRGGovernanceAction.DEFER
            else "MODERATE" if eff_action == ECRGGovernanceAction.WATCH
            else "LOW"
        )

        return GovernanceStatusResponse(
            model_id=model_id,
            latest_action=eff_action,
            mode=ECRGOperatingMode(latest_eval.operating_mode),
            warning_severity=warning_severity,
            consecutive_state_count=1,
            in_cooldown="COOLDOWN" in (latest_eval.transition_reason or ""),
            last_evaluated_at=latest_eval.created_at,
            total_evaluations=len(evaluations),
            total_transitions=len(transitions),
        )

    @classmethod
    def get_history(
        cls,
        model_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> GovernanceHistoryResponse:
        """
        Retrieve paginated governance evaluation history for a model.

        Raises:
            ValueError: If model is not found or not owned by user_id.
        """
        model_repo = get_model_repository()
        model = model_repo.get_by_id(model_id, owner_id=user_id)
        if not model:
            raise ValueError(f"Model '{model_id}' not found or access denied.")

        gov_repo = get_governance_repository()
        all_evals = gov_repo.list_evaluations(model_id, owner_id=user_id, limit=1000, offset=0)
        total = len(all_evals)

        paginated = gov_repo.list_evaluations(model_id, owner_id=user_id, limit=limit, offset=offset)

        eval_responses = [
            cls._record_to_response(e, dataset_id="evaluated_dataset", signal_disagreement=0.0)
            for e in paginated
        ]

        return GovernanceHistoryResponse(
            model_id=model_id,
            total=total,
            limit=limit,
            offset=offset,
            evaluations=eval_responses,
        )

    @classmethod
    def _record_to_response(
        cls,
        rec: GovernanceEvaluationRecord,
        dataset_id: str,
        signal_disagreement: float,
    ) -> GovernanceEvaluationResponse:
        """Convert a GovernanceEvaluationRecord DB object to an API GovernanceEvaluationResponse."""
        eff_action = ECRGGovernanceAction(rec.effective_action)
        warning_severity = (
            "CRITICAL" if eff_action == ECRGGovernanceAction.ESCALATE
            else "HIGH" if eff_action == ECRGGovernanceAction.DEFER
            else "MODERATE" if eff_action == ECRGGovernanceAction.WATCH
            else "LOW"
        )
        banner = "FORMALLY CALIBRATED RISK BOUND" if rec.calibrated else "LABEL-FREE GOVERNANCE"
        reason_codes = json.loads(rec.reason_codes_json) if rec.reason_codes_json else []

        return GovernanceEvaluationResponse(
            evaluation_id=rec.id,
            model_id=rec.model_id,
            user_id=rec.user_id,
            dataset_id=dataset_id,
            mode=ECRGOperatingMode(rec.operating_mode),
            action=eff_action,
            warning_severity=warning_severity,
            certification_banner=banner,
            calibrated=rec.calibrated,
            primary_supporting_signal="fused_risk",
            supporting_evidence=[],
            contradictory_evidence=[],
            signal_disagreement_index=signal_disagreement,
            consecutive_state_count=1,
            in_cooldown="COOLDOWN" in (rec.transition_reason or ""),
            state_transition_occurred=rec.transition_occurred,
            evidence_snapshot_hash=rec.evidence_snapshot_hash,
            p_adverse=rec.p_adverse or 0.0,
            transition_reason=rec.transition_reason or "",
            reason_codes=reason_codes,
            result_json_path=rec.result_path,
            created_at=rec.created_at,
        )

    @classmethod
    def _build_failsafe_response(
        cls,
        request: GovernanceEvaluationRequest,
        user_id: str,
        timestamp: str,
        error_msg: str,
    ) -> GovernanceEvaluationResponse:
        """Construct fail-safe ESCALATE response when evidence is corrupted or processing fails."""
        eval_id = str(uuid.uuid4())
        gov_repo = get_governance_repository()

        reason_codes = ["CRITICAL_EVIDENCE_CORRUPTED", "SAFE_ESCALATION_TRIGGERED"]
        eval_record = GovernanceEvaluationRecord(
            id=eval_id,
            user_id=user_id,
            model_id=request.model_id,
            decision_id=eval_id,
            state_index=request.state_index,
            operating_mode=request.mode.value,
            raw_action=ECRGGovernanceAction.ESCALATE.value,
            effective_action=ECRGGovernanceAction.ESCALATE.value,
            transition_occurred=True,
            evidence_snapshot_hash="corrupted_hash",
            result_path="",
            created_at=timestamp,
            transition_reason=f"Safe escalation triggered due to error: {error_msg}",
            p_adverse=1.0,
            reason_codes_json=json.dumps(reason_codes),
            calibrated=False,
        )
        gov_repo.create_evaluation(eval_record)

        return cls._record_to_response(eval_record, request.dataset_id, 1.0)
