"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisSummary, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { ReliabilitySummary } from "@/components/ui/ReliabilitySummary";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { Download, FileText, Info, Layers, Printer, ShieldCheck } from "lucide-react";

export default function ReportsPageV1() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>("");
  const [fullAnalysis, setFullAnalysis] = useState<any | null>(null);

  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listModels();
        const loaded = res.models || [];
        setModels(loaded);
        if (loaded.length > 0) {
          const activeId = selectedModelId || loaded[0].model_id;
          setSelectedModelId(activeId);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load models.");
      } finally {
        setLoading(false);
      }
    }
    loadModels();
  }, []);

  useEffect(() => {
    async function loadAnalyses() {
      if (!selectedModelId) {
        setAnalyses([]);
        setSelectedAnalysisId("");
        setFullAnalysis(null);
        return;
      }
      setAnalysisLoading(true);
      setReportError(null);
      try {
        const res = await api.listModelAnalyses(selectedModelId);
        const runs = res.analyses || [];
        setAnalyses(runs);
        if (runs.length > 0) {
          const firstAnalysisId = runs[0].analysis_id;
          setSelectedAnalysisId(firstAnalysisId);
          try {
            const data = await api.getAnalysis(firstAnalysisId);
            setFullAnalysis(data);
          } catch (err: any) {
            setFullAnalysis(null);
            setReportError(err.message || "Failed to retrieve analysis report payload.");
          }
        } else {
          setSelectedAnalysisId("");
          setFullAnalysis(null);
        }
      } catch (err: any) {
        setAnalyses([]);
        setSelectedAnalysisId("");
        setFullAnalysis(null);
        setReportError(err.message || "Failed to load model analyses.");
      } finally {
        setAnalysisLoading(false);
      }
    }
    loadAnalyses();
  }, [selectedModelId]);

  const handleSelectAnalysis = async (analysisId: string) => {
    setSelectedAnalysisId(analysisId);
    if (!analysisId) {
      setFullAnalysis(null);
      return;
    }
    setAnalysisLoading(true);
    setReportError(null);
    try {
      const data = await api.getAnalysis(analysisId);
      setFullAnalysis(data);
    } catch (err: any) {
      setFullAnalysis(null);
      setReportError(err.message || "Failed to retrieve selected analysis report.");
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleDownloadJSON = () => {
    if (!fullAnalysis) return;
    try {
      const jsonStr = JSON.stringify(fullAnalysis, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `aegisx_report_${selectedAnalysisId.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Report Exported", "Downloaded JSON report payload.");
    } catch (err: any) {
      toast.error("Export Failed", err.message || "Could not generate JSON report.");
    }
  };

  const handleDownloadCSV = () => {
    if (!fullAnalysis) return;
    try {
      const rows = [
        ["Metric", "Value"],
        ["Analysis ID", fullAnalysis.analysis_id],
        ["Model ID", fullAnalysis.model_id],
        ["Evaluation Dataset ID", fullAnalysis.evaluation_dataset_id],
        ["Fusion Method", fullAnalysis.fusion?.method || "stress_robust"],
        ["OOD Risk", fullAnalysis.ood?.aggregate_score ?? "N/A"],
        ["Uncertainty Risk", fullAnalysis.uncertainty?.aggregate_score ?? "N/A"],
        ["Drift Risk", fullAnalysis.drift?.aggregate_score ?? "N/A"],
        ["Fused Risk", fullAnalysis.fusion?.aggregate_fused_risk ?? "N/A"],
      ];
      const csvContent = "data:text/csv;charset=utf-8," + rows.map((e) => e.join(",")).join("\n");
      const encodedUri = encodeURI(csvContent);
      const a = document.createElement("a");
      a.href = encodedUri;
      a.download = `aegisx_summary_${selectedAnalysisId.slice(0, 8)}.csv`;
      a.click();
      toast.success("Report Exported", "Downloaded CSV report summary.");
    } catch (err: any) {
      toast.error("Export Failed", err.message || "Could not generate CSV report.");
    }
  };

  if (loading) return <LoadingState message="Compiling reliability report payloads..." />;
  if (error) return <ErrorState message={error} />;

  const activeModel = models.find((m) => m.model_id === selectedModelId);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reliability Reports V1"
        description="Structured operational reliability report compilation and lightweight export."
        icon={<FileText className="w-6 h-6 text-indigo-400" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Reliability Reports" }]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => window.print()}
              disabled={!fullAnalysis}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700/80 transition-all disabled:opacity-50 inline-flex items-center space-x-1 shadow-sm focus:outline-none"
            >
              <Printer className="w-3.5 h-3.5 mr-1" /> Print Report
            </button>
            <button
              onClick={handleDownloadJSON}
              disabled={!fullAnalysis}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all disabled:opacity-50 inline-flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <Download className="w-3.5 h-3.5 mr-1" /> Export JSON
            </button>
            <button
              onClick={handleDownloadCSV}
              disabled={!fullAnalysis}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700/80 transition-all disabled:opacity-50 inline-flex items-center space-x-1 shadow-sm focus:outline-none"
            >
              <FileText className="w-3.5 h-3.5 mr-1" /> Export CSV
            </button>
          </div>
        }
      />

      {/* Model & Analysis Selectors */}
      {models.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs font-mono shadow-sm">
          <div className="flex items-center space-x-3">
            <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="font-semibold text-slate-200">Model Context:</span>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500 text-xs"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-3">
            <span className="font-semibold text-slate-200">Analysis Run:</span>
            <select
              value={selectedAnalysisId}
              onChange={(e) => handleSelectAnalysis(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500 text-xs"
            >
              {analyses.length === 0 ? (
                <option value="">No analyses available</option>
              ) : (
                analyses.map((a) => (
                  <option key={a.analysis_id} value={a.analysis_id}>
                    {a.analysis_id.slice(0, 8)}... ({new Date(a.created_at).toLocaleDateString()})
                  </option>
                ))
              )}
            </select>
            {selectedAnalysisId && <CopyButton text={selectedAnalysisId} label="Copy Analysis ID" />}
          </div>
        </div>
      )}

      {analysisLoading ? (
        <LoadingState message="Fetching operational analysis report payload..." />
      ) : reportError ? (
        <ErrorState message={reportError} />
      ) : fullAnalysis ? (
        <div className="space-y-6 print:text-black">
          {/* Executive Summary Card */}
          <SectionCard
            title="Executive Reliability Summary"
            subtitle={`Analysis ID: ${fullAnalysis.analysis_id} | Status: ${fullAnalysis.status}`}
            action={
              <div className="flex items-center space-x-3">
                <CopyButton text={fullAnalysis.analysis_id} />
                <StatusBadge status={fullAnalysis.status} />
              </div>
            }
          >
            <div className="p-4 bg-slate-950/80 border border-slate-800/80 rounded-xl space-y-3 text-xs shadow-md">
              <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm">
                <ShieldCheck className="w-5 h-5 shrink-0" />
                <span>Operational Assessment</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Elevated reliability risk evaluated across operational OOD, Uncertainty, and Feature Drift detectors. Pre-label signal fusion method:{" "}
                <strong className="text-slate-100 uppercase font-mono">{fullAnalysis.fusion?.method || "stress_robust"}</strong>.
              </p>
            </div>
          </SectionCard>

          {/* Model & Dataset Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <SectionCard title="Model Specification" subtitle="Registered user classification model">
              <div className="space-y-2 text-slate-300 font-mono">
                <div className="flex items-center justify-between"><span className="text-slate-400">Name:</span> <span className="font-bold text-slate-200">{activeModel?.model_name || "N/A"}</span></div>
                <div className="flex items-center justify-between"><span className="text-slate-400">Task Type:</span> <span>{activeModel?.task_type || "binary_classification"}</span></div>
                <div className="flex items-center justify-between"><span className="text-slate-400">Features:</span> <span>{activeModel?.n_features_in ?? "N/A"}</span></div>
                <div className="flex items-center justify-between"><span className="text-slate-400">predict_proba:</span> <span>{activeModel?.predict_proba_supported ? "Yes" : "No"}</span></div>
              </div>
            </SectionCard>

            <SectionCard title="Evaluation Batch Metadata" subtitle="Assessed operational dataset">
              <div className="space-y-2 text-slate-300 font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Eval Dataset ID:</span>
                  <div className="flex items-center space-x-1">
                    <span>{fullAnalysis.evaluation_dataset_id?.slice(0, 8)}...</span>
                    <CopyButton text={fullAnalysis.evaluation_dataset_id} />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Ref Dataset ID:</span>
                  <div className="flex items-center space-x-1">
                    <span>{fullAnalysis.reference_dataset_id?.slice(0, 8)}...</span>
                    <CopyButton text={fullAnalysis.reference_dataset_id} />
                  </div>
                </div>
                <div className="flex items-center justify-between"><span className="text-slate-400">Evaluated At:</span> <span>{new Date(fullAnalysis.created_at).toLocaleString()}</span></div>
              </div>
            </SectionCard>
          </div>

          {/* Reliability Signals Breakdown */}
          <SectionCard title="Reliability Signal Breakdown" subtitle="Independent detector risk outputs">
            <ReliabilitySummary
              oodRisk={fullAnalysis.ood?.aggregate_score}
              uncertaintyRisk={fullAnalysis.uncertainty?.aggregate_score}
              driftRisk={fullAnalysis.drift?.aggregate_score}
              fusedRisk={fullAnalysis.fusion?.aggregate_fused_risk}
            />
          </SectionCard>

          {/* Retrospective Diagnostics (If present) */}
          {fullAnalysis.diagnostics && (
            <SectionCard title="Retrospective Diagnostics" subtitle="Computed with ground-truth target labels">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Accuracy</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1 font-sans">
                    {(fullAnalysis.diagnostics.accuracy * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Error Rate</div>
                  <div className="text-xl font-bold text-amber-400 mt-1 font-sans">
                    {(fullAnalysis.diagnostics.error_rate * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Total Failures</div>
                  <div className="text-xl font-bold text-rose-400 mt-1 font-sans">
                    {fullAnalysis.diagnostics.num_failures}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Spearman Correlation</div>
                  <div className="text-xl font-bold text-indigo-400 mt-1 font-sans">
                    {fullAnalysis.diagnostics.correlation_fused_risk_vs_error ?? "N/A"}
                  </div>
                </div>
              </div>
            </SectionCard>
          )}

          {/* Scientific Warnings & Limitations */}
          <SectionCard title="Scientific Disclosures & Limitations" subtitle="Methodological bounds">
            <div className="space-y-2 text-xs text-slate-300">
              {(fullAnalysis.limitations || []).map((lim: string, idx: number) => (
                <div key={idx} className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 font-mono text-[11px]">
                  • {lim}
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      ) : (
        <div className="p-8 text-center text-slate-400 border border-slate-800/80 rounded-2xl bg-slate-900/40 font-mono text-xs shadow-md">
          No operational analysis selected for report generation. Run an analysis in Batch Monitor to inspect reports.
        </div>
      )}
    </div>
  );
}

