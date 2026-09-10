"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalysisSummary, ECRGOperatingMode, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { GovernanceOverviewCard } from "@/components/governance/GovernanceOverviewCard";
import { GovernanceHistoryTimeline } from "@/components/governance/GovernanceHistoryTimeline";
import { useAuth } from "@/components/providers/AuthProvider";
import { Activity, AlertOctagon, CheckCircle2, Info, Layers, ShieldCheck, Zap } from "lucide-react";

export default function GovernancePage() {
  const { loading: authLoading, authenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<ECRGOperatingMode>("EVIDENCE_ONLY");
  const [historyTrigger, setHistoryTrigger] = useState(0);

  useEffect(() => {
    async function loadModels() {
      if (authLoading || !authenticated) return;
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
        setError(err.message || "Failed to load models for governance.");
      } finally {
        setLoading(false);
      }
    }
    loadModels();
  }, [authLoading, authenticated]);

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
      } catch (_) {
        setAnalyses([]);
        setSelectedAnalysisId("");
      }
    }
    loadAnalyses();
  }, [selectedModelId]);

  if (loading) return <LoadingState message="Loading ECRG governance environment..." />;
  if (error) return <ErrorState message={error} />;

  const activeAnalysis = analyses.find((a) => a.analysis_id === selectedAnalysisId) || (analyses.length > 0 ? analyses[0] : null);

  const isModelReady = models.length > 0 && !!selectedModelId;
  const isAnalysisReady = !!activeAnalysis;
  const isEvidenceReady = !!(activeAnalysis && activeAnalysis.aggregate_fused_risk !== undefined);
  const isCalibrationReady = selectedMode === "CALIBRATED_GOVERNANCE";

  return (
    <div className="space-y-8 font-sans">
      <PageHeader
        title="Evidence-Calibrated Reliability Governance (ECRG)"
        description="Formal risk-controlled decision framework, conformal prediction sets, and anti-flapping governance state machine."
        icon={<ShieldCheck className="w-6 h-6 text-[#3B82F6]" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Governance" }]}
      />

      {/* Selector & Mode Configuration Bar */}
      {models.length > 0 && (
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4 shadow-sm font-sans">
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#3B82F6] shrink-0" />
              <span className="font-semibold text-[#F3F4F6]">Model:</span>
              <select
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
                className="bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-1.5 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] text-xs font-mono"
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
                <span className="font-semibold text-[#F3F4F6]">Analysis Run:</span>
                <select
                  value={selectedAnalysisId}
                  onChange={(e) => setSelectedAnalysisId(e.target.value)}
                  className="bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-1.5 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] text-xs font-mono"
                >
                  {analyses.map((a) => (
                    <option key={a.analysis_id} value={a.analysis_id}>
                      {a.evaluation_dataset_filename || "evaluation.csv"} | Fused {a.aggregate_fused_risk !== undefined && a.aggregate_fused_risk !== null ? a.aggregate_fused_risk.toFixed(3) : "N/A"} · {new Date(a.created_at).toLocaleTimeString()} ({a.analysis_id.slice(0, 8)}...)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex items-center space-x-2 border-l border-[#26303D] pl-4">
              <span className="font-semibold text-[#F3F4F6]">Governance Mode:</span>
              <select
                value={selectedMode}
                onChange={(e) => setSelectedMode(e.target.value as ECRGOperatingMode)}
                className="bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-1.5 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] text-xs font-mono"
              >
                <option value="EVIDENCE_ONLY">EVIDENCE_ONLY (Advisory)</option>
                <option value="CALIBRATED_GOVERNANCE">CALIBRATED_GOVERNANCE (Certified)</option>
              </select>
            </div>
          </div>

          {activeAnalysis && (
            <div className="flex items-center space-x-2 text-xs font-mono">
              <CopyButton text={activeAnalysis.analysis_id} label="Copy Analysis ID" />
              <StatusBadge status={activeAnalysis.has_labels ? "LABEL_VERIFIED" : "LABEL_FREE"} />
            </div>
          )}
        </div>
      )}

      {/* Explicit Readiness Status Bar */}
      <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <span className="text-[#6B7280]">Model Readiness:</span>
          <span className={`px-2 py-0.5 rounded ${isModelReady ? 'bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30' : 'bg-rose-950/40 text-rose-400 border border-rose-800/40'}`}>
            {isModelReady ? "READY" : "INVALID"}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[#6B7280]">Analysis Readiness:</span>
          <span className={`px-2 py-0.5 rounded ${isAnalysisReady ? 'bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30' : 'bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/30'}`}>
            {isAnalysisReady ? "READY" : "INCOMPLETE"}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[#6B7280]">Evidence Telemetry:</span>
          <span className={`px-2 py-0.5 rounded ${isEvidenceReady ? 'bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30' : 'bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/30'}`}>
            {isEvidenceReady ? "READY" : "MISSING"}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[#6B7280]">Conformal Calibration:</span>
          <span className={`px-2 py-0.5 rounded ${isCalibrationReady ? 'bg-[#3B82F6]/10 text-[#60A5FA] border border-[#3B82F6]/30' : 'bg-[#1A222C] text-[#9CA3AF] border border-[#26303D]'}`}>
            {isCalibrationReady ? "CERTIFIED" : "UNAVAILABLE"}
          </span>
        </div>
      </div>

      {!selectedModelId ? (
        <EmptyState
          title="No Active Model Selected"
          description="Register or select an AI model to evaluate Evidence-Calibrated Reliability Governance (ECRG)."
          actionText="Go to Models"
          actionHref="/models"
          icon={<ShieldCheck className="w-8 h-8" />}
        />
      ) : (
        <div className="space-y-8">
          {/* Main Governance Decision Layer */}
          <GovernanceOverviewCard
            modelId={selectedModelId}
            selectedAnalysis={activeAnalysis}
            mode={selectedMode}
            onEvaluationCompleted={() => setHistoryTrigger((prev) => prev + 1)}
          />

          {/* Governance State Transition Audit Trail */}
          <GovernanceHistoryTimeline
            modelId={selectedModelId}
            refreshTrigger={historyTrigger}
          />
        </div>
      )}
    </div>
  );
}
