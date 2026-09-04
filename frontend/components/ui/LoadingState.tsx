import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = "Loading reliability telemetry..." }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 className="w-7 h-7 text-cyan-400 animate-spin mb-3" />
      <span className="text-xs font-mono font-medium text-slate-400">{message}</span>
    </div>
  );
};
