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
  const { user, authenticated, loading: authLoading, signOut, isConfigured } = useAuth();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isVercel = isVercelEnvironment();

  useEffect(() => {
    async function loadHeaderTelemetry() {
      if (authLoading || !authenticated) {
        setLoading(false);
        return;
      }
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
  }, [authLoading, authenticated]);

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
    <header className="h-16 bg-[#11161D] border-b border-[#26303D] px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 select-none">
      <div className="flex items-center space-x-3">
        {onOpenMobileNav && (
          <button
            onClick={onOpenMobileNav}
            className="md:hidden text-[#9CA3AF] hover:text-[#F3F4F6] p-2 rounded-lg hover:bg-[#1A222C] border border-[#26303D] transition-colors"
            aria-label="Open Navigation Drawer"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <span className="text-xs font-sans font-semibold text-[#F3F4F6] uppercase tracking-wider flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#3B82F6] shrink-0" />
          <span className="hidden sm:inline">AI Reliability Command Center</span>
          <span className="sm:hidden">AEGIS-X</span>
        </span>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4 text-xs">
        {/* Backend Connection Indicator */}
        <div className="flex items-center space-x-2 bg-[#0F141B] border border-[#26303D] px-3 py-1.5 rounded-lg shadow-sm">
          {loading ? (
            <>
              <span className="w-2 h-2 rounded-full bg-[#F59E0B] animate-pulse" />
              <span className="text-[#9CA3AF] font-sans hidden sm:inline">API:</span>
              <span className="font-sans font-medium text-[#F59E0B]">Connecting</span>
            </>
          ) : isConnected ? (
            <>
              <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
              <span className="text-[#9CA3AF] font-sans hidden sm:inline">API:</span>
              <span className="font-sans font-medium text-[#F3F4F6]">Connected</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-[#EF4444]" />
              <span className="text-[#9CA3AF] font-sans hidden sm:inline">API:</span>
              <span className="font-sans font-medium text-[#EF4444]">Unavailable</span>
            </>
          )}
        </div>

        {/* Database & Storage Badges */}
        <div className="hidden lg:flex items-center space-x-2 text-[#9CA3AF] bg-[#0F141B] border border-[#26303D] px-3 py-1.5 rounded-lg font-sans text-[11px]">
          <Database className="w-3.5 h-3.5 text-[#64748B]" />
          <span className="text-[#F3F4F6] font-medium uppercase">{dbLabel}</span>
          <span className="text-[#6B7280]">|</span>
          <span className="text-[#F3F4F6] font-medium uppercase">{storageLabel}</span>
        </div>

        {/* User Account Menu Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setShowMenu(!showMenu)}
            aria-expanded={showMenu}
            aria-label="User Account Menu"
            className="flex items-center space-x-2 bg-[#0F141B] hover:bg-[#1A222C] border border-[#26303D] px-3 py-1.5 rounded-lg text-[#F3F4F6] font-sans text-xs transition-colors focus:outline-none focus:ring-1 focus:ring-[#3B82F6]"
          >
            <User className="w-3.5 h-3.5 text-[#3B82F6] shrink-0" />
            <span className="max-w-[100px] sm:max-w-[140px] truncate">{userLabel}</span>
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-60 bg-[#151B23] border border-[#26303D] rounded-xl shadow-2xl py-2 z-50 text-xs font-sans animate-in fade-in zoom-in-95 duration-100">
              <div className="px-4 py-2 border-b border-[#26303D] text-[#9CA3AF]">
                <div className="font-semibold text-[#F3F4F6] truncate">{menuUserTitle}</div>
                <div className="text-[10px] text-[#3B82F6] mt-0.5 font-sans">
                  Auth Mode: {authModeLabel}
                </div>
              </div>

              <Link
                href="/settings"
                onClick={() => setShowMenu(false)}
                className="flex items-center space-x-2.5 px-4 py-2.5 text-[#F3F4F6] hover:bg-[#1A222C] transition-colors"
              >
                <Settings className="w-4 h-4 text-[#9CA3AF]" />
                <span>Account & Settings</span>
              </Link>

              <button
                type="button"
                onClick={handleSignOut}
                className="w-full flex items-center space-x-2.5 px-4 py-2.5 text-[#EF4444] hover:bg-[#1A222C] transition-colors text-left font-medium"
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

