import React from "react";
import { RiskIndicator } from "./RiskIndicator";

interface ReliabilitySummaryProps {
  oodRisk?: number | null;
  uncertaintyRisk?: number | null;
  driftRisk?: number | null;
  fusedRisk?: number | null;
}

export const ReliabilitySummary: React.FC<ReliabilitySummaryProps> = ({
  oodRisk,
  uncertaintyRisk,
  driftRisk,
  fusedRisk,
}) => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <RiskIndicator label="OOD Risk" value={oodRisk} />
        <RiskIndicator label="Uncertainty Risk" value={uncertaintyRisk} />
        <RiskIndicator label="Drift Risk" value={driftRisk} />
        <RiskIndicator label="Fused Risk Score" value={fusedRisk} />
      </div>
      <p className="text-[11px] text-slate-400 font-mono">
        Note: Individual risk detectors are preserved independently. Multi-signal fusion integrates detectors pre-label.
      </p>
    </div>
  );
};
