"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { ReadinessResponse, SystemStatus, UserMe } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Database, KeyRound, Server, Settings as SettingsIcon, Shield, User } from "lucide-react";

import { isVercelEnvironment } from "@/lib/config";

export default function SettingsPage() {
  const { user, isConfigured } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);

  const isVercel = isVercelEnvironment();

  useEffect(() => {
    async function loadSettingsData() {
      setLoading(true);
      setError(null);
      try {
        const [stRes, rdRes, meRes] = await Promise.all([
          api.getStatus().catch(() => null),
          api.getReadiness().catch(() => null),
          api.getUserMe().catch(() => null),
        ]);
        if (stRes) setStatus(stRes);
        if (rdRes) setReadiness(rdRes);
        if (meRes) setMe(meRes);
      } catch (err: any) {
        setError(err.message || "Failed to load settings configuration.");
      } finally {
        setLoading(false);
      }
    }
    loadSettingsData();
  }, []);

  if (loading) return <LoadingState message="Fetching system telemetry configuration..." />;
  if (error) return <ErrorState message={error} />;

  const displayUserId = me?.user_id || (isVercel ? "Unauthenticated" : "local_dev_user");
  const authStateLabel = me?.authenticated
    ? "Supabase Bearer Verified"
    : isVercel
    ? "Unauthenticated Session"
    : "Local Development Context";
  const authStatusBadge = me?.authenticated ? "AUTHENTICATED" : isVercel ? "UNAUTHENTICATED" : "LOCAL_DEV";

  const dbBackendLabel = status?.database_backend
    ? status.database_backend.toUpperCase()
    : isVercel
    ? "SUPABASE PG"
    : "SQLITE";
  const dbStatusBadge = status?.database_backend === "supabase" ? "SUPABASE_PG" : isVercel ? "RAILWAY_PG" : "SQLITE_LOCAL";

  const storageAdapterLabel = status?.storage_backend
    ? status.storage_backend.toUpperCase()
    : isVercel
    ? "SUPABASE STORAGE"
    : "LOCAL";
  const storageStatusBadge = status?.storage_backend === "supabase" ? "SUPABASE_STORAGE" : isVercel ? "RAILWAY_FS" : "LOCAL_FS";

  return (
    <div className="space-y-8">
      <PageHeader
        title="Account & System Settings"
        description="Inspect authenticated user identity, active database repositories, storage adapters, and API readiness."
        icon={<SettingsIcon className="w-6 h-6 text-slate-400" />}
        breadcrumbs={[{ label: "System" }, { label: "Settings" }]}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-sans">
        {/* User Account Context */}
        <SectionCard title="User Account Context" subtitle="Identity information acknowledged by FastAPI backend">
          <div className="space-y-4 text-xs font-sans">
            <div className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl flex items-center justify-between shadow-sm font-mono">
              <div className="flex items-center space-x-3">
                <User className="w-5 h-5 text-[#3B82F6] shrink-0" />
                <div>
                  <div className="text-[#9CA3AF] font-semibold text-[11px] font-sans">User ID</div>
                  <div className="text-sm font-bold text-[#F3F4F6] mt-0.5">{displayUserId}</div>
                </div>
              </div>
              <CopyButton text={displayUserId} label="Copy ID" />
            </div>

            <div className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl flex items-center justify-between shadow-sm font-sans">
              <div>
                <div className="text-[#9CA3AF] font-mono text-[11px]">Authenticated State</div>
                <div className="text-xs font-semibold text-[#F3F4F6] mt-0.5">
                  {authStateLabel}
                </div>
              </div>
              <StatusBadge status={authStatusBadge} />
            </div>
          </div>
        </SectionCard>

        {/* Backend Environment Configuration */}
        <SectionCard title="Backend Operations" subtitle="Operational infrastructure mode configuration">
          <div className="space-y-4 text-xs font-sans">
            <div className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl flex items-center justify-between shadow-sm font-sans">
              <div className="flex items-center space-x-3 font-mono">
                <Database className="w-5 h-5 text-[#3B82F6] shrink-0" />
                <div>
                  <div className="text-[#9CA3AF] font-semibold text-[11px] font-sans">Database Backend</div>
                  <div className="text-sm font-bold text-[#F3F4F6] uppercase mt-0.5 font-sans">
                    {dbBackendLabel}
                  </div>
                </div>
              </div>
              <StatusBadge status={dbStatusBadge} />
            </div>

            <div className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl flex items-center justify-between shadow-sm font-sans">
              <div className="flex items-center space-x-3 font-mono">
                <Server className="w-5 h-5 text-[#22C55E] shrink-0" />
                <div>
                  <div className="text-[#9CA3AF] font-semibold text-[11px] font-sans">Storage Adapter</div>
                  <div className="text-sm font-bold text-[#F3F4F6] uppercase mt-0.5 font-sans">
                    {storageAdapterLabel}
                  </div>
                </div>
              </div>
              <StatusBadge status={storageStatusBadge} />
            </div>
          </div>
        </SectionCard>
      </div>

      {/* API Readiness & Capabilities Summary */}
      <SectionCard title="Engine Capabilities & Readiness" subtitle="Exposed API capabilities and readiness check">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
          <div className="bg-[#0F141B] p-4 rounded-xl border border-[#26303D] shadow-sm">
            <div className="text-[#9CA3AF] font-semibold uppercase text-[11px]">API Status</div>
            <div className="text-lg font-bold text-[#22C55E] mt-1 font-sans">{status?.api_status || "operational"}</div>
          </div>

          <div className="bg-[#0F141B] p-4 rounded-xl border border-[#26303D] shadow-sm">
            <div className="text-[#9CA3AF] font-semibold uppercase text-[11px]">API Version</div>
            <div className="text-lg font-bold text-[#F3F4F6] mt-1 font-sans">{status?.api_version || "1.0.0"}</div>
          </div>

          <div className="bg-[#0F141B] p-4 rounded-xl border border-[#26303D] shadow-sm">
            <div className="text-[#9CA3AF] font-semibold uppercase text-[11px]">Auth Requirement</div>
            <div className="text-lg font-bold text-[#3B82F6] uppercase mt-1 font-sans">{status?.auth_mode || "disabled"}</div>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

