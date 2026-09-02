"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { ReadinessResponse, SystemStatus, UserMe } from "@/types/api";
import { Database, LogOut, Menu, Settings, Shield, User } from "lucide-react";
import { isVercelEnvironment } from "@/lib/config";

interface HeaderProps {
  onOpenMobileNav?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileNav }) => {
  const router = useRouter();
  const { user, signOut, isConfigured } = useAuth();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isVercel = isVercelEnvironment();

  useEffect(() => {
    async function loadHeaderTelemetry() {
      setLoading(true);
      try {
        const [st, _, meRes] = await Promise.all([
          api.getStatus().catch(() => null),
          api.getReadiness().catch(() => null),
          api.getUserMe().catch(() => null),
        ]);
        if (st) setStatus(st);
        if (meRes) setMe(meRes);
      } catch {
      } finally {
        setLoading(false);
      }
    }
    loadHeaderTelemetry();
  }, []);

  // Dropdown click-outside & Escape key handler
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowMenu(false);
      }
    };
    if (showMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [showMenu]);

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
    <header className="h-16 bg-slate-950 border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 select-none">
      <div className="flex items-center space-x-3">
        {onOpenMobileNav && (
          <button
            onClick={onOpenMobileNav}
            className="md:hidden text-slate-400 hover:text-slate-200 p-2 rounded-lg hover:bg-slate-900 border border-slate-800 transition-colors"
            aria-label="Open Navigation Drawer"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <span className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Shield className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="hidden sm:inline">AI Reliability Command Center</span>
          <span className="sm:hidden">AEGIS-X</span>
        </span>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4 text-xs">
        {/* Backend Connection Indicator */}
        <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-800/80 px-3 py-1.5 rounded-lg shadow-sm">
          {loading ? (
            <>
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-slate-400 font-mono hidden sm:inline">API:</span>
              <span className="font-mono font-medium text-amber-300">Connecting</span>
            </>
          ) : isConnected ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-slate-400 font-mono hidden sm:inline">API:</span>
              <span className="font-mono font-medium text-slate-200">Connected</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-slate-400 font-mono hidden sm:inline">API:</span>
              <span className="font-mono font-medium text-rose-300">Unavailable</span>
            </>
          )}
        </div>

        {/* Database & Storage Badges */}
        <div className="hidden lg:flex items-center space-x-2 text-slate-400 bg-slate-900/80 border border-slate-800/80 px-3 py-1.5 rounded-lg font-mono text-[11px]">
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-slate-300 font-semibold uppercase">{dbLabel}</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300 font-semibold uppercase">{storageLabel}</span>
        </div>

        {/* User Account Menu Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setShowMenu(!showMenu)}
            aria-expanded={showMenu}
            aria-label="User Account Menu"
            className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-200 font-mono text-xs transition-colors focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <User className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span className="max-w-[100px] sm:max-w-[140px] truncate">{userLabel}</span>
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-60 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-2 z-50 text-xs animate-in fade-in zoom-in-95 duration-100">
              <div className="px-4 py-2 border-b border-slate-800 text-slate-400">
                <div className="font-semibold text-slate-200 truncate">{menuUserTitle}</div>
                <div className="text-[10px] font-mono text-cyan-400 mt-0.5">
                  Auth Mode: {authModeLabel}
                </div>
              </div>

              <Link
                href="/settings"
                onClick={() => setShowMenu(false)}
                className="flex items-center space-x-2.5 px-4 py-2.5 text-slate-300 hover:bg-slate-800 transition-colors"
              >
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Account & Settings</span>
              </Link>

              <button
                type="button"
                onClick={handleSignOut}
                className="w-full flex items-center space-x-2.5 px-4 py-2.5 text-rose-400 hover:bg-slate-800 transition-colors text-left font-medium"
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

