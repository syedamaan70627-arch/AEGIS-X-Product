"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { AnalysisSummary, ModelRecord, ReadinessResponse, SystemStatus } from "@/types/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Database,
  Layers,
  LineChart,
  ShieldCheck,
} from "lucide-react";

export default function DashboardOverview() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisSummary[]>([]);

  useEffect(() => {
    async function loadOverviewData() {
      setLoading(true);
      setError(null);
      try {
        const [modelsRes, statusRes, readinessRes] = await Promise.all([
          api.listModels().catch(() => ({ total: 0, models: [] })),
          api.getStatus().catch(() => null),
          api.getReadiness().catch(() => null),
        ]);

        setModels(modelsRes.models || []);
        if (statusRes) setStatus(statusRes);
        if (readinessRes) setReadiness(readinessRes);

        if (modelsRes.models && modelsRes.models.length > 0) {
          const activeId = modelsRes.models[0].model_id;
          const analysesRes = await api.listModelAnalyses(activeId).catch(() => ({ total: 0, analyses: [] }));
          setRecentAnalyses(analysesRes.analyses || []);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard telemetry.");
      } finally {
        setLoading(false);
      }
    }
    loadOverviewData();
  }, []);

  if (loading) return <LoadingState message="Connecting to AEGIS-X operational engine..." />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  const activeModel = models.length > 0 ? models[0] : null;
  const latestAnalysis = recentAnalyses.length > 0 ? recentAnalyses[0] : null;

  return (
    <div className="space-y-8">
      <PageHeader
        title="AI Reliability Command Center"
        description="Unified operational observability dashboard for machine learning classification models."
        badge={<StatusBadge status={readiness?.status || "HEALTHY"} />}
        actions={
          <Link
            href="/models"
            className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-md transition-colors"
          >
            Manage Models <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Link>
        }
      />

      {/* Telemetry Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Registered Models"
          value={models.length}
          subtitle={activeModel ? `Active: ${activeModel.model_name}` : "No models registered"}
          icon={<Layers className="w-5 h-5" />}
          statusColor={models.length > 0 ? "emerald" : "amber"}
        />
        <MetricCard
          title="Engine Status"
          value={status?.api_status === "operational" ? "Operational" : "Degraded"}
          subtitle={`Backend: ${status?.database_backend || "sqlite"} / ${status?.storage_backend || "local"}`}
          icon={<ShieldCheck className="w-5 h-5" />}
          statusColor={status?.api_status === "operational" ? "emerald" : "amber"}
        />
        <MetricCard
          title="Recent Analyses"
          value={recentAnalyses.length}
          subtitle={latestAnalysis ? `Latest: ${new Date(latestAnalysis.created_at).toLocaleTimeString()}` : "No analyses run yet"}
          icon={<Activity className="w-5 h-5" />}
          statusColor="indigo"
        />
        <MetricCard
          title="High-Risk Events"
          value={latestAnalysis?.aggregate_fused_risk && latestAnalysis.aggregate_fused_risk >= 0.7 ? "Detected" : "0 Warning(s)"}
          subtitle="Pre-label operational risk"
          icon={<AlertTriangle className="w-5 h-5" />}
          statusColor={latestAnalysis?.aggregate_fused_risk && latestAnalysis.aggregate_fused_risk >= 0.7 ? "rose" : "slate"}
        />
      </div>

      {/* Active Model Signal Summary */}
      {models.length === 0 ? (
        <EmptyState
          title="No Models Registered"
          description="Register your first scikit-learn classification model (.joblib or .pkl) to start AEGIS-X operational reliability monitoring."
          actionText="Register Model"
          actionHref="/models"
          icon={<Layers className="w-8 h-8" />}
        />
      ) : (
        <div className="space-y-6">
          <SectionCard
            title="Reliability Signal Summary"
            subtitle={`Active Model: ${activeModel?.model_name} (${activeModel?.model_id})`}
            action={
              <Link
                href="/monitor"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center"
              >
                Run New Analysis <ArrowRight className="w-3 h-3 ml-1" />
              </Link>
            }
          >
            {latestAnalysis ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <RiskIndicator label="OOD Risk" value={latestAnalysis.aggregate_ood_risk} />
                <RiskIndicator label="Uncertainty Risk" value={latestAnalysis.aggregate_uncertainty} />
                <RiskIndicator label="Drift Risk" value={latestAnalysis.aggregate_drift_score} />
                <RiskIndicator label="Fused Risk Score" value={latestAnalysis.aggregate_fused_risk} />
              </div>
            ) : (
              <EmptyState
                title="No Reliability Analyses Run"
                description="Upload reference baseline data and evaluation CSV to generate operational OOD, Uncertainty, Drift, and Fusion risk signals."
                actionText="Go to Batch Monitor"
                actionHref="/monitor"
                icon={<LineChart className="w-8 h-8" />}
              />
            )}
          </SectionCard>

          {/* Recent Executions Table */}
          {recentAnalyses.length > 0 && (
            <SectionCard title="Recent Execution History" subtitle="Historical operational analysis runs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-3">Analysis ID</th>
                      <th className="p-3">Fusion Method</th>
                      <th className="p-3">Fused Risk</th>
                      <th className="p-3">True Target Labels</th>
                      <th className="p-3">Executed At</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {recentAnalyses.map((a) => (
                      <tr key={a.analysis_id} className="hover:bg-slate-800/40">
                        <td className="p-3 font-mono text-slate-300">{a.analysis_id.slice(0, 8)}...</td>
                        <td className="p-3 font-medium text-slate-200 capitalize">{a.fusion_method}</td>
                        <td className="p-3 font-mono font-semibold">
                          <span
                            className={
                              (a.aggregate_fused_risk || 0) >= 0.7
                                ? "text-rose-400"
                                : (a.aggregate_fused_risk || 0) >= 0.35
                                ? "text-amber-400"
                                : "text-emerald-400"
                            }
                          >
                            {((a.aggregate_fused_risk || 0) * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="p-3">
                          {a.has_labels ? (
                            <span className="text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60">
                              Present
                            </span>
                          ) : (
                            <span className="text-slate-400 font-mono">Absent (Label-Free)</span>
                          )}
                        </td>
                        <td className="p-3 text-slate-400">{new Date(a.created_at).toLocaleString()}</td>
                        <td className="p-3 text-right">
                          <Link
                            href="/reliability"
                            className="text-indigo-400 hover:text-indigo-300 font-medium"
                          >
                            Inspect Signals →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          )}
        </div>
      )}
    </div>
  );
}
