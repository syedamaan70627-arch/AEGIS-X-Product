"use client";

import React, { useState } from "react";
import { GovernanceEvaluationResponse } from "@/types/api";
import { CheckCircle2, ChevronDown, ChevronUp, Code, FileText, Info, ShieldAlert, X } from "lucide-react";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <FileText className="w-6 h-6 text-indigo-400" />
            <div>
              <h3 className="text-lg font-bold text-slate-100 font-mono">Governance Audit & Explanation</h3>
              <p className="text-xs text-slate-400 font-mono">Decision ID: {evaluation.evaluation_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-slate-300">
          {/* Banner */}
          <div className="p-3.5 bg-indigo-950/50 border border-indigo-800/50 rounded-xl flex items-center justify-between">
            <span className="font-mono text-xs font-semibold text-indigo-300 uppercase tracking-wider">
              {evaluation.certification_banner}
            </span>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-indigo-900/60 text-indigo-200 border border-indigo-700/50">
              Mode: {evaluation.mode}
            </span>
          </div>

          {/* Explanation Section */}
          <div className="space-y-4">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
              Human-Readable Explanation Layer
            </h4>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
              <div className="flex items-start space-x-3">
                <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-200 block mb-0.5">Decision Rationale</span>
                  <p className="text-xs leading-relaxed text-slate-300">{exp.summary}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 pt-2 border-t border-slate-900">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-200 block mb-0.5">Automation Permission</span>
                  <p className="text-xs leading-relaxed text-slate-300">{exp.allowed}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 pt-2 border-t border-slate-900">
                <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-200 block mb-0.5">Operator Review Protocol</span>
                  <p className="text-xs leading-relaxed text-slate-300">{exp.review}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Reason Codes & Transition Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
              <span className="font-mono text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
                Machine Reason Codes
              </span>
              <div className="flex flex-wrap gap-1.5">
                {evaluation.reason_codes.length > 0 ? (
                  evaluation.reason_codes.map((code) => (
                    <span
                      key={code}
                      className="px-2 py-0.5 text-[11px] font-mono rounded bg-slate-900 text-slate-300 border border-slate-800"
                    >
                      {code}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 font-mono">NOMINAL_RELIABILITY</span>
                )}
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
              <span className="font-mono text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
                State Transition Rationale
              </span>
              <p className="text-xs font-mono text-slate-300 leading-relaxed">
                {evaluation.transition_reason || "State machine held previous governance level."}
              </p>
            </div>
          </div>

          {/* Provenance Metadata */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 font-mono text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Provenance & Cryptographic Audit
            </span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Evaluation Timestamp:</span>
              <span className="text-slate-200">{new Date(evaluation.created_at).toISOString()}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Evidence Snapshot SHA-256:</span>
              <span className="text-slate-200 truncate max-w-[240px]">{evaluation.evidence_snapshot_hash}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-500">Estimated Adverse Risk P(Y=1|x):</span>
              <span className="text-slate-200">{(evaluation.p_adverse * 100).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Signal Disagreement Index:</span>
              <span className="text-slate-200">{evaluation.signal_disagreement_index.toFixed(4)}</span>
            </div>
          </div>

          {/* Expandable Raw Technical Payload */}
          <div className="pt-2">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="flex items-center space-x-2 text-xs font-mono text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              <Code className="w-4 h-4" />
              <span>{showRawJson ? "Hide Raw Decision JSON" : "Show Raw Decision JSON"}</span>
              {showRawJson ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showRawJson && (
              <pre className="mt-3 p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-emerald-400 overflow-x-auto max-h-60 leading-normal">
                {JSON.stringify(evaluation, null, 2)}
              </pre>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold rounded-lg transition-colors"
          >
            Close Explanation
          </button>
        </div>
      </div>
    </div>
  );
}
