import React from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  statusColor?: "emerald" | "amber" | "rose" | "indigo" | "purple" | "slate";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  statusColor = "indigo",
}) => {
  let borderTop = "border-t-indigo-500 text-indigo-400";
  let bgGlow = "hover:border-indigo-500/40";
  if (statusColor === "emerald") {
    borderTop = "border-t-emerald-500 text-emerald-400";
    bgGlow = "hover:border-emerald-500/40";
  } else if (statusColor === "amber") {
    borderTop = "border-t-amber-500 text-amber-400";
    bgGlow = "hover:border-amber-500/40";
  } else if (statusColor === "rose") {
    borderTop = "border-t-rose-500 text-rose-400";
    bgGlow = "hover:border-rose-500/40";
  } else if (statusColor === "purple") {
    borderTop = "border-t-purple-500 text-purple-400";
    bgGlow = "hover:border-purple-500/40";
  } else if (statusColor === "slate") {
    borderTop = "border-t-slate-600 text-slate-400";
    bgGlow = "hover:border-slate-700";
  }

  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-5 border-t-2 ${borderTop.split(" ")[0]} shadow-sm transition-colors ${bgGlow}`}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-medium">{title}</span>
        {icon && <div className={`p-1.5 rounded-lg bg-slate-950 border border-slate-800 ${borderTop.split(" ")[1]}`}>{icon}</div>}
      </div>
      <div className="mt-3 text-2xl font-bold text-slate-100 tracking-tight font-sans">{value}</div>
      {subtitle && <div className="mt-1 text-xs text-slate-400 font-medium truncate">{subtitle}</div>}
    </div>
  );
};

