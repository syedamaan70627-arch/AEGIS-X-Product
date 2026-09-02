import React, { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = "Confirm Action",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onCancel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      onClick={onCancel}
      className="fixed inset-0 z-50 bg-slate-950/80 flex items-center justify-center p-4"
      aria-modal="true"
      role="dialog"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150"
      >
        <div className="flex items-center space-x-3 text-rose-400">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <h3 className="text-sm font-bold text-slate-100">{title}</h3>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">{message}</p>
        <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800/80">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2 text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white rounded-lg shadow-md transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

