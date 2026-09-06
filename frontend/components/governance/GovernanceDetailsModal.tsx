"use client";

import React, { useState } from "react";
import { GovernanceEvaluationResponse } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { GovernanceBadge } from "./GovernanceBadge";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Code,
  Database,
  FileText,
  Info,
  Layers,
  Lock,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  User,
  X,
} from "lucide-react";

interface GovernanceDetailsModalProps {
  evaluation: GovernanceEvaluationResponse;
  isOpen: boolean;
  onClose: () => void;
}

export function GovernanceDetailsModal({ evaluation, isOpen, onClose }: GovernanceDetailsModalProps) {
  const [showRawJson, setShowRawJson] = useState(false);

  if (!isOpen) return null;

  const actionExplanations: Record<string, { summary: string; allowed: string; review: string }> = {
    CONTINUE: {
      summary: "Reliability signals are within nominal statistical bounds. Conformal risk target is satisfied.",
      allowed: "Full automated model deployment and automated decision-making permitted.",
      review: "No manual review required at this step.",
    },
    WATCH: {
      summary: "Minor reliability signal disagreement or elevated risk detected. Pre-warning threshold active.",
      allowed: "Automated execution permitted with increased telemetry log frequency.",
      review: "Operator review recommended during next routine maintenance window.",
    },
    DEFER: {
      summary: "Significant reliability degradation or high fused risk score exceeds safety limits.",
      allowed: "Automated decision execution suspended.",
      review: "Immediate human operator sign-off / review mandatory before execution.",
    },
    ESCALATE: {
      summary: "Critical reliability risk detected, consecutive persistence exceeded, or evidence pipeline failure.",
      allowed: "All automated decision-making strictly prohibited. Fail-safe isolation engaged.",
      review: "Urgent engineering escalation and incident investigation required.",
    },
  };

  const exp = actionExplanations[evaluation.action] || actionExplanations.ESCALATE;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0B0F14]/80 backdrop-blur-sm animate-in fade-in duration-200 font-sans">
      <div className="bg-[#151B23] border border-[#26303D] rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="p-6 border-b border-[#26303D] flex items-center justify-between bg-[#0F141B]">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-xl text-[#3B82F6]">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#F3F4F6] font-sans">Governance Audit &amp; Cryptographic Provenance</h3>
              <div className="flex items-center space-x-2 mt-0.5">
                <span className="text-xs text-[#9CA3AF] font-mono">ID: {evaluation.evaluation_id}</span>
                <CopyButton text={evaluation.evaluation_id} />
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-[#1A222C] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-[#F3F4F6]">
          {/* Certification Banner */}
          <div className="p-4 bg-[#0F141B] border border-[#3B82F6]/30 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <GovernanceBadge action={evaluation.action} size="sm" />
              <span className="font-sans text-xs font-semibold text-[#60A5FA] uppercase tracking-wider">
                {evaluation.certification_banner}
              </span>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#1A222C] text-[#F3F4F6] border border-[#26303D] self-start sm:self-auto">
              Mode: {evaluation.mode}
            </span>
          </div>

          {/* Group A: Decision Identity */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-[#9CA3AF] flex items-center space-x-2">
              <FileText className="w-4 h-4 text-[#3B82F6]" />
              <span>A. Decision Identity</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-sans">
              <div className="flex justify-between p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280]">Decision ID:</span>
                <div className="flex items-center space-x-1 font-mono text-[#F3F4F6]">
                  <span>{evaluation.evaluation_id.slice(0, 16)}...</span>
                  <CopyButton text={evaluation.evaluation_id} />
                </div>
              </div>
              <div className="flex justify-between p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280]">Evaluation Timestamp:</span>
                <span className="font-mono text-[#F3F4F6]">{new Date(evaluation.created_at).toISOString()}</span>
              </div>
            </div>
          </div>

          {/* Group B: Context */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-[#9CA3AF] flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#3B82F6]" />
              <span>B. Operational Context</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-sans">
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg space-y-1">
                <span className="text-[#6B7280] text-[11px] block">Model ID:</span>
                <div className="flex items-center justify-between font-mono text-[#F3F4F6]">
                  <span className="truncate">{evaluation.model_id}</span>
                  <CopyButton text={evaluation.model_id} />
                </div>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg space-y-1">
                <span className="text-[#6B7280] text-[11px] block">Dataset ID:</span>
                <div className="flex items-center justify-between font-mono text-[#F3F4F6]">
                  <span className="truncate">{evaluation.dataset_id}</span>
                  <CopyButton text={evaluation.dataset_id} />
                </div>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg space-y-1">
                <span className="text-[#6B7280] text-[11px] block">User / Owner Reference:</span>
                <div className="flex items-center justify-between font-mono text-[#F3F4F6]">
                  <span className="truncate">{evaluation.user_id.slice(0, 12)}...</span>
                  <CopyButton text={evaluation.user_id} />
                </div>
              </div>
            </div>
          </div>

          {/* Group C: Evidence */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-[#9CA3AF] flex items-center space-x-2">
              <Activity className="w-4 h-4 text-[#3B82F6]" />
              <span>C. Reliability Evidence Signals</span>
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-sans">
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Primary Signal:</span>
                <span className="font-mono text-[#3B82F6] font-semibold">{evaluation.primary_supporting_signal}</span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Adverse Risk P(Y=1|x):</span>
                <span className="font-mono text-[#F3F4F6] font-semibold">{(evaluation.p_adverse * 100).toFixed(2)}%</span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Signal Disagreement:</span>
                <span className="font-mono text-[#F3F4F6] font-semibold">{evaluation.signal_disagreement_index.toFixed(4)}</span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Warning Severity:</span>
                <span className={`font-semibold ${evaluation.warning_severity === 'CRITICAL' ? 'text-[#EF4444]' : evaluation.warning_severity === 'HIGH' ? 'text-[#F59E0B]' : evaluation.warning_severity === 'MODERATE' ? 'text-[#3B82F6]' : 'text-[#22C55E]'}`}>
                  {evaluation.warning_severity}
                </span>
              </div>
            </div>
          </div>

          {/* Group D: Calibration */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-[#9CA3AF] flex items-center space-x-2">
              <Lock className="w-4 h-4 text-[#3B82F6]" />
              <span>D. Conformal Calibration Guarantees</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-sans">
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg space-y-1">
                <span className="text-[#6B7280] text-[11px] block">Calibration Status:</span>
                <span className={`font-semibold ${evaluation.calibrated ? 'text-[#22C55E]' : 'text-[#9CA3AF]'}`}>
                  {evaluation.calibrated ? "FORMALLY CALIBRATED" : "UNCALIBRATED ADVISORY"}
                </span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg space-y-1">
                <span className="text-[#6B7280] text-[11px] block">Prediction Set C_α(x):</span>
                <span className="font-mono text-[#F3F4F6] font-semibold">
                  {evaluation.prediction_set ? `{${evaluation.prediction_set.join(", ")}}` : "N/A (Label-Free)"}
                </span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg space-y-1">
                <span className="text-[#6B7280] text-[11px] block">Calibrator Artifact SHA-256:</span>
                <div className="flex items-center justify-between font-mono text-[#F3F4F6]">
                  <span className="truncate">{evaluation.calibrator_artifact_sha256 ? `${evaluation.calibrator_artifact_sha256.slice(0, 12)}...` : "UNAVAILABLE"}</span>
                  {evaluation.calibrator_artifact_sha256 && <CopyButton text={evaluation.calibrator_artifact_sha256} />}
                </div>
              </div>
            </div>
          </div>

          {/* Group E: State Machine */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-[#9CA3AF] flex items-center space-x-2">
              <RotateCcw className="w-4 h-4 text-[#3B82F6]" />
              <span>E. Anti-Flapping &amp; State Machine Metrics</span>
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-sans">
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Recommended (Raw):</span>
                <span className="font-mono text-[#F3F4F6] font-semibold">{evaluation.raw_action || evaluation.action}</span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Effective Action:</span>
                <span className="font-mono text-[#3B82F6] font-semibold">{evaluation.action}</span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Consecutive Steps:</span>
                <span className="font-mono text-[#F3F4F6] font-semibold">{evaluation.consecutive_state_count}</span>
              </div>
              <div className="p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280] text-[11px] block">Cooldown Active:</span>
                <span className={evaluation.in_cooldown ? "text-[#F59E0B] font-semibold" : "text-[#9CA3AF]"}>
                  {evaluation.in_cooldown ? "YES" : "NO"}
                </span>
              </div>
            </div>
            <div className="p-3 bg-[#151B23] border border-[#26303D] rounded-lg text-xs font-mono text-[#9CA3AF] leading-relaxed">
              <span className="text-[#F3F4F6] font-semibold block font-sans mb-0.5">Transition Rationale:</span>
              {evaluation.transition_reason}
            </div>
          </div>

          {/* Group F: Cryptographic Provenance */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-[#9CA3AF] flex items-center space-x-2">
              <Database className="w-4 h-4 text-[#3B82F6]" />
              <span>F. Cryptographic Evidence &amp; Persistence Provenance</span>
            </h4>
            <div className="space-y-2 text-xs font-sans">
              <div className="flex items-center justify-between p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                <span className="text-[#6B7280]">Evidence Snapshot SHA-256:</span>
                <div className="flex items-center space-x-1.5 font-mono text-[#F3F4F6]">
                  <span className="truncate max-w-[280px]">{evaluation.evidence_snapshot_hash}</span>
                  <CopyButton text={evaluation.evidence_snapshot_hash} />
                </div>
              </div>
              {evaluation.result_json_path && (
                <div className="flex items-center justify-between p-2.5 bg-[#151B23] border border-[#26303D] rounded-lg">
                  <span className="text-[#6B7280]">Artifact Storage Path:</span>
                  <div className="flex items-center space-x-1.5 font-mono text-[#22C55E]">
                    <span className="truncate max-w-[280px]">{evaluation.result_json_path}</span>
                    <CopyButton text={evaluation.result_json_path} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Machine Reason Codes */}
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-4 space-y-2">
            <span className="font-sans text-xs font-bold text-[#9CA3AF] uppercase tracking-wider block">
              Machine Reason Codes
            </span>
            <div className="flex flex-wrap gap-1.5">
              {evaluation.reason_codes.length > 0 ? (
                evaluation.reason_codes.map((code) => (
                  <span
                    key={code}
                    className="px-2.5 py-1 text-[11px] font-mono rounded bg-[#1A222C] text-[#F3F4F6] border border-[#26303D]"
                  >
                    {code}
                  </span>
                ))
              ) : (
                <span className="text-xs text-[#6B7280] font-mono">NOMINAL_RELIABILITY</span>
              )}
            </div>
          </div>

          {/* Expandable Raw Technical Payload */}
          <div className="pt-2">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="flex items-center space-x-2 text-xs font-sans text-[#3B82F6] hover:text-[#60A5FA] transition-colors"
            >
              <Code className="w-4 h-4" />
              <span>{showRawJson ? "Hide Raw Decision JSON" : "Show Raw Decision JSON"}</span>
              {showRawJson ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showRawJson && (
              <pre className="mt-3 p-4 bg-[#0F141B] border border-[#26303D] rounded-xl font-mono text-[11px] text-[#22C55E] overflow-x-auto max-h-60 leading-normal">
                {JSON.stringify(evaluation, null, 2)}
              </pre>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#26303D] bg-[#0F141B] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#1A222C] hover:bg-[#26303D] text-[#F3F4F6] text-xs font-sans font-semibold rounded-lg transition-colors"
          >
            Close Audit Drawer
          </button>
        </div>
      </div>
    </div>
  );
}
