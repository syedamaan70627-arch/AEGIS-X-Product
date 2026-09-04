"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  AnalysisSummary,
  GovernanceEvaluationResponse,
  GovernanceStatusResponse,
} from "@/types/api";
import { GovernanceBadge } from "./GovernanceBadge";
import { GovernanceDetailsModal } from "./GovernanceDetailsModal";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileText,
  HelpCircle,
  Play,
  RefreshCw,
  ShieldCheck,
  Zap,
} from "lucide-react";

interface GovernanceOverviewCardProps {
  modelId: string;
  selectedAnalysis?: AnalysisSummary | null;
  onEvaluationCompleted?: () => void;
}

export function GovernanceOverviewCard({
  modelId,
  selectedAnalysis,
  onEvaluationCompleted,
}: GovernanceOverviewCardProps) {
  const [status, setStatus] = useState<GovernanceStatusResponse | null>(null);
  const [latestEval, setLatestEval] = useState<GovernanceEvaluationResponse | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  useEffect(() => {
    async function loadStatus() {
      if (!modelId) return;
      setLoadingStatus(true);
      setError(null);
      try {
        const st = await api.getGovernanceStatus(modelId);
        setStatus(st);
      } catch (err: any) {
        if (err.status === 404) {
          setStatus(null);
        } else {
          setError(err.message || "Failed to load governance status.");
        }
      } finally {
        setLoadingStatus(false);
      }
    }
    loadStatus();
  }, [modelId]);

  const handleEvaluate = async () => {
    if (!modelId || !selectedAnalysis) return;
    setEvaluating(true);
    setError(null);

    try {
      const payload = {
        model_id: modelId,
        dataset_id: selectedAnalysis.evaluation_dataset_id,
        source_analysis_id: selectedAnalysis.analysis_id,
        ood_score: selectedAnalysis.aggregate_ood_risk ?? 0.0,
        uncertainty_score: selectedAnalysis.aggregate_uncertainty ?? 0.0,
        drift_score: selectedAnalysis.aggregate_drift_score ?? 0.0,
        fused_risk: selectedAnalysis.aggregate_fused_risk ?? 0.0,
        signal_disagreement: 0.05,
        stress_robustness: 0.95,
        fault_sensitivity: 0.05,
        temporal_failure_probability: 0.0,
        mode: "EVIDENCE_ONLY" as const,
      };

      const res = await api.evaluateGovernance(payload);
      setLatestEval(res);

      const updatedStatus = await api.getGovernanceStatus(modelId);
      setStatus(updatedStatus);

      if (onEvaluationCompleted) {
        onEvaluationCompleted();
      }
    } catch (err: any) {
      setError(err.message || "Failed to evaluate reliability governance.");
    } finally {
      setEvaluating(false);
    }
  };

  const activeAction = latestEval?.action || status?.latest_action;
  const activeMode = latestEval?.mode || status?.mode;
  const lastEvaluatedAt = latestEval?.created_at || status?.last_evaluated_at;

  const hasTelemetry = !!selectedAnalysis;
  const isMissingEvidence = !hasTelemetry && !status;

  return (
    <div className="bg-[#151B23] border border-[#26303D] rounded-2xl p-6 shadow-sm space-y-6 font-sans">
      {/* Top Bar: Title & Evaluation Trigger Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#26303D] pb-5">
        <div className="flex items-start space-x-3.5">
          <div className="p-3 bg-[#0F141B] border border-[#26303D] rounded-xl text-[#3B82F6] shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-[#F3F4F6] font-sans tracking-tight">
                Evidence-Calibrated Reliability Governance (ECRG)
              </h2>
              <span className="px-2 py-0.5 text-[10px] font-sans font-semibold bg-[#1A222C] text-[#9CA3AF] border border-[#26303D] rounded">
                MODULE 14
              </span>
            </div>
            <p className="text-xs text-[#9CA3AF] mt-0.5 font-sans">
              Conformal risk-controlled decision framework &amp; state-machine anti-flapping protection.
            </p>
          </div>
        </div>

        {/* Evaluate Action Button - STEEL BLUE */}
        <button
          onClick={handleEvaluate}
          disabled={!hasTelemetry || evaluating}
          className="px-4 py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] disabled:opacity-50 disabled:cursor-not-allowed text-white font-sans text-xs font-semibold rounded-xl shadow-sm transition-all flex items-center justify-center space-x-2 shrink-0 border border-[#3B82F6]/50"
        >
          {evaluating ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Evaluating Governance...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              <span>Evaluate Governance</span>
            </>
          )}
        </button>
      </div>

      {/* Fail-Safe Warning if evidence is missing */}
      {isMissingEvidence && (
        <div className="p-4 bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-xl flex items-start space-x-3 text-xs text-[#F59E0B]">
          <AlertTriangle className="w-5 h-5 text-[#F59E0B] shrink-0 mt-0.5" />
          <div>
            <span className="font-sans font-bold uppercase tracking-wider block mb-0.5">
              Fail-Safe Protection Active
            </span>
            No operational analysis telemetry is selected for this model. Unrestricted automation is strictly disabled until reliability evidence is evaluated.
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl text-xs font-sans text-[#EF4444] flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 text-[#EF4444] shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active State Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Current Governance Action */}
        <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <span className="text-[11px] font-sans font-semibold uppercase tracking-wider text-[#9CA3AF] block">
            1. Active Governance Action
          </span>

          {loadingStatus ? (
            <div className="flex items-center space-x-2 text-xs font-sans text-[#6B7280] py-2">
              <RefreshCw className="w-4 h-4 animate-spin text-[#3B82F6]" />
              <span>Loading state...</span>
            </div>
          ) : (latestEval || (status && status.total_evaluations > 0)) ? (
            <div className="space-y-2">
              <GovernanceBadge action={activeAction || "CONTINUE"} size="lg" />
              <p className="text-xs text-[#9CA3AF] leading-relaxed font-sans pt-1">
                {activeAction === "CONTINUE" && "Model operating nominally. Full automation permitted."}
                {activeAction === "WATCH" && "Minor risk anomaly. Execution allowed with high-frequency logging."}
                {activeAction === "DEFER" && "High risk detected. Execution deferred pending operator approval."}
                {activeAction === "ESCALATE" && "Critical risk or corrupted evidence. Automation strictly disabled."}
              </p>
            </div>
          ) : (
            <div className="p-3 bg-[#1A222C] border border-[#26303D] rounded-xl space-y-1.5">
              <div className="inline-flex items-center text-[#9CA3AF] font-sans text-xs font-semibold space-x-1.5">
                <AlertTriangle className="w-4 h-4 text-[#F59E0B] shrink-0" />
                <span>GOVERNANCE NOT EVALUATED</span>
              </div>
              <p className="text-xs text-[#6B7280] font-sans leading-relaxed">
                No governance evaluation recorded for this model. Click &quot;Evaluate Governance&quot; to run conformal risk analysis. Unrestricted automation is not certified.
              </p>
            </div>
          )}
        </div>

        {/* Card 2: Operating Mode & Certification */}
        <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <span className="text-[11px] font-sans font-semibold uppercase tracking-wider text-[#9CA3AF] block">
            2. Operating Mode &amp; Certification
          </span>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-1 rounded bg-[#1A222C] border border-[#26303D] text-[#F3F4F6] font-sans text-xs font-semibold">
                {activeMode || "EVIDENCE_ONLY"}
              </span>
            </div>

            <p className="text-xs text-[#9CA3AF] leading-relaxed font-sans pt-1">
              {latestEval?.certification_banner || "Label-Free Production Governance"}
            </p>
          </div>
        </div>

        {/* Card 3: Anti-Flapping & Transition Telemetry */}
        <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <span className="text-[11px] font-sans font-semibold uppercase tracking-wider text-[#9CA3AF] block">
            3. Anti-Flapping Status
          </span>

          <div className="space-y-1.5 font-sans text-xs text-[#F3F4F6]">
            <div className="flex justify-between py-1 border-b border-[#26303D]">
              <span className="text-[#6B7280]">Consecutive Steps:</span>
              <span className="text-[#F3F4F6] font-bold font-mono tabular-nums">{status?.consecutive_state_count || latestEval?.consecutive_state_count || 1}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#26303D]">
              <span className="text-[#6B7280]">Cooldown Active:</span>
              <span className={status?.in_cooldown ? "text-[#F59E0B] font-semibold" : "text-[#9CA3AF]"}>
                {status?.in_cooldown ? "YES (Enforced)" : "NO"}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#6B7280]">Total Evaluations:</span>
              <span className="text-[#F3F4F6] font-bold font-mono tabular-nums">{status?.total_evaluations || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Explanation Bar */}
      {latestEval && (
        <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1 text-xs">
            <span className="font-sans font-semibold text-[#9CA3AF] uppercase tracking-wider block">
              Governance Decision Rationale
            </span>
            <p className="text-[#F3F4F6] font-sans text-xs">{latestEval.transition_reason}</p>
          </div>

          <button
            onClick={() => setShowDetailsModal(true)}
            className="px-3.5 py-1.5 bg-[#1A222C] hover:bg-[#26303D] text-[#F3F4F6] border border-[#26303D] rounded-lg font-sans text-xs font-medium transition-colors flex items-center space-x-1.5 shrink-0"
          >
            <FileText className="w-4 h-4 text-[#3B82F6]" />
            <span>Audit &amp; Provenance Details</span>
          </button>
        </div>
      )}

      {/* Details Modal */}
      {latestEval && (
        <GovernanceDetailsModal
          evaluation={latestEval}
          isOpen={showDetailsModal}
          onClose={() => setShowDetailsModal(false)}
        />
      )}

    </div>
  );
}
