"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { FailureExplorerResponse, FaultTestListResponse, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
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
        icon={<ShieldAlert className="w-6 h-6 text-rose-400" />}
        breadcrumbs={[{ label: "Intelligence" }, { label: "Failure Explorer" }]}
      />

      {/* Model & Fault Run Selectors */}
      {models.length > 0 && (
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs shadow-md">
          <div className="flex items-center space-x-3 font-mono">
            <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="font-semibold text-slate-200">Active Model:</span>
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

          <div className="flex items-center space-x-3 font-mono">
            <span className="font-semibold text-slate-200">Fault Run ID:</span>
            <select
              value={selectedFaultTestId}
              onChange={(e) => setSelectedFaultTestId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500 text-xs"
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
            {selectedFaultTestId && <CopyButton text={selectedFaultTestId} />}
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
              <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 shadow-md">
                <div className="text-slate-400 uppercase font-semibold text-[11px]">Total Observations</div>
                <div className="text-xl font-bold text-slate-100 mt-1 font-sans">{explorerData.total_samples}</div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 shadow-md">
                <div className="text-slate-400 uppercase font-semibold text-[11px]">
                  {explorerData.is_label_aware ? "Confirmed Failures" : "High-Risk Observations"}
                </div>
                <div className="text-xl font-bold text-amber-400 mt-1 font-sans">{explorerData.total_warnings}</div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 shadow-md">
                <div className="text-slate-400 uppercase font-semibold text-[11px]">Silent Failures</div>
                <div className="text-xl font-bold text-rose-400 mt-1 font-sans">
                  {explorerData.is_label_aware ? explorerData.silent_failures : "Requires Labels"}
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 shadow-md">
                <div className="text-slate-400 uppercase font-semibold text-[11px]">Silent Failure Status</div>
                <div className="mt-1">
                  <StatusBadge status={explorerData.silent_failure_status} />
                </div>
              </div>
            </div>

            {/* Scientific Terminology Safeguard Notice */}
            {!explorerData.is_label_aware && (
              <div className="p-4 bg-slate-900/80 border border-slate-800/80 rounded-xl text-xs text-slate-300 flex items-center justify-between shadow-md">
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
              <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-950/40">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono tracking-wider text-[11px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">Sample ID</th>
                      <th className="p-3.5">Fused Risk</th>
                      <th className="p-3.5">OOD Risk</th>
                      <th className="p-3.5">Uncertainty</th>
                      <th className="p-3.5">Drift Risk</th>
                      <th className="p-3.5">High-Risk Flag</th>
                      {explorerData.is_label_aware && <th className="p-3.5">Actual Failure</th>}
                      {explorerData.is_label_aware && <th className="p-3.5">Silent Failure</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {explorerData.failure_events.slice(0, 50).map((ev) => (
                      <tr key={ev.sample_id} className="hover:bg-slate-800/40 font-mono transition-colors">
                        <td className="p-3.5 text-slate-300 font-bold">#{ev.sample_id}</td>
                        <td className="p-3.5 font-bold text-slate-100 font-sans">{(ev.fused_risk * 100).toFixed(1)}%</td>
                        <td className="p-3.5 text-slate-400 font-sans">{(ev.ood_risk * 100).toFixed(1)}%</td>
                        <td className="p-3.5 text-slate-400 font-sans">{(ev.uncertainty_risk * 100).toFixed(1)}%</td>
                        <td className="p-3.5 text-slate-400 font-sans">{(ev.drift_risk * 100).toFixed(1)}%</td>
                        <td className="p-3.5">
                          {ev.is_high_risk_warning ? (
                            <span className="text-amber-400 font-semibold px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800/60 font-sans">
                              HIGH RISK
                            </span>
                          ) : (
                            <span className="text-slate-500 font-sans">Normal</span>
                          )}
                        </td>
                        {explorerData.is_label_aware && (
                          <td className="p-3.5">
                            {ev.has_actual_failure ? (
                              <span className="text-rose-400 font-semibold font-sans">FAILURE</span>
                            ) : (
                              <span className="text-emerald-400 font-sans">Correct</span>
                            )}
                          </td>
                        )}
                        {explorerData.is_label_aware && (
                          <td className="p-3.5">
                            {ev.is_silent_failure ? (
                              <span className="text-rose-400 font-bold px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800 font-sans">
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

