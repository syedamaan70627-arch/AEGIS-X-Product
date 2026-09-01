"use client";

import React from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { getEnvConfig } from "@/lib/config";
import { AlertTriangle, Server, Key, Globe } from "lucide-react";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const cfg = getEnvConfig();

  if (cfg.isVercel && !cfg.isValid) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-slate-100 font-sans antialiased">
        <div className="max-w-xl w-full bg-slate-900 border border-rose-800/80 rounded-2xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center space-x-3 text-rose-400 font-bold text-lg border-b border-slate-800 pb-4">
            <AlertTriangle className="w-6 h-6 shrink-0 text-rose-500" />
            <span>Vercel Deployment Configuration Error</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            This Vercel deployment is missing required public production configuration. AEGIS-X fails closed on Vercel deployments and will not silently fall back to local-development mode or localhost.
          </p>

          <div className="p-4 bg-slate-950 border border-rose-900/50 rounded-xl space-y-2 text-xs font-mono text-rose-300">
            <div className="font-bold text-slate-300 flex items-center gap-2">
              <span>Missing / Invalid Environment Variables:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-rose-400 font-semibold">
              {cfg.missingVars.map((v) => (
                <li key={v}>{v}</li>
              ))}
            </ul>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-[11px] text-slate-400 space-y-2 font-mono">
            <div className="font-semibold text-slate-300">Required Vercel Production Environment Scope:</div>
            <div className="flex items-center space-x-2 text-indigo-300">
              <Globe className="w-3.5 h-3.5 shrink-0 text-indigo-400" />
              <span>NEXT_PUBLIC_API_BASE_URL: https://aegis-x-product-production.up.railway.app/api/v1</span>
            </div>
            <div className="flex items-center space-x-2 text-indigo-300">
              <Server className="w-3.5 h-3.5 shrink-0 text-indigo-400" />
              <span>NEXT_PUBLIC_SUPABASE_URL: Your Supabase Project URL</span>
            </div>
            <div className="flex items-center space-x-2 text-indigo-300">
              <Key className="w-3.5 h-3.5 shrink-0 text-indigo-400" />
              <span>NEXT_PUBLIC_SUPABASE_ANON_KEY: Your Supabase Anon Public Key</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-600 selection:text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-8 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
};

