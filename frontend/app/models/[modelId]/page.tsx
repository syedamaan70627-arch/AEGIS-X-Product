"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ModelCapabilitiesResponse, ModelRecord } from "@/types/api";
import { CapabilityBadge } from "@/components/ui/CapabilityBadge";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ArrowLeft, ArrowRight, Database, Layers, ShieldCheck, Zap } from "lucide-react";

export default function ModelDetailsPage() {
  const params = useParams();
  const modelId = params.modelId as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<ModelRecord | null>(null);
  const [capabilities, setCapabilities] = useState<ModelCapabilitiesResponse | null>(null);

  useEffect(() => {
    async function loadModelDetails() {
      setLoading(true);
      setError(null);
      try {
        const [mRes, cRes] = await Promise.all([
          api.getModel(modelId),
          api.getModelCapabilities(modelId),
        ]);
        setModel(mRes);
        setCapabilities(cRes);
      } catch (err: any) {
        setError(err.message || "Failed to load model details.");
      } finally {
        setLoading(false);
      }
    }
    if (modelId) loadModelDetails();
  }, [modelId]);

  if (loading) return <LoadingState message="Inspecting model readiness and capabilities..." />;
  if (error || !model) return <ErrorState message={error || "Model not found."} />;

  const caps = capabilities?.capabilities;

  return (
    <div className="space-y-8">
      <PageHeader
        title={model.model_name}
        description={`Model ID: ${model.model_id} | Filename: ${model.filename}`}
        icon={<Layers className="w-6 h-6 text-[#3B82F6]" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Model Registry", href: "/models" }, { label: model.model_name }]}
        badge={<StatusBadge status={model.status} />}
        actions={
          <div className="flex items-center space-x-2">
            <CopyButton text={model.model_id} label="Copy Model ID" />
          </div>
        }
      />

      {/* Metadata Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm">
          <div className="text-[#9CA3AF] uppercase font-semibold text-[11px] font-sans">Task Type</div>
          <div className="mt-1.5 font-bold text-[#F3F4F6] text-sm capitalize">{model.task_type.replace("_", " ")}</div>
        </div>
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm">
          <div className="text-[#9CA3AF] uppercase font-semibold text-[11px] font-sans">Expected Features</div>
          <div className="mt-1.5 font-bold text-[#3B82F6] text-sm">{model.n_features_in ?? "Unknown"}</div>
        </div>
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm">
          <div className="text-[#9CA3AF] uppercase font-semibold text-[11px] font-sans">Probability Output</div>
          <div className="mt-1.5 font-bold text-[#22C55E] text-sm">{model.predict_proba_supported ? "Supported (predict_proba)" : "Not Supported"}</div>
        </div>
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm">
          <div className="text-[#9CA3AF] uppercase font-semibold text-[11px] font-sans">Registered Date</div>
          <div className="mt-1.5 font-bold text-[#F3F4F6] text-xs">{new Date(model.created_at).toLocaleString()}</div>
        </div>
      </div>

      {/* Capability Readiness Inspection Card */}
      <SectionCard title="Operational Capability Readiness" subtitle="Evaluates AEGIS-X engine readiness for this model deployment">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <CapabilityBadge label="Core Analysis (OOD/Drift/Fusion)" capability={caps?.core_analysis} />
          <CapabilityBadge label="Stress Lab Testing" capability={caps?.stress_testing} />
          <CapabilityBadge label="Fault Lab Injection" capability={caps?.fault_testing} />
          <CapabilityBadge label="Failure Signature Memory" capability={caps?.failure_memory} />
          <CapabilityBadge label="Failure Prediction" capability={caps?.failure_prediction} />
          <CapabilityBadge label="Early Warning Engine" capability={caps?.early_warning} />
        </div>
      </SectionCard>

      {/* Quick Action Workflows */}
      <SectionCard title="Action Workflows" subtitle="Execute model reference baseline setup or operational analyses">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center space-x-2 text-[#3B82F6] font-semibold text-sm font-sans">
                <Database className="w-4 h-4 shrink-0" />
                <span>Reference Fit Baseline</span>
              </div>
              <p className="text-xs text-[#9CA3AF] mt-2 leading-relaxed font-sans">
                Fit baseline distributions on a registered REFERENCE dataset before monitoring evaluation batches.
              </p>
            </div>
            <Link
              href="/data"
              className="mt-4 inline-flex items-center text-xs font-semibold text-[#3B82F6] hover:text-[#2563EB] font-sans"
            >
              Configure Reference Data <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>

          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center space-x-2 text-[#22C55E] font-semibold text-sm font-sans">
                <ShieldCheck className="w-4 h-4 shrink-0" />
                <span>Batch Operational Monitor</span>
              </div>
              <p className="text-xs text-[#9CA3AF] mt-2 leading-relaxed font-sans">
                Run core reliability detection across OOD, Uncertainty, Drift, and Fusion signals on evaluation data.
              </p>
            </div>
            <Link
              href="/monitor"
              className="mt-4 inline-flex items-center text-xs font-semibold text-[#22C55E] hover:text-emerald-300 font-sans"
            >
              Go to Batch Monitor <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>

          <div className="bg-[#0F141B] border border-[#26303D] rounded-xl p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center space-x-2 text-[#F59E0B] font-semibold text-sm font-sans">
                <Zap className="w-4 h-4 shrink-0" />
                <span>Stress & Fault Testing</span>
              </div>
              <p className="text-xs text-[#9CA3AF] mt-2 leading-relaxed font-sans">
                Execute controlled noise stress or inject sensor bias/gain faults to evaluate robust performance.
              </p>
            </div>
            <Link
              href="/stress"
              className="mt-4 inline-flex items-center text-xs font-semibold text-[#F59E0B] hover:text-amber-300 font-sans"
            >
              Open Stress Lab <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

