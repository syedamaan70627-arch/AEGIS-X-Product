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
      color: "text-emerald-400",
      bg: "bg-emerald-950/50",
      border: "border-emerald-800/50",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />,
    },
    WATCH: {
      label: "WATCH",
      subtext: "Increased Monitoring Enforced",
      color: "text-amber-400",
      bg: "bg-amber-950/50",
      border: "border-amber-800/50",
      icon: <Eye className="w-4 h-4 text-amber-400 shrink-0" />,
    },
    DEFER: {
      label: "DEFER",
      subtext: "Manual Review Required",
      color: "text-orange-400",
      bg: "bg-orange-950/50",
      border: "border-orange-800/50",
      icon: <PauseCircle className="w-4 h-4 text-orange-400 shrink-0" />,
    },
    ESCALATE: {
      label: "ESCALATE",
      subtext: "Automated Action Disabled",
      color: "text-rose-400",
      bg: "bg-rose-950/50",
      border: "border-rose-800/50",
      icon: <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0" />,
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
      className={`inline-flex items-center rounded-lg border font-mono ${cfg.bg} ${cfg.border} ${cfg.color} ${sizeClasses[size]}`}
      title={`${cfg.label}: ${cfg.subtext}`}
    >
      {cfg.icon}
      <span className="font-bold tracking-wider">{cfg.label}</span>
      {showLabel && size !== "sm" && <span className="opacity-80 font-sans hidden sm:inline">({cfg.subtext})</span>}
    </div>
  );
}
