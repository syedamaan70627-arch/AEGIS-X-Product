"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { AnalysisResponse, DatasetRecord, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { Activity, ArrowRight, CheckCircle2, ChevronRight, Play, ShieldAlert } from "lucide-react";

export default function BatchMonitorPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [fusionMethod, setFusionMethod] = useState<string>("stress_robust");

  // Analysis Execution State
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listModels();
        const loadedModels = res.models || [];
        setModels(loadedModels);

        if (loadedModels.length > 0) {
          const activeId = selectedModelId || loadedModels[0].model_id;
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
    async function loadDatasetsForModel() {
      if (!selectedModelId) return;
      try {
        const res = await api.listDatasets(selectedModelId);
        const evalDatasets = (res.datasets || []).filter((d) => d.dataset_type === "EVALUATION");
        setDatasets(evalDatasets);
        if (evalDatasets.length > 0) {
          setSelectedDatasetId(evalDatasets[0].dataset_id);
        } else {
          setSelectedDatasetId("");
        }
      } catch (_) {}
    }
    loadDatasetsForModel();
  }, [selectedModelId]);

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedDatasetId) {
      setAnalysisError("Please select both a model and an evaluation dataset.");
      return;
    }

    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await api.runAnalysis({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
        fusion_method: fusionMethod,
      });
      setAnalysisResult(res);
      toast.success("Analysis Complete", `Fused risk score: ${(res.fusion.aggregate_fused_risk * 100).toFixed(1)}%`);
    } catch (err: any) {
      setAnalysisError(err.message || "Operational analysis execution failed.");
      toast.error("Analysis Failed", err.message || "Could not complete analysis.");
    } finally {
      setAnalyzing(false);
    }
  };

  const steps = [
    { num: 1, label: "Active Model", done: !!selectedModelId },
    { num: 2, label: "Reference State", done: true },
    { num: 3, label: "Evaluation Batch", done: !!selectedDatasetId },
    { num: 4, label: "Fusion Engine", done: !!fusionMethod },
    { num: 5, label: "Execute", done: !!analysisResult },
    { num: 6, label: "Inspect Results", done: !!analysisResult },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Batch Operational Monitor"
        description="Execute AEGIS-X multi-signal operational analysis across OOD, Uncertainty, Drift, and Fusion detectors."
        icon={<Activity className="w-6 h-6 text-cyan-400" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Batch Monitor" }]}
      />

      {/* Guided 6-Step Workflow Stepper */}
      <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 shadow-md">
        <div className="flex items-center justify-between overflow-x-auto gap-2 text-xs font-mono py-1">
          {steps.map((s, idx) => (
            <React.Fragment key={s.num}>
              <div className="flex items-center space-x-2 shrink-0">
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold ${
                    s.done
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-950 border border-slate-800 text-slate-500"
                  }`}
                >
                  {s.num}
                </span>
                <span className={s.done ? "text-slate-200 font-semibold" : "text-slate-500"}>{s.label}</span>
              </div>
              {idx < steps.length - 1 && <ChevronRight className="w-4 h-4 text-slate-700 shrink-0" />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingState message="Initializing batch monitor..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="space-y-8">
          {/* Analysis Form Configuration */}
          <SectionCard title="Execution Setup" subtitle="Configure operational analysis parameter options">
            {analysisError && <ErrorState message={analysisError} />}

            <form onSubmit={handleRunAnalysis} className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs items-end">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Target Model *</label>
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  {models.map((m) => (
                    <option key={m.model_id} value={m.model_id}>
                      {m.model_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Evaluation Dataset *</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  {datasets.length === 0 ? (
                    <option value="">No EVALUATION datasets available</option>
                  ) : (
                    datasets.map((d) => (
                      <option key={d.dataset_id} value={d.dataset_id}>
                        {d.filename} ({d.num_samples} samples)
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Operational Fusion Engine *</label>
                <select
                  value={fusionMethod}
                  onChange={(e) => setFusionMethod(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  <option value="stress_robust">StressRobust Fusion (Recommended)</option>
                  <option value="original">Original Fusion</option>
                </select>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={analyzing || !selectedDatasetId}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow-md transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{analyzing ? "Running Analysis..." : "Execute Analysis"}</span>
                </button>
              </div>
            </form>
          </SectionCard>

          {/* Analysis Results View */}
          {analyzing && <LoadingState message="Running OOD, Uncertainty, Drift, and Fusion detectors..." />}

          {analysisResult && (
            <div className="space-y-8 animate-fadeIn">
              {/* Separate Reliability Signals Display */}
              <SectionCard
                title="Operational Reliability Signals"
                subtitle={`Analysis ID: ${analysisResult.analysis_id} | Status: ${analysisResult.status}`}
                action={
                  <div className="flex items-center space-x-3">
                    <CopyButton text={analysisResult.analysis_id} label="Copy Analysis ID" />
                    <StatusBadge status={analysisResult.status} />
                  </div>
                }
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <RiskIndicator label="OOD Risk" value={analysisResult.ood.aggregate_score} />
                  <RiskIndicator label="Uncertainty Risk" value={analysisResult.uncertainty.aggregate_score} />
                  <RiskIndicator label="Drift Risk" value={analysisResult.drift.aggregate_score} />
                  <RiskIndicator label="Fused Risk Score" value={analysisResult.fusion.aggregate_fused_risk} />
                </div>

                <div className="mt-4 p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl text-[11px] font-sans text-slate-400 flex items-center justify-between">
                  <span>
                    <strong className="text-slate-300">Scientific Scope Notice:</strong> Individual reliability signals (OOD, Uncertainty, Drift) are preserved independently because their operational usefulness varies by deployment context.
                  </span>
                  <Link href="/reliability" className="text-cyan-400 hover:text-cyan-300 font-semibold inline-flex items-center shrink-0 ml-4 font-mono">
                    Inspect Diagnostics →
                  </Link>
                </div>
              </SectionCard>

              {/* Separate Label-Aware Retrospective Diagnostics Section */}
              {analysisResult.diagnostics ? (
                <div className="p-6 bg-slate-900/90 border border-slate-800/80 rounded-2xl space-y-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      <div>
                        <h3 className="text-sm font-bold text-slate-100">Retrospective Diagnostics</h3>
                        <p className="text-xs text-slate-400">
                          Computed using ground-truth target labels present in evaluation dataset.
                        </p>
                      </div>
                    </div>
                    <StatusBadge status="LABEL_VERIFIED" />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Accuracy</div>
                      <div className="text-xl font-bold text-emerald-400 mt-1">
                        {(analysisResult.diagnostics.accuracy * 100).toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Error Rate</div>
                      <div className="text-xl font-bold text-amber-400 mt-1">
                        {(analysisResult.diagnostics.error_rate * 100).toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Total Failures</div>
                      <div className="text-xl font-bold text-rose-400 mt-1">
                        {analysisResult.diagnostics.num_failures} / {analysisResult.diagnostics.metrics.total_evaluation_samples}
                      </div>
                    </div>

                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Spearman Correlation</div>
                      <div className="text-xl font-bold text-indigo-400 mt-1">
                        {analysisResult.diagnostics.correlation_fused_risk_vs_error ?? "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 flex items-center justify-between shadow-md">
                  <span>Target labels absent: Evaluation dataset is processed label-free for operational risk.</span>
                  <StatusBadge status="LABEL_FREE" />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

