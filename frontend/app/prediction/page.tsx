"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DatasetRecord, ModelCapabilitiesResponse, ModelRecord, PredictionResponse } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { AlertCircle, Clock, FileCheck, Layers, Play } from "lucide-react";

export default function FailurePredictionPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [capabilities, setCapabilities] = useState<ModelCapabilitiesResponse | null>(null);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");

  const [executing, setExecuting] = useState(false);
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [selectedTrajectoryId, setSelectedTrajectoryId] = useState<string>("");
  const [fitting, setFitting] = useState(false);
  const [fitSuccess, setFitSuccess] = useState<string | null>(null);

  const handleFitPrediction = async () => {
    if (!selectedModelId || !selectedTrajectoryId) return;
    setFitting(true);
    setPredictionError(null);
    setFitSuccess(null);
    try {
      await api.fitFailurePrediction(selectedModelId, { trajectory_dataset_id: selectedTrajectoryId });
      setFitSuccess("Failure prediction model fitted successfully! Capability updated to READY.");
      toast.success("Prediction Setup Complete", "Predictor model fitted and capability set to READY.");
      const updatedCap = await api.getModelCapabilities(selectedModelId);
      setCapabilities(updatedCap);
    } catch (err: any) {
      setPredictionError(err.message || "Failed to fit failure predictor.");
      toast.error("Setup Failed", err.message || "Could not fit predictor.");
    } finally {
      setFitting(false);
    }
  };

  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listModels();
        const loaded = res.models || [];
        setModels(loaded);
        if (loaded.length > 0) {
          setSelectedModelId(loaded[0].model_id);
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
    if (!selectedModelId) return;
    async function loadCapabilitiesAndDatasets() {
      try {
        const [capRes, dsRes] = await Promise.all([
          api.getModelCapabilities(selectedModelId),
          api.listDatasets(selectedModelId),
        ]);
        setCapabilities(capRes);
        const dsList = dsRes.datasets || [];
        setDatasets(dsList);
        const trajDsList = dsList.filter((d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY");
        if (trajDsList.length > 0) {
          setSelectedDatasetId(trajDsList[0].dataset_id);
          setSelectedTrajectoryId(trajDsList[0].dataset_id);
        } else {
          setSelectedDatasetId("");
          setSelectedTrajectoryId("");
        }

      } catch (err: any) {
        setPredictionError(err.message || "Failed to load capabilities or datasets.");
      }
    }
    loadCapabilitiesAndDatasets();
  }, [selectedModelId]);

  const handleRunPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedDatasetId) {
      setPredictionError("Please select both a model and an evaluation dataset.");
      return;
    }

    setExecuting(true);
    setPredictionError(null);
    try {
      const res = await api.runFailurePrediction({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
      });
      setPredictionResult(res);
      toast.success("Prediction Executed", `Mean probability: ${res.mean_predicted_probability != null ? (res.mean_predicted_probability * 100).toFixed(1) : 0}%`);
    } catch (err: any) {
      setPredictionError(err.message || "Failure prediction execution failed.");
      toast.error("Prediction Failed", err.message || "Execution failed.");
    } finally {
      setExecuting(false);
    }
  };

  if (loading) return <LoadingState message="Checking Failure Prediction readiness..." />;

  const predCap = capabilities?.capabilities?.failure_prediction;
  const trajectoryDatasets = datasets.filter((d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY");

  return (
    <div className="space-y-8">
      <PageHeader
        title="Failure Prediction Engine"
        description="Predict future failure onset probabilities across operational degradation trajectories using temporal reliability features."
        icon={<FileCheck className="w-6 h-6 text-indigo-400" />}
        breadcrumbs={[{ label: "Intelligence" }, { label: "Failure Prediction" }]}
      />

      {error && <ErrorState message={error} />}

      {/* Model Selector Card */}
      {models.length > 0 && (
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono shadow-md">
          <div className="flex items-center space-x-3">
            <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="font-semibold text-slate-200">Active Model:</span>
            <select
              value={selectedModelId}
              onChange={(e) => {
                setSelectedModelId(e.target.value);
                setPredictionResult(null);
                setPredictionError(null);
                setFitSuccess(null);
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500 text-xs"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name}
                </option>
              ))}
            </select>
          </div>
          {selectedModelId && <CopyButton text={selectedModelId} label="Copy Model ID" />}
        </div>
      )}

      {/* Capability State Safeguard */}
      {predCap?.status !== "READY" ? (
        <div className="space-y-4">
          <div className="p-6 bg-slate-900/90 border border-slate-800/80 rounded-2xl space-y-4 shadow-xl">
            <div className="flex items-center space-x-3 text-amber-400 font-bold text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>Failure Prediction Requires Setup</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Failure Prediction fits a model to estimate failure onset probability over temporal degradation trajectories.
              Ordinary <code className="text-amber-300 font-mono">REFERENCE</code> or <code className="text-amber-300 font-mono">EVALUATION</code> raw feature datasets cannot be used for predictor setup.
              Select an uploaded <code className="text-emerald-400 font-mono">TEMPORAL_TRAJECTORY</code> dataset containing temporal reliability features and ground-truth failure labels to fit the predictor.
            </p>
            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 font-mono flex items-center justify-between">
              <span>Status: {predCap?.status || "NOT_AVAILABLE"}</span>
              <span className="text-indigo-400">Horizon Unit: controlled_degradation_states</span>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300">
                Select Labeled Temporal Trajectory Dataset (*Required)
              </label>
              <select
                value={selectedTrajectoryId}
                onChange={(e) => setSelectedTrajectoryId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              >
                <option value="">-- Choose TEMPORAL_TRAJECTORY Dataset --</option>
                {trajectoryDatasets.map((ds) => (
                  <option key={ds.dataset_id} value={ds.dataset_id}>
                    {ds.filename} ({ds.num_samples} samples, {ds.dataset_type})
                  </option>
                ))}
              </select>

              {trajectoryDatasets.length === 0 && (
                <p className="text-[11px] text-amber-400/90 italic font-mono">
                  No TEMPORAL_TRAJECTORY datasets found. Upload a temporal trajectory CSV on the Data page to proceed.
                </p>
              )}
            </div>

            {predictionError && <ErrorState message={predictionError} />}
            {fitSuccess && (
              <div className="p-3 bg-emerald-950/80 border border-emerald-800 rounded-lg text-emerald-300 text-xs font-semibold font-mono">
                {fitSuccess}
              </div>
            )}

            <button
              onClick={handleFitPrediction}
              disabled={fitting || !selectedModelId || !selectedTrajectoryId}
              className="w-full md:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold text-xs shadow-md transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{fitting ? "Fitting Predictor Engine..." : "Setup Failure Prediction"}</span>
            </button>
          </div>

          <EmptyState
            title="Prediction Artifact Not Fitted"
            description="Select an uploaded TEMPORAL_TRAJECTORY dataset above and click 'Setup Failure Prediction' to fit the engine."
            icon={<FileCheck className="w-8 h-8" />}
          />
        </div>
      ) : (
        <div className="space-y-6">
          <SectionCard title="Execute Failure Prediction" subtitle="Predict onset probability across evaluation dataset">
            {predictionError && <ErrorState message={predictionError} />}

            <form onSubmit={handleRunPrediction} className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs items-end">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Temporal Trajectory Dataset *</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  <option value="">-- Choose TEMPORAL_TRAJECTORY Dataset --</option>
                  {trajectoryDatasets.map((d) => (
                    <option key={d.dataset_id} value={d.dataset_id}>
                      {d.filename}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <button
                  type="submit"
                  disabled={executing || !selectedDatasetId}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow-md transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{executing ? "Running Prediction..." : "Execute Failure Prediction"}</span>
                </button>
              </div>
            </form>
          </SectionCard>

          {executing && <LoadingState message="Executing onset-aware failure prediction..." />}

          {predictionResult && (
            <SectionCard
              title="Prediction Result Payload"
              subtitle={`Prediction ID: ${predictionResult.prediction_id}`}
              action={<CopyButton text={predictionResult.prediction_id} label="Copy Prediction ID" />}
            >
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Status</div>
                  <div className="mt-1">
                    <StatusBadge status={predictionResult.status} />
                  </div>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Horizon Steps</div>
                  <div className="text-xl font-bold text-slate-100 mt-1 font-sans">
                    {predictionResult.horizon_steps} <span className="text-xs text-indigo-400 font-mono">({predictionResult.horizon_unit})</span>
                  </div>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Mean Predicted Probability</div>
                  <div className="text-xl font-bold text-indigo-400 mt-1 font-sans">
                    {predictionResult.mean_predicted_probability != null
                      ? `${(predictionResult.mean_predicted_probability * 100).toFixed(1)}%`
                      : "N/A"}
                  </div>
                </div>
              </div>
            </SectionCard>
          )}
        </div>
      )}
    </div>
  );
}

