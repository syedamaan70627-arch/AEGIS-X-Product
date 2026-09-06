"use me";
"use client";

import React from "react";
import Link from "next/link";
import { ReportPayload, RiskDriver } from "@/types/api";
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
  ExternalLink,
  Info,
} from "lucide-react";

interface IntegratedReportViewProps {
  report: ReportPayload;
  reportId: string;
  activeTab?: string;
}

export function IntegratedReportView({ report, reportId, activeTab = "integrated" }: IntegratedReportViewProps) {
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

  const formatRiskDriver = (driver: any): string => {
    if (!driver) return "None identified under current baseline.";
    if (typeof driver === "string") return driver;
    if (driver.driver_name) {
      return `${driver.category ? `[${driver.category}] ` : ""}${driver.driver_name}: ${driver.impact_description || ""} (Severity: ${driver.severity_score ?? "N/A"})`;
    }
    return String(driver);
  };

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

  // Derive Automation Permission based on ECRG Effective Action
  const getAutomationPermission = (action?: string) => {
    switch (action) {
      case "CONTINUE":
        return { text: "Full Autonomous Execution Permitted", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" };
      case "WATCH":
        return { text: "Supervised Automation (Monitoring Required)", color: "text-amber-400 bg-amber-500/10 border-amber-500/30" };
      case "DEFER":
        return { text: "Human-in-the-Loop Supervision Required", color: "text-orange-400 bg-orange-500/10 border-orange-500/30" };
      case "ESCALATE":
      case "RESTRICT":
        return { text: "Manual Override Only (Automation Suspended)", color: "text-rose-400 bg-rose-500/10 border-rose-500/30" };
      default:
        return { text: "NOT EVALUATED", color: "text-slate-400 bg-slate-800 border-slate-700" };
    }
  };

  const automationPerm = getAutomationPermission(ecrg_governance_summary?.effective_action);

  // Derive Primary Concern and Recommended Next Action
  const primaryConcernStr = top_risk_drivers && top_risk_drivers.length > 0 ? formatRiskDriver(top_risk_drivers[0]) : (why_this_decision && why_this_decision.length > 0 ? why_this_decision[0].factor + ": " + why_this_decision[0].description : "None identified under current baseline.");
  const recommendedAction = action_plan && action_plan.length > 0 ? action_plan[0] : null;

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
          <span className="text-sm font-medium text-slate-300">
            Report Snapshot ID: <code className="text-indigo-300 font-mono">{reportId}</code>
          </span>
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

      {/* EXECUTIVE VIEWPORT LAYER (FIRST VIEWPORT POLISH) */}
      <div className="relative p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-slate-950 border border-slate-800 shadow-2xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 uppercase tracking-wider">
              <ShieldAlert className="w-4 h-4" /> Executive Decision Summary
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {context.model_name}
            </h1>
            <p className="text-xs text-slate-400 max-w-2xl font-mono">
              Report: {context.report_id} | Analysis: {context.analysis_id} | Generated: {new Date(context.generated_at).toLocaleString()}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-semibold uppercase mb-1">Operational Trust</div>
              <div className={`px-3 py-1.5 rounded-lg border text-xs font-bold tracking-wide uppercase ${getTrustBadgeClass(trust_disposition)}`}>
                {trust_disposition}
              </div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-semibold uppercase mb-1">ECRG Action</div>
              <div className="px-3 py-1.5 rounded-lg border text-xs font-bold font-mono bg-indigo-500/10 text-indigo-400 border-indigo-500/30">
                {ecrg_governance_summary?.effective_action || "UNAVAILABLE"}
              </div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-semibold uppercase mb-1">Completeness</div>
              <div className="text-base font-extrabold text-indigo-400 font-mono">
                {overall_completeness_pct}%
              </div>
            </div>
          </div>
        </div>

        {/* 8-Point Executive Summary Panel */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-slate-800/80">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Automation Permission</div>
            <div className={`text-xs font-bold px-2 py-1 rounded border inline-block ${automationPerm.color}`}>
              {automationPerm.text}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Retraining Disposition</div>
            <div className="text-xs font-bold font-mono text-indigo-300">
              {retraining_disposition}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1 col-span-1 md:col-span-2">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Primary Concern / Risk Driver</div>
            <div className="text-xs text-rose-300 font-medium line-clamp-2">
              {primaryConcernStr}
            </div>
          </div>
        </div>

        {recommendedAction && (
          <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-900/60 flex items-start gap-3">
            <Zap className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5 text-xs">
              <span className="font-bold text-white uppercase tracking-wider">Recommended Next Action ({recommendedAction.priority}): </span>
              <span className="font-bold text-indigo-200">{recommendedAction.title} — </span>
              <span className="text-slate-300">{recommendedAction.rationale}</span>
            </div>
          </div>
        )}
      </div>

      {/* DETAILED 18-SECTION INTEGRATED REPORT (A through R) */}
      <div className="space-y-8">
        {/* SECTION A: Model & Analysis Identity */}
        <div id="section-a" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" /> Section A: Model & Analysis Identity
            </h2>
            <span className="text-xs font-mono text-slate-400">Context Lock Verified</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[11px] font-sans">Model Name / ID</div>
              <div className="font-bold text-slate-200 mt-1">{context.model_name}</div>
              <div className="text-[10px] text-slate-500">{context.model_id}</div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[11px] font-sans">Analysis Run ID</div>
              <div className="font-bold text-indigo-300 mt-1">{context.analysis_id}</div>
              <div className="text-[10px] text-slate-500">{new Date(context.generated_at).toLocaleDateString()}</div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[11px] font-sans">Reference Dataset</div>
              <div className="font-bold text-slate-200 mt-1">{context.reference_dataset_name || "Ref Dataset"}</div>
              <div className="text-[10px] text-slate-500">{context.reference_dataset_id}</div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[11px] font-sans">Evaluation Dataset</div>
              <div className="font-bold text-slate-200 mt-1">{context.evaluation_dataset_name || "Eval Dataset"}</div>
              <div className="text-[10px] text-slate-500">{context.evaluation_dataset_id}</div>
            </div>
          </div>
        </div>

        {/* SECTION B: Evidence Completeness Matrix */}
        <div id="section-b" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-sky-400" /> Section B: Evidence Completeness Matrix (12 Telemetry Modules)
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
                  <div className="text-[11px] text-slate-400 space-y-0.5 font-mono">
                    <div>Items: {mod.evidence_count}</div>
                  </div>
                ) : (
                  <div className="text-[11px] text-amber-300/80">
                    Reason: {mod.prerequisite_missing || "Module not run for this analysis context."}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* SECTION C: Reliability Evidence */}
        <div id="section-c" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-indigo-400" /> Section C: Reliability Evidence
            </h2>
            <Link href="/analysis" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold">
              View Source Analysis <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Fused Risk Index</div>
              <div className="text-xl font-bold font-mono text-indigo-400 mt-1">
                {reliability_summary.aggregate_fused_risk !== null ? reliability_summary.aggregate_fused_risk.toFixed(3) : "N/A"}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">OOD Risk</div>
              <div className="text-xl font-bold font-mono text-sky-400 mt-1">
                {reliability_summary.aggregate_ood_risk !== null ? reliability_summary.aggregate_ood_risk.toFixed(3) : "N/A"}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Epistemic Uncertainty</div>
              <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                {reliability_summary.aggregate_uncertainty !== null ? reliability_summary.aggregate_uncertainty.toFixed(3) : "N/A"}
              </div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-xs text-slate-400">Feature Drift Score</div>
              <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                {reliability_summary.aggregate_drift_score !== null ? reliability_summary.aggregate_drift_score.toFixed(3) : "N/A"}
              </div>
            </div>
          </div>
        </div>

        {/* SECTION D: Stress Robustness */}
        <div id="section-d" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-amber-400" /> Section D: Stress Robustness
            </h2>
            <Link href="/stress" className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 font-semibold">
              View Source Stress Lab <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          {stress_lab_summary.status === "VERIFIED" ? (
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Executed Stress Tests</div>
                <div className="text-lg font-bold font-mono text-slate-200 mt-1">{stress_lab_summary.test_count}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Avg Risk Delta</div>
                <div className="text-lg font-bold font-mono text-amber-400 mt-1">{stress_lab_summary.avg_risk_delta}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Max Stressed Risk</div>
                <div className="text-lg font-bold font-mono text-rose-400 mt-1">{stress_lab_summary.max_stressed_risk}</div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800 text-xs text-slate-400 italic">
              NOT EVALUATED: Stress Lab perturbation suite was not executed for this analysis context.
            </div>
          )}
        </div>

        {/* SECTION E: Fault Sensitivity */}
        <div id="section-e" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-400" /> Section E: Fault Sensitivity
            </h2>
            <Link href="/faults" className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 font-semibold">
              View Source Fault Lab <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          {fault_lab_summary.status === "VERIFIED" ? (
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Fault Injection Count</div>
                <div className="text-lg font-bold font-mono text-slate-200 mt-1">{fault_lab_summary.test_count}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Fault Pass Rate</div>
                <div className="text-lg font-bold font-mono text-emerald-400 mt-1">{fault_lab_summary.pass_rate * 100}%</div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800 text-xs text-slate-400 italic">
              NOT EVALUATED: Fault injection suite was not executed for this run.
            </div>
          )}
        </div>

        {/* SECTION F: Failure Intelligence */}
        <div id="section-f" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" /> Section F: Failure Intelligence
            </h2>
            <Link href="/failure-explorer" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold">
              View Source Failure Explorer <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1 text-slate-300">
            <div>Status: <span className="font-mono font-bold text-indigo-300">{failure_explorer_summary.status}</span></div>
            <div>Signatures Analyzed: <span className="font-mono">{failure_explorer_summary.signature_count || 0}</span></div>
          </div>
        </div>

        {/* SECTION G: Temporal Intelligence */}
        <div id="section-g" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-sky-400" /> Section G: Temporal Intelligence & Early Warning
            </h2>
            <Link href="/early-warning" className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-semibold">
              View Source Early Warning <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          {temporal_intelligence_summary.status === "VERIFIED" ? (
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Early Warning Trigger</div>
                <div className="text-base font-bold font-mono text-rose-400 mt-1">
                  {temporal_intelligence_summary.warning?.is_warning_triggered ? "TRIGGERED" : "NOMINAL"}
                </div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400">Warning Score</div>
                <div className="text-base font-bold font-mono text-sky-400 mt-1">
                  {temporal_intelligence_summary.warning?.warning_score ?? "N/A"}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800 text-xs text-slate-400 italic">
              NOT EVALUATED: Temporal early warning model was not evaluated for this dataset context.
            </div>
          )}
        </div>

        {/* SECTION H: Model Trust Interpretation */}
        <div id="section-h" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Compass className="w-5 h-5 text-indigo-400" /> Section H: Model Trust Interpretation
            </h2>
          </div>
          <div className="p-4 bg-slate-950/70 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="font-bold text-white">Trust Rationale Synthesis:</div>
            <p className="leading-relaxed">{trust_rationale}</p>
          </div>
        </div>

        {/* SECTION I: ECRG Governance */}
        <div id="section-i" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Lock className="w-5 h-5 text-emerald-400" /> Section I: ECRG Governance Integration
            </h2>
            <Link href="/governance" className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold">
              View Source Governance <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans">Operating Mode</div>
              <div className="font-bold text-emerald-400 mt-1">{ecrg_governance_summary.operating_mode}</div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans">Effective Action</div>
              <div className="font-bold text-indigo-300 mt-1">{ecrg_governance_summary.effective_action}</div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans">State Index</div>
              <div className="font-bold text-slate-200 mt-1">{ecrg_governance_summary.state_index}</div>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans">Conformal Calibration</div>
              <div className="font-bold text-sky-400 mt-1">{ecrg_governance_summary.calibrated ? "CALIBRATED" : "UNSET"}</div>
            </div>
          </div>
        </div>

        {/* SECTION J: Why This Decision? */}
        <div id="section-j" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" /> Section J: Why This Decision? (Evidence Traceability)
            </h2>
          </div>
          <div className="space-y-3">
            {why_this_decision.map((item, idx) => (
              <div key={idx} className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-slate-200">{item.factor}</span>
                  <span className={`px-2 py-0.5 rounded font-mono font-bold ${
                    item.impact === "POSITIVE" ? "bg-emerald-500/10 text-emerald-400" :
                    item.impact === "CRITICAL" ? "bg-rose-500/10 text-rose-400" : "bg-amber-500/10 text-amber-400"
                  }`}>
                    {item.impact}
                  </span>
                </div>
                <p className="text-slate-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION K: Operator Action Plan */}
        <div id="section-k" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" /> Section K: Operator Action Plan
            </h2>
          </div>
          <div className="space-y-3">
            {action_plan.map((item, idx) => (
              <div key={idx} className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded border ${getPriorityBadgeClass(item.priority)}`}>
                      {item.priority}
                    </span>
                    <span className="font-bold text-white">{item.title}</span>
                  </div>
                  <span className="font-mono text-slate-400">{item.target_component}</span>
                </div>
                <p className="text-slate-300">{item.rationale}</p>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION L: Retraining / Recalibration */}
        <div id="section-l" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <History className="w-5 h-5 text-indigo-400" /> Section L: Retraining & Recalibration Disposition
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 text-xs font-bold font-mono">
              {retraining_disposition}
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{retraining_rationale}</p>
        </div>

        {/* SECTION M: Deployment Suitability */}
        <div id="section-m" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" /> Section M: Deployment Suitability & Risk Tier
            </h2>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold font-mono">
              {deployment_suitability.recommended_environment}
            </span>
            <span className="text-slate-400 font-mono">({deployment_suitability.risk_tier})</span>
          </div>
        </div>

        {/* SECTION N: Trend vs Previous Assessment */}
        <div id="section-n" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-sky-400" /> Section N: Trend vs Previous Assessment
            </h2>
          </div>
          <div className="text-xs text-slate-300 font-mono">
            {trend_comparison ? (
              <div>Trend Direction: <span className="font-bold text-indigo-300">{trend_comparison.direction || "STABLE"}</span></div>
            ) : (
              <div className="text-slate-400 italic">No prior baseline run recorded for historical delta comparison.</div>
            )}
          </div>
        </div>

        {/* SECTION O: Top Risk Drivers */}
        <div id="section-o" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-400" /> Section O: Top Risk Drivers
            </h2>
          </div>
          <ul className="text-xs text-slate-300 space-y-1 list-disc pl-4">
            {top_risk_drivers && top_risk_drivers.length > 0 ? (
              top_risk_drivers.map((driver, i) => <li key={i}>{formatRiskDriver(driver)}</li>)
            ) : (
              <li className="text-slate-400 italic">No critical risk drivers identified above nominal threshold.</li>
            )}
          </ul>
        </div>

        {/* SECTION P: Scientific Limitations */}
        <div id="section-p" className="p-6 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Info className="w-4 h-4 text-slate-400" /> Section P: Scientific & Operational Limitations Disclosures
            </h2>
          </div>
          <ul className="text-xs text-slate-400 space-y-1.5 list-disc pl-4 leading-relaxed">
            {scientific_limitations.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>

        {/* SECTION Q: Audit & Provenance */}
        <div id="section-q" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2 font-sans">
              <Lock className="w-5 h-5 text-indigo-400" /> Section Q: Audit & Provenance Metadata
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-400">
            <div>Report ID: <span className="text-slate-200">{context.report_id}</span></div>
            <div>User ID: <span className="text-slate-200">{context.user_id}</span></div>
            <div>Generated At: <span className="text-slate-200">{context.generated_at}</span></div>
            <div>Evidence Completeness: <span className="text-slate-200">{overall_completeness_pct}%</span></div>
          </div>
        </div>

        {/* SECTION R: Final Disposition */}
        <div id="section-r" className="p-6 rounded-xl bg-slate-950/90 border border-slate-800 space-y-3 text-center">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Section R: Final Operational Trust Disposition
          </h2>
          <div className="inline-block">
            <span className={`px-6 py-2 rounded-xl border text-base font-extrabold uppercase ${getTrustBadgeClass(trust_disposition)}`}>
              {trust_disposition}
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-lg mx-auto">
            This snapshot is immutable and sealed under authenticated owner context. Historical evidence is locked to report ID <code className="font-mono text-indigo-300">{reportId}</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
