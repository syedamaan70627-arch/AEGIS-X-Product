import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = "Loading reliability telemetry..." }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center font-sans">
      <Loader2 className="w-7 h-7 text-[#3B82F6] animate-spin mb-3" />
      <span className="text-xs font-sans font-medium text-[#9CA3AF]">{message}</span>
    </div>
  );
};
