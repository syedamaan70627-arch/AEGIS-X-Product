"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisSummary, ModelRecord } from "@/types/api";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { ReliabilitySummary } from "@/components/ui/ReliabilitySummary";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Download, FileText, Info, Layers, Printer, ShieldCheck } from "lucide-react";

export default function ReportsPageV1() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
      if (!selectedModelId) return;
      try {
        const res = await api.listModelAnalyses(selectedModelId);
        const runs = res.analyses || [];
        setAnalyses(runs);
        if (runs.length > 0) {
          setSelectedAnalysisId(runs[0].analysis_id);
        } else {
          setSelectedAnalysisId("");
          setFullAnalysis(null);
        }
      } catch (_) {}
    }
    loadAnalyses();
  }, [selectedModelId]);

  useEffect(() => {
    async function fetchFullAnalysisPayload() {
      if (!selectedAnalysisId) return;
      try {
        const data = await api.getAnalysis(selectedAnalysisId);
        setFullAnalysis(data);
      } catch (_) {
        setFullAnalysis(null);
      }
    }
    fetchFullAnalysisPayload();
  }, [selectedAnalysisId]);

  const handleDownloadJSON = () => {
    if (!fullAnalysis) return;
    const jsonStr = JSON.stringify(fullAnalysis, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aegisx_report_${selectedAnalysisId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadCSV = () => {
    if (!fullAnalysis) return;
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
  };

  if (loading) return <LoadingState message="Compiling reliability report payloads..." />;
  if (error) return <ErrorState message={error} />;

  const activeModel = models.find((m) => m.model_id === selectedModelId);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reliability Reports V1"
        description="Structured operational reliability report compilation and lightweight export."
        actions={
          <div className="flex items-center space-x-2">
            <button
              onClick={() => window.print()}
              disabled={!fullAnalysis}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
            >
              <Printer className="w-3.5 h-3.5 mr-1" /> Print Report
            </button>
            <button
              onClick={handleDownloadJSON}
              disabled={!fullAnalysis}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-md transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
            >
              <Download className="w-3.5 h-3.5 mr-1" /> Export JSON
            </button>
            <button
              onClick={handleDownloadCSV}
              disabled={!fullAnalysis}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
            >
              <FileText className="w-3.5 h-3.5 mr-1" /> Export CSV
            </button>
          </div>
        }
      />

      {/* Model & Analysis Selectors */}
      {models.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-3">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-slate-200">Model Context:</span>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
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
              onChange={(e) => setSelectedAnalysisId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
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
          </div>
        </div>
      )}

      {fullAnalysis ? (
        <div className="space-y-6 print:text-black">
          {/* Executive Summary Card */}
          <SectionCard
            title="Executive Reliability Summary"
            subtitle={`Analysis ID: ${fullAnalysis.analysis_id} | Status: ${fullAnalysis.status}`}
            action={<StatusBadge status={fullAnalysis.status} />}
          >
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-xs">
              <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm">
                <ShieldCheck className="w-5 h-5" />
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
                <div><span className="text-slate-400">Name:</span> {activeModel?.model_name || "N/A"}</div>
                <div><span className="text-slate-400">Task Type:</span> {activeModel?.task_type || "binary_classification"}</div>
                <div><span className="text-slate-400">Features:</span> {activeModel?.n_features_in ?? "N/A"}</div>
                <div><span className="text-slate-400">predict_proba:</span> {activeModel?.predict_proba_supported ? "Yes" : "No"}</div>
              </div>
            </SectionCard>

            <SectionCard title="Evaluation Batch Metadata" subtitle="Assessed operational dataset">
              <div className="space-y-2 text-slate-300 font-mono">
                <div><span className="text-slate-400">Eval Dataset ID:</span> {fullAnalysis.evaluation_dataset_id}</div>
                <div><span className="text-slate-400">Ref Dataset ID:</span> {fullAnalysis.reference_dataset_id}</div>
                <div><span className="text-slate-400">Evaluated At:</span> {new Date(fullAnalysis.created_at).toLocaleString()}</div>
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
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono">Accuracy</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">
                    {(fullAnalysis.diagnostics.accuracy * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono">Error Rate</div>
                  <div className="text-xl font-bold text-amber-400 mt-1">
                    {(fullAnalysis.diagnostics.error_rate * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono">Total Failures</div>
                  <div className="text-xl font-bold text-rose-400 mt-1">
                    {fullAnalysis.diagnostics.num_failures}
                  </div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono">Spearman Correlation</div>
                  <div className="text-xl font-bold text-indigo-400 mt-1">
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
                <div key={idx} className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 font-mono text-[11px]">
                  • {lim}
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      ) : (
        <div className="p-8 text-center text-slate-400 border border-slate-800 rounded-xl bg-slate-900/40">
          No operational analysis selected for report generation. Run an analysis in Batch Monitor to inspect reports.
        </div>
      )}
    </div>
  );
}
