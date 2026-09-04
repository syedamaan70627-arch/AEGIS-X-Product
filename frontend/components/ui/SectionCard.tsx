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
    <div className={`bg-[#151B23] border border-[#26303D] rounded-xl p-5 shadow-sm ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-[#26303D] gap-2">
        <div>
          <h3 className="text-sm sm:text-base font-bold text-[#F3F4F6] font-sans tracking-tight">{title}</h3>
          {subtitle && <p className="text-xs text-[#9CA3AF] mt-0.5 font-sans">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </div>
  );
};

