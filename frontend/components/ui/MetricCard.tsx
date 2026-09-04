import React from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  statusColor?: "emerald" | "amber" | "rose" | "steel" | "slate";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  statusColor = "steel",
}) => {
  let borderTop = "border-t-[#3B82F6] text-[#3B82F6]";
  if (statusColor === "emerald") {
    borderTop = "border-t-[#22C55E] text-[#22C55E]";
  } else if (statusColor === "amber") {
    borderTop = "border-t-[#F59E0B] text-[#F59E0B]";
  } else if (statusColor === "rose") {
    borderTop = "border-t-[#EF4444] text-[#EF4444]";
  } else if (statusColor === "slate") {
    borderTop = "border-t-[#64748B] text-[#9CA3AF]";
  }

  return (
    <div className={`bg-[#151B23] border border-[#26303D] rounded-xl p-5 border-t-2 ${borderTop.split(" ")[0]} shadow-sm transition-all hover:border-[#3B82F6]/40`}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-sans uppercase tracking-wider text-[#9CA3AF] font-semibold">{title}</span>
        {icon && <div className={`p-1.5 rounded-lg bg-[#0F141B] border border-[#26303D] ${borderTop.split(" ")[1]}`}>{icon}</div>}
      </div>
      <div className="mt-3 text-2xl font-bold text-[#F3F4F6] tracking-tight font-mono tabular-nums">{value}</div>
      {subtitle && <div className="mt-1 text-xs text-[#9CA3AF] font-sans truncate">{subtitle}</div>}
    </div>
  );
};

