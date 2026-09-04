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
    <div className="pb-6 mb-8 border-b border-[#26303D]">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center space-x-1.5 text-xs text-[#9CA3AF] mb-2 font-sans" aria-label="Breadcrumb">
          <Link href="/dashboard" className="hover:text-[#3B82F6] transition-colors">
            AEGIS-X
          </Link>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              <ChevronRight className="w-3.5 h-3.5 text-[#6B7280] shrink-0" />
              {crumb.href ? (
                <Link href={crumb.href} className="hover:text-[#F3F4F6] transition-colors">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-[#F3F4F6] font-medium">{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          {icon && (
            <div className="p-2.5 rounded-xl bg-[#151B23] border border-[#26303D] text-[#3B82F6] shrink-0 mt-0.5 shadow-sm">
              {icon}
            </div>
          )}
          <div>
            <div className="flex items-center space-x-3 flex-wrap gap-y-1">
              <h1 className="text-xl sm:text-2xl font-bold text-[#F3F4F6] tracking-tight font-sans">{title}</h1>
              {badge}
            </div>
            <p className="mt-1 text-xs sm:text-sm text-[#9CA3AF] max-w-3xl leading-relaxed font-sans">{description}</p>
          </div>
        </div>
        {actions && <div className="flex items-center space-x-3 shrink-0">{actions}</div>}
      </div>
    </div>
  );
};

