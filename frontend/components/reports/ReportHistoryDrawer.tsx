"use me";
"use client";

import React, { useEffect, useState } from "react";
import { ReportRecord } from "@/types/api";
import { api } from "@/lib/api";
import { Clock, FileText, ChevronRight, RefreshCw, X, ShieldAlert } from "lucide-react";

interface ReportHistoryDrawerProps {
  modelId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectReport: (report: ReportRecord) => void;
}

export function ReportHistoryDrawer({
  modelId,
  isOpen,
  onClose,
  onSelectReport,
}: ReportHistoryDrawerProps) {
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    if (!modelId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.listReportsByModel(modelId);
      setReports(data);
    } catch (err: any) {
      setError(err.message || "Failed to load report history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && modelId) {
      fetchHistory();
    }
  }, [isOpen, modelId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col justify-between shadow-2xl overflow-y-auto">
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">Report History Timeline</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Model: <code className="font-mono text-indigo-300">{modelId}</code></span>
            <button
              onClick={fetchHistory}
              className="flex items-center gap-1 text-slate-300 hover:text-white transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400 text-sm">Loading historical report snapshots...</div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          ) : reports.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              No historical report snapshots found for this model.
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  onClick={() => {
                    onSelectReport(rep);
                    onClose();
                  }}
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-indigo-500/50 hover:bg-slate-800/40 cursor-pointer transition group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="text-sm font-bold text-slate-200 group-hover:text-indigo-300 transition">
                        {rep.title}
                      </div>
                      <div className="text-xs font-mono text-slate-400">
                        Snapshot ID: {rep.id}
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition" />
                  </div>

                  <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      rep.disposition === "HIGH" ? "bg-emerald-500/10 text-emerald-400" :
                      rep.disposition === "RESTRICTED" ? "bg-rose-500/10 text-rose-400" : "bg-amber-500/10 text-amber-400"
                    }`}>
                      {rep.disposition}
                    </span>
                    <span className="font-mono">{rep.completeness_score}% Score</span>
                    <span>{new Date(rep.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="pt-6 border-t border-slate-800 text-xs text-slate-500 text-center">
          AEGIS-X Immutable Database Snapshots (<code className="font-mono">public.reports</code>)
        </div>
      </div>
    </div>
  );
}
