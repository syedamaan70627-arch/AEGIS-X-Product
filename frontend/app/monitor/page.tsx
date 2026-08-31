"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisResponse, DatasetRecord, ModelRecord } from "@/types/api";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Activity, AlertCircle, BarChart3, CheckCircle2, Play, ShieldAlert } from "lucide-react";

export default function BatchMonitorPage() {
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
    } catch (err: any) {
      setAnalysisError(err.message || "Operational analysis execution failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Batch Operational Monitor"
        description="Execute AEGIS-X multi-signal operational analysis across OOD, Uncertainty, Drift, and Fusion detectors."
      />

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
                <label className="block font-medium text-slate-300 mb-1">Target Model *</label>
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  {models.map((m) => (
                    <option key={m.model_id} value={m.model_id}>
                      {m.model_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Evaluation Dataset *</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
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
                <label className="block font-medium text-slate-300 mb-1">Operational Fusion Engine *</label>
                <select
                  value={fusionMethod}
                  onChange={(e) => setFusionMethod(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  <option value="stress_robust">StressRobust Fusion (Recommended)</option>
                  <option value="original">Original Fusion</option>
                </select>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={analyzing || !selectedDatasetId}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow-md transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{analyzing ? "Running Analysis..." : "Execute Operational Analysis"}</span>
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
                action={<StatusBadge status={analysisResult.status} />}
              >
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <RiskIndicator label="OOD Risk" value={analysisResult.ood.aggregate_score} />
                  <RiskIndicator label="Uncertainty Risk" value={analysisResult.uncertainty.aggregate_score} />
                  <RiskIndicator label="Drift Risk" value={analysisResult.drift.aggregate_score} />
                  <RiskIndicator label="Fused Risk Score" value={analysisResult.fusion.aggregate_fused_risk} />
                </div>

                <div className="mt-4 p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">Scientific Note:</span> Individual reliability signals (OOD, Uncertainty, Drift) are preserved independently because their operational usefulness varies by deployment context.
                </div>
              </SectionCard>

              {/* Separate Label-Aware Retrospective Diagnostics Section */}
              {analysisResult.diagnostics ? (
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h3 className="text-sm font-bold text-slate-100">Retrospective Diagnostics</h3>
                      <p className="text-xs text-slate-400">
                        Computed using ground-truth target labels present in evaluation dataset.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <div className="text-slate-400 uppercase font-mono">Accuracy</div>
                      <div className="text-xl font-bold text-emerald-400 mt-1">
                        {(analysisResult.diagnostics.accuracy * 100).toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <div className="text-slate-400 uppercase font-mono">Error Rate</div>
                      <div className="text-xl font-bold text-amber-400 mt-1">
                        {(analysisResult.diagnostics.error_rate * 100).toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <div className="text-slate-400 uppercase font-mono">Total Failures</div>
                      <div className="text-xl font-bold text-rose-400 mt-1">
                        {analysisResult.diagnostics.num_failures} / {analysisResult.diagnostics.metrics.total_evaluation_samples}
                      </div>
                    </div>

                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <div className="text-slate-400 uppercase font-mono">Spearman Correlation</div>
                      <div className="text-xl font-bold text-indigo-400 mt-1">
                        {analysisResult.diagnostics.correlation_fused_risk_vs_error ?? "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-center justify-between">
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
