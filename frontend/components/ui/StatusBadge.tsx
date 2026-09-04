import React from "react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const upper = status.toUpperCase();

  let colorClasses = "bg-[#1A222C] text-[#9CA3AF] border-[#26303D]";
  let dotColor = "bg-[#6B7280]";
  if (upper === "READY" || upper === "OPERATIONAL" || upper === "HEALTHY" || upper === "OK" || upper === "FITTED" || upper === "COMPLETED") {
    colorClasses = "bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/30";
    dotColor = "bg-[#22C55E]";
  } else if (upper === "REQUIRES_SETUP" || upper === "DEGRADED" || upper === "WARNING") {
    colorClasses = "bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30";
    dotColor = "bg-[#F59E0B]";
  } else if (upper === "NOT_AVAILABLE" || upper === "DISABLED" || upper === "UNCONFIGURED") {
    colorClasses = "bg-[#1A222C] text-[#9CA3AF] border-[#26303D]";
    dotColor = "bg-[#6B7280]";
  } else if (upper === "ERROR" || upper === "FAILED" || upper === "HIGH_RISK") {
    colorClasses = "bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/30";
    dotColor = "bg-[#EF4444]";
  }

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-sans font-medium border ${colorClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{status}</span>
    </span>
  );
};

