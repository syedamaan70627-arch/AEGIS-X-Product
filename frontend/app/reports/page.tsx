"use me";
"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisSummary, ModelRecord, ReportRecord, ReportPayload } from "@/types/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { IntegratedReportView } from "@/components/reports/IntegratedReportView";
import { ReportHistoryDrawer } from "@/components/reports/ReportHistoryDrawer";
import { useToast } from "@/components/providers/ToastProvider";
import {
  FileText,
  Layers,
  Clock,
  Sparkles,
  ShieldCheck,
  BarChart2,
  Lock,
  Compass,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

type ReportTab = "integrated" | "reliability" | "model_trust" | "governance";

export default function ReportsPage() {
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const [errorObj, setErrorObj] = useState<{
    message: string;
    reason?: string;
    action?: string;
    techDetails?: string;
  } | null>(null);
  const [showTechDetails, setShowTechDetails] = useState(false);

  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>("");

  const [activeTab, setActiveTab] = useState<ReportTab>("integrated");
  const [activeReport, setActiveReport] = useState<ReportRecord | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  // 1. Initial Models Load
  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      setErrorObj(null);
      try {
        const res = await api.listModels();
        const loaded = res.models || [];
        setModels(loaded);
        if (loaded.length > 0) {
          setSelectedModelId(loaded[0].model_id);
        }
      } catch (err: any) {
        setErrorObj({
          message: "Report generation failed",
          reason: err.reason || "Unable to retrieve registered model context.",
          action: err.action || "Please ensure the backend service is running and retry.",
          techDetails: err.details || err.message || String(err),
        });
      } finally {
        setLoading(false);
      }
    }
    loadModels();
  }, []);

  // Helper to load or generate report
  const loadExistingOrGenerateReport = async (
    modelId: string,
    analysisId: string,
    reportType: string
  ) => {
    try {
      setErrorObj(null);
      // Check existing reports
      const existing = await api.listReportsByModel(modelId);
      const match = existing.find((r) => r.analysis_id === analysisId);
      if (match) {
        setActiveReport(match);
      } else {
        // Auto-generate initial report snapshot if none exists
        const generated = await api.generateReport({
          model_id: modelId,
          analysis_id: analysisId,
          report_type: reportType,
        });
        setActiveReport(generated);
      }
    } catch (err: any) {
      setActiveReport(null);
      setErrorObj({
        message: "Report generation failed",
        reason: err.reason || "Report storage is currently unavailable.",
        action: err.action || "Please retry after the reporting service becomes available.",
        techDetails: err.details || err.message || String(err),
      });
    }
  };

  // 2. Load Analyses for Selected Model
  useEffect(() => {
    async function loadAnalyses() {
      if (!selectedModelId) {
        setAnalyses([]);
        setSelectedAnalysisId("");
        setActiveReport(null);
        return;
      }
      setLoading(true);
      setErrorObj(null);
      try {
        const res = await api.listModelAnalyses(selectedModelId);
        const runs = res.analyses || [];
        setAnalyses(runs);
        if (runs.length > 0) {
          const firstAnalysisId = runs[0].analysis_id;
          setSelectedAnalysisId(firstAnalysisId);
          await loadExistingOrGenerateReport(selectedModelId, firstAnalysisId, activeTab);
        } else {
          setSelectedAnalysisId("");
          setActiveReport(null);
        }
      } catch (err: any) {
        setAnalyses([]);
        setSelectedAnalysisId("");
        setActiveReport(null);
        setErrorObj({
          message: "Report generation failed",
          reason: err.reason || "Failed to retrieve analysis runs for the selected model.",
          action: err.action || "Run an analysis under Core Reliability before generating reports.",
          techDetails: err.details || err.message || String(err),
        });
      } finally {
        setLoading(false);
      }
    }
    loadAnalyses();
  }, [selectedModelId]);

  const handleSelectAnalysis = async (analysisId: string) => {
    setSelectedAnalysisId(analysisId);
    if (!analysisId || !selectedModelId) return;
    setLoading(true);
    await loadExistingOrGenerateReport(selectedModelId, analysisId, activeTab);
    setLoading(false);
  };

  const handleGenerateNewSnapshot = async () => {
    if (!selectedModelId || !selectedAnalysisId) {
      toast.error("Generation Failed", "Please select a valid model and analysis run.");
      return;
    }
    setGenerating(true);
    setErrorObj(null);
    try {
      const rep = await api.generateReport({
        model_id: selectedModelId,
        analysis_id: selectedAnalysisId,
        report_type: activeTab,
      });
      setActiveReport(rep);
      toast.success("Snapshot Generated", `Created immutable report snapshot ${rep.id}.`);
    } catch (err: any) {
      setErrorObj({
        message: "Report generation failed",
        reason: err.reason || "Report storage is currently unavailable.",
        action: err.action || "Please retry after the reporting service becomes available.",
        techDetails: err.details || err.message || String(err),
      });
      toast.error("Generation Error", "Report storage is currently unavailable.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading && models.length === 0) {
    return <LoadingState message="Initializing AEGIS-X Decision Support & Reporting Engine..." />;
  }

  // Derive Readiness Strip Statuses
  const modelStatus = selectedModelId ? "READY" : "INVALID";
  const analysisStatus = selectedAnalysisId ? "READY" : "INCOMPLETE";
  const selectedAnalysisObj = analyses.find((a) => a.analysis_id === selectedAnalysisId);
  const evidenceStatus = selectedAnalysisObj?.reference_dataset_id && selectedAnalysisObj?.evaluation_dataset_id ? "READY" : "MISSING";
  const payload: ReportPayload | null = activeReport?.snapshot_json || null;
  const governanceStatus = payload?.ecrg_governance_summary?.effective_action && payload.ecrg_governance_summary.effective_action !== "UNAVAILABLE" ? "READY" : "NOT_EVALUATED";
  const storageStatus = errorObj ? "UNAVAILABLE" : "READY";

  const isPrereqSatisfied = modelStatus === "READY" && analysisStatus === "READY";

  return (
    <div className="space-y-8">
      <PageHeader
        title="AEGIS-X Reports & Decision Support Layer"
        description="Integrated reliability, operational trust, and governance decision-support reporting engine."
        icon={<FileText className="w-6 h-6 text-indigo-400" />}
        breadcrumbs={[{ label: "Governance" }, { label: "Reports & Decision Support" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={() => setHistoryOpen(true)}
              disabled={!selectedModelId}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition disabled:opacity-50"
            >
              <Clock className="w-3.5 h-3.5 text-indigo-400" /> Report History Timeline
            </button>
            <button
              onClick={handleGenerateNewSnapshot}
              disabled={!isPrereqSatisfied || generating}
              className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg shadow-lg shadow-indigo-600/20 transition disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${generating ? "animate-spin" : ""}`} />
              {generating ? "Generating..." : "Generate New Snapshot"}
            </button>
          </div>
        }
      />

      {/* Compact Readiness Strip */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-sans font-semibold">MODEL:</span>
          <span className={`px-2 py-0.5 rounded font-bold ${modelStatus === "READY" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/10 text-rose-400 border border-rose-500/30"}`}>
            {modelStatus}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-sans font-semibold">ANALYSIS:</span>
          <span className={`px-2 py-0.5 rounded font-bold ${analysisStatus === "READY" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-amber-500/10 text-amber-400 border border-amber-500/30"}`}>
            {analysisStatus}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-sans font-semibold">EVIDENCE:</span>
          <span className={`px-2 py-0.5 rounded font-bold ${evidenceStatus === "READY" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/10 text-rose-400 border border-rose-500/30"}`}>
            {evidenceStatus}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-sans font-semibold">GOVERNANCE:</span>
          <span className={`px-2 py-0.5 rounded font-bold ${governanceStatus === "READY" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-slate-800 text-slate-400 border border-slate-700"}`}>
            {governanceStatus}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-sans font-semibold">REPORT STORAGE:</span>
          <span className={`px-2 py-0.5 rounded font-bold ${storageStatus === "READY" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/10 text-rose-400 border border-rose-500/30"}`}>
            {storageStatus}
          </span>
        </div>
      </div>

      {/* Model & Analysis Selector Bar */}
      {models.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="font-semibold text-slate-200">Model Context:</span>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-200">Analysis Run:</span>
            <select
              value={selectedAnalysisId}
              onChange={(e) => handleSelectAnalysis(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
            >
              {analyses.length === 0 ? (
                <option value="">No analyses run for this model</option>
              ) : (
                analyses.map((a) => (
                  <option key={a.analysis_id} value={a.analysis_id}>
                    {a.analysis_id.slice(0, 8)}... ({new Date(a.created_at).toLocaleDateString()}) - Fused Risk: {typeof a.aggregate_fused_risk === "number" ? a.aggregate_fused_risk.toFixed(3) : "N/A"}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>
      )}

      {/* 4 Report View Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab("integrated")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === "integrated"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <ShieldCheck className="w-4 h-4" /> Integrated Report (Principal)
        </button>

        <button
          onClick={() => setActiveTab("reliability")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === "reliability"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <BarChart2 className="w-4 h-4" /> Reliability Assessment Summary
        </button>

        <button
          onClick={() => setActiveTab("model_trust")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === "model_trust"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Compass className="w-4 h-4" /> Model Trust & Governance
        </button>

        <button
          onClick={() => setActiveTab("governance")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === "governance"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Lock className="w-4 h-4" /> Governance Decision Report
        </button>
      </div>

      {/* User-Friendly Error Component */}
      {errorObj && (
        <div className="p-6 rounded-2xl bg-rose-950/30 border border-rose-900/60 text-slate-200 space-y-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">{errorObj.message}</h3>
              <p className="text-sm text-slate-300">
                <span className="font-semibold text-rose-300">Reason:</span> {errorObj.reason}
              </p>
              <p className="text-sm text-slate-300">
                <span className="font-semibold text-emerald-400">Action:</span> {errorObj.action}
              </p>
            </div>
          </div>

          {errorObj.techDetails && (
            <div className="pt-3 border-t border-rose-900/40">
              <button
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1 transition"
              >
                {showTechDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {showTechDetails ? "Hide Developer / Audit Details" : "Show Developer / Audit Details"}
              </button>
              {showTechDetails && (
                <pre className="mt-2 p-3 bg-slate-950 rounded-lg text-[11px] font-mono text-rose-200/90 overflow-x-auto border border-slate-800">
                  {errorObj.techDetails}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <LoadingState message="Retrieving persisted report snapshot..." />
      ) : !selectedAnalysisId ? (
        <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
          <AlertCircle className="w-10 h-10 text-amber-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No Analysis Run Available</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Please run an analysis under the Core Reliability tab for model <code className="font-mono text-indigo-300">{selectedModelId}</code> before compiling integrated decision reports.
          </p>
        </div>
      ) : payload ? (
        <IntegratedReportView report={payload} reportId={activeReport?.id || "N/A"} activeTab={activeTab} />
      ) : (
        <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 text-slate-400 text-sm">
          No report snapshot loaded for the selected analysis context. Click &quot;Generate New Snapshot&quot; above.
        </div>
      )}

      {/* Report History Drawer */}
      <ReportHistoryDrawer
        modelId={selectedModelId}
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectReport={(rep) => {
          setActiveReport(rep);
          toast.success("Snapshot Loaded", `Loaded report snapshot ${rep.id}.`);
        }}
      />
    </div>
  );
}
