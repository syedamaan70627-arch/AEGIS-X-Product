import React from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

export interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  breadcrumbs?: Breadcrumb[];
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  icon,
  breadcrumbs,
  badge,
  actions,
}) => {
  return (
    <div className="pb-6 mb-8 border-b border-slate-800/80">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center space-x-1.5 text-xs text-slate-400 mb-2 font-mono" aria-label="Breadcrumb">
          <Link href="/dashboard" className="hover:text-cyan-400 transition-colors">
            AEGIS-X
          </Link>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
              {crumb.href ? (
                <Link href={crumb.href} className="hover:text-slate-200 transition-colors">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-slate-300 font-medium">{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          {icon && (
            <div className="p-2.5 rounded-xl bg-[#0e131f] border border-slate-800/80 text-cyan-400 shrink-0 mt-0.5 shadow-sm">
              {icon}
            </div>
          )}
          <div>
            <div className="flex items-center space-x-3 flex-wrap gap-y-1">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-100 tracking-tight">{title}</h1>
              {badge}
            </div>
            <p className="mt-1 text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">{description}</p>
          </div>
        </div>
        {actions && <div className="flex items-center space-x-3 shrink-0">{actions}</div>}
      </div>
    </div>
  );
};

