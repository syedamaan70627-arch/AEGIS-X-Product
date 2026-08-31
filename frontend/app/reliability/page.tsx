"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisSummary, ModelRecord } from "@/types/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import { Info, Layers, LineChart, ShieldCheck } from "lucide-react";

export default function ReliabilityPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);

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
        setAnalyses(res.analyses || []);
      } catch (_) {}
    }
    loadAnalyses();
  }, [selectedModelId]);

  if (loading) return <LoadingState message="Loading reliability signal history..." />;
  if (error) return <ErrorState message={error} />;

  const activeAnalysis = analyses.length > 0 ? analyses[0] : null;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reliability Signal Breakdown"
        description="Inspect operational Out-of-Distribution, Uncertainty, Feature Drift, and Fused Risk detectors."
      />

      {/* Model Selector */}
      {models.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3 text-xs">
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
        </div>
      )}

      {/* Scientific Principle Information Note */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-start space-x-3 text-xs text-slate-300">
        <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-100 block mb-0.5">Scientific Principle</span>
          Individual reliability signals (OOD, Uncertainty, Drift) remain independently inspectable because their usefulness can vary by deployment environment. Pre-label fusion does not require true target labels.
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
            subtitle={`Latest Analysis: ${activeAnalysis.analysis_id.slice(0, 8)}... (${new Date(activeAnalysis.created_at).toLocaleString()})`}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
