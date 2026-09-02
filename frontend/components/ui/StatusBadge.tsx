import React from "react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const upper = status.toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";
  if (upper === "READY" || upper === "OPERATIONAL" || upper === "HEALTHY" || upper === "OK" || upper === "FITTED" || upper === "COMPLETED") {
    colorClasses = "bg-emerald-950/60 text-emerald-300 border-emerald-800/60";
    dotColor = "bg-emerald-400";
  } else if (upper === "REQUIRES_SETUP" || upper === "DEGRADED" || upper === "WARNING") {
    colorClasses = "bg-amber-950/60 text-amber-300 border-amber-800/60";
    dotColor = "bg-amber-400";
  } else if (upper === "NOT_AVAILABLE" || upper === "DISABLED" || upper === "UNCONFIGURED") {
    colorClasses = "bg-slate-900 text-slate-400 border-slate-800";
    dotColor = "bg-slate-500";
  } else if (upper === "ERROR" || upper === "FAILED" || upper === "HIGH_RISK") {
    colorClasses = "bg-rose-950/60 text-rose-300 border-rose-800/60";
    dotColor = "bg-rose-400";
  }

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium border ${colorClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{status}</span>
    </span>
  );
};

