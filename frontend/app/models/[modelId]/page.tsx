"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ModelCapabilitiesResponse, ModelRecord } from "@/types/api";
import { CapabilityBadge } from "@/components/ui/CapabilityBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ArrowLeft, ArrowRight, CheckCircle, Clock, Database, Layers, ShieldCheck, Zap } from "lucide-react";

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
      <div>
        <Link
          href="/models"
          className="inline-flex items-center text-xs font-medium text-slate-400 hover:text-slate-200 mb-4 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Models
        </Link>
        <PageHeader
          title={model.model_name}
          description={`ID: ${model.model_id} | Filename: ${model.filename}`}
          badge={<StatusBadge status={model.status} />}
        />
      </div>

      {/* Metadata Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 uppercase font-mono font-semibold">Task Type</div>
          <div className="mt-1 font-bold text-slate-100">{model.task_type}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 uppercase font-mono font-semibold">Expected Features</div>
          <div className="mt-1 font-bold text-slate-100">{model.n_features_in ?? "Unknown"}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 uppercase font-mono font-semibold">Probability Output</div>
          <div className="mt-1 font-bold text-slate-100">{model.predict_proba_supported ? "Yes (predict_proba)" : "No"}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 uppercase font-mono font-semibold">Registered Date</div>
          <div className="mt-1 font-bold text-slate-100">{new Date(model.created_at).toLocaleString()}</div>
        </div>
      </div>

      {/* Capability Readiness Inspection Card */}
      <SectionCard title="Operational Capability Readiness" subtitle="Evaluates AEGIS-X engine readiness for this model deployment">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-sm">
                <Database className="w-4 h-4" />
                <span>Reference Fit Baseline</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Fit baseline distributions on a registered REFERENCE dataset before monitoring evaluation batches.
              </p>
            </div>
            <Link
              href="/data"
              className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-400 hover:text-indigo-300"
            >
              Configure Reference Data <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
                <ShieldCheck className="w-4 h-4" />
                <span>Batch Operational Monitor</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Run core reliability detection across OOD, Uncertainty, Drift, and Fusion signals on evaluation data.
              </p>
            </div>
            <Link
              href="/monitor"
              className="mt-4 inline-flex items-center text-xs font-semibold text-emerald-400 hover:text-emerald-300"
            >
              Go to Batch Monitor <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm">
                <Zap className="w-4 h-4" />
                <span>Stress & Fault Testing</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Execute controlled noise stress or inject sensor bias/gain faults to evaluate robust performance.
              </p>
            </div>
            <Link
              href="/stress"
              className="mt-4 inline-flex items-center text-xs font-semibold text-amber-400 hover:text-amber-300"
            >
              Open Stress Lab <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
