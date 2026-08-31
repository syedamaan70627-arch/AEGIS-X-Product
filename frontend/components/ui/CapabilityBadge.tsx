import React from "react";
import { CapabilityStatusDetail } from "@/types/api";

interface CapabilityBadgeProps {
  label: string;
  capability?: CapabilityStatusDetail;
}

export const CapabilityBadge: React.FC<CapabilityBadgeProps> = ({ label, capability }) => {
  const status = capability?.status || "NOT_AVAILABLE";

  let badgeStyle = "bg-slate-900 text-slate-400 border-slate-800";
  if (status === "READY") {
    badgeStyle = "bg-emerald-950/60 text-emerald-400 border-emerald-800/60";
  } else if (status === "REQUIRES_SETUP") {
    badgeStyle = "bg-amber-950/60 text-amber-400 border-amber-800/60";
  }

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${badgeStyle}`}>
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold px-2 py-0.5 rounded border">{status}</span>
      </div>
    </div>
  );
};
