"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisSummary, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Info, Layers, LineChart, ShieldCheck } from "lucide-react";

export default function ReliabilityPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>("");

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
    async function loadAnalyses() {
      if (!selectedModelId) return;
      try {
        const res = await api.listModelAnalyses(selectedModelId);
        const loadedAnalyses = res.analyses || [];
        setAnalyses(loadedAnalyses);
        if (loadedAnalyses.length > 0) {
          setSelectedAnalysisId(loadedAnalyses[0].analysis_id);
        } else {
          setSelectedAnalysisId("");
        }
      } catch (_) {}
    }
    loadAnalyses();
  }, [selectedModelId]);

  if (loading) return <LoadingState message="Loading reliability signal history..." />;
  if (error) return <ErrorState message={error} />;

  const activeAnalysis = analyses.find((a) => a.analysis_id === selectedAnalysisId) || (analyses.length > 0 ? analyses[0] : null);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reliability Signal Breakdown"
        description="Inspect operational Out-of-Distribution, Uncertainty, Feature Drift, and Fused Risk detectors."
        icon={<LineChart className="w-6 h-6 text-cyan-400" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Reliability" }]}
      />

      {/* Model & Analysis Selector Bar */}
      {models.length > 0 && (
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md">
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="font-semibold text-slate-200">Model:</span>
              <select
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs"
              >
                {models.map((m) => (
                  <option key={m.model_id} value={m.model_id}>
                    {m.model_name}
                  </option>
                ))}
              </select>
            </div>

            {analyses.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-200">Analysis Run:</span>
                <select
                  value={selectedAnalysisId}
                  onChange={(e) => setSelectedAnalysisId(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs"
                >
                  {analyses.map((a) => (
                    <option key={a.analysis_id} value={a.analysis_id}>
                      {a.analysis_id.slice(0, 8)}... ({new Date(a.created_at).toLocaleTimeString()})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {activeAnalysis && (
            <div className="flex items-center space-x-2 text-xs font-mono">
              <CopyButton text={activeAnalysis.analysis_id} label="Copy Analysis ID" />
              <StatusBadge status={activeAnalysis.has_labels ? "LABEL_VERIFIED" : "LABEL_FREE"} />
            </div>
          )}
        </div>
      )}

      {/* Scientific Scope Disclosure */}
      <div className="p-4 bg-slate-900/80 border border-slate-800/80 rounded-xl flex items-start space-x-3 text-xs text-slate-300 shadow-md">
        <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-mono font-bold text-slate-100 uppercase tracking-wider block mb-0.5 text-[11px]">
            Scientific Scope Notice
          </span>
          Individual reliability signals (OOD, Uncertainty, Drift) remain independently inspectable because their operational usefulness varies by deployment environment. Pre-label fusion does not require true target labels.
        </div>
      </div>

      {!activeAnalysis ? (
        <EmptyState
          title="No Reliability Telemetry Available"
          description="Execute an operational analysis run in the Batch Monitor to inspect OOD, Uncertainty, Drift, and Fusion risk signals."
          actionText="Go to Batch Monitor"
          actionHref="/monitor"
          icon={<LineChart className="w-8 h-8" />}
        />
      ) : (
        <div className="space-y-6">
          <SectionCard
            title="Individual Reliability Signals"
            subtitle={`Analysis Run: ${activeAnalysis.analysis_id} | Fusion Method: ${activeAnalysis.fusion_method}`}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <RiskIndicator label="OOD Risk" value={activeAnalysis.aggregate_ood_risk} />
              <RiskIndicator label="Uncertainty Risk" value={activeAnalysis.aggregate_uncertainty} />
              <RiskIndicator label="Drift Score" value={activeAnalysis.aggregate_drift_score} />
              <RiskIndicator label="Fused Risk Score" value={activeAnalysis.aggregate_fused_risk} />
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}

