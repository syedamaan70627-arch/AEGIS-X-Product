"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { ReadinessResponse, SystemStatus, UserMe } from "@/types/api";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Database, KeyRound, Server, Shield, User } from "lucide-react";

export default function SettingsPage() {
  const { user, isConfigured } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);

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

  return (
    <div className="space-y-8">
      <PageHeader
        title="Account & System Settings"
        description="Inspect authenticated user identity, active database repositories, storage adapters, and API readiness."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Account Context */}
        <SectionCard title="User Account Context" subtitle="Identity information acknowledged by FastAPI backend">
          <div className="space-y-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex items-center space-x-3">
              <User className="w-5 h-5 text-indigo-400 shrink-0" />
              <div>
                <div className="text-slate-400 font-mono">User ID</div>
                <div className="text-sm font-bold text-slate-100 font-mono mt-0.5">{me?.user_id || "local_dev_user"}</div>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-slate-400 font-mono">Authenticated State</div>
                <div className="text-xs font-semibold text-slate-200 mt-0.5">
                  {me?.authenticated ? "Supabase Bearer Verified" : "Local Development Context"}
                </div>
              </div>
              <StatusBadge status={me?.authenticated ? "AUTHENTICATED" : "LOCAL_DEV"} />
            </div>
          </div>
        </SectionCard>

        {/* Backend Environment Configuration */}
        <SectionCard title="Backend Operations" subtitle="Operational infrastructure mode configuration">
          <div className="space-y-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5 text-indigo-400" />
                <div>
                  <div className="text-slate-400 font-mono">Database Backend</div>
                  <div className="text-sm font-bold text-slate-100 uppercase font-mono mt-0.5">
                    {status?.database_backend || "sqlite"}
                  </div>
                </div>
              </div>
              <StatusBadge status={status?.database_backend === "supabase" ? "SUPABASE_PG" : "SQLITE_LOCAL"} />
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Server className="w-5 h-5 text-emerald-400" />
                <div>
                  <div className="text-slate-400 font-mono">Storage Adapter</div>
                  <div className="text-sm font-bold text-slate-100 uppercase font-mono mt-0.5">
                    {status?.storage_backend || "local"}
                  </div>
                </div>
              </div>
              <StatusBadge status={status?.storage_backend === "supabase" ? "SUPABASE_STORAGE" : "LOCAL_FS"} />
            </div>
          </div>
        </SectionCard>
      </div>

      {/* API Readiness & Capabilities Summary */}
      <SectionCard title="Engine Capabilities & Readiness" subtitle="Exposed API capabilities and readiness check">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 font-mono uppercase">API Status</div>
            <div className="text-lg font-bold text-emerald-400 mt-1">{status?.api_status || "operational"}</div>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 font-mono uppercase">API Version</div>
            <div className="text-lg font-bold text-slate-200 mt-1">{status?.api_version || "1.0.0"}</div>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 font-mono uppercase">Auth Requirement</div>
            <div className="text-lg font-bold text-indigo-400 uppercase mt-1">{status?.auth_mode || "disabled"}</div>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
