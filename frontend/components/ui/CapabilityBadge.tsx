import React from "react";
import { CapabilityStatusDetail } from "@/types/api";

interface CapabilityBadgeProps {
  label: string;
  capability?: CapabilityStatusDetail;
}

export const CapabilityBadge: React.FC<CapabilityBadgeProps> = ({ label, capability }) => {
  const status = capability?.status || "NOT_AVAILABLE";

  let badgeStyle = "bg-[#151B23] text-[#9CA3AF] border-[#26303D]";
  if (status === "READY") {
    badgeStyle = "bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/30";
  } else if (status === "REQUIRES_SETUP") {
    badgeStyle = "bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30";
  }

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border font-sans ${badgeStyle}`}>
      <span className="text-sm font-medium text-[#F3F4F6]">{label}</span>
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold px-2 py-0.5 rounded border">{status}</span>
      </div>
    </div>
  );
};
