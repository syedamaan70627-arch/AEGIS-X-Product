"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

interface CopyButtonProps {
  text: string;
  className?: string;
  label?: string;
}

export const CopyButton: React.FC<CopyButtonProps> = ({ text, className = "", label }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      title="Copy to clipboard"
      className={`inline-flex items-center space-x-1.5 px-1.5 py-0.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors ${className}`}
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-[#22C55E] shrink-0" />
      ) : (
        <Copy className="w-3.5 h-3.5 text-[#9CA3AF] hover:text-[#3B82F6] shrink-0" />
      )}
      {label && (
        <span className={`text-[10px] font-medium ${copied ? "text-emerald-400" : ""}`}>
          {copied ? "Copied!" : label}
        </span>
      )}
    </button>
  );
};
