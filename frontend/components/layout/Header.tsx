"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { ReadinessResponse, SystemStatus, UserMe } from "@/types/api";
import { Database, LogOut, Server, Settings, Shield, User } from "lucide-react";

import { isVercelEnvironment } from "@/lib/config";

export const Header: React.FC = () => {
  const router = useRouter();
  const { user, signOut, isConfigured } = useAuth();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);
  const [showMenu, setShowMenu] = useState(false);

  const isVercel = isVercelEnvironment();

  useEffect(() => {
    async function loadHeaderTelemetry() {
      try {
        const [st, rd, meRes] = await Promise.all([
          api.getStatus().catch(() => null),
          api.getReadiness().catch(() => null),
          api.getUserMe().catch(() => null),
        ]);
        if (st) setStatus(st);
        if (rd) setReadiness(rd);
        if (meRes) setMe(meRes);
      } catch (_) {}
    }
    loadHeaderTelemetry();
  }, []);

  const handleSignOut = async () => {
    await signOut();
    setShowMenu(false);
    router.push("/login");
  };

  const isConnected = status !== null;

  const dbLabel = status?.database_backend
    ? status.database_backend.toUpperCase()
    : isVercel
    ? "SUPABASE PG"
    : "SQLITE";

  const storageLabel = status?.storage_backend
    ? status.storage_backend.toUpperCase()
    : isVercel
    ? "SUPABASE STORAGE"
    : "LOCAL";

  const userLabel = user?.email || me?.user_id || (isVercel ? "Unauthenticated" : "local_dev_user");
  const menuUserTitle = user?.email || (isVercel ? "Unauthenticated Session" : "Local Development User");
  const authModeLabel = isConfigured ? "Supabase Auth" : isVercel ? "Vercel Session" : "Local Context";

  return (
    <header className="h-16 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-4">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-400" />
          AI Reliability Command Center
        </span>
      </div>

      <div className="flex items-center space-x-4 text-xs">
        {/* Backend Connection Indicator */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
            }`}
          />
          <span className="text-slate-400">API:</span>
          <span className="font-semibold text-slate-200">
            {isConnected ? "Connected" : "Unavailable"}
          </span>
        </div>

        {/* Database & Storage Badges */}
        <div className="hidden md:flex items-center space-x-2 text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-mono text-slate-300 uppercase">{dbLabel}</span>
          <span className="text-slate-600">|</span>
          <span className="font-mono text-slate-300 uppercase">{storageLabel}</span>
        </div>

        {/* User Account Menu Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-200 font-mono transition-colors"
          >
            <User className="w-3.5 h-3.5 text-indigo-400" />
            <span className="max-w-[120px] truncate">{userLabel}</span>
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-2 z-50 text-xs">
              <div className="px-4 py-2 border-b border-slate-800 text-slate-400">
                <div className="font-semibold text-slate-200 truncate">{menuUserTitle}</div>
                <div className="text-[11px] font-mono mt-0.5">
                  Auth Mode: {authModeLabel}
                </div>
              </div>


              <Link
                href="/settings"
                onClick={() => setShowMenu(false)}
                className="flex items-center space-x-2 px-4 py-2 text-slate-300 hover:bg-slate-800 transition-colors"
              >
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Account & Settings</span>
              </Link>

              <button
                onClick={handleSignOut}
                className="w-full flex items-center space-x-2 px-4 py-2 text-rose-400 hover:bg-slate-800 transition-colors text-left"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
