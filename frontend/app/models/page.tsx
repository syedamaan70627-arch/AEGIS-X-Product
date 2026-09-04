"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAuth } from "@/components/providers/AuthProvider";
import { useToast } from "@/components/providers/ToastProvider";
import { CheckCircle2, Layers, Plus, Search, ShieldAlert, XCircle } from "lucide-react";

export default function ModelsPage() {
  const toast = useToast();
  const { loading: authLoading, authenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  // Registration modal state
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [modelName, setModelName] = useState("");
  const [taskType, setTaskType] = useState("binary_classification");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      if (authLoading || !authenticated) return;
      setLoading(true);
      setError(null);
      try {
        const res = await api.listModels();
        if (active) setModels(res.models || []);
      } catch (err: any) {
        if (active) setError(err.message || "Failed to load models list.");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [authLoading, authenticated]);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listModels();
      setModels(res.models || []);
    } catch (err: any) {
      setError(err.message || "Failed to load models list.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modelName || !selectedFile) {
      setSubmitError("Please fill out model name and select a valid model file.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      const formData = new FormData();
      formData.append("model_name", modelName);
      formData.append("task_type", taskType);
      if (description) formData.append("description", description);
      formData.append("file", selectedFile);

      await api.registerModel(formData);
      toast.success("Model Registered", `Successfully registered ${modelName}`);
      setShowRegisterModal(false);
      setModelName("");
      setDescription("");
      setSelectedFile(null);
      await fetchModels();
    } catch (err: any) {
      setSubmitError(err.message || "Failed to register model.");
      toast.error("Registration Failed", err.message || "Could not upload model.");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredModels = models.filter((m) =>
    m.model_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.model_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 font-sans">
      <PageHeader
        title="Model Registry"
        description="Register and inspect classification models (.joblib or .pkl) for AEGIS-X operational reliability evaluation."
        icon={<Layers className="w-6 h-6 text-[#3B82F6]" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Model Registry" }]}
        actions={
          <button
            onClick={() => setShowRegisterModal(true)}
            className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-[#3B82F6] hover:bg-[#2563EB] rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Register Model
          </button>
        }
      />

      {/* Security Warning Callout */}
      <div className="p-4 bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-xl flex items-start space-x-3 shadow-sm text-xs text-[#F59E0B] font-sans">
        <ShieldAlert className="w-5 h-5 text-[#F59E0B] shrink-0 mt-0.5" />
        <div className="text-xs text-[#F59E0B] leading-relaxed font-sans">
          <span className="font-sans font-bold uppercase tracking-wider block mb-0.5 text-[11px]">
            Deserialization Security Warning
          </span>
          Only upload trusted scikit-learn model files (.joblib or .pkl). Deserializing untrusted Python pickle objects executes arbitrary code.
        </div>
      </div>

      {loading ? (
        <LoadingState message="Fetching registered model metadata..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchModels} />
      ) : models.length === 0 ? (
        <EmptyState
          title="No Models Registered"
          description="Register your first scikit-learn model to unlock AEGIS-X operational capability inspection and baseline fitting."
          actionText="Register Model"
          actionHref="#"
          icon={<Layers className="w-8 h-8" />}
        />
      ) : (
        <SectionCard
          title="Registered Classification Models"
          subtitle={`Total Models: ${models.length}`}
          action={
            <div className="relative w-full sm:w-64 font-sans">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#6B7280] pointer-events-none" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] font-sans"
              />
            </div>
          }
        >
          <div className="overflow-x-auto rounded-xl border border-[#26303D] bg-[#151B23]">
            <table className="w-full text-left text-xs border-collapse font-sans">
              <thead className="bg-[#0F141B] text-[#9CA3AF] uppercase font-sans tracking-wider text-[11px] border-b border-[#26303D]">
                <tr>
                  <th className="p-3.5">Model Identity</th>
                  <th className="p-3.5">Task Type</th>
                  <th className="p-3.5 font-mono">Features In</th>
                  <th className="p-3.5 font-mono">predict_proba</th>
                  <th className="p-3.5">Created Date</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#26303D]/60 font-sans">
                {filteredModels.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-[#9CA3AF] font-sans">
                      No models matching &quot;{searchTerm}&quot;.
                    </td>
                  </tr>
                ) : (
                  filteredModels.map((m) => (
                    <tr key={m.model_id} className="hover:bg-[#1A222C] transition-colors">
                      <td className="p-3.5">
                        <div className="font-bold text-[#F3F4F6] text-sm font-sans">{m.model_name}</div>
                        <div className="flex items-center space-x-1.5 text-[11px] font-mono text-[#9CA3AF] mt-0.5">
                          <span>ID: {m.model_id.slice(0, 12)}...</span>
                          <CopyButton text={m.model_id} />
                        </div>
                      </td>
                      <td className="p-3.5 font-sans text-[#F3F4F6] capitalize">{m.task_type.replace("_", " ")}</td>
                      <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold tabular-nums">{m.n_features_in ?? "N/A"}</td>
                      <td className="p-3.5">
                        {m.predict_proba_supported ? (
                          <span className="inline-flex items-center text-[#22C55E] text-[11px] font-sans font-medium px-2 py-0.5 rounded bg-[#22C55E]/10 border border-[#22C55E]/30">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Supported
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-[#9CA3AF] text-[11px] font-sans font-medium px-2 py-0.5 rounded bg-[#1A222C] border border-[#26303D]">
                            <XCircle className="w-3.5 h-3.5 mr-1" /> Not Supported
                          </span>
                        )}
                      </td>
                      <td className="p-3.5 text-[#9CA3AF] font-mono text-[11px] tabular-nums">{new Date(m.created_at).toLocaleDateString()}</td>
                      <td className="p-3.5">
                        <StatusBadge status={m.status} />
                      </td>
                      <td className="p-3.5 text-right">
                        <Link
                          href={`/models/${m.model_id}`}
                          className="px-3 py-1.5 text-xs font-semibold bg-[#1A222C] hover:bg-[#26303D] text-[#F3F4F6] rounded-lg transition-colors border border-[#26303D] inline-block font-sans"
                        >
                          Capabilities →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      {/* Register Model Modal */}
      {showRegisterModal && (
        <div
          onClick={() => setShowRegisterModal(false)}
          className="fixed inset-0 z-50 bg-[#0B0F14]/80 backdrop-blur-sm flex items-center justify-center p-4"
          aria-modal="true"
          role="dialog"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-[#151B23] border border-[#26303D] rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150 font-sans"
          >
            <div className="flex items-center justify-between border-b border-[#26303D] pb-3">
              <div className="flex items-center space-x-2">
                <Layers className="w-5 h-5 text-[#3B82F6]" />
                <h3 className="text-sm font-bold text-[#F3F4F6] font-sans">Register Scikit-Learn Model</h3>
              </div>
              <button
                onClick={() => setShowRegisterModal(false)}
                className="text-[#9CA3AF] hover:text-[#F3F4F6] text-sm font-bold p-1 rounded hover:bg-[#1A222C]"
              >
                ✕
              </button>
            </div>

            {submitError && <ErrorState message={submitError} />}

            <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs font-sans">
              <div>
                <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Model Name *</label>
                <input
                  type="text"
                  required
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. Production XGBoost Classifier"
                  className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] font-sans"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Task Type *</label>
                <select
                  value={taskType}
                  onChange={(e) => setTaskType(e.target.value)}
                  className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-sans"
                >
                  <option value="binary_classification">Binary Classification</option>
                  <option value="multiclass_classification">Multiclass Classification</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Short operational notes or feature pipeline summary"
                  className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] h-20 font-sans"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Model File (.joblib or .pkl) *</label>
                <input
                  type="file"
                  required
                  accept=".joblib,.pkl"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#9CA3AF] text-xs file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#3B82F6] file:text-white hover:file:bg-[#2563EB] cursor-pointer font-sans"
                />
              </div>

              <div className="pt-3 border-t border-[#26303D] flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 bg-[#1A222C] hover:bg-[#26303D] text-[#F3F4F6] rounded-lg font-semibold transition-colors font-sans"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg font-semibold shadow-sm transition-colors disabled:opacity-50 font-sans"
                >
                  {submitting ? "Uploading & Registering..." : "Confirm Registration"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

