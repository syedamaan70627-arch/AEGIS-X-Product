import React from "react";

interface RiskIndicatorProps {
  label: string;
  value?: number | null;
  status?: string;
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({ label, value, status }) => {
  if (value === undefined || value === null) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-xs font-semibold uppercase text-slate-400">{label}</div>
        <div className="mt-2 text-sm font-medium text-slate-500">Unavailable</div>
        <div className="mt-1 text-xs text-slate-400">Signal not computed</div>
      </div>
    );
  }

  const score = Math.max(0, Math.min(1, value));
  const percentage = (score * 100).toFixed(1);

  let riskLevel = "Low";
  let barColor = "bg-emerald-500";
  let textColor = "text-emerald-400";
  let bgStyle = "bg-emerald-950/30 border-emerald-900/50";

  if (score >= 0.7) {
    riskLevel = "High";
    barColor = "bg-rose-500";
    textColor = "text-rose-400";
    bgStyle = "bg-rose-950/30 border-rose-900/50";
  } else if (score >= 0.35) {
    riskLevel = "Moderate";
    barColor = "bg-amber-500";
    textColor = "text-amber-400";
    bgStyle = "bg-amber-950/30 border-amber-900/50";
  }

  return (
    <div className={`border rounded-lg p-4 ${bgStyle}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">{label}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded border border-current ${textColor}`}>
          {riskLevel} Risk
        </span>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-xl font-bold text-slate-100">{percentage}%</span>
        <span className="text-xs text-slate-400 font-mono">score: {score.toFixed(4)}</span>
      </div>
      <div className="mt-2 w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
        <div className={`h-full ${barColor} transition-all duration-500`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
};
