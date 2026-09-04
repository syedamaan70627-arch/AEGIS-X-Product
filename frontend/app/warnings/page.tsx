"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DatasetRecord, ModelCapabilitiesResponse, ModelRecord, WarningEvaluationResponse, WarningResponse } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { Activity, AlertCircle, Clock, Layers, Play, ShieldAlert } from "lucide-react";

export default function EarlyWarningPage() {
  const toast = useToast();
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
      toast.success("Early Warning Setup Complete", "Engine fitted and capability updated to READY.");
      const updatedCap = await api.getModelCapabilities(selectedModelId);
      setCapabilities(updatedCap);
    } catch (err: any) {
      setWarningError(err.message || "Failed to fit early warning engine.");
      toast.error("Setup Failed", err.message || "Could not fit early warning engine.");
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
      toast.success("Warning Query Complete", res.is_warning_triggered ? "WARNING TRIGGERED" : "Normal Operational State");
    } catch (err: any) {
      setWarningError(err.message || "Early warning query execution failed.");
      toast.error("Query Error", err.message || "Execution failed.");
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
      toast.success("Trajectory Evaluation Complete", `Coverage: ${res.trajectory_level_metrics.early_warning_coverage != null ? (res.trajectory_level_metrics.early_warning_coverage * 100).toFixed(1) : 0}%`);
    } catch (err: any) {
      setWarningError(err.message || "Trajectory evaluation failed.");
      toast.error("Evaluation Failed", err.message || "Execution failed.");
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) return <LoadingState message="Checking Early Warning engine readiness..." />;

  const warnCap = capabilities?.capabilities?.early_warning;
  const trajectoryDatasets = datasets.filter((d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY");

  return (
    <div className="space-y-8">
      <PageHeader
        title="Early Warning System"
        description="Multi-signal temporal warning status and lead-time evaluation across controlled degradation trajectories."
        icon={<Activity className="w-6 h-6 text-amber-400" />}
        breadcrumbs={[{ label: "Intelligence" }, { label: "Early Warning" }]}
      />

      {error && <ErrorState message={error} />}

      {/* Model Selector Card */}
      {models.length > 0 && (
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-sans shadow-sm">
          <div className="flex items-center space-x-3">
            <Layers className="w-4 h-4 text-[#3B82F6] shrink-0" />
            <span className="font-semibold text-[#F3F4F6]">Active Model:</span>
            <select
              value={selectedModelId}
              onChange={(e) => {
                setSelectedModelId(e.target.value);
                setEvalResult(null);
                setWarningError(null);
                setFitSuccess(null);
              }}
              className="bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-1.5 text-[#F3F4F6] font-mono focus:outline-none focus:border-[#3B82F6] text-xs"
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

      <div className="p-4 bg-[#151B23] border border-[#26303D] rounded-xl text-xs text-[#9CA3AF] flex items-start space-x-3 shadow-sm font-sans">
        <Clock className="w-4 h-4 text-[#3B82F6] shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-sans font-bold text-[#F3F4F6] uppercase tracking-wider block mb-0.5 text-[11px]">Horizon Unit Standard</span>
          Warning lead horizons are strictly measured in <strong className="text-[#F59E0B] font-mono">controlled_degradation_states</strong>. They reflect controlled degradation trajectory steps and must not be translated into wall-clock time (hours/minutes/days).
        </div>
      </div>

      {warnCap?.status !== "READY" ? (
        <div className="space-y-4 font-sans">
          <div className="p-6 bg-[#151B23] border border-[#26303D] rounded-xl space-y-4 shadow-sm">
            <div className="flex items-center space-x-3 text-[#F59E0B] font-bold text-sm font-sans">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>Early Warning Requires Setup</span>
            </div>
            <p className="text-xs text-[#9CA3AF] leading-relaxed font-sans">
              Early Warning fits multi-signal thresholds over temporal degradation trajectories.
              Ordinary <code className="text-[#F59E0B] font-mono">REFERENCE</code> or <code className="text-[#F59E0B] font-mono">EVALUATION</code> raw feature datasets cannot be used for warning setup.
              Select an uploaded <code className="text-[#22C55E] font-mono">TEMPORAL_TRAJECTORY</code> dataset containing temporal reliability features and ground-truth failure labels to fit the warning engine.
            </p>
            <div className="p-3 bg-[#0F141B] rounded-xl border border-[#26303D] text-[11px] text-[#9CA3AF] font-mono flex items-center justify-between">
              <span>Status: {warnCap?.status || "NOT_AVAILABLE"}</span>
              <span className="text-[#3B82F6]">Horizon Unit: controlled_degradation_states</span>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-[#F3F4F6] font-sans">
                Select Labeled Temporal Trajectory Dataset (*Required)
              </label>
              <select
                value={selectedTrajectoryId}
                onChange={(e) => setSelectedTrajectoryId(e.target.value)}
                className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-xs text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono"
              >
                <option value="">-- Choose TEMPORAL_TRAJECTORY Dataset --</option>
                {trajectoryDatasets.map((ds) => (
                  <option key={ds.dataset_id} value={ds.dataset_id}>
                    {ds.filename} ({ds.num_samples} samples, {ds.dataset_type})
                  </option>
                ))}
              </select>

              {trajectoryDatasets.length === 0 && (
                <p className="text-[11px] text-[#F59E0B]/90 italic font-mono">
                  No TEMPORAL_TRAJECTORY datasets found. Upload a temporal trajectory CSV on the Data page to proceed.
                </p>
              )}
            </div>

            {warningError && <ErrorState message={warningError} />}
            {fitSuccess && (
              <div className="p-3 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-lg text-[#22C55E] text-xs font-semibold font-mono">
                {fitSuccess}
              </div>
            )}

            <button
              onClick={handleFitWarning}
              disabled={fitting || !selectedModelId || !selectedTrajectoryId}
              className="w-full md:w-auto px-6 py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg font-semibold text-xs shadow-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
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

        <div className="space-y-6 font-sans">
          <SectionCard title="Query Early Warning Status" subtitle="Query multi-signal temporal warning state">
            {warningError && <ErrorState message={warningError} />}

            <form onSubmit={handleQueryWarning} className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-sans items-end">
              <div>
                <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Temporal Trajectory Dataset *</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono"
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
                  className="flex-1 py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg font-semibold shadow-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{querying ? "Querying..." : "Query Early Warning"}</span>
                </button>

                <button
                  type="button"
                  onClick={handleEvaluateTrajectories}
                  disabled={evaluating || !selectedDatasetId}
                  className="flex-1 py-2.5 bg-[#1A222C] hover:bg-[#26303D] text-[#F3F4F6] rounded-lg font-semibold border border-[#26303D] transition-all disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
                >
                  {evaluating ? "Evaluating..." : "Evaluate Lead Trajectories"}
                </button>
              </div>
            </form>
          </SectionCard>

          {querying && <LoadingState message="Evaluating multi-signal temporal early warning state..." />}

          {warningResult && (
            <SectionCard
              title="Early Warning Query Response"
              subtitle={`Warning ID: ${warningResult.warning_id}`}
              action={<CopyButton text={warningResult.warning_id} label="Copy Warning ID" />}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Triggered Status</div>
                  <div className="mt-1">
                    <StatusBadge status={warningResult.is_warning_triggered ? "WARNING_TRIGGERED" : "NORMAL"} />
                  </div>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Warning Score</div>
                  <div className="text-xl font-bold text-amber-400 mt-1 font-sans">
                    {warningResult.warning_score != null ? warningResult.warning_score.toFixed(4) : "N/A"}
                  </div>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Threshold</div>
                  <div className="text-xl font-bold text-slate-200 mt-1 font-sans">{warningResult.threshold}</div>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Target Horizon</div>
                  <div className="text-sm font-bold text-slate-100 mt-1">
                    {warningResult.horizon_value} <span className="text-xs text-[#3B82F6]">{warningResult.horizon_unit}</span>
                  </div>
                </div>
              </div>
            </SectionCard>
          )}

          {evalResult && (
            <SectionCard title="Retrospective Trajectory Evaluation Results" subtitle="Evaluated lead times and false warning rates">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Failing Trajectories</div>
                  <div className="text-lg font-bold text-slate-100 mt-1 font-sans">
                    {evalResult.trajectory_level_metrics.failing_trajectories ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Warned Failing</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1 font-sans">
                    {evalResult.trajectory_level_metrics.warned_failing_trajectories ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Early Warning Coverage</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1 font-sans">
                    {evalResult.trajectory_level_metrics.early_warning_coverage != null
                      ? `${(evalResult.trajectory_level_metrics.early_warning_coverage * 100).toFixed(1)}%`
                      : "0.0%"}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">False Warning Rate</div>
                  <div className="text-lg font-bold text-amber-400 mt-1 font-sans">
                    {evalResult.trajectory_level_metrics.false_trajectory_warning_rate != null
                      ? `${(evalResult.trajectory_level_metrics.false_trajectory_warning_rate * 100).toFixed(1)}%`
                      : "0.0%"}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Mean Lead</div>
                  <div className="text-base font-bold text-amber-300 mt-1">
                    {evalResult.trajectory_level_metrics.mean_lead_steps != null
                      ? `${evalResult.trajectory_level_metrics.mean_lead_steps.toFixed(1)} controlled_degradation_states`
                      : "N/A"}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Median Lead</div>
                  <div className="text-base font-bold text-amber-300 mt-1">
                    {evalResult.trajectory_level_metrics.median_lead_steps != null
                      ? `${evalResult.trajectory_level_metrics.median_lead_steps.toFixed(1)} controlled_degradation_states`
                      : "N/A"}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">Non-Failing Trajectories</div>
                  <div className="text-lg font-bold text-slate-300 mt-1 font-sans">
                    {evalResult.trajectory_level_metrics.non_failing_trajectories ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 shadow-md">
                  <div className="text-slate-400 uppercase font-semibold text-[11px]">False Warnings</div>
                  <div className="text-lg font-bold text-rose-400 mt-1 font-sans">
                    {evalResult.trajectory_level_metrics.false_trajectory_warnings ?? 0}
                  </div>
                </div>
              </div>

              {evalResult.trajectory_results && evalResult.trajectory_results.length > 0 && (
                <div className="mt-6 border-t border-slate-800/80 pt-4">
                  <h4 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider mb-3">Trajectory Lead-Time Breakdown</h4>
                  <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-950/40">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase tracking-wider text-[11px] border-b border-slate-800">
                        <tr>
                          <th className="py-3 px-3.5">Trajectory ID</th>
                          <th className="py-3 px-3.5">Eventually Fails</th>
                          <th className="py-3 px-3.5">First Warning Index</th>
                          <th className="py-3 px-3.5">Failure Index</th>
                          <th className="py-3 px-3.5">Lead Steps</th>
                          <th className="py-3 px-3.5">Early Warning</th>
                          <th className="py-3 px-3.5">False Warning</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono">
                        {evalResult.trajectory_results.map((tr, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                            <td className="py-3 px-3.5 font-bold text-slate-200">{tr.trajectory_id ?? "-"}</td>
                            <td className="py-3 px-3.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tr.eventually_fails ? "bg-rose-950/80 text-rose-300 border border-rose-800/80" : "bg-emerald-950/80 text-emerald-300 border border-emerald-800/80"}`}>
                                {tr.eventually_fails ? "Yes" : "No"}
                              </span>
                            </td>
                            <td className="py-3 px-3.5 text-slate-300">{tr.first_warning_state_index != null ? tr.first_warning_state_index : "-"}</td>
                            <td className="py-3 px-3.5 text-slate-300">{tr.failure_state_index != null ? tr.failure_state_index : "-"}</td>
                            <td className="py-3 px-3.5 text-amber-300 font-bold">{tr.lead_steps != null ? `${tr.lead_steps} controlled_degradation_states` : "-"}</td>
                            <td className="py-3 px-3.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tr.is_early_warning ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800/80" : "bg-slate-900 text-slate-500 border border-slate-800"}`}>
                                {tr.is_early_warning ? "Yes" : "No"}
                              </span>
                            </td>
                            <td className="py-3 px-3.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tr.is_false_trajectory_warning ? "bg-rose-950/80 text-rose-300 border border-rose-800/80" : "bg-slate-900 text-slate-500 border border-slate-800"}`}>
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

