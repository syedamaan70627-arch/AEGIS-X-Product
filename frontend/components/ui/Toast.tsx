import React, { useEffect } from "react";
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
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

  let icon = <Info className="w-4 h-4 text-indigo-400" />;
  let style = "bg-slate-900 border-slate-800 text-slate-200";

  if (toast.type === "success") {
    icon = <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    style = "bg-emerald-950/90 border-emerald-800/80 text-emerald-100";
  } else if (toast.type === "error") {
    icon = <AlertTriangle className="w-4 h-4 text-rose-400" />;
    style = "bg-rose-950/90 border-rose-800/80 text-rose-100";
  }

  return (
    <div className={`p-4 rounded-xl border shadow-xl flex items-start space-x-3 text-xs max-w-sm ${style}`}>
      <div className="shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1">
        <div className="font-semibold">{toast.title}</div>
        {toast.message && <div className="mt-0.5 opacity-90">{toast.message}</div>}
      </div>
      <button onClick={() => onClose(toast.id)} className="opacity-70 hover:opacity-100">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
