"use client";

import React from "react";
import Link from "next/link";
import { ReportPayload, RiskDriver } from "@/types/api";
import { api } from "@/lib/api";
import { ROUTES } from "@/lib/routes";
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

export function IntegratedReportView({
  report,
  reportId,
  activeTab = "integrated",
}: IntegratedReportViewProps) {
  const {
    context,
    trust_disposition,
    trust_rationale,
    completeness,
    overall_completeness_pct,
    reliability_summary,
    stress_lab_summary,
    fault_lab_summary,
    failure_explorer_summary = {},
    temporal_intelligence_summary = {},
    ecrg_governance_summary = {},
    why_this_decision = [],
    action_plan = [],
    retraining_disposition,
    retraining_rationale,
    deployment_suitability = { recommended_environment: "NOT EVALUATED", risk_tier: "UNSET" },
    trend_comparison,
    top_risk_drivers = [],
    scientific_limitations = [],
  } = report;

  const formatRiskDriver = (driver: any): string => {
    if (!driver) return "None identified under current baseline.";
    if (typeof driver === "string") return driver;
    if (driver.driver_name) {
      return `${driver.category ? `[${driver.category}] ` : ""}${driver.driver_name}: ${driver.impact_description || ""} (Severity: ${driver.severity_score ?? "N/A"})`;
    }
    return String(driver);
  };

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

  const primaryConcernStr =
    top_risk_drivers && top_risk_drivers.length > 0
      ? formatRiskDriver(top_risk_drivers[0])
      : why_this_decision && why_this_decision.length > 0
      ? why_this_decision[0].factor + ": " + why_this_decision[0].description
      : "None identified under current baseline.";

  const recommendedAction = action_plan && action_plan.length > 0 ? action_plan[0] : null;

  const handlePrint = () => {
    window.print();
  };

  const handleExport = (fmt: string) => {
    const url = api.getReportExportUrl(reportId, fmt);
    window.open(url, "_blank");
  };

  // Shared Top Action Bar
  const renderActionBar = () => (
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
  );

  // TAB 2: RELIABILITY ASSESSMENT SUMMARY VIEW ONLY
  if (activeTab === "reliability") {
    const oodVal = reliability_summary.aggregate_ood_risk;
    const uncVal = reliability_summary.aggregate_uncertainty;
    const driftVal = reliability_summary.aggregate_drift_score;
    const fusedVal = reliability_summary.aggregate_fused_risk;

    const getSeverityLabel = (val: number | null | undefined, thresholds: { high: number; mod: number }) => {
      if (val === null || val === undefined) return { text: "NOT EVALUATED", color: "text-slate-400 bg-slate-800 border-slate-700" };
      if (val >= thresholds.high) return { text: "HIGH RISK", color: "text-rose-400 bg-rose-500/10 border-rose-500/30" };
      if (val >= thresholds.mod) return { text: "MODERATE", color: "text-amber-400 bg-amber-500/10 border-amber-500/30" };
      return { text: "LOW / NOMINAL", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" };
    };

    return (
      <div className="space-y-8 text-slate-200" data-testid="reliability-view">
        {renderActionBar()}

        {/* Reliability Overview Header */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 uppercase tracking-wider mb-1">
                <BarChart2 className="w-4 h-4" /> Telemetry & Reliability Assessment Summary
              </div>
              <h1 className="text-xl font-bold text-white">{context.model_name}</h1>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Analysis: {context.analysis_id} | Reference: {context.reference_dataset_name || context.reference_dataset_id} | Evaluation: {context.evaluation_dataset_name || context.evaluation_dataset_id}
              </p>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-right">
              <div className="text-[10px] text-slate-400 font-semibold uppercase">Fused Reliability Index</div>
              <div className="text-2xl font-extrabold font-mono text-indigo-400">
                {fusedVal !== null && fusedVal !== undefined ? fusedVal.toFixed(3) : "N/A"}
              </div>
              <div className="text-[10px] text-slate-500 font-mono uppercase">Method: {reliability_summary.fusion_method}</div>
            </div>
          </div>

          {/* 4 Reliability Telemetry Signals Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* OOD */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Out-of-Distribution (OOD)</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${getSeverityLabel(oodVal, { high: 0.6, mod: 0.3 }).color}`}>
                  {getSeverityLabel(oodVal, { high: 0.6, mod: 0.3 }).text}
                </span>
              </div>
              <div className="text-2xl font-extrabold font-mono text-sky-400">
                {oodVal !== null && oodVal !== undefined ? oodVal.toFixed(3) : "N/A"}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {oodVal !== null && oodVal > 0.6 ? "High feature density deviation from baseline reference manifold." : "Evaluation density aligns within nominal reference manifold bounds."}
              </p>
            </div>

            {/* Uncertainty */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Prediction Uncertainty</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${getSeverityLabel(uncVal, { high: 0.35, mod: 0.25 }).color}`}>
                  {getSeverityLabel(uncVal, { high: 0.35, mod: 0.25 }).text}
                </span>
              </div>
              <div className="text-2xl font-extrabold font-mono text-amber-400">
                {uncVal !== null && uncVal !== undefined ? uncVal.toFixed(3) : "N/A"}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {uncVal !== null && uncVal > 0.35 ? "High prediction variance indicating unconfident decision boundary." : "Prediction variance remains within expected confidence limits."}
              </p>
            </div>

            {/* Drift */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Feature & Concept Drift</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${getSeverityLabel(driftVal, { high: 0.35, mod: 0.15 }).color}`}>
                  {getSeverityLabel(driftVal, { high: 0.35, mod: 0.15 }).text}
                </span>
              </div>
              <div className="text-2xl font-extrabold font-mono text-rose-400">
                {driftVal !== null && driftVal !== undefined ? driftVal.toFixed(3) : "N/A"}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {driftVal !== null && driftVal > 0.35 ? "Significant feature distribution drift requiring parameter recalibration." : "Feature distribution drift remains low across evaluation dimensions."}
              </p>
            </div>

            {/* Fused Risk */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Fused Reliability Risk</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${getSeverityLabel(fusedVal, { high: 0.5, mod: 0.2 }).color}`}>
                  {getSeverityLabel(fusedVal, { high: 0.5, mod: 0.2 }).text}
                </span>
              </div>
              <div className="text-2xl font-extrabold font-mono text-indigo-400">
                {fusedVal !== null && fusedVal !== undefined ? fusedVal.toFixed(3) : "N/A"}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Unified composite risk weighted by uncertainty and feature divergence metrics.
              </p>
            </div>
          </div>
        </div>

        {/* Primary Concern & Signal Disagreement */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" /> Primary Reliability Concern
            </h3>
            <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-rose-300 font-medium">
              {primaryConcernStr}
            </div>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" /> Signal Disagreement Analysis
            </h3>
            <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 space-y-1">
              <p className="leading-relaxed">
                {oodVal !== null && oodVal > 0.6 && (uncVal === null || uncVal < 0.3)
                  ? "Elevated OOD risk occurs with low uncertainty, indicating out-of-manifold inputs where model confidence is artificially high."
                  : "Reliability signals exhibit consistent risk alignment across evaluation dimensions."}
              </p>
            </div>
          </div>
        </div>

        {/* Source Traceability Panel */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" /> Source Analysis Traceability
            </h3>
            <Link href="/analysis" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold">
              Open Analysis Workbench <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[10px]">Model ID</div>
              <div className="text-slate-200 font-bold mt-0.5">{context.model_id}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[10px]">Analysis ID</div>
              <div className="text-indigo-300 font-bold mt-0.5">{context.analysis_id}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-[10px]">Evaluation Result Path</div>
              <div className="text-slate-300 font-bold mt-0.5 truncate">{reliability_summary.result_path || "N/A"}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // TAB 3: MODEL TRUST & GOVERNANCE VIEW ONLY
  if (activeTab === "model_trust") {
    return (
      <div className="space-y-8 text-slate-200" data-testid="trust-view">
        {renderActionBar()}

        {/* Operational Trust Header */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 uppercase tracking-wider">
                <Compass className="w-4 h-4" /> Model Operational Trust & Risk Interpretation
              </div>
              <h1 className="text-xl font-bold text-white">{context.model_name}</h1>
              <p className="text-xs text-slate-400 font-mono">
                Report ID: {reportId} | Analysis: {context.analysis_id}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 font-semibold uppercase mb-1">Trust Disposition</div>
                <div className={`px-3 py-1 rounded-lg border text-xs font-bold uppercase ${getTrustBadgeClass(trust_disposition)}`}>
                  {trust_disposition}
                </div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-400 font-semibold uppercase mb-1">ECRG Effective Action</div>
                <div className="px-3 py-1 rounded-lg border text-xs font-bold font-mono bg-indigo-500/10 text-indigo-400 border-indigo-500/30">
                  {ecrg_governance_summary?.effective_action || "UNAVAILABLE"}
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="font-bold text-white">Trust Rationale Synthesis:</div>
            <p className="leading-relaxed">{trust_rationale}</p>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <span className="text-xs font-semibold text-slate-400">Automation Permission:</span>
            <span className={`text-xs font-bold px-3 py-1 rounded border ${automationPerm.color}`}>
              {automationPerm.text}
            </span>
          </div>
        </div>

        {/* Supporting vs Reducing Trust Reasons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Reasons Supporting Trust
            </h3>
            <div className="space-y-2">
              {why_this_decision.filter((w) => w.impact === "POSITIVE").length > 0 ? (
                why_this_decision
                  .filter((w) => w.impact === "POSITIVE")
                  .map((w, idx) => (
                    <div key={idx} className="p-3 bg-slate-950/70 rounded-lg border border-slate-800/80 text-xs space-y-1">
                      <div className="font-semibold text-emerald-300">{w.factor}</div>
                      <p className="text-slate-400">{w.description}</p>
                    </div>
                  ))
              ) : (
                <div className="p-3 bg-slate-950/50 rounded-lg text-xs text-slate-500 italic">
                  No positive trust factors identified under current evaluation context.
                </div>
              )}
            </div>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <XCircle className="w-4 h-4 text-rose-400" /> Reasons Reducing Trust / Risk Factors
            </h3>
            <div className="space-y-2">
              {why_this_decision.filter((w) => w.impact !== "POSITIVE").length > 0 ? (
                why_this_decision
                  .filter((w) => w.impact !== "POSITIVE")
                  .map((w, idx) => (
                    <div key={idx} className="p-3 bg-slate-950/70 rounded-lg border border-slate-800/80 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-rose-300">{w.factor}</span>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">{w.impact}</span>
                      </div>
                      <p className="text-slate-400">{w.description}</p>
                    </div>
                  ))
              ) : (
                <div className="p-3 bg-slate-950/50 rounded-lg text-xs text-slate-500 italic">
                  No adverse risk factors identified under current evaluation context.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Top Risk Drivers & Action Recommendations */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" /> Top Risk Drivers Breakdown
            </h3>
            <div className="space-y-2">
              {top_risk_drivers && top_risk_drivers.length > 0 ? (
                top_risk_drivers.map((driver, idx) => (
                  <div key={idx} className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">[{driver.category}] {driver.driver_name}</span>
                      <span className="font-mono text-rose-400 font-bold">Severity: {driver.severity_score}</span>
                    </div>
                    <p className="text-slate-400">{driver.impact_description}</p>
                  </div>
                ))
              ) : (
                <div className="p-3 bg-slate-950/50 rounded-lg text-xs text-slate-400 italic">
                  No critical risk drivers identified above nominal threshold.
                </div>
              )}
            </div>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" /> Retraining & Recalibration Disposition
            </h3>
            <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400 font-semibold">Disposition:</span>
                <span className="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-bold font-mono">
                  {retraining_disposition}
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed">{retraining_rationale}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // TAB 4: GOVERNANCE DECISION REPORT VIEW ONLY
  if (activeTab === "governance") {
    return (
      <div className="space-y-8 text-slate-200" data-testid="governance-view">
        {renderActionBar()}

        {/* Governance Master Header */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 uppercase tracking-wider">
                <Lock className="w-4 h-4" /> ECRG Conformal Governance Decision Report
              </div>
              <h1 className="text-xl font-bold text-white">{context.model_name}</h1>
              <p className="text-xs text-slate-400 font-mono">
                Decision ID: {ecrg_governance_summary.decision_id || "N/A"} | Operating Mode: {ecrg_governance_summary.operating_mode || "EVIDENCE_ONLY"}
              </p>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-right">
              <div className="text-[10px] text-slate-400 font-semibold uppercase">Effective Action</div>
              <div className="text-2xl font-extrabold font-mono text-indigo-400 mt-0.5">
                {ecrg_governance_summary.effective_action || "UNAVAILABLE"}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Raw Action: {ecrg_governance_summary.raw_action || "N/A"}</div>
            </div>
          </div>

          {/* Key ECRG State Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">Operating Mode</div>
              <div className="font-bold text-emerald-400 mt-1">{ecrg_governance_summary.operating_mode || "EVIDENCE_ONLY"}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">Previous Action</div>
              <div className="font-bold text-slate-300 mt-1">{ecrg_governance_summary.previous_effective_action || "NONE"}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">State Index</div>
              <div className="font-bold text-slate-200 mt-1">{ecrg_governance_summary.state_index ?? 0}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">State Transition</div>
              <div className="font-bold text-sky-400 mt-1">
                {ecrg_governance_summary.transition_occurred ? "TRANSITIONED" : "NOMINAL STATE"}
              </div>
            </div>
          </div>
        </div>

        {/* Conformal Calibration & Set Prediction Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-400" /> Conformal Calibration & Coverage Disclosure
            </h3>
            <div className="space-y-3 text-xs">
              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">Calibration Status:</span>
                  <span className={`px-2 py-0.5 rounded font-mono font-bold ${ecrg_governance_summary.calibrated ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-slate-800 text-slate-400 border border-slate-700"}`}>
                    {ecrg_governance_summary.calibrated ? "CALIBRATED" : "UNSET"}
                  </span>
                </div>
                <p className="text-slate-400 pt-1 leading-relaxed">
                  {ecrg_governance_summary.calibrated_disclosure || (ecrg_governance_summary.calibrated ? "Conformal calibration active." : `Conformal calibration was not active for this ${ecrg_governance_summary.operating_mode || "EVIDENCE_ONLY"} snapshot.`)}
                </p>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1 font-mono">
                <div className="flex items-center justify-between">
                  <div className="text-slate-400 font-sans">Prediction Set Output</div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${ecrg_governance_summary.calibrated ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-amber-500/10 text-amber-400 border-amber-500/30"}`}>
                    {ecrg_governance_summary.calibrated ? "CALIBRATED" : "ADVISORY / UNCALIBRATED / NON-CERTIFIED"}
                  </span>
                </div>
                <div className="text-slate-200 font-bold">
                  {ecrg_governance_summary.calibrated
                    ? JSON.stringify(ecrg_governance_summary.prediction_set || [])
                    : (ecrg_governance_summary.prediction_set && ecrg_governance_summary.prediction_set.length > 0
                        ? `${JSON.stringify(ecrg_governance_summary.prediction_set)} (Advisory Non-Certified Output)`
                        : "NOT AVAILABLE / NOT ACTIVE")}
                </div>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1 font-mono">
                <div className="text-slate-400 font-sans">Calibrator Artifact ID</div>
                <div className="text-slate-300 truncate">
                  {ecrg_governance_summary.calibrator_artifact_id || "NONE (Uncalibrated Snapshot)"}
                </div>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-400" /> Machine Reason Codes & Cryptographic Audit
            </h3>
            <div className="space-y-3 text-xs">
              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1 font-mono">
                <div className="text-slate-400 font-sans">Machine Reason Codes</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(ecrg_governance_summary.reason_codes || []).map((code: string, i: number) => (
                    <span key={i} className="px-2 py-0.5 bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 rounded text-[11px]">
                      {code}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1 font-mono">
                <div className="text-slate-400 font-sans">Evidence Snapshot Hash</div>
                <div className="text-slate-300 text-[11px] break-all">
                  {ecrg_governance_summary.evidence_snapshot_hash || "N/A"}
                </div>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <div className="text-slate-400 font-semibold">Transition Rationale</div>
                <p className="text-slate-300 leading-relaxed">
                  {ecrg_governance_summary.transition_reason || "Nominal state maintenance under active governance."}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Operational Protocol Instructions */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" /> ECRG Operator Protocol
          </h3>
          <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 space-y-2 leading-relaxed">
            {ecrg_governance_summary.effective_action === "WATCH" && (
              <p>
                <span className="font-bold text-indigo-300">WATCH Protocol:</span> Model execution is permitted under active operational surveillance. Telemetry and prediction variance are logged continuously. Operators should inspect early warning trajectory alerts if risk elevation persists.
              </p>
            )}
            {ecrg_governance_summary.effective_action === "CONTINUE" && (
              <p>
                <span className="font-bold text-emerald-300">CONTINUE Protocol:</span> Nominal model operation permitted without restriction. Continuous telemetry verification remains active.
              </p>
            )}
            {ecrg_governance_summary.effective_action === "DEFER" && (
              <p>
                <span className="font-bold text-amber-300">DEFER Protocol:</span> Human-in-the-loop fallback required. Automated model inference routing suspended for set predictions.
              </p>
            )}
            {ecrg_governance_summary.effective_action === "ESCALATE" && (
              <p>
                <span className="font-bold text-rose-300">ESCALATE Protocol:</span> Operational restriction enforced. Emergency manual override required; model execution suspended until recalibrated.
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // TAB 1: INTEGRATED REPORT (PRINCIPAL) - FULL CONSOLIDATED REPORT VIEW
  return (
    <div className="space-y-8 text-slate-200" data-testid="integrated-view">
      {renderActionBar()}

      {/* EXECUTIVE VIEWPORT LAYER */}
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
            <Link href={`${ROUTES.reliability}?model_id=${context.model_id}&analysis_id=${context.analysis_id}`} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold">
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
            <Link href={`${ROUTES.stressLab}?model_id=${context.model_id}`} className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 font-semibold">
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
            <Link href={`${ROUTES.faultLab}?model_id=${context.model_id}`} className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 font-semibold">
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
            <Link href={`${ROUTES.failureExplorer}?model_id=${context.model_id}`} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold">
              View Source Failure Explorer <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1 text-slate-300">
            <div>Status: <span className="font-mono font-bold text-indigo-300">{failure_explorer_summary.status}</span></div>
            <div>Signatures Analyzed: <span className="font-mono">{failure_explorer_summary.signature_count || failure_explorer_summary.n_signatures || 0}</span></div>
            {failure_explorer_summary.details && (
              <div className="text-slate-400 italic pt-1">{failure_explorer_summary.details}</div>
            )}
          </div>
        </div>

        {/* SECTION G: Temporal Intelligence */}
        <div id="section-g" className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-sky-400" /> Section G: Temporal Intelligence & Early Warning
            </h2>
            <Link href={`${ROUTES.earlyWarning}?model_id=${context.model_id}`} className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-semibold">
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
            {trend_comparison && trend_comparison.has_previous_analysis ? (
              <div>Trend Direction: <span className="font-bold text-indigo-300">{trend_comparison.trend_direction || "STABLE"}</span></div>
            ) : (
              <div className="text-slate-400 font-bold text-amber-300">NO VALID COMPARABLE PRIOR ASSESSMENT</div>
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
