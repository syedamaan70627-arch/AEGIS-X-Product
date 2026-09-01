"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DatasetRecord, ModelCapabilitiesResponse, ModelRecord, WarningEvaluationResponse, WarningResponse } from "@/types/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Activity, AlertCircle, Clock, Layers, Play, ShieldAlert } from "lucide-react";

export default function EarlyWarningPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [capabilities, setCapabilities] = useState<ModelCapabilitiesResponse | null>(null);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");

  const [querying, setQuerying] = useState(false);
  const [warningResult, setWarningResult] = useState<WarningResponse | null>(null);
  const [warningError, setWarningError] = useState<string | null>(null);

  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<WarningEvaluationResponse | null>(null);
  const [selectedTrajectoryId, setSelectedTrajectoryId] = useState<string>("");
  const [fitting, setFitting] = useState(false);
  const [fitSuccess, setFitSuccess] = useState<string | null>(null);

  const handleFitWarning = async () => {
    if (!selectedModelId || !selectedTrajectoryId) return;
    setFitting(true);
    setWarningError(null);
    setFitSuccess(null);
    try {
      await api.fitEarlyWarning(selectedModelId, { trajectory_dataset_id: selectedTrajectoryId });
      setFitSuccess("Early Warning engine fitted successfully! Capability updated to READY.");
      const updatedCap = await api.getModelCapabilities(selectedModelId);
      setCapabilities(updatedCap);
    } catch (err: any) {
      setWarningError(err.message || "Failed to fit early warning engine.");
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
        setWarningError(err.message || "Failed to load capabilities or datasets.");
      }
    }
    loadCapabilitiesAndDatasets();
  }, [selectedModelId]);

  const handleQueryWarning = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedDatasetId) {
      setWarningError("Please select both a model and an evaluation dataset.");
      return;
    }

    setQuerying(true);
    setWarningError(null);
    try {
      const res = await api.queryEarlyWarning({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
      });
      setWarningResult(res);
    } catch (err: any) {
      setWarningError(err.message || "Early warning query execution failed.");
    } finally {
      setQuerying(false);
    }
  };

  const handleEvaluateTrajectories = async () => {
    if (!selectedModelId || !selectedDatasetId) return;
    setEvaluating(true);
    try {
      const res = await api.evaluateEarlyWarning({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
      });
      setEvalResult(res);
    } catch (err: any) {
      setWarningError(err.message || "Trajectory evaluation failed.");
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) return <LoadingState message="Checking Early Warning engine readiness..." />;

  const warnCap = capabilities?.capabilities?.early_warning;
  const trajectoryDatasets = datasets.filter((d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center space-x-3">
          <Activity className="w-7 h-7 text-indigo-400" />
          <span>Early Warning System</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Multi-signal temporal warning status and lead-time evaluation across controlled degradation trajectories.
        </p>
      </div>

      {error && <ErrorState message={error} />}

      {/* Model Selector Card */}
      {models.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3 text-xs">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-slate-200">Active Model:</span>
            <select
              value={selectedModelId}
              onChange={(e) => {
                setSelectedModelId(e.target.value);
                setEvalResult(null);
                setWarningError(null);
                setFitSuccess(null);
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 flex items-start space-x-3">
        <Clock className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-100 block mb-0.5">Horizon Unit Standard</span>
          Warning lead horizons are strictly measured in <strong>controlled_degradation_states</strong>. They reflect controlled degradation trajectory steps and must not be translated into wall-clock time (hours/minutes/days).
        </div>
      </div>

      {warnCap?.status !== "READY" ? (
        <div className="space-y-4">
          <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center space-x-3 text-amber-400 font-bold text-sm">
              <AlertCircle className="w-5 h-5" />
              <span>Early Warning Requires Setup</span>
            </div>
            <p className="text-xs text-slate-300">
              Early Warning fits multi-signal thresholds over temporal degradation trajectories.
              Ordinary <code className="text-amber-300">REFERENCE</code> or <code className="text-amber-300">EVALUATION</code> raw feature datasets cannot be used for warning setup.
              Select an uploaded <code className="text-emerald-400">TEMPORAL_TRAJECTORY</code> dataset containing temporal reliability features and ground-truth failure labels to fit the warning engine.
            </p>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 font-mono">
              Status: {warnCap?.status || "NOT_AVAILABLE"} | Horizon Unit: controlled_degradation_states
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300">
                Select Labeled Temporal Trajectory Dataset (*Required)
              </label>
              <select
                value={selectedTrajectoryId}
                onChange={(e) => setSelectedTrajectoryId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">-- Choose TEMPORAL_TRAJECTORY Dataset --</option>
                {trajectoryDatasets.map((ds) => (
                  <option key={ds.dataset_id} value={ds.dataset_id}>
                    {ds.filename} ({ds.num_samples} samples, {ds.dataset_type})
                  </option>
                ))}
              </select>

              {trajectoryDatasets.length === 0 && (
                <p className="text-[11px] text-amber-400/90 italic">
                  No TEMPORAL_TRAJECTORY datasets found. Upload a temporal trajectory CSV on the Data page to proceed.
                </p>
              )}
            </div>

            {warningError && <ErrorState message={warningError} />}
            {fitSuccess && (
              <div className="p-3 bg-emerald-950/80 border border-emerald-800 rounded-lg text-emerald-300 text-xs font-semibold">
                {fitSuccess}
              </div>
            )}

            <button
              onClick={handleFitWarning}
              disabled={fitting || !selectedModelId || !selectedTrajectoryId}
              className="w-full md:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold text-xs shadow-md transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{fitting ? "Fitting Warning Engine..." : "Setup Early Warning"}</span>
            </button>
          </div>

          <EmptyState
            title="Warning Engine Not Fitted"
            description="Select an uploaded TEMPORAL_TRAJECTORY dataset above and click 'Setup Early Warning' to fit the warning engine."
            icon={<Activity className="w-8 h-8" />}
          />
        </div>
      ) : (

        <div className="space-y-6">
          <SectionCard title="Query Early Warning Status" subtitle="Query multi-signal temporal warning state">
            {warningError && <ErrorState message={warningError} />}

            <form onSubmit={handleQueryWarning} className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs items-end">
              <div>
                <label className="block font-medium text-slate-300 mb-1">Temporal Trajectory Dataset *</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">-- Choose TEMPORAL_TRAJECTORY Dataset --</option>
                  {trajectoryDatasets.map((d) => (
                    <option key={d.dataset_id} value={d.dataset_id}>
                      {d.filename}
                    </option>
                  ))}
                </select>

              </div>

              <div className="md:col-span-2 flex space-x-3">
                <button
                  type="submit"
                  disabled={querying || !selectedDatasetId}
                  className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow-md transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{querying ? "Querying..." : "Query Early Warning"}</span>
                </button>

                <button
                  type="button"
                  onClick={handleEvaluateTrajectories}
                  disabled={evaluating || !selectedDatasetId}
                  className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-semibold border border-slate-700 transition-colors disabled:opacity-50"
                >
                  {evaluating ? "Evaluating..." : "Evaluate Lead Trajectories"}
                </button>
              </div>
            </form>
          </SectionCard>

          {querying && <LoadingState message="Evaluating multi-signal temporal early warning state..." />}

          {warningResult && (
            <SectionCard title="Early Warning Query Response" subtitle={`Warning ID: ${warningResult.warning_id}`}>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono uppercase">Triggered Status</div>
                  <div className="mt-1">
                    <StatusBadge status={warningResult.is_warning_triggered ? "WARNING_TRIGGERED" : "NORMAL"} />
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono uppercase">Warning Score</div>
                  <div className="text-xl font-bold text-amber-400 mt-1">
                    {warningResult.warning_score != null ? warningResult.warning_score.toFixed(4) : "N/A"}
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono uppercase">Threshold</div>
                  <div className="text-xl font-bold text-slate-200 mt-1">{warningResult.threshold}</div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-slate-400 font-mono uppercase">Target Horizon</div>
                  <div className="text-sm font-bold text-slate-100 mt-1">
                    {warningResult.horizon_value} {warningResult.horizon_unit}
                  </div>
                </div>
              </div>
            </SectionCard>
          )}

          {evalResult && (
            <SectionCard title="Retrospective Trajectory Evaluation Results" subtitle="Evaluated lead times and false warning rates">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">Failing Trajectories</div>
                  <div className="text-lg font-bold text-slate-100 mt-1">
                    {evalResult.trajectory_level_metrics.failing_trajectories ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">Warned Failing Trajectories</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">
                    {evalResult.trajectory_level_metrics.warned_failing_trajectories ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">Early Warning Coverage</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">
                    {evalResult.trajectory_level_metrics.early_warning_coverage != null
                      ? `${(evalResult.trajectory_level_metrics.early_warning_coverage * 100).toFixed(1)}%`
                      : "0.0%"}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">False Warning Rate</div>
                  <div className="text-lg font-bold text-amber-400 mt-1">
                    {evalResult.trajectory_level_metrics.false_trajectory_warning_rate != null
                      ? `${(evalResult.trajectory_level_metrics.false_trajectory_warning_rate * 100).toFixed(1)}%`
                      : "0.0%"}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">Mean Lead</div>
                  <div className="text-base font-bold text-amber-300 mt-1">
                    {evalResult.trajectory_level_metrics.mean_lead_steps != null
                      ? `${evalResult.trajectory_level_metrics.mean_lead_steps.toFixed(1)} controlled_degradation_states`
                      : "N/A"}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">Median Lead</div>
                  <div className="text-base font-bold text-amber-300 mt-1">
                    {evalResult.trajectory_level_metrics.median_lead_steps != null
                      ? `${evalResult.trajectory_level_metrics.median_lead_steps.toFixed(1)} controlled_degradation_states`
                      : "N/A"}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">Non-Failing Trajectories</div>
                  <div className="text-lg font-bold text-slate-300 mt-1">
                    {evalResult.trajectory_level_metrics.non_failing_trajectories ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-mono">False Trajectory Warnings</div>
                  <div className="text-lg font-bold text-rose-400 mt-1">
                    {evalResult.trajectory_level_metrics.false_trajectory_warnings ?? 0}
                  </div>
                </div>
              </div>

              {evalResult.trajectory_results && evalResult.trajectory_results.length > 0 && (
                <div className="mt-6 border-t border-slate-800 pt-4">
                  <h4 className="text-sm font-semibold text-slate-200 mb-3">Trajectory Lead-Time Breakdown</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 font-mono">
                          <th className="py-2 px-3">Trajectory ID</th>
                          <th className="py-2 px-3">Eventually Fails</th>
                          <th className="py-2 px-3">First Warning Index</th>
                          <th className="py-2 px-3">Failure Index</th>
                          <th className="py-2 px-3">Lead Steps</th>
                          <th className="py-2 px-3">Early Warning</th>
                          <th className="py-2 px-3">False Warning</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {evalResult.trajectory_results.map((tr, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/50">
                            <td className="py-2 px-3 font-mono text-slate-200">{tr.trajectory_id ?? "-"}</td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tr.eventually_fails ? "bg-rose-950 text-rose-300 border border-rose-800" : "bg-emerald-950 text-emerald-300 border border-emerald-800"}`}>
                                {tr.eventually_fails ? "Yes" : "No"}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-slate-300">{tr.first_warning_state_index != null ? tr.first_warning_state_index : "-"}</td>
                            <td className="py-2 px-3 text-slate-300">{tr.failure_state_index != null ? tr.failure_state_index : "-"}</td>
                            <td className="py-2 px-3 text-amber-300 font-medium">{tr.lead_steps != null ? `${tr.lead_steps} controlled_degradation_states` : "-"}</td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tr.is_early_warning ? "bg-emerald-950 text-emerald-300 border border-emerald-800" : "bg-slate-900 text-slate-400 border border-slate-800"}`}>
                                {tr.is_early_warning ? "Yes" : "No"}
                              </span>
                            </td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tr.is_false_trajectory_warning ? "bg-rose-950 text-rose-300 border border-rose-800" : "bg-slate-900 text-slate-400 border border-slate-800"}`}>
                                {tr.is_false_trajectory_warning ? "Yes" : "No"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </SectionCard>
          )}
        </div>
      )}
    </div>
  );
}
