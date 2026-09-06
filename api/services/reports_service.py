"""
AEGIS-X Reports API Service Layer.

Orchestrates report generation, database snapshot persistence, file storage,
and export formatting (JSON, CSV, HTML/PDF) while enforcing owner context isolation.
"""

import json
import uuid
import datetime
from typing import Any, Dict, List, Optional

from aegis.core.exceptions import AegisError
from aegis.reports.generator import ReportGenerator
from aegis.reports.schemas import ReportPayload
from api.core.dependencies import (
    get_analysis_repository,
    get_dataset_repository,
    get_failure_memory_repository,
    get_fault_test_repository,
    get_governance_repository,
    get_model_repository,
    get_prediction_repository,
    get_reference_state_repository,
    get_report_repository,
    get_storage_provider,
    get_stress_test_repository,
    get_warning_repository,
)
from api.db.models import ReportRecord


class ReportServiceError(AegisError):
    """Raised when report generation or export fails."""
    pass


class ReportsService:
    """Service layer managing AEGIS-X report creation, persistence, and exports."""

    def __init__(self) -> None:
        self.model_repo = get_model_repository()
        self.dataset_repo = get_dataset_repository()
        self.ref_state_repo = get_reference_state_repository()
        self.analysis_repo = get_analysis_repository()
        self.stress_repo = get_stress_test_repository()
        self.fault_repo = get_fault_test_repository()
        self.memory_repo = get_failure_memory_repository()
        self.prediction_repo = get_prediction_repository()
        self.warning_repo = get_warning_repository()
        self.governance_repo = get_governance_repository()
        self.report_repo = get_report_repository()
        self.storage = get_storage_provider()

    def generate_report(
        self,
        user_id: str,
        model_id: str,
        analysis_id: str,
        report_type: str = "integrated",
    ) -> ReportRecord:
        """Generates and persists an immutable AEGIS-X report for the given context."""
        # 1. Fetch & validate model
        model = self.model_repo.get_by_id(model_id, owner_id=user_id)
        if not model:
            raise FileNotFoundError(f"Model with id '{model_id}' not found for user '{user_id}'.")

        # 2. Fetch & validate analysis
        analysis = self.analysis_repo.get_by_id(analysis_id, owner_id=user_id)
        if not analysis:
            raise FileNotFoundError(f"Analysis with id '{analysis_id}' not found for user '{user_id}'.")
        if analysis.model_id != model_id:
            raise ValueError(f"Analysis '{analysis_id}' belongs to model '{analysis.model_id}', not '{model_id}'.")

        # 3. Fetch datasets
        ref_dataset = self.dataset_repo.get_by_id(analysis.reference_dataset_id, owner_id=user_id)
        if not ref_dataset:
            raise FileNotFoundError(f"Reference dataset '{analysis.reference_dataset_id}' not found.")

        eval_dataset = self.dataset_repo.get_by_id(analysis.evaluation_dataset_id, owner_id=user_id)
        if not eval_dataset:
            raise FileNotFoundError(f"Evaluation dataset '{analysis.evaluation_dataset_id}' not found.")

        # 4. Fetch telemetry modules
        ref_state = self.ref_state_repo.get_by_model_id(model_id, owner_id=user_id)
        stress_tests = self.stress_repo.list_by_model(model_id, owner_id=user_id)
        fault_tests = self.fault_repo.list_by_model(model_id, owner_id=user_id)
        memory_list = self.memory_repo.list_by_model(model_id, owner_id=user_id)
        failure_memory = memory_list[0] if memory_list else None
        predictions = self.prediction_repo.list_by_model(model_id, owner_id=user_id)
        warnings = self.warning_repo.list_by_model(model_id, owner_id=user_id)
        governance_evals = self.governance_repo.list_evaluations(model_id, owner_id=user_id)

        # Fetch previous analysis for trend comparison if available
        all_analyses = self.analysis_repo.list_by_model(model_id, owner_id=user_id)
        previous_analysis = None
        for a in all_analyses:
            if a.id != analysis_id:
                previous_analysis = a
                break

        # 5. Generate Report Payload
        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        generator = ReportGenerator(
            user_id=user_id,
            model=model,
            analysis=analysis,
            ref_dataset=ref_dataset,
            eval_dataset=eval_dataset,
            reference_state=ref_state,
            stress_tests=stress_tests,
            fault_tests=fault_tests,
            failure_memory=failure_memory,
            predictions=predictions,
            warnings=warnings,
            governance_evals=governance_evals,
            previous_analysis=previous_analysis,
        )
        payload: ReportPayload = generator.generate(report_id=report_id, report_type=report_type)

        # 6. Save payload file in storage
        snapshot_dict = payload.model_dump()
        result_path = f"reports/{report_id}.json"
        self.storage.save_json(result_path, snapshot_dict)

        # 7. Create DB record
        title_map = {
            "reliability": "Reliability Assessment Summary",
            "model_trust": "Model Trust & Governance Report",
            "governance": "Governance Decision Report",
            "integrated": "AEGIS-X Integrated Reliability & Governance Report",
        }
        title = title_map.get(report_type, "AEGIS-X Report")

        record = ReportRecord(
            id=report_id,
            user_id=user_id,
            model_id=model_id,
            analysis_id=analysis_id,
            report_type=report_type,
            title=title,
            disposition=payload.trust_disposition.value,
            completeness_score=payload.overall_completeness_pct,
            result_path=result_path,
            snapshot_json=snapshot_dict,
            created_at=payload.context.generated_at,
        )

        return self.report_repo.create(record)

    def get_report(self, report_id: str, user_id: str) -> ReportRecord:
        """Retrieves report by ID ensuring user authorization."""
        report = self.report_repo.get_by_id(report_id, owner_id=user_id)
        if not report:
            raise FileNotFoundError(f"Report '{report_id}' not found for user '{user_id}'.")
        return report

    def list_reports_by_model(self, model_id: str, user_id: str, limit: int = 50, offset: int = 0) -> List[ReportRecord]:
        """Lists report history for a model."""
        return self.report_repo.list_by_model(model_id, owner_id=user_id, limit=limit, offset=offset)

    def export_report(self, report_id: str, user_id: str, export_format: str) -> tuple[str, str]:
        """Exports a report as JSON, CSV, or HTML string with correct content-type header."""
        report = self.get_report(report_id, user_id=user_id)
        snapshot = report.snapshot_json if isinstance(report.snapshot_json, dict) else json.loads(report.snapshot_json)

        fmt = export_format.lower()

        if fmt == "json":
            content = json.dumps(snapshot, indent=2)
            media_type = "application/json"
        elif fmt == "csv":
            content = self._format_report_csv(snapshot)
            media_type = "text/csv"
        elif fmt in ["pdf", "html"]:
            content = self._format_report_html(snapshot)
            media_type = "text/html"
        else:
            raise ValueError(f"Unsupported export format '{export_format}'. Must be json, csv, or pdf.")

        return content, media_type

    def _format_report_csv(self, snapshot: Dict[str, Any]) -> str:
        ctx = snapshot.get("context", {})
        lines = [
            "Section,Metric,Value",
            f"Context,Report ID,{ctx.get('report_id')}",
            f"Context,Model Name,{ctx.get('model_name')}",
            f"Context,Analysis ID,{ctx.get('analysis_id')}",
            f"Context,Generated At,{ctx.get('generated_at')}",
            f"Executive,Trust Disposition,{snapshot.get('trust_disposition')}",
            f"Executive,Completeness Pct,{snapshot.get('overall_completeness_pct')}%",
            f"Executive,Retraining Disposition,{snapshot.get('retraining_disposition')}",
            f"Reliability,Fused Risk,{snapshot.get('reliability_summary', {}).get('aggregate_fused_risk')}",
            f"Reliability,OOD Risk,{snapshot.get('reliability_summary', {}).get('aggregate_ood_risk')}",
            f"Reliability,Uncertainty,{snapshot.get('reliability_summary', {}).get('aggregate_uncertainty')}",
            f"Reliability,Drift Score,{snapshot.get('reliability_summary', {}).get('aggregate_drift_score')}",
            f"Governance,Operating Mode,{snapshot.get('ecrg_governance_summary', {}).get('operating_mode')}",
            f"Governance,Effective Action,{snapshot.get('ecrg_governance_summary', {}).get('effective_action')}",
            f"Governance,State Index,{snapshot.get('ecrg_governance_summary', {}).get('state_index')}",
        ]
        return "\n".join(lines)

    def _format_report_html(self, snapshot: Dict[str, Any]) -> str:
        ctx = snapshot.get("context", {})
        rel = snapshot.get("reliability_summary", {})
        gov = snapshot.get("ecrg_governance_summary", {})
        actions = snapshot.get("action_plan", [])

        action_rows = "".join(
            f"<tr><td><b>{a.get('priority')}</b></td><td>{a.get('title')}</td><td>{a.get('rationale')}</td><td><code>{a.get('target_component')}</code></td></tr>"
            for a in actions
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>AEGIS-X Integrated Report - {ctx.get('model_name')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #090d16; color: #e2e8f0; padding: 40px; margin: 0; }}
        .header {{ border-bottom: 2px solid #334155; padding-bottom: 20px; margin-bottom: 30px; }}
        .badge {{ display: inline-block; padding: 6px 14px; border-radius: 6px; font-weight: bold; background: #1e293b; border: 1px solid #475569; margin-right: 10px; }}
        .badge-HIGH {{ background: #064e3b; color: #34d399; border-color: #059669; }}
        .badge-CONDITIONAL {{ background: #78350f; color: #fbbf24; border-color: #d97706; }}
        .badge-RESTRICTED {{ background: #7f1d1d; color: #f87171; border-color: #dc2626; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #1e293b; text-align: left; }}
        th {{ background: #1e293b; color: #94a3b8; }}
        @media print {{ body {{ background: #fff; color: #000; }} .card {{ border-color: #ccc; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AEGIS-X Integrated Reliability & Governance Report</h1>
        <p>Report ID: <code>{ctx.get('report_id')}</code> | Model: <b>{ctx.get('model_name')}</b> | Generated: {ctx.get('generated_at')}</p>
        <span class="badge badge-{snapshot.get('trust_disposition')}">Trust Disposition: {snapshot.get('trust_disposition')}</span>
        <span class="badge">Completeness: {snapshot.get('overall_completeness_pct')}%</span>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Reliability Assessment</h3>
            <p><b>Fused Risk Index:</b> {rel.get('aggregate_fused_risk')}</p>
            <p><b>OOD Risk:</b> {rel.get('aggregate_ood_risk')}</p>
            <p><b>Uncertainty:</b> {rel.get('aggregate_uncertainty')}</p>
            <p><b>Drift Score:</b> {rel.get('aggregate_drift_score')}</p>
        </div>
        <div class="card">
            <h3>ECRG Governance</h3>
            <p><b>Operating Mode:</b> {gov.get('operating_mode')}</p>
            <p><b>Effective Action:</b> {gov.get('effective_action')}</p>
            <p><b>State Index:</b> {gov.get('state_index')}</p>
            <p><b>Conformal Calibrated:</b> {gov.get('calibrated')}</p>
        </div>
    </div>

    <div class="card">
        <h3>Operator Action Plan</h3>
        <table>
            <thead>
                <tr><th>Priority</th><th>Action Title</th><th>Rationale</th><th>Target Component</th></tr>
            </thead>
            <tbody>
                {action_rows}
            </tbody>
        </table>
    </div>
</body>
</html>"""
        return html
