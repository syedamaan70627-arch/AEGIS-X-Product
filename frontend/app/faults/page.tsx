"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { DatasetRecord, FaultTestResponse, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { AlertOctagon, ArrowRight, Layers, Play } from "lucide-react";

export default function FaultLabPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");

  // Fault Parameters
  const [faultType, setFaultType] = useState<string>("Sensor_Bias");
  const [severity, setSeverity] = useState<number>(0.5);
  const [affectedFeatures, setAffectedFeatures] = useState<string>("");
  const [stuckValue, setStuckValue] = useState<number>(0.0);
  const [featurePair, setFeaturePair] = useState<string>("");

  // Execution State
  const [executing, setExecuting] = useState(false);
  const [faultResult, setFaultResult] = useState<FaultTestResponse | null>(null);
  const [faultError, setFaultError] = useState<string | null>(null);

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

  const handleRunFaultTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedDatasetId) {
      setFaultError("Please select both a model and an evaluation dataset.");
      return;
    }

    setExecuting(true);
    setFaultError(null);
    try {
      const featList = affectedFeatures
        ? affectedFeatures.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined;

      const pairList = featurePair
        ? featurePair.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined;

      const res = await api.runFaultTest({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
        fault_type: faultType,
        severity: Number(severity),
        affected_features: featList,
        stuck_value: faultType === "Stuck_At" ? Number(stuckValue) : undefined,
        feature_pair: faultType === "Channel_Swap" ? pairList : undefined,
      });
      setFaultResult(res);
      toast.success("Fault Injection Executed", `Injected ${faultType} fault successfully`);
    } catch (err: any) {
      setFaultError(err.message || "Fault injection execution failed.");
      toast.error("Fault Injection Error", err.message || "Execution failed.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Fault Lab Engine"
        description="Structured sensor bias, gain error, stuck-at, channel swap, and sign inversion fault injection on dataset copies."
        icon={<AlertOctagon className="w-6 h-6 text-rose-400" />}
        breadcrumbs={[{ label: "Testing" }, { label: "Fault Lab" }]}
      />

      {loading ? (
        <LoadingState message="Initializing Fault Lab engine..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="space-y-8">
          {/* Fault Configuration Card */}
          <SectionCard title="Fault Injection Parameters" subtitle="Select structured physical fault family and severity">
            {faultError && <ErrorState message={faultError} />}

            <form onSubmit={handleRunFaultTest} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Target Model *</label>
                  <select
                    value={selectedModelId}
                    onChange={(e) => setSelectedModelId(e.target.value)}
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono"
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
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono"
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
                  <label className="block font-semibold text-[#F3F4F6] mb-1">Fault Family *</label>
                  <select
                    value={faultType}
                    onChange={(e) => setFaultType(e.target.value)}
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-sans"
                  >
                    <option value="Sensor_Bias">Sensor Bias</option>
                    <option value="Gain_Error">Gain Error</option>
                    <option value="Stuck_At">Stuck-At Sensor</option>
                    <option value="Channel_Swap">Channel Swap</option>
                    <option value="Sign_Inversion">Sign Inversion</option>
                  </select>
                </div>
              </div>

              {/* Dynamic Fault Inputs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1 font-mono">Severity ({severity}) *</label>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={severity}
                    onChange={(e) => setSeverity(parseFloat(e.target.value))}
                    className="w-full accent-[#3B82F6] cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Affected Feature(s) (Comma separated)</label>
                  <input
                    type="text"
                    value={affectedFeatures}
                    onChange={(e) => setAffectedFeatures(e.target.value)}
                    placeholder="e.g. f1, f2 (Leave empty for random)"
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] font-mono"
                  />
                </div>

                {faultType === "Stuck_At" && (
                  <div>
                    <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Stuck Value</label>
                    <input
                      type="number"
                      step="any"
                      value={stuckValue}
                      onChange={(e) => setStuckValue(parseFloat(e.target.value))}
                      className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono"
                    />
                  </div>
                )}

                {faultType === "Channel_Swap" && (
                  <div>
                    <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Feature Pair (Comma separated)</label>
                    <input
                      type="text"
                      value={featurePair}
                      onChange={(e) => setFeaturePair(e.target.value)}
                      placeholder="e.g. f1, f2"
                      className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono"
                    />
                  </div>
                )}
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={executing || !selectedDatasetId}
                  className="w-full py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg font-semibold shadow-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
                >
                  <AlertOctagon className="w-4 h-4" />
                  <span>{executing ? "Injecting Fault..." : "Inject Fault & Evaluate Failure Discovery"}</span>
                </button>
              </div>
            </form>
          </SectionCard>

          {/* Execution Loading */}
          {executing && <LoadingState message="Injecting physical fault transformation and running failure discovery..." />}

          {/* Fault Test Result Overview */}
          {faultResult && (
            <div className="space-y-6">
              <SectionCard
                title="Fault Injection Execution Summary"
                subtitle={`Run ID: ${faultResult.fault_test_id} | Family: ${faultResult.fault_type} | Severity: ${faultResult.severity}`}
                action={
                  <div className="flex items-center space-x-3">
                    <CopyButton text={faultResult.fault_test_id} label="Copy Run ID" />
                    <StatusBadge status={faultResult.status} />
                  </div>
                }
              >
                <div className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl space-y-3 text-xs shadow-sm font-sans">
                  <div>
                    <span className="font-mono text-[#9CA3AF] font-semibold">Affected Features:</span>{" "}
                    <span className="font-bold text-[#F3F4F6] font-mono">
                      {faultResult.affected_features.length > 0
                        ? faultResult.affected_features.join(", ")
                        : "All/Random"}
                    </span>
                  </div>

                  <div className="pt-3 border-t border-[#26303D] flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-sans">
                    <span className="text-[#9CA3AF]">Explore observation-level failure events & silent failures:</span>
                    <Link
                      href="/failures"
                      className="px-4 py-2 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold rounded-lg shadow-sm transition-all inline-flex items-center space-x-1 shrink-0 font-sans"
                    >
                      <span>Open Failure Explorer</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Link>
                  </div>
                </div>
              </SectionCard>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

