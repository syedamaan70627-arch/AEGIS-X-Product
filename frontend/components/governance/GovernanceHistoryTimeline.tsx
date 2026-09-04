"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { GovernanceEvaluationResponse, GovernanceHistoryResponse } from "@/types/api";
import { GovernanceBadge } from "./GovernanceBadge";
import { ChevronLeft, ChevronRight, Clock, FileJson, RefreshCw, ShieldAlert } from "lucide-react";
import { GovernanceDetailsModal } from "./GovernanceDetailsModal";

interface GovernanceHistoryTimelineProps {
  modelId: string;
  refreshTrigger?: number;
}

export function GovernanceHistoryTimeline({ modelId, refreshTrigger = 0 }: GovernanceHistoryTimelineProps) {
  const [history, setHistory] = useState<GovernanceHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 5;

  const [selectedEval, setSelectedEval] = useState<GovernanceEvaluationResponse | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      if (!modelId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await api.getGovernanceHistory(modelId, limit, offset);
        setHistory(res);
      } catch (err: any) {
        setError(err.message || "Failed to load governance history.");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [modelId, offset, refreshTrigger]);

  const handlePrevPage = () => {
    if (offset >= limit) setOffset(offset - limit);
  };

  const handleNextPage = () => {
    if (history && offset + limit < history.total) setOffset(offset + limit);
  };

  return (
    <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-6 shadow-sm space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#26303D] pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-[#0F141B] border border-[#26303D] rounded-xl text-[#3B82F6]">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#F3F4F6] font-sans tracking-tight">
              Governance State Transition Audit History
            </h3>
            <p className="text-xs text-[#9CA3AF]">
              Immutable log of ECRG evaluations, anti-flapping transitions, and evidence snapshot hashes.
            </p>
          </div>
        </div>

        {history && history.total > 0 && (
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="text-[#9CA3AF]">
              Showing {offset + 1} - {Math.min(offset + limit, history.total)} of {history.total}
            </span>
            <div className="flex items-center space-x-1 pl-2">
              <button
                onClick={handlePrevPage}
                disabled={offset === 0 || loading}
                className="p-1.5 bg-[#0F141B] border border-[#26303D] hover:bg-[#1A222C] disabled:opacity-40 rounded-lg text-[#F3F4F6] transition-colors"
                title="Previous page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleNextPage}
                disabled={!history || offset + limit >= history.total || loading}
                className="p-1.5 bg-[#0F141B] border border-[#26303D] hover:bg-[#1A222C] disabled:opacity-40 rounded-lg text-[#F3F4F6] transition-colors"
                title="Next page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Loading & Error States */}
      {loading && !history && (
        <div className="py-8 flex items-center justify-center space-x-3 text-xs font-mono text-[#9CA3AF]">
          <RefreshCw className="w-4 h-4 animate-spin text-[#3B82F6]" />
          <span>Fetching governance evaluation audit trail...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/40 rounded-xl text-xs font-mono text-rose-300 flex items-center space-x-3">
          <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && history && history.evaluations.length === 0 && (
        <div className="py-10 text-center space-y-2">
          <Clock className="w-8 h-8 text-[#6B7280] mx-auto" />
          <h4 className="text-sm font-semibold text-[#F3F4F6] font-sans">No Governance Evaluation History Recorded</h4>
          <p className="text-xs text-[#9CA3AF] max-w-md mx-auto">
            Click &quot;Evaluate Governance&quot; above to run the initial conformal risk evaluation.
          </p>
        </div>
      )}

      {/* Timeline Table */}
      {history && history.evaluations.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-[#26303D]">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#26303D] bg-[#0F141B] text-[#9CA3AF] uppercase tracking-wider text-[11px] font-sans">
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold">State / Action</th>
                <th className="py-3 px-4 font-semibold">Transition</th>
                <th className="py-3 px-4 font-semibold">Mode / Calibrated</th>
                <th className="py-3 px-4 font-semibold">Evidence Hash</th>
                <th className="py-3 px-4 font-semibold text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#26303D]">
              {history.evaluations.map((ev) => (
                <tr key={ev.evaluation_id} className="bg-[#151B23] hover:bg-[#1A222C] transition-colors group">
                  <td className="py-3.5 px-4 text-[#F3F4F6] whitespace-nowrap font-mono">
                    {new Date(ev.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                    <span className="text-[10px] text-[#6B7280] block font-mono">
                      {new Date(ev.created_at).toLocaleDateString()}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <GovernanceBadge action={ev.action} size="sm" showLabel={false} />
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {ev.state_transition_occurred ? (
                      <span className="px-2 py-0.5 rounded bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[#F59E0B] font-semibold text-[10px] font-sans">
                        STATE TRANSITION
                      </span>
                    ) : (
                      <span className="text-[#6B7280] text-[10px] font-sans">HOLD_STATE</span>
                    )}
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                        ev.calibrated
                          ? "bg-[#0F141B] border border-[#3B82F6]/40 text-[#60A5FA]"
                          : "bg-[#0F141B] border border-[#26303D] text-[#9CA3AF]"
                      }`}
                    >
                      {ev.mode}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-[#9CA3AF] text-[11px] whitespace-nowrap font-mono">
                    <span className="bg-[#0F141B] px-2 py-1 rounded border border-[#26303D]">
                      {ev.evidence_snapshot_hash.slice(0, 12)}...
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => setSelectedEval(ev)}
                      className="px-2.5 py-1 bg-[#1A222C] hover:bg-[#26303D] text-[#F3F4F6] rounded border border-[#26303D] transition-colors inline-flex items-center space-x-1 font-sans text-xs"
                    >
                      <FileJson className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Details Modal */}
      {selectedEval && (
        <GovernanceDetailsModal
          evaluation={selectedEval}
          isOpen={!!selectedEval}
          onClose={() => setSelectedEval(null)}
        />
      )}
    </div>
  );
}
