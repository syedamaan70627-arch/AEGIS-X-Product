import React from "react";
import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Backend Error Encountered",
  message,
  onRetry,
}) => {
  return (
    <div className="p-6 bg-rose-950/40 border border-rose-900/60 rounded-xl text-left">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
          <p className="mt-1 text-sm text-rose-300/80 font-mono text-xs whitespace-pre-wrap">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-4 px-3 py-1.5 text-xs font-medium bg-rose-900/60 hover:bg-rose-900 text-rose-200 border border-rose-700/60 rounded-md transition-colors"
            >
              Retry Operation
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
