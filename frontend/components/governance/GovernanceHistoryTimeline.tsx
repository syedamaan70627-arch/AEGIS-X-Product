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
    <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-950/60 border border-indigo-800/50 rounded-xl text-indigo-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 font-mono tracking-tight">
              Governance State Transition Audit History
            </h3>
            <p className="text-xs text-slate-400">
              Immutable log of ECRG evaluations, anti-flapping transitions, and evidence snapshot hashes.
            </p>
          </div>
        </div>

        {history && history.total > 0 && (
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="text-slate-400">
              Showing {offset + 1} - {Math.min(offset + limit, history.total)} of {history.total}
            </span>
            <div className="flex items-center space-x-1 pl-2">
              <button
                onClick={handlePrevPage}
                disabled={offset === 0 || loading}
                className="p-1.5 bg-slate-950 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 rounded-lg text-slate-300 transition-colors"
                title="Previous page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleNextPage}
                disabled={!history || offset + limit >= history.total || loading}
                className="p-1.5 bg-slate-950 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 rounded-lg text-slate-300 transition-colors"
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
        <div className="py-8 flex items-center justify-center space-x-3 text-xs font-mono text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
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
          <Clock className="w-8 h-8 text-slate-600 mx-auto" />
          <h4 className="text-sm font-semibold text-slate-300 font-mono">No Governance Evaluation History Recorded</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Click &quot;Evaluate Reliability Governance&quot; above to run the initial conformal risk evaluation.
          </p>
        </div>
      )}

      {/* Timeline Table */}
      {history && history.evaluations.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">State / Action</th>
                <th className="py-3 px-4">Transition</th>
                <th className="py-3 px-4">Mode / Calibrated</th>
                <th className="py-3 px-4">Evidence Hash</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {history.evaluations.map((ev) => (
                <tr key={ev.evaluation_id} className="hover:bg-slate-950/50 transition-colors group">
                  <td className="py-3.5 px-4 text-slate-300 whitespace-nowrap">
                    {new Date(ev.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                    <span className="text-[10px] text-slate-500 block">
                      {new Date(ev.created_at).toLocaleDateString()}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <GovernanceBadge action={ev.action} size="sm" showLabel={false} />
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {ev.state_transition_occurred ? (
                      <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-700/50 text-amber-300 font-semibold text-[10px]">
                        STATE TRANSITION
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">HOLD_STATE</span>
                    )}
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] ${
                        ev.calibrated
                          ? "bg-indigo-950/60 border border-indigo-700/50 text-indigo-300"
                          : "bg-slate-950 border border-slate-800 text-slate-400"
                      }`}
                    >
                      {ev.mode}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-slate-400 text-[11px] whitespace-nowrap font-mono">
                    <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800">
                      {ev.evidence_snapshot_hash.slice(0, 12)}...
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => setSelectedEval(ev)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-indigo-900/60 hover:text-indigo-200 text-slate-300 rounded border border-slate-700/60 transition-colors inline-flex items-center space-x-1"
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
