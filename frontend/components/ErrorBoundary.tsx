"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught UI Error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-rose-950/40 border border-rose-900/60 rounded-xl text-left max-w-2xl mx-auto my-12">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-base font-bold text-rose-200">Application Error Encountered</h3>
              <p className="mt-1 text-xs text-rose-300/90">
                An unhandled UI error occurred. Please refresh or navigate back to the dashboard overview.
              </p>
              <pre className="mt-3 p-3 bg-slate-950 rounded border border-rose-900/50 text-[11px] font-mono text-rose-400 overflow-x-auto">
                {this.state.error?.message || "Unknown client error"}
              </pre>
              <button
                onClick={() => window.location.assign("/dashboard")}
                className="mt-4 px-4 py-2 text-xs font-semibold bg-rose-900/80 hover:bg-rose-900 text-rose-100 rounded-lg transition-colors"
              >
                Reload Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
