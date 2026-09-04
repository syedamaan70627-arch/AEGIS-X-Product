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
  if (statusColor === "emerald") {
    borderTop = "border-t-emerald-500 text-emerald-400";
  } else if (statusColor === "amber") {
    borderTop = "border-t-amber-500 text-amber-400";
  } else if (statusColor === "rose") {
    borderTop = "border-t-rose-500 text-rose-400";
  } else if (statusColor === "purple") {
    borderTop = "border-t-cyan-500 text-cyan-400";
  } else if (statusColor === "slate") {
    borderTop = "border-t-slate-700 text-slate-400";
  }

  return (
    <div className={`bg-[#0e131f] border border-slate-800/80 rounded-xl p-5 border-t-2 ${borderTop.split(" ")[0]} shadow-sm transition-all hover:border-slate-700/80`}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">{title}</span>
        {icon && <div className={`p-1.5 rounded-lg bg-[#080c14] border border-slate-800/80 ${borderTop.split(" ")[1]}`}>{icon}</div>}
      </div>
      <div className="mt-3 text-2xl font-bold text-slate-100 tracking-tight font-mono tabular-nums">{value}</div>
      {subtitle && <div className="mt-1 text-xs text-slate-400 font-sans truncate">{subtitle}</div>}
    </div>
  );
};

