import React from "react";

interface RiskIndicatorProps {
  label: string;
  value?: number | null;
  status?: string;
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({ label, value, status }) => {
  if (value === undefined || value === null) {
    return (
      <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm">
        <div className="text-[11px] font-sans font-semibold uppercase tracking-wider text-[#9CA3AF]">{label}</div>
        <div className="mt-3 text-sm font-medium text-[#6B7280]">Unavailable</div>
        <div className="mt-1 text-[11px] text-[#6B7280] font-sans">Signal not computed</div>
      </div>
    );
  }

  const score = Math.max(0, Math.min(1, value));
  const percentage = (score * 100).toFixed(1);

  let riskLevel = "Low";
  let barColor = "bg-[#22C55E]";
  let textColor = "text-[#22C55E]";
  let badgeBg = "bg-[#22C55E]/10 border-[#22C55E]/30";

  if (score >= 0.7) {
    riskLevel = "High";
    barColor = "bg-[#EF4444]";
    textColor = "text-[#EF4444]";
    badgeBg = "bg-[#EF4444]/10 border-[#EF4444]/30";
  } else if (score >= 0.35) {
    riskLevel = "Moderate";
    barColor = "bg-[#F59E0B]";
    textColor = "text-[#F59E0B]";
    badgeBg = "bg-[#F59E0B]/10 border-[#F59E0B]/30";
  }

  // Label specific signal accent line
  const isOOD = label.toLowerCase().includes("ood");
  const isUncertainty = label.toLowerCase().includes("uncertainty");
  const isDrift = label.toLowerCase().includes("drift");
  const isFused = label.toLowerCase().includes("fused");

  let signalBadge = null;
  if (isOOD) signalBadge = <span className="text-[10px] font-sans uppercase px-1.5 py-0.5 rounded bg-[#0F141B] text-[#9CA3AF] border border-[#26303D]">OOD</span>;
  if (isUncertainty) signalBadge = <span className="text-[10px] font-sans uppercase px-1.5 py-0.5 rounded bg-[#0F141B] text-[#9CA3AF] border border-[#26303D]">Uncertainty</span>;
  if (isDrift) signalBadge = <span className="text-[10px] font-sans uppercase px-1.5 py-0.5 rounded bg-[#0F141B] text-[#9CA3AF] border border-[#26303D]">Drift</span>;
  if (isFused) signalBadge = <span className="text-[10px] font-sans uppercase px-1.5 py-0.5 rounded bg-[#0F141B] text-[#9CA3AF] border border-[#26303D]">Fused</span>;

  return (
    <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {signalBadge}
          <span className="text-xs font-semibold uppercase tracking-wider text-[#F3F4F6] font-sans">{label}</span>
        </div>
        <span className={`text-[11px] font-sans font-semibold px-2 py-0.5 rounded border ${badgeBg} ${textColor}`}>
          {riskLevel} Risk
        </span>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold text-[#F3F4F6] font-mono tracking-tight tabular-nums">{percentage}%</span>
        <span className="text-[11px] text-[#9CA3AF] font-mono tabular-nums">score: {score.toFixed(4)}</span>
      </div>
      <div className="mt-2.5 w-full bg-[#0F141B] rounded-full h-1.5 overflow-hidden border border-[#26303D]">
        <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
};

