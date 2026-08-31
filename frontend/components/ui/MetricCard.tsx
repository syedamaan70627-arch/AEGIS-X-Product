import React from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  statusColor?: "emerald" | "amber" | "rose" | "indigo" | "slate";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  statusColor = "indigo",
}) => {
  let borderTop = "border-t-indigo-500";
  if (statusColor === "emerald") borderTop = "border-t-emerald-500";
  if (statusColor === "amber") borderTop = "border-t-amber-500";
  if (statusColor === "rose") borderTop = "border-t-rose-500";
  if (statusColor === "slate") borderTop = "border-t-slate-600";

  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-5 border-t-2 ${borderTop} shadow-lg shadow-slate-950/40`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div className="mt-3 text-2xl font-bold text-slate-100 tracking-tight">{value}</div>
      {subtitle && <div className="mt-1 text-xs text-slate-400 font-medium">{subtitle}</div>}
    </div>
  );
};
