"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DatasetRecord, ModelRecord, StressTestResponse } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { Layers, Play, Zap } from "lucide-react";

export default function StressLabPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");

  // Stress Parameters
  const [stressType, setStressType] = useState<string>("Gaussian_Noise");
  const [severity, setSeverity] = useState<number>(0.3);
  const [randomState, setRandomState] = useState<number>(42);

  // Execution State
  const [executing, setExecuting] = useState(false);
  const [stressResult, setStressResult] = useState<StressTestResponse | null>(null);
  const [stressError, setStressError] = useState<string | null>(null);

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
    async function loadDatasetsForModel() {
      if (!selectedModelId) return;
      try {
        const res = await api.listDatasets(selectedModelId);
        const evals = (res.datasets || []).filter((d) => d.dataset_type === "EVALUATION");
        setDatasets(evals);
        if (evals.length > 0) setSelectedDatasetId(evals[0].dataset_id);
        else setSelectedDatasetId("");
      } catch (_) {}
    }
    loadDatasetsForModel();
  }, [selectedModelId]);

  const handleRunStressTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedDatasetId) {
      setStressError("Please select both a model and an evaluation dataset.");
      return;
    }

    setExecuting(true);
    setStressError(null);
    try {
      const res = await api.runStressTest({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
        stress_type: stressType,
        severity: Number(severity),
        random_state: Number(randomState),
      });
      setStressResult(res);
      toast.success("Stress Test Executed", `Stressed fused risk: ${res.stressed_risk != null ? (res.stressed_risk * 100).toFixed(1) : 0}%`);
    } catch (err: any) {
      setStressError(err.message || "Stress lab test execution failed.");
      toast.error("Stress Test Error", err.message || "Execution failed.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Stress Lab Engine"
        description="Controlled synthetic stress testing (Gaussian Noise, Feature Dropout, Permutation, Combined Stress) on dataset copies without mutating source data."
        icon={<Zap className="w-6 h-6 text-amber-400" />}
        breadcrumbs={[{ label: "Testing" }, { label: "Stress Lab" }]}
      />

      {loading ? (
        <LoadingState message="Initializing Stress Lab engine..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="space-y-8">
          {/* Stress Setup */}
          <SectionCard title="Stress Test Parameters" subtitle="Configure controlled perturbation parameters">
            {stressError && <ErrorState message={stressError} />}

            <form onSubmit={handleRunStressTest} className="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs items-end">
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
                        {d.filename}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Stress Family *</label>
                <select
                  value={stressType}
                  onChange={(e) => setStressType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  <option value="Gaussian_Noise">Gaussian Noise</option>
                  <option value="Feature_Dropout">Feature Dropout</option>
                  <option value="Feature_Permutation">Feature Permutation</option>
                  <option value="Combined_Stress">Combined Stress</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1 font-mono">Severity ({severity}) *</label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={severity}
                  onChange={(e) => setSeverity(parseFloat(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={executing || !selectedDatasetId}
                  className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-semibold shadow-md transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <Zap className="w-4 h-4 fill-current" />
                  <span>{executing ? "Running Stress..." : "Run Stress Test"}</span>
                </button>
              </div>
            </form>
          </SectionCard>

          {/* Execution Progress */}
          {executing && <LoadingState message="Applying controlled stress perturbations to evaluation copy..." />}

          {/* Results Comparison */}
          {stressResult && (
            <div className="space-y-6">
              <SectionCard
                title="Stress Impact Results (Original vs Stressed)"
                subtitle={`Stress Run ID: ${stressResult.stress_test_id} | Family: ${stressResult.stress_type} | Severity: ${stressResult.severity}`}
                action={
                  <div className="flex items-center space-x-3">
                    <CopyButton text={stressResult.stress_test_id} label="Copy Run ID" />
                    <StatusBadge status={stressResult.status} />
                  </div>
                }
              >
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                    <div className="text-slate-400 font-semibold uppercase text-[11px]">Original Fused Risk</div>
                    <div className="text-xl font-bold text-slate-200 mt-1">
                      {stressResult.original_risk != null ? `${(stressResult.original_risk * 100).toFixed(1)}%` : "N/A"}
                    </div>
                  </div>

                  <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                    <div className="text-slate-400 font-semibold uppercase text-[11px]">Stressed Fused Risk</div>
                    <div className="text-xl font-bold text-amber-400 mt-1">
                      {stressResult.stressed_risk != null ? `${(stressResult.stressed_risk * 100).toFixed(1)}%` : "N/A"}
                    </div>
                  </div>

                  <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                    <div className="text-slate-400 font-semibold uppercase text-[11px]">Risk Delta (Increase)</div>
                    <div className="text-xl font-bold text-rose-400 mt-1">
                      {stressResult.risk_delta != null ? `+${(stressResult.risk_delta * 100).toFixed(1)}%` : "N/A"}
                    </div>
                  </div>
                </div>

                {/* Additional accuracy comparison if labels existed */}
                {stressResult.original_accuracy != null && (
                  <div className="mt-4 p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono shadow-md">
                    <div>
                      <span className="text-slate-400 font-semibold">Original Accuracy:</span>{" "}
                      <span className="font-bold text-emerald-400 font-sans">{(stressResult.original_accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold">Stressed Accuracy:</span>{" "}
                      <span className="font-bold text-amber-400 font-sans">{(stressResult.stressed_accuracy! * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold">Accuracy Delta:</span>{" "}
                      <span className="font-bold text-rose-400 font-sans">{(stressResult.accuracy_delta! * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}
              </SectionCard>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

