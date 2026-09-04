"use client";

import React from "react";
import { ECRGGovernanceAction } from "@/types/api";
import { AlertOctagon, Eye, PauseCircle, ShieldCheck } from "lucide-react";

interface GovernanceBadgeProps {
  action: ECRGGovernanceAction;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function GovernanceBadge({ action, size = "md", showLabel = true }: GovernanceBadgeProps) {
  const configs: Record<
    ECRGGovernanceAction,
    {
      label: string;
      subtext: string;
      color: string;
      bg: string;
      border: string;
      icon: React.ReactNode;
    }
  > = {
    CONTINUE: {
      label: "CONTINUE",
      subtext: "Automated Execution Allowed",
      color: "text-[#22C55E]",
      bg: "bg-[#22C55E]/10",
      border: "border-[#22C55E]/30",
      icon: <ShieldCheck className="w-4 h-4 text-[#22C55E] shrink-0" />,
    },
    WATCH: {
      label: "WATCH",
      subtext: "Increased Monitoring Enforced",
      color: "text-[#F59E0B]",
      bg: "bg-[#F59E0B]/10",
      border: "border-[#F59E0B]/30",
      icon: <Eye className="w-4 h-4 text-[#F59E0B] shrink-0" />,
    },
    DEFER: {
      label: "DEFER",
      subtext: "Manual Review Required",
      color: "text-[#F59E0B]",
      bg: "bg-[#F59E0B]/10",
      border: "border-[#F59E0B]/30",
      icon: <PauseCircle className="w-4 h-4 text-[#F59E0B] shrink-0" />,
    },
    ESCALATE: {
      label: "ESCALATE",
      subtext: "Automated Action Disabled",
      color: "text-[#EF4444]",
      bg: "bg-[#EF4444]/10",
      border: "border-[#EF4444]/30",
      icon: <AlertOctagon className="w-4 h-4 text-[#EF4444] shrink-0" />,
    },
  };

  const cfg = configs[action] || configs.ESCALATE;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1.5",
    md: "px-3 py-1.5 text-xs gap-2",
    lg: "px-4 py-2 text-sm gap-2.5 font-medium",
  };

  return (
    <div
      className={`inline-flex items-center rounded-lg border font-sans ${cfg.bg} ${cfg.border} ${cfg.color} ${sizeClasses[size]}`}
      title={`${cfg.label}: ${cfg.subtext}`}
    >
      {cfg.icon}
      <span className="font-bold tracking-wider font-sans">{cfg.label}</span>
      {showLabel && size !== "sm" && <span className="opacity-80 font-sans hidden sm:inline">({cfg.subtext})</span>}
    </div>
  );
}
