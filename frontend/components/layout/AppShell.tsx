"use client";

import React, { useState, Suspense } from "react";
import { usePathname } from "next/navigation";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { ToastProvider } from "@/components/providers/ToastProvider";
import { ProtectedRoute } from "@/components/providers/ProtectedRoute";
import { getEnvConfig } from "@/lib/config";
import { AlertTriangle, Server, Key, Globe } from "lucide-react";
import { LoadingState } from "@/components/ui/LoadingState";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const pathname = usePathname();
  const cfg = getEnvConfig();

  const isPublicAuthPage = pathname === "/login" || pathname === "/signup";

  if (cfg.isVercel && !cfg.isValid) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center p-6 text-[#F3F4F6] font-sans antialiased">
        <div className="max-w-xl w-full bg-[#151B23] border border-[#26303D] rounded-2xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center space-x-3 text-rose-400 font-bold text-lg border-b border-[#26303D] pb-4">
            <AlertTriangle className="w-6 h-6 shrink-0 text-rose-500" />
            <span>Vercel Deployment Configuration Error</span>
          </div>

          <p className="text-xs text-[#9CA3AF] leading-relaxed">
            This Vercel deployment is missing required public production configuration. AEGIS-X fails closed on Vercel deployments and will not silently fall back to local-development mode or localhost.
          </p>

          <div className="p-4 bg-[#0F141B] border border-rose-900/50 rounded-xl space-y-2 text-xs font-mono text-rose-300">
            <div className="font-bold text-[#F3F4F6] flex items-center gap-2">
              <span>Missing / Invalid Environment Variables:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-rose-400 font-semibold">
              {cfg.missingVars.map((v) => (
                <li key={v}>{v}</li>
              ))}
            </ul>
          </div>

          <div className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl text-[11px] text-[#9CA3AF] space-y-2 font-mono">
            <div className="font-semibold text-[#F3F4F6]">Required Vercel Production Environment Scope:</div>
            <div className="flex items-center space-x-2 text-[#9CA3AF]">
              <Globe className="w-3.5 h-3.5 shrink-0 text-[#3B82F6]" />
              <span>NEXT_PUBLIC_API_BASE_URL: https://aegis-x-product-production.up.railway.app/api/v1</span>
            </div>
            <div className="flex items-center space-x-2 text-[#9CA3AF]">
              <Server className="w-3.5 h-3.5 shrink-0 text-[#3B82F6]" />
              <span>NEXT_PUBLIC_SUPABASE_URL: Your Supabase Project URL</span>
            </div>
            <div className="flex items-center space-x-2 text-[#9CA3AF]">
              <Key className="w-3.5 h-3.5 shrink-0 text-[#3B82F6]" />
              <span>NEXT_PUBLIC_SUPABASE_ANON_KEY: Your Supabase Anon Public Key</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isPublicAuthPage) {
    return (
      <ToastProvider>
        <Suspense fallback={<LoadingState message="Loading..." />}>
          <ProtectedRoute>{children}</ProtectedRoute>
        </Suspense>
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <div className="flex min-h-screen bg-[#0B0F14] text-[#F3F4F6] font-sans antialiased selection:bg-[#3B82F6] selection:text-white">
        <Sidebar isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
        <div className="flex-1 flex flex-col min-w-0">
          <Header onOpenMobileNav={() => setMobileNavOpen(true)} />
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            <Suspense fallback={<LoadingState message="Loading..." />}>
              <ProtectedRoute>{children}</ProtectedRoute>
            </Suspense>
          </main>
        </div>
      </div>
    </ToastProvider>
  );
};
