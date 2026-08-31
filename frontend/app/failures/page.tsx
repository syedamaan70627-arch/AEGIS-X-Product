"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { FailureExplorerResponse, FaultTestListResponse, ModelRecord } from "@/types/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AlertCircle, AlertTriangle, CheckCircle2, FileSpreadsheet, Layers, ShieldAlert } from "lucide-react";

export default function FailureExplorerPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [faultTests, setFaultTests] = useState<any[]>([]);
  const [selectedFaultTestId, setSelectedFaultTestId] = useState<string>("");

  const [explorerData, setExplorerData] = useState<FailureExplorerResponse | null>(null);
  const [fetchingExplorer, setFetchingExplorer] = useState(false);

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
    async function loadFaultTests() {
      if (!selectedModelId) return;
      try {
        const res = await api.listModelFaultTests(selectedModelId);
        const runs = res.fault_tests || [];
        setFaultTests(runs);
        if (runs.length > 0) {
          setSelectedFaultTestId(runs[0].fault_test_id);
        } else {
          setSelectedFaultTestId("");
          setExplorerData(null);
        }
      } catch (_) {}
    }
    loadFaultTests();
  }, [selectedModelId]);

  useEffect(() => {
    async function loadExplorer() {
      if (!selectedFaultTestId) return;
      setFetchingExplorer(true);
      try {
        const res = await api.getFailureExplorerData(selectedFaultTestId);
        setExplorerData(res);
      } catch (_) {
        setExplorerData(null);
      } finally {
        setFetchingExplorer(false);
      }
    }
    loadExplorer();
  }, [selectedFaultTestId]);

  if (loading) return <LoadingState message="Initializing Failure Explorer telemetry..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Failure Explorer"
        description="Observation-level failure event analysis, high-risk observation warnings, and silent failure identification."
      />

      {/* Model & Fault Run Selectors */}
      {models.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-3">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-slate-200">Active Model:</span>
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
            <span className="font-semibold text-slate-200">Fault Run ID:</span>
            <select
              value={selectedFaultTestId}
              onChange={(e) => setSelectedFaultTestId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
            >
              {faultTests.length === 0 ? (
                <option value="">No fault test runs available</option>
              ) : (
                faultTests.map((ft) => (
                  <option key={ft.fault_test_id} value={ft.fault_test_id}>
                    {ft.fault_test_id.slice(0, 8)}... ({ft.fault_type} sev={ft.severity})
                  </option>
                ))
              )}
            </select>
          </div>
        </div>
      )}

      {fetchingExplorer && <LoadingState message="Fetching observation-level failure events..." />}

      {!fetchingExplorer && !explorerData ? (
        <EmptyState
          title="No Failure Explorer Data Available"
          description="Run a fault injection test run in the Fault Lab to generate observation-level failure events and silent failure telemetry."
          actionText="Go to Fault Lab"
          actionHref="/faults"
          icon={<FileSpreadsheet className="w-8 h-8" />}
        />
      ) : (
        explorerData && (
          <div className="space-y-6">
            {/* Header Telemetry Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-slate-400 font-mono uppercase">Total Observations</div>
                <div className="text-xl font-bold text-slate-100 mt-1">{explorerData.total_samples}</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-slate-400 font-mono uppercase">
                  {explorerData.is_label_aware ? "Confirmed Failures" : "High-Risk Observations"}
                </div>
                <div className="text-xl font-bold text-amber-400 mt-1">{explorerData.total_warnings}</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-slate-400 font-mono uppercase">Silent Failures</div>
                <div className="text-xl font-bold text-rose-400 mt-1">
                  {explorerData.is_label_aware ? explorerData.silent_failures : "Requires Labels"}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-slate-400 font-mono uppercase">Silent Failure Status</div>
                <div className="mt-1">
                  <StatusBadge status={explorerData.silent_failure_status} />
                </div>
              </div>
            </div>

            {/* Scientific Terminology Safeguard Notice */}
            {!explorerData.is_label_aware && (
              <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-300 flex items-center justify-between">
                <span>
                  Label-Free Mode: Observations exceeding risk thresholds are classified as <strong className="text-amber-400">High-Risk Observations</strong>. True silent failure rate requires ground-truth target labels.
                </span>
                <StatusBadge status="LABEL_FREE" />
              </div>
            )}

            {/* Events Detail Table */}
            <SectionCard
              title={explorerData.is_label_aware ? "Observation-Level Failure Events" : "Reliability Events / High-Risk Observations"}
              subtitle={`Showing first ${Math.min(50, explorerData.failure_events.length)} observation samples`}
            >
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-3">Sample ID</th>
                      <th className="p-3">Fused Risk</th>
                      <th className="p-3">OOD Risk</th>
                      <th className="p-3">Uncertainty</th>
                      <th className="p-3">Drift Risk</th>
                      <th className="p-3">High-Risk Flag</th>
                      {explorerData.is_label_aware && <th className="p-3">Actual Failure</th>}
                      {explorerData.is_label_aware && <th className="p-3">Silent Failure</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {explorerData.failure_events.slice(0, 50).map((ev) => (
                      <tr key={ev.sample_id} className="hover:bg-slate-800/40 font-mono">
                        <td className="p-3 text-slate-300 font-bold">#{ev.sample_id}</td>
                        <td className="p-3 font-bold text-slate-100">{(ev.fused_risk * 100).toFixed(1)}%</td>
                        <td className="p-3 text-slate-400">{(ev.ood_risk * 100).toFixed(1)}%</td>
                        <td className="p-3 text-slate-400">{(ev.uncertainty_risk * 100).toFixed(1)}%</td>
                        <td className="p-3 text-slate-400">{(ev.drift_risk * 100).toFixed(1)}%</td>
                        <td className="p-3">
                          {ev.is_high_risk_warning ? (
                            <span className="text-amber-400 font-semibold px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800/60">
                              HIGH RISK
                            </span>
                          ) : (
                            <span className="text-slate-500">Normal</span>
                          )}
                        </td>
                        {explorerData.is_label_aware && (
                          <td className="p-3">
                            {ev.has_actual_failure ? (
                              <span className="text-rose-400 font-semibold">FAILURE</span>
                            ) : (
                              <span className="text-emerald-400">Correct</span>
                            )}
                          </td>
                        )}
                        {explorerData.is_label_aware && (
                          <td className="p-3">
                            {ev.is_silent_failure ? (
                              <span className="text-rose-400 font-bold px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800">
                                SILENT FAILURE
                              </span>
                            ) : (
                              <span className="text-slate-500">-</span>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          </div>
        )
      )}
    </div>
  );
}
