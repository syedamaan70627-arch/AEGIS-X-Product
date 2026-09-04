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
    <div className="flex flex-col items-center justify-center p-12 border border-[#26303D] rounded-xl bg-[#151B23] text-center shadow-sm font-sans">
      <div className="p-3 bg-[#0F141B] rounded-xl text-[#3B82F6] mb-4 border border-[#26303D]">
        {icon || <FolderPlus className="w-8 h-8" />}
      </div>
      <h3 className="text-base font-bold text-[#F3F4F6] mb-1 font-sans">{title}</h3>
      <p className="text-xs text-[#9CA3AF] max-w-md mb-6 leading-relaxed font-sans">{description}</p>
      {actionText && actionHref && (
        <Link
          href={actionHref}
          className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-[#3B82F6] hover:bg-[#2563EB] rounded-lg shadow-sm transition-colors font-sans"
        >
          {actionText}
        </Link>
      )}
    </div>
  );
};
