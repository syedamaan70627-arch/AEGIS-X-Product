import React, { useEffect } from "react";
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info" | "warning";
  title: string;
  message?: string;
}

interface ToastProps {
  toast: ToastMessage;
  onClose: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ toast, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(toast.id);
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onClose]);

  let icon = <Info className="w-4 h-4 text-[#3B82F6]" />;
  let borderClass = "border-[#26303D]";

  if (toast.type === "success") {
    icon = <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />;
    borderClass = "border-[#22C55E]/40";
  } else if (toast.type === "error") {
    icon = <AlertTriangle className="w-4 h-4 text-[#EF4444]" />;
    borderClass = "border-[#EF4444]/40";
  } else if (toast.type === "warning") {
    icon = <AlertTriangle className="w-4 h-4 text-[#F59E0B]" />;
    borderClass = "border-[#F59E0B]/40";
  }

  return (
    <div
      className={`flex items-start justify-between p-4 bg-[#151B23] border ${borderClass} rounded-xl shadow-2xl space-x-3 text-xs font-sans max-w-md w-full animate-in fade-in slide-in-from-top-2 duration-200`}
    >
      <div className="flex items-start space-x-3 shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1 space-y-0.5">
        <h4 className="font-semibold text-[#F3F4F6] font-sans">{toast.title}</h4>
        <p className="text-[#9CA3AF] leading-relaxed font-sans">{toast.message}</p>
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className="text-[#6B7280] hover:text-[#F3F4F6] transition-colors p-1"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
