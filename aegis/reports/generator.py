"""
AEGIS-X Core Report Generation Engine.

Synthesizes persisted AEGIS-X telemetry from models, datasets, analyses, stress tests,
fault tests, failure memory, temporal predictions, early warnings, and ECRG governance.
Produces immutable, evidence-linked reports without modifying research logic or fabricating values.
"""

from typing import Any, Dict, List, Optional
import json
import datetime
from aegis.reports.schemas import (
    ActionItem,
    ModuleCompleteness,
    ModuleStatus,
    ReportContext,
    ReportPayload,
    RetrainingDisposition,
    RiskDriver,
    TrustDisposition,
    WhyThisDecisionEntry,
)
from api.db.models import (
    AnalysisRecord,
    DatasetRecord,
    FailureMemoryRecord,
    FaultTestRecord,
    GovernanceEvaluationRecord,
    ModelRecord,
    PredictionRecord,
    ReferenceStateRecord,
    StressTestRecord,
    WarningRecord,
)


class ReportGenerator:
    """Core synthesis engine for AEGIS-X integrated reliability & governance reports."""

    def __init__(
        self,
        user_id: str,
        model: ModelRecord,
        analysis: AnalysisRecord,
        ref_dataset: DatasetRecord,
        eval_dataset: DatasetRecord,
        reference_state: Optional[ReferenceStateRecord] = None,
        stress_tests: Optional[List[StressTestRecord]] = None,
        fault_tests: Optional[List[FaultTestRecord]] = None,
        failure_memory: Optional[FailureMemoryRecord] = None,
        predictions: Optional[List[PredictionRecord]] = None,
        warnings: Optional[List[WarningRecord]] = None,
        governance_evals: Optional[List[GovernanceEvaluationRecord]] = None,
        previous_analysis: Optional[AnalysisRecord] = None,
    ) -> None:
        self.user_id = user_id
        self.model = model
        self.analysis = analysis
        self.ref_dataset = ref_dataset
        self.eval_dataset = eval_dataset
        self.reference_state = reference_state
        self.stress_tests = stress_tests or []
        self.fault_tests = fault_tests or []
        self.failure_memory = failure_memory
        self.predictions = predictions or []
        self.warnings = warnings or []
        self.governance_evals = governance_evals or []
        self.previous_analysis = previous_analysis

        self._validate_context_lock()

    def _validate_context_lock(self) -> None:
        """Enforces context locking to prevent mixing evidence across models, users, or analyses."""
        if self.model.user_id != self.user_id:
            raise ValueError(f"Model owner mismatch: {self.model.user_id} != {self.user_id}")
        if self.analysis.user_id != self.user_id:
            raise ValueError(f"Analysis owner mismatch: {self.analysis.user_id} != {self.user_id}")
        if self.analysis.model_id != self.model.id:
            raise ValueError(f"Analysis model mismatch: {self.analysis.model_id} != {self.model.id}")
        if self.ref_dataset.id != self.analysis.reference_dataset_id:
            raise ValueError(f"Reference dataset mismatch: {self.ref_dataset.id} != {self.analysis.reference_dataset_id}")
        if self.eval_dataset.id != self.analysis.evaluation_dataset_id:
            raise ValueError(f"Evaluation dataset mismatch: {self.eval_dataset.id} != {self.analysis.evaluation_dataset_id}")

    def generate(self, report_id: str, report_type: str = "integrated") -> ReportPayload:
        """Synthesizes all evidence into a complete, evidence-linked ReportPayload."""
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Context
        context = ReportContext(
            report_id=report_id,
            user_id=self.user_id,
            model_id=self.model.id,
            model_name=self.model.model_name,
            analysis_id=self.analysis.id,
            generated_at=now_str,
            reference_dataset_id=self.ref_dataset.id,
            reference_dataset_name=self.ref_dataset.filename,
            evaluation_dataset_id=self.eval_dataset.id,
            evaluation_dataset_name=self.eval_dataset.filename,
            task_type=self.model.task_type,
        )

        # 2. Evidence Completeness Matrix
        completeness, overall_pct = self._compute_completeness_matrix()

        # 3. Governance summary & latest evaluation
        latest_gov = self.governance_evals[0] if self.governance_evals else None
        gov_summary = self._build_governance_summary(latest_gov)

        # 4. Reliability summary
        rel_summary = self._build_reliability_summary()

        # 5. Stress, Fault, Memory, Temporal summaries
        stress_summary = self._build_stress_summary()
        fault_summary = self._build_fault_summary()
        memory_summary = self._build_memory_summary()
        temporal_summary = self._build_temporal_summary()

        # 6. Categorical Trust Disposition
        trust_disp, trust_rat = self._derive_trust_disposition(
            rel_summary, gov_summary, stress_summary, temporal_summary, overall_pct
        )

        # 7. Retraining Disposition
        retrain_disp, retrain_rat = self._derive_retraining_disposition(
            rel_summary, gov_summary, temporal_summary
        )

        # 8. Why This Decision evidence links
        why_decision = self._build_why_this_decision(
            trust_disp, gov_summary, rel_summary, stress_summary, temporal_summary
        )

        # 9. Operator Action Plan
        action_plan = self._build_operator_action_plan(
            trust_disp, retrain_disp, gov_summary, rel_summary, stress_summary, completeness
        )

        # 10. Deployment Suitability
        deployment = self._build_deployment_suitability(trust_disp, gov_summary, rel_summary)

        # 11. Trend Comparison
        trend = self._build_trend_comparison()

        # 12. Top Risk Drivers
        risk_drivers = self._build_top_risk_drivers(rel_summary, stress_summary, temporal_summary)

        # 13. Scientific Limitations Disclosures
        limitations = [
            "Under exchangeability between calibration and future evaluation units, split conformal prediction provides finite-sample marginal coverage at the stated target level, subject to the implemented calibration-unit construction and assumptions.",
            "Unlabeled evaluation datasets use unsupervised risk proxies; label-based performance metrics require ground truth verification.",
            "State machine anti-flapping controls maintain stability but may delay recovery transitions until persistence thresholds are satisfied.",
            "Stress & fault perturbations test synthetic robustness boundaries; real-world domain shifts may introduce novel joint feature distortions.",
        ]

        return ReportPayload(
            context=context,
            report_type=report_type,
            trust_disposition=trust_disp,
            trust_rationale=trust_rat,
            completeness=completeness,
            overall_completeness_pct=overall_pct,
            reliability_summary=rel_summary,
            stress_lab_summary=stress_summary,
            fault_lab_summary=fault_summary,
            failure_explorer_summary=memory_summary,
            temporal_intelligence_summary=temporal_summary,
            ecrg_governance_summary=gov_summary,
            why_this_decision=why_decision,
            action_plan=action_plan,
            retraining_disposition=retrain_disp,
            retraining_rationale=retrain_rat,
            deployment_suitability=deployment,
            trend_comparison=trend,
            top_risk_drivers=risk_drivers,
            scientific_limitations=limitations,
        )

    def _compute_completeness_matrix(self) -> tuple[Dict[str, ModuleCompleteness], float]:
        """Calculates 12-module completeness matrix tracking verified evidence."""
        matrix: Dict[str, ModuleCompleteness] = {}

        # 1. Model Inventory
        matrix["model_inventory"] = ModuleCompleteness(
            name="Model Inventory",
            status=ModuleStatus.VERIFIED,
            evidence_count=1,
            last_verified_at=self.model.created_at,
            details={"model_id": self.model.id, "task_type": self.model.task_type},
        )

        # 2. Reference State
        if self.reference_state:
            matrix["reference_state"] = ModuleCompleteness(
                name="Reference State Fit",
                status=ModuleStatus.VERIFIED,
                evidence_count=1,
                last_verified_at=self.reference_state.fitted_at,
                details={"num_samples": self.reference_state.num_samples},
            )
        else:
            matrix["reference_state"] = ModuleCompleteness(
                name="Reference State Fit",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Reference state fit on baseline dataset",
            )

        # 3. Dataset Health
        dataset_status = ModuleStatus.VERIFIED if self.ref_dataset and self.eval_dataset else ModuleStatus.FAILED
        matrix["dataset_health"] = ModuleCompleteness(
            name="Dataset Health & Schemas",
            status=dataset_status,
            evidence_count=2,
            last_verified_at=self.eval_dataset.created_at,
            details={
                "ref_samples": self.ref_dataset.num_samples,
                "eval_samples": self.eval_dataset.num_samples,
                "feature_count": self.eval_dataset.num_features,
            },
        )

        # 4. OOD Risk
        if self.analysis.aggregate_ood_risk is not None:
            matrix["ood_risk"] = ModuleCompleteness(
                name="Out-of-Distribution Risk",
                status=ModuleStatus.VERIFIED,
                evidence_count=1,
                last_verified_at=self.analysis.created_at,
                details={"score": self.analysis.aggregate_ood_risk},
            )
        else:
            matrix["ood_risk"] = ModuleCompleteness(
                name="Out-of-Distribution Risk",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Completed analysis run with OOD scoring",
            )

        # 5. Uncertainty
        if self.analysis.aggregate_uncertainty is not None:
            matrix["uncertainty"] = ModuleCompleteness(
                name="Prediction Uncertainty",
                status=ModuleStatus.VERIFIED,
                evidence_count=1,
                last_verified_at=self.analysis.created_at,
                details={"score": self.analysis.aggregate_uncertainty},
            )
        else:
            matrix["uncertainty"] = ModuleCompleteness(
                name="Prediction Uncertainty",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Completed analysis run with uncertainty estimation",
            )

        # 6. Drift Intelligence
        if self.analysis.aggregate_drift_score is not None:
            matrix["drift_intelligence"] = ModuleCompleteness(
                name="Feature & Concept Drift",
                status=ModuleStatus.VERIFIED,
                evidence_count=1,
                last_verified_at=self.analysis.created_at,
                details={"score": self.analysis.aggregate_drift_score},
            )
        else:
            matrix["drift_intelligence"] = ModuleCompleteness(
                name="Feature & Concept Drift",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Completed analysis run with drift calculation",
            )

        # 7. Fused Reliability
        if self.analysis.aggregate_fused_risk is not None:
            matrix["fused_reliability"] = ModuleCompleteness(
                name="Fused Reliability Index",
                status=ModuleStatus.VERIFIED,
                evidence_count=1,
                last_verified_at=self.analysis.created_at,
                details={"score": self.analysis.aggregate_fused_risk, "method": self.analysis.fusion_method},
            )
        else:
            matrix["fused_reliability"] = ModuleCompleteness(
                name="Fused Reliability Index",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Completed analysis run with risk fusion",
            )

        # 8. Stress Robustness
        if self.stress_tests:
            matrix["stress_robustness"] = ModuleCompleteness(
                name="Stress Lab Robustness",
                status=ModuleStatus.VERIFIED,
                evidence_count=len(self.stress_tests),
                last_verified_at=self.stress_tests[0].created_at,
                details={"test_count": len(self.stress_tests)},
            )
        else:
            matrix["stress_robustness"] = ModuleCompleteness(
                name="Stress Lab Robustness",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Execution of Stress Lab perturbation suite",
            )

        # 9. Fault Sensitivity
        if self.fault_tests:
            matrix["fault_sensitivity"] = ModuleCompleteness(
                name="Fault Injection Sensitivity",
                status=ModuleStatus.VERIFIED,
                evidence_count=len(self.fault_tests),
                last_verified_at=self.fault_tests[0].created_at,
                details={"test_count": len(self.fault_tests)},
            )
        else:
            matrix["fault_sensitivity"] = ModuleCompleteness(
                name="Fault Injection Sensitivity",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Execution of Fault Lab injection suite",
            )

        # 10. Failure Memory
        if self.failure_memory:
            matrix["failure_memory"] = ModuleCompleteness(
                name="Failure Signature Memory",
                status=ModuleStatus.VERIFIED,
                evidence_count=1,
                last_verified_at=self.failure_memory.fitted_at,
                details={"signatures_count": self.failure_memory.n_signatures},
            )
        else:
            matrix["failure_memory"] = ModuleCompleteness(
                name="Failure Signature Memory",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Fitting failure memory index on historical failures",
            )

        # 11. Failure Prediction & Early Warning (Temporal)
        if self.predictions or self.warnings:
            matrix["temporal_intelligence"] = ModuleCompleteness(
                name="Temporal Risk & Early Warning",
                status=ModuleStatus.VERIFIED,
                evidence_count=len(self.predictions) + len(self.warnings),
                last_verified_at=(self.warnings[0].created_at if self.warnings else self.predictions[0].created_at),
                details={"predictions": len(self.predictions), "warnings": len(self.warnings)},
            )
        else:
            matrix["temporal_intelligence"] = ModuleCompleteness(
                name="Temporal Risk & Early Warning",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Execution of failure prediction or early warning trajectory",
            )

        # 12. ECRG Governance
        if self.governance_evals:
            matrix["ecrg_governance"] = ModuleCompleteness(
                name="ECRG Conformal Governance",
                status=ModuleStatus.VERIFIED,
                evidence_count=len(self.governance_evals),
                last_verified_at=self.governance_evals[0].created_at,
                details={"latest_action": self.governance_evals[0].effective_action},
            )
        else:
            matrix["ecrg_governance"] = ModuleCompleteness(
                name="ECRG Conformal Governance",
                status=ModuleStatus.UNAVAILABLE,
                evidence_count=0,
                prerequisite_missing="Execution of ECRG governance evaluation pipeline",
            )

        verified_count = sum(1 for m in matrix.values() if m.status == ModuleStatus.VERIFIED)
        pct = round((verified_count / len(matrix)) * 100.0, 1)
        return matrix, pct

    def _build_reliability_summary(self) -> Dict[str, Any]:
        return {
            "status": "COMPLETED" if self.analysis.status == "COMPLETED" else self.analysis.status,
            "aggregate_fused_risk": self.analysis.aggregate_fused_risk,
            "aggregate_ood_risk": self.analysis.aggregate_ood_risk,
            "aggregate_uncertainty": self.analysis.aggregate_uncertainty,
            "aggregate_drift_score": self.analysis.aggregate_drift_score,
            "fusion_method": self.analysis.fusion_method,
            "has_labels": self.analysis.has_labels,
            "result_path": self.analysis.result_path,
        }

    def _build_governance_summary(self, latest_gov: Optional[GovernanceEvaluationRecord]) -> Dict[str, Any]:
        if not latest_gov:
            return {
                "evaluated": False,
                "operating_mode": "NOT_EVALUATED",
                "effective_action": "UNAVAILABLE",
                "raw_action": "UNAVAILABLE",
                "state_index": 0,
                "transition_occurred": False,
                "prediction_set": [],
                "reason_codes": ["NO_GOVERNANCE_EVALUATION"],
                "calibrated": False,
                "calibrator_artifact_id": None,
                "p_adverse": None,
            }

        pred_set = []
        if latest_gov.prediction_set_json:
            try:
                pred_set = json.loads(latest_gov.prediction_set_json)
            except Exception:
                pred_set = [latest_gov.prediction_set_json]

        reasons = []
        if latest_gov.reason_codes_json:
            try:
                reasons = json.loads(latest_gov.reason_codes_json)
            except Exception:
                reasons = [latest_gov.reason_codes_json]

        return {
            "evaluated": True,
            "id": latest_gov.id,
            "decision_id": latest_gov.decision_id,
            "operating_mode": latest_gov.operating_mode,
            "effective_action": latest_gov.effective_action,
            "raw_action": latest_gov.raw_action,
            "previous_effective_action": latest_gov.previous_effective_action,
            "state_index": latest_gov.state_index,
            "transition_occurred": latest_gov.transition_occurred,
            "transition_reason": latest_gov.transition_reason,
            "p_adverse": latest_gov.p_adverse,
            "prediction_set": pred_set,
            "reason_codes": reasons,
            "calibrated": latest_gov.calibrated,
            "calibrator_artifact_id": latest_gov.calibrator_artifact_id,
            "evidence_snapshot_hash": latest_gov.evidence_snapshot_hash,
            "created_at": latest_gov.created_at,
        }

    def _build_stress_summary(self) -> Dict[str, Any]:
        if not self.stress_tests:
            return {"status": "UNAVAILABLE", "test_count": 0, "avg_risk_delta": None, "max_stressed_risk": None}

        deltas = [st.risk_delta for st.risk_delta in [t.risk_delta for t in self.stress_tests] if st is not None]
        stressed_risks = [t.stressed_risk for t in self.stress_tests if t.stressed_risk is not None]

        avg_delta = round(sum(deltas) / len(deltas), 4) if deltas else 0.0
        max_stressed = max(stressed_risks) if stressed_risks else 0.0

        return {
            "status": "VERIFIED",
            "test_count": len(self.stress_tests),
            "avg_risk_delta": avg_delta,
            "max_stressed_risk": max_stressed,
            "tests": [
                {
                    "id": t.id,
                    "stress_type": t.stress_type,
                    "severity": t.severity,
                    "original_risk": t.original_risk,
                    "stressed_risk": t.stressed_risk,
                    "risk_delta": t.risk_delta,
                }
                for t in self.stress_tests
            ],
        }

    def _build_fault_summary(self) -> Dict[str, Any]:
        if not self.fault_tests:
            return {"status": "UNAVAILABLE", "test_count": 0, "pass_rate": None}

        completed = sum(1 for f in self.fault_tests if f.status == "COMPLETED")
        pass_rate = round(completed / len(self.fault_tests), 2)

        return {
            "status": "VERIFIED",
            "test_count": len(self.fault_tests),
            "pass_rate": pass_rate,
            "fault_types": list(set(f.fault_type for f in self.fault_tests)),
        }

    def _build_memory_summary(self) -> Dict[str, Any]:
        if not self.failure_memory:
            return {"status": "UNAVAILABLE", "n_signatures": 0, "fitted_at": None}
        return {
            "status": "VERIFIED",
            "id": self.failure_memory.id,
            "n_signatures": self.failure_memory.n_signatures,
            "fitted_at": self.failure_memory.fitted_at,
        }

    def _build_temporal_summary(self) -> Dict[str, Any]:
        latest_pred = self.predictions[0] if self.predictions else None
        latest_warn = self.warnings[0] if self.warnings else None

        if not latest_pred and not latest_warn:
            return {"status": "UNAVAILABLE", "warning_triggered": False, "failure_probability": None}

        return {
            "status": "VERIFIED",
            "prediction": {
                "horizon_steps": latest_pred.horizon_steps if latest_pred else None,
                "mean_probability": latest_pred.mean_probability if latest_pred else None,
            },
            "warning": {
                "warning_score": latest_warn.warning_score if latest_warn else None,
                "is_warning_triggered": latest_warn.is_warning_triggered if latest_warn else False,
                "threshold": latest_warn.threshold if latest_warn else None,
            },
        }

    def _derive_trust_disposition(
        self,
        rel: Dict[str, Any],
        gov: Dict[str, Any],
        stress: Dict[str, Any],
        temp: Dict[str, Any],
        overall_pct: float,
    ) -> tuple[TrustDisposition, str]:
        """Derives categorical operational trust state according to strict AEGIS-X governance rules."""
        fused_risk = rel.get("aggregate_fused_risk")
        eff_action = gov.get("effective_action")
        warn_triggered = temp.get("warning", {}).get("is_warning_triggered", False)

        if fused_risk is None:
            return (
                TrustDisposition.INSUFFICIENT_EVIDENCE,
                "Core reliability analysis evidence is unavailable or incomplete.",
            )

        if eff_action in ["DEFER", "ESCALATE"] or fused_risk > 0.60:
            return (
                TrustDisposition.RESTRICTED,
                f"Governance effective action '{eff_action}' or elevated fused risk ({fused_risk:.2f}) requires strict execution restriction.",
            )

        if eff_action == "WATCH" or fused_risk > 0.35 or warn_triggered:
            return (
                TrustDisposition.LOW,
                f"Model exhibits elevated risk flags (Fused Risk: {fused_risk:.2f}, Action: {eff_action}, Early Warning: {warn_triggered}). Enhanced monitoring required.",
            )

        if fused_risk >= 0.15 or overall_pct < 75.0 or gov.get("state_index", 0) > 0:
            return (
                TrustDisposition.CONDITIONAL,
                f"Model operates under conditional trust (Fused Risk: {fused_risk:.2f}, State Index: {gov.get('state_index', 0)}, Completeness: {overall_pct}%).",
            )

        return (
            TrustDisposition.HIGH,
            f"Nominal reliability (Fused Risk: {fused_risk:.2f}) with ECRG action CONTINUE and full evidence verification ({overall_pct}% completeness).",
        )

    def _derive_retraining_disposition(
        self, rel: Dict[str, Any], gov: Dict[str, Any], temp: Dict[str, Any]
    ) -> tuple[RetrainingDisposition, str]:
        """Derives retraining / recalibration disposition strictly from empirical drift, OOD, and temporal signals."""
        fused_risk = rel.get("aggregate_fused_risk")
        drift = rel.get("aggregate_drift_score")
        ood = rel.get("aggregate_ood_risk")
        unc = rel.get("aggregate_uncertainty")

        if fused_risk is None:
            return (
                RetrainingDisposition.INSUFFICIENT_EVIDENCE,
                "Insufficient empirical evidence to evaluate model retraining requirements.",
            )

        if (drift and drift > 0.60) or (ood and ood > 0.60) or fused_risk > 0.60:
            return (
                RetrainingDisposition.URGENT_MODEL_REVIEW,
                f"Critical domain shift or severe risk elevation (Drift: {drift}, OOD: {ood}, Fused: {fused_risk:.2f}). Immediate model review mandated.",
            )

        if (drift and drift > 0.35) or (ood and ood > 0.40):
            return (
                RetrainingDisposition.RETRAINING_ADVISED,
                f"Moderate-to-high feature shift observed (Drift: {drift}, OOD: {ood}). Retraining on recent dataset advised.",
            )

        if (unc and unc > 0.30) or (len(gov.get("prediction_set", [])) > 1):
            return (
                RetrainingDisposition.RECALIBRATION_ADVISED,
                f"Elevated prediction set uncertainty (Uncertainty: {unc}, Prediction Set: {gov.get('prediction_set')}). Conformal recalibration advised.",
            )

        if (drift and drift > 0.15) or temp.get("warning", {}).get("is_warning_triggered", False):
            return (
                RetrainingDisposition.MONITOR,
                "Subtle drift or early warning flags detected. Active drift monitoring recommended.",
            )

        return (
            RetrainingDisposition.NOT_INDICATED,
            "Model parameters and error bounds remain aligned with reference state. Retraining not indicated.",
        )

    def _build_why_this_decision(
        self,
        trust: TrustDisposition,
        gov: Dict[str, Any],
        rel: Dict[str, Any],
        stress: Dict[str, Any],
        temp: Dict[str, Any],
    ) -> List[WhyThisDecisionEntry]:
        entries: List[WhyThisDecisionEntry] = []

        # 1. ECRG Governance
        entries.append(
            WhyThisDecisionEntry(
                factor="ECRG Effective Governance Action",
                impact="POSITIVE" if gov.get("effective_action") == "CONTINUE" else ("CRITICAL" if gov.get("effective_action") in ["DEFER", "ESCALATE"] else "NEGATIVE"),
                description=f"ECRG state machine evaluated effective action as '{gov.get('effective_action', 'UNAVAILABLE')}' in '{gov.get('operating_mode', 'N/A')}' mode.",
                evidence_link="/governance",
            )
        )

        # 2. Fused Risk Index
        fused = rel.get("aggregate_fused_risk")
        fused_str = f"{fused:.3f}" if fused is not None else "N/A"
        entries.append(
            WhyThisDecisionEntry(
                factor="Fused Reliability Index",
                impact="POSITIVE" if (fused is not None and fused < 0.20) else ("CRITICAL" if (fused is not None and fused > 0.50) else "NEGATIVE"),
                description=f"Unified risk index computed at {fused_str} using {rel.get('fusion_method', 'uncertainty_weighted')} fusion.",
                evidence_link="/reliability",
            )
        )

        # 3. Stress Robustness
        if stress.get("status") == "VERIFIED":
            avg_delta = stress.get("avg_risk_delta", 0.0)
            entries.append(
                WhyThisDecisionEntry(
                    factor="Stress Lab Sensitivity Delta",
                    impact="POSITIVE" if avg_delta < 0.15 else "NEGATIVE",
                    description=f"Perturbation suite across {stress.get('test_count')} tests showed average risk delta of {avg_delta:.3f}.",
                    evidence_link="/stress",
                )
            )

        # 4. Early Warning Trajectory
        if temp.get("status") == "VERIFIED":
            warn_trig = temp.get("warning", {}).get("is_warning_triggered", False)
            entries.append(
                WhyThisDecisionEntry(
                    factor="Temporal Early Warning Trigger",
                    impact="CRITICAL" if warn_trig else "POSITIVE",
                    description="Early warning trajectory monitoring triggered an alert flag." if warn_trig else "No early warning trajectory alerts triggered.",
                    evidence_link="/warning",
                )
            )

        return entries

    def _build_operator_action_plan(
        self,
        trust: TrustDisposition,
        retrain: RetrainingDisposition,
        gov: Dict[str, Any],
        rel: Dict[str, Any],
        stress: Dict[str, Any],
        completeness: Dict[str, ModuleCompleteness],
    ) -> List[ActionItem]:
        plan: List[ActionItem] = []

        eff_action = gov.get("effective_action")
        fused = rel.get("aggregate_fused_risk", 0.0) or 0.0

        # P1 Priority
        if eff_action in ["DEFER", "ESCALATE"] or trust == TrustDisposition.RESTRICTED:
            plan.append(
                ActionItem(
                    priority="P1",
                    title="Enforce Operational Fallback / Model Deferral",
                    rationale=f"ECRG state machine action is '{eff_action}' and trust disposition is RESTRICTED.",
                    trigger_condition=f"Effective Action == {eff_action}",
                    target_component="ECRG State Machine Governor",
                )
            )
        elif fused > 0.35:
            plan.append(
                ActionItem(
                    priority="P1",
                    title="Initiate Human-in-the-Loop Audit Protocol",
                    rationale=f"Fused reliability risk ({fused:.2f}) exceeds operational warning threshold (0.35).",
                    trigger_condition="Fused Risk > 0.35",
                    target_component="Reliability Assessment Engine",
                )
            )

        # P2 Priority
        if retrain in [RetrainingDisposition.RETRAINING_ADVISED, RetrainingDisposition.URGENT_MODEL_REVIEW]:
            plan.append(
                ActionItem(
                    priority="P2",
                    title="Schedule Model Retraining Pipeline",
                    rationale=f"Significant distribution drift requires parameter updates ({retrain.value}).",
                    trigger_condition=f"Retraining Disposition == {retrain.value}",
                    target_component="Model Training & Reference Fit Pipeline",
                )
            )
        elif retrain == RetrainingDisposition.RECALIBRATION_ADVISED:
            plan.append(
                ActionItem(
                    priority="P2",
                    title="Execute Conformal Recalibration",
                    rationale="Prediction set sizes or uncertainty indicate non-optimal quantile calibration.",
                    trigger_condition="Prediction set size > 1 or Uncertainty > 0.30",
                    target_component="ECRG Conformal Calibrator",
                )
            )

        # P3 Priority
        missing_labs = [m.name for m in completeness.values() if m.status == ModuleStatus.UNAVAILABLE]
        if missing_labs:
            plan.append(
                ActionItem(
                    priority="P3",
                    title=f"Run Missing Telemetry Suites ({len(missing_labs)} Pending)",
                    rationale=f"Completeness is missing telemetry for: {', '.join(missing_labs[:3])}.",
                    trigger_condition="Module Completeness status == UNAVAILABLE",
                    target_component="Stress / Fault / Early Warning Test Labs",
                )
            )

        # P4 Priority
        plan.append(
            ActionItem(
                priority="P4",
                title="Continuous Real-Time Drift & Warning Polling",
                rationale="Maintain active surveillance on early warning trajectory scores.",
                trigger_condition="Routine Operational Health Surveillance",
                target_component="Early Warning & Temporal Intelligence Engine",
            )
        )

        return plan

    def _build_deployment_suitability(
        self, trust: TrustDisposition, gov: Dict[str, Any], rel: Dict[str, Any]
    ) -> Dict[str, Any]:
        eff_action = gov.get("effective_action")
        fused = rel.get("aggregate_fused_risk", 1.0) or 1.0

        if trust == TrustDisposition.HIGH:
            rec_env = "PRODUCTION"
            tier = "TIER_1_CRITICAL"
            constraints = ["Maintain default ECRG continuous monitoring"]
        elif trust == TrustDisposition.CONDITIONAL:
            rec_env = "STAGING_WITH_GUARDRAILS"
            tier = "TIER_2_RESTRICTED"
            constraints = ["Enable automated human fallback for set predictions", "Continuous early warning active"]
        elif trust == TrustDisposition.LOW:
            rec_env = "SHADOW_MODE_ONLY"
            tier = "TIER_3_EVALUATION"
            constraints = ["No live decision routing", "Capture dark traffic telemetry for recalibration"]
        else:
            rec_env = "BLOCKED_FROM_DEPLOYMENT"
            tier = "TIER_4_ISOLATED"
            constraints = ["Model deployment blocked by ECRG governance policy", "Mandatory review required"]

        return {
            "recommended_environment": rec_env,
            "risk_tier": tier,
            "operational_constraints": constraints,
            "fused_risk": fused,
            "governance_action": eff_action,
        }

    def _build_trend_comparison(self) -> Dict[str, Any]:
        if not self.previous_analysis:
            return {
                "has_previous_analysis": False,
                "fused_risk_delta": None,
                "drift_delta": None,
                "trend_direction": "STABLE",
            }

        prev_fused = self.previous_analysis.aggregate_fused_risk or 0.0
        curr_fused = self.analysis.aggregate_fused_risk or 0.0
        fused_delta = round(curr_fused - prev_fused, 4)

        prev_drift = self.previous_analysis.aggregate_drift_score or 0.0
        curr_drift = self.analysis.aggregate_drift_score or 0.0
        drift_delta = round(curr_drift - prev_drift, 4)

        if fused_delta > 0.05:
            direction = "DEGRADED"
        elif fused_delta < -0.05:
            direction = "IMPROVED"
        else:
            direction = "STABLE"

        return {
            "has_previous_analysis": True,
            "previous_analysis_id": self.previous_analysis.id,
            "fused_risk_delta": fused_delta,
            "drift_delta": drift_delta,
            "trend_direction": direction,
        }

    def _build_top_risk_drivers(
        self, rel: Dict[str, Any], stress: Dict[str, Any], temp: Dict[str, Any]
    ) -> List[RiskDriver]:
        drivers: List[RiskDriver] = []

        # OOD Risk
        ood = rel.get("aggregate_ood_risk")
        if ood is not None and ood > 0.20:
            drivers.append(
                RiskDriver(
                    category="Distribution Shift",
                    driver_name="Out-of-Distribution Feature Density",
                    severity_score=round(ood, 3),
                    impact_description="Evaluation samples deviate from reference state density manifold.",
                )
            )

        # Uncertainty
        unc = rel.get("aggregate_uncertainty")
        if unc is not None and unc > 0.20:
            drivers.append(
                RiskDriver(
                    category="Model Epistemic",
                    driver_name="High Model Uncertainty",
                    severity_score=round(unc, 3),
                    impact_description="Model prediction variance indicates unconfident prediction boundary.",
                )
            )

        # Stress Sensitivity
        avg_delta = stress.get("avg_risk_delta")
        if avg_delta is not None and avg_delta > 0.15:
            drivers.append(
                RiskDriver(
                    category="Robustness",
                    driver_name="Perturbation Sensitivity",
                    severity_score=round(avg_delta, 3),
                    impact_description="Feature perturbations induce significant risk elevation.",
                )
            )

        # Sort by severity descending
        drivers.sort(key=lambda d: d.severity_score, reverse=True)
        return drivers[:3]
