import React from "react";

interface RiskIndicatorProps {
  label: string;
  value?: number | null;
  status?: string;
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({ label, value, status }) => {
  if (value === undefined || value === null) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 shadow-md">
        <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">{label}</div>
        <div className="mt-3 text-sm font-medium text-slate-500">Unavailable</div>
        <div className="mt-1 text-[11px] text-slate-400">Signal not computed</div>
      </div>
    );
  }

  const score = Math.max(0, Math.min(1, value));
  const percentage = (score * 100).toFixed(1);

  let riskLevel = "Low";
  let barColor = "bg-emerald-500";
  let textColor = "text-emerald-400";
  let bgStyle = "bg-emerald-950/30 border-emerald-800/50";

  if (score >= 0.7) {
    riskLevel = "High";
    barColor = "bg-rose-500";
    textColor = "text-rose-400";
    bgStyle = "bg-rose-950/30 border-rose-800/50";
  } else if (score >= 0.35) {
    riskLevel = "Moderate";
    barColor = "bg-amber-500";
    textColor = "text-amber-400";
    bgStyle = "bg-amber-950/30 border-amber-800/50";
  }

  // Label specific signal accent line
  const isOOD = label.toLowerCase().includes("ood");
  const isUncertainty = label.toLowerCase().includes("uncertainty");
  const isDrift = label.toLowerCase().includes("drift");
  const isFused = label.toLowerCase().includes("fused");

  let signalBadge = null;
  if (isOOD) signalBadge = <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">OOD</span>;
  if (isUncertainty) signalBadge = <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">Uncertainty</span>;
  if (isDrift) signalBadge = <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-800/60">Drift</span>;
  if (isFused) signalBadge = <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800/60">Fused</span>;

  return (
    <div className={`border rounded-xl p-4 shadow-sm transition-all ${bgStyle}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {signalBadge}
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">{label}</span>
        </div>
        <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border border-current ${textColor}`}>
          {riskLevel} Risk
        </span>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold text-slate-100 font-mono tracking-tight tabular-nums">{percentage}%</span>
        <span className="text-[11px] text-slate-400 font-mono tabular-nums">score: {score.toFixed(4)}</span>
      </div>
      <div className="mt-2.5 w-full bg-[#080c14] rounded-full h-2 overflow-hidden border border-slate-800/80 p-0.5">
        <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
};

