import React from "react";

interface PageHeaderProps {
  title: string;
  description: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  actions,
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-8 border-b border-slate-800 gap-4">
      <div>
        <div className="flex items-center space-x-3">
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">{title}</h1>
          {badge}
        </div>
        <p className="mt-1 text-sm text-slate-400 max-w-2xl">{description}</p>
      </div>
      {actions && <div className="flex items-center space-x-3">{actions}</div>}
    </div>
  );
};
