"use me";
"use client";

import React from "react";
import { ReportPayload } from "@/types/api";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  Zap,
  Cpu,
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Download,
  Printer,
  History,
  Compass,
  ArrowRight,
  BarChart2,
  Clock,
  Layers,
  Lock,
} from "lucide-react";

interface IntegratedReportViewProps {
  report: ReportPayload;
  reportId: string;
}

export function IntegratedReportView({ report, reportId }: IntegratedReportViewProps) {
  const {
    context,
    trust_disposition,
    trust_rationale,
    completeness,
    overall_completeness_pct,
    reliability_summary,
    stress_lab_summary,
    fault_lab_summary,
    failure_explorer_summary,
    temporal_intelligence_summary,
    ecrg_governance_summary,
    why_this_decision,
    action_plan,
    retraining_disposition,
    retraining_rationale,
    deployment_suitability,
    trend_comparison,
    top_risk_drivers,
    scientific_limitations,
  } = report;

  // Colors for trust disposition
  const getTrustBadgeClass = (disp: string) => {
    switch (disp) {
      case "HIGH":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "CONDITIONAL":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "LOW":
        return "bg-orange-500/10 text-orange-400 border-orange-500/30";
      case "RESTRICTED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
    }
  };

  const getPriorityBadgeClass = (priority: string) => {
    switch (priority) {
      case "P1":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40 font-bold";
      case "P2":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "P3":
        return "bg-sky-500/20 text-sky-300 border-sky-500/40";
      default:
        return "bg-slate-500/20 text-slate-300 border-slate-500/40";
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExport = (fmt: string) => {
    const url = api.getReportExportUrl(reportId, fmt);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-8 text-slate-200">
      {/* Action Bar (Print & Download Controls) */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md print:hidden">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-medium text-slate-300">Report Snapshot ID: <code className="text-indigo-300 font-mono">{reportId}</code></span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport("json")}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            <Download className="w-3.5 h-3.5" /> Export JSON
          </button>
          <button
            onClick={() => handleExport("csv")}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition"
          >
            <Printer className="w-3.5 h-3.5" /> Print / Save PDF
          </button>
        </div>
      </div>

      {/* SECTION 1: Executive Summary Hero */}
      <div className="relative p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-slate-950 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 uppercase tracking-wider">
              <ShieldAlert className="w-4 h-4" /> AEGIS-X Decision Support Layer
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {context.model_name}
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl">
              Context-locked evaluation across reference dataset <code className="text-slate-300 font-mono">{context.reference_dataset_name || context.reference_dataset_id}</code> and evaluation dataset <code className="text-slate-300 font-mono">{context.evaluation_dataset_name || context.evaluation_dataset_id}</code>.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-slate-950/80 p-4 rounded-xl border border-slate-800/80">
            <div>
              <div className="text-xs text-slate-400 font-semibold mb-1">Operational Trust Disposition</div>
              <div className={`px-4 py-2 rounded-lg border text-sm font-bold tracking-wide uppercase ${getTrustBadgeClass(trust_disposition)}`}>
                {trust_disposition}
              </div>
            </div>

            <div className="sm:border-l sm:border-slate-800 sm:pl-4">
              <div className="text-xs text-slate-400 font-semibold mb-1">Evidence Completeness</div>
              <div className="text-xl font-extrabold text-indigo-400 font-mono">
                {overall_completeness_pct}%
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-2">
          <div>Report ID: <span className="font-mono text-slate-300">{context.report_id}</span></div>
          <div>Analysis ID: <span className="font-mono text-slate-300">{context.analysis_id}</span></div>
          <div>Generated: <span className="font-mono text-slate-300">{new Date(context.generated_at).toLocaleString()}</span></div>
        </div>
      </div>

      {/* Rationale Banner */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 text-sm text-slate-300 flex items-start gap-3">
        <Compass className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-white">Trust Rationale: </span>
          {trust_rationale}
        </div>
      </div>

      {/* SECTION 2 & 3: Why This Decision & Operator Action Plan */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Why This Decision */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" /> Why This Decision? (Evidence Links)
          </h2>
          <div className="space-y-3">
            {why_this_decision.map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-slate-200">{item.factor}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${
                    item.impact === "POSITIVE" ? "bg-emerald-500/10 text-emerald-400" :
                    item.impact === "CRITICAL" ? "bg-rose-500/10 text-rose-400" : "bg-amber-500/10 text-amber-400"
                  }`}>
                    {item.impact}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Operator Action Plan */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" /> Operator Action Plan
          </h2>
          <div className="space-y-3">
            {action_plan.map((item, idx) => (
              <div key={idx} className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded border ${getPriorityBadgeClass(item.priority)}`}>
                      {item.priority}
                    </span>
                    <span className="text-sm font-bold text-white">{item.title}</span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">{item.target_component}</span>
                </div>
                <p className="text-xs text-slate-300">{item.rationale}</p>
                <div className="text-[11px] font-mono text-indigo-300/80 bg-indigo-950/30 px-2 py-1 rounded border border-indigo-900/40">
                  Trigger: {item.trigger_condition}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SECTION 4: 12-Module Evidence Completeness Matrix */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-sky-400" /> Evidence Completeness Matrix (12 Telemetry Modules)
          </h2>
          <span className="text-xs font-mono text-slate-400">Score: {overall_completeness_pct}% Verified</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(completeness).map(([key, mod]) => (
            <div key={key} className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200">{mod.name}</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  mod.status === "VERIFIED" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                  mod.status === "UNAVAILABLE" ? "bg-slate-800 text-slate-400 border border-slate-700" :
                  "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                }`}>
                  {mod.status}
                </span>
              </div>
              {mod.status === "VERIFIED" ? (
                <div className="text-[11px] text-slate-400 space-y-0.5">
                  <div>Evidence Items: <span className="font-mono text-slate-200">{mod.evidence_count}</span></div>
                  {mod.last_verified_at && (
                    <div>Verified: <span className="font-mono text-slate-300">{new Date(mod.last_verified_at).toLocaleTimeString()}</span></div>
                  )}
                </div>
              ) : (
                <div className="text-[11px] text-amber-300/80">
                  Prerequisite: {mod.prerequisite_missing || "Execution required"}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* SECTION 5 & 6: Core Reliability & ECRG Governance Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Core Reliability Summary */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-indigo-400" /> Integrated Reliability Assessment
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Fused Reliability Risk</div>
              <div className="text-xl font-bold font-mono text-indigo-400">
                {reliability_summary.aggregate_fused_risk !== null ? reliability_summary.aggregate_fused_risk.toFixed(3) : "N/A"}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Out-of-Distribution Risk</div>
              <div className="text-xl font-bold font-mono text-sky-400">
                {reliability_summary.aggregate_ood_risk !== null ? reliability_summary.aggregate_ood_risk.toFixed(3) : "N/A"}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Epistemic Uncertainty</div>
              <div className="text-xl font-bold font-mono text-amber-400">
                {reliability_summary.aggregate_uncertainty !== null ? reliability_summary.aggregate_uncertainty.toFixed(3) : "N/A"}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Feature Drift Score</div>
              <div className="text-xl font-bold font-mono text-rose-400">
                {reliability_summary.aggregate_drift_score !== null ? reliability_summary.aggregate_drift_score.toFixed(3) : "N/A"}
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <div>Fusion Method: <code className="text-slate-200">{reliability_summary.fusion_method}</code></div>
            <div>Ground Truth Labels: <code className="text-slate-200">{reliability_summary.has_labels ? "Available" : "Unlabelled Evaluation"}</code></div>
          </div>
        </div>

        {/* ECRG Governance Summary */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-emerald-400" /> ECRG Governance Integration
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Operating Mode</div>
              <div className="text-base font-bold font-mono text-emerald-400">
                {ecrg_governance_summary.operating_mode}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Effective Action</div>
              <div className="text-base font-bold font-mono text-indigo-400">
                {ecrg_governance_summary.effective_action}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">State Machine Index</div>
              <div className="text-xl font-bold font-mono text-slate-200">
                {ecrg_governance_summary.state_index}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Conformal Calibration</div>
              <div className="text-base font-bold font-mono text-sky-400">
                {ecrg_governance_summary.calibrated ? "CALIBRATED" : "UNSET"}
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <div>Conformal Prediction Set: <code className="text-slate-200">{JSON.stringify(ecrg_governance_summary.prediction_set)}</code></div>
            <div>Reason Codes: <code className="text-slate-200">{JSON.stringify(ecrg_governance_summary.reason_codes)}</code></div>
          </div>
        </div>
      </div>

      {/* SECTION 7, 8, 9: Robustness, Fault Sensitivity & Temporal */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stress Lab */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-amber-400" /> Stress Lab Robustness
          </h3>
          {stress_lab_summary.status === "VERIFIED" ? (
            <div className="text-xs space-y-1 text-slate-300">
              <div>Executed Tests: <span className="font-mono text-slate-100">{stress_lab_summary.test_count}</span></div>
              <div>Avg Risk Delta: <span className="font-mono text-amber-400">{stress_lab_summary.avg_risk_delta}</span></div>
              <div>Max Stressed Risk: <span className="font-mono text-rose-400">{stress_lab_summary.max_stressed_risk}</span></div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">Stress Lab perturbations not executed for this run.</div>
          )}
        </div>

        {/* Fault Lab */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" /> Fault Sensitivity
          </h3>
          {fault_lab_summary.status === "VERIFIED" ? (
            <div className="text-xs space-y-1 text-slate-300">
              <div>Executed Faults: <span className="font-mono text-slate-100">{fault_lab_summary.test_count}</span></div>
              <div>Pass Rate: <span className="font-mono text-emerald-400">{fault_lab_summary.pass_rate * 100}%</span></div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">Fault injection suite not executed for this run.</div>
          )}
        </div>

        {/* Temporal Early Warning */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-sky-400" /> Temporal Intelligence
          </h3>
          {temporal_intelligence_summary.status === "VERIFIED" ? (
            <div className="text-xs space-y-1 text-slate-300">
              <div>Early Warning Trigger: <span className="font-mono font-bold text-rose-400">{temporal_intelligence_summary.warning?.is_warning_triggered ? "TRIGGERED" : "NOMINAL"}</span></div>
              <div>Warning Score: <span className="font-mono text-sky-400">{temporal_intelligence_summary.warning?.warning_score || "N/A"}</span></div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">Temporal warning trajectory not evaluated.</div>
          )}
        </div>
      </div>

      {/* SECTION 10 & 11: Retraining Disposition & Deployment Suitability */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Retraining Disposition */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" /> Retraining & Recalibration Disposition
          </h2>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 text-sm font-bold font-mono">
              {retraining_disposition}
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{retraining_rationale}</p>
        </div>

        {/* Deployment Suitability */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" /> Deployment Suitability & Constraints
          </h2>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-sm font-bold font-mono">
              {deployment_suitability.recommended_environment}
            </span>
            <span className="text-xs text-slate-400 font-mono">({deployment_suitability.risk_tier})</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-1 list-disc pl-4">
            {deployment_suitability.operational_constraints?.map((c: string, i: number) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* SECTION 12: Scientific Limitations Disclosures */}
      <div className="p-6 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">
          Scientific & Operational Limitations Disclosures
        </h2>
        <ul className="text-xs text-slate-400 space-y-1.5 list-disc pl-4 leading-relaxed">
          {scientific_limitations.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
