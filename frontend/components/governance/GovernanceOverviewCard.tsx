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
    <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-6 shadow-2xl space-y-6">
      {/* Top Bar: Title & Evaluation Trigger Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div className="flex items-start space-x-3.5">
          <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-xl text-indigo-400 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-slate-100 font-mono tracking-tight">
                Evidence-Calibrated Reliability Governance (ECRG)
              </h2>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800/60 rounded">
                MODULE 14
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Conformal risk-controlled decision framework &amp; state-machine anti-flapping protection.
            </p>
          </div>
        </div>

        {/* Evaluate Action Button */}
        <button
          onClick={handleEvaluate}
          disabled={!hasTelemetry || evaluating}
          className="px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-mono text-xs font-semibold rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2 shrink-0 border border-indigo-500/30"
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
        <div className="p-4 bg-amber-950/40 border border-amber-800/50 rounded-xl flex items-start space-x-3 text-xs text-amber-300">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-mono font-bold uppercase tracking-wider block mb-0.5">
              Fail-Safe Protection Active
            </span>
            No operational analysis telemetry is selected for this model. Unrestricted automation is strictly disabled until reliability evidence is evaluated.
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/50 rounded-xl text-xs font-mono text-rose-300 flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active State Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Current Governance Action */}
        <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
            1. Active Governance Action
          </span>

          {loadingStatus ? (
            <div className="flex items-center space-x-2 text-xs font-mono text-slate-500 py-2">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Loading state...</span>
            </div>
          ) : activeAction ? (
            <div className="space-y-2">
              <GovernanceBadge action={activeAction} size="lg" />
              <p className="text-xs text-slate-400 leading-relaxed font-sans pt-1">
                {activeAction === "CONTINUE" && "Model operating nominally. Full automation permitted."}
                {activeAction === "WATCH" && "Minor risk anomaly. Execution allowed with high-frequency logging."}
                {activeAction === "DEFER" && "High risk detected. Execution deferred pending operator approval."}
                {activeAction === "ESCALATE" && "Critical risk or corrupted evidence. Automation strictly disabled."}

              </p>
            </div>
          ) : (
            <div className="text-xs font-mono text-slate-500 italic py-2">
              Unevaluated (Run evaluation above)
            </div>
          )}
        </div>

        {/* Card 2: Operating Mode & Certification */}
        <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
            2. Operating Mode &amp; Certification
          </span>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-1 rounded bg-indigo-950 border border-indigo-800/60 text-indigo-300 font-mono text-xs font-bold">
                {activeMode || "EVIDENCE_ONLY"}
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed font-sans pt-1">
              {latestEval?.certification_banner || "Label-Free Production Governance"}
            </p>
          </div>
        </div>

        {/* Card 3: Anti-Flapping & Transition Telemetry */}
        <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
            3. Anti-Flapping Status
          </span>

          <div className="space-y-1.5 font-mono text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Consecutive Steps:</span>
              <span className="text-slate-100 font-bold">{status?.consecutive_state_count || latestEval?.consecutive_state_count || 1}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Cooldown Active:</span>
              <span className={status?.in_cooldown ? "text-amber-400 font-bold" : "text-slate-400"}>
                {status?.in_cooldown ? "YES (Enforced)" : "NO"}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Total Evaluations:</span>
              <span className="text-slate-100 font-bold">{status?.total_evaluations || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Explanation Bar */}
      {latestEval && (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1 text-xs">
            <span className="font-mono font-bold text-slate-400 uppercase tracking-wider block">
              Governance Decision Rationale
            </span>
            <p className="text-slate-200 font-mono text-xs">{latestEval.transition_reason}</p>
          </div>

          <button
            onClick={() => setShowDetailsModal(true)}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-700/80 rounded-lg font-mono text-xs font-semibold transition-colors flex items-center space-x-1.5 shrink-0"
          >
            <FileText className="w-4 h-4" />
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
