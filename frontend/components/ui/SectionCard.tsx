import React from "react";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const SectionCard: React.FC<SectionCardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = "",
}) => {
  return (
    <div className={`bg-[#0e131f] border border-slate-800/80 rounded-xl p-5 shadow-sm ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-slate-800/80 gap-2">
        <div>
          <h3 className="text-sm sm:text-base font-bold text-slate-100 tracking-tight">{title}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5 font-mono">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </div>
  );
};

