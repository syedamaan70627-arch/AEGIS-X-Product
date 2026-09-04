import React from "react";
import Link from "next/link";
import { FolderPlus } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  actionHref?: string;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  actionHref,
  icon,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 border border-slate-800/80 rounded-xl bg-[#0e131f] text-center shadow-sm">
      <div className="p-3 bg-[#080c14] rounded-xl text-cyan-400 mb-4 border border-slate-800/80">
        {icon || <FolderPlus className="w-8 h-8" />}
      </div>
      <h3 className="text-base font-bold text-slate-200 mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">{description}</p>
      {actionText && actionHref && (
        <Link
          href={actionHref}
          className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-sm transition-colors"
        >
          {actionText}
        </Link>
      )}
    </div>
  );
};
