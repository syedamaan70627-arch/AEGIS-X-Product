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
import { useToast } from "@/components/providers/ToastProvider";
import { CheckCircle2, Layers, Plus, Search, ShieldAlert, XCircle } from "lucide-react";

export default function ModelsPage() {
  const toast = useToast();
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
  }, []);

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
    <div className="space-y-6">
      <PageHeader
        title="Model Registry"
        description="Register and inspect classification models (.joblib or .pkl) for AEGIS-X operational reliability evaluation."
        icon={<Layers className="w-6 h-6 text-indigo-400" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Model Registry" }]}
        actions={
          <button
            onClick={() => setShowRegisterModal(true)}
            className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Register Model
          </button>
        }
      />

      {/* Security Warning Callout */}
      <div className="p-4 bg-amber-950/40 border border-amber-800/60 rounded-xl flex items-start space-x-3 shadow-md">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200/90 leading-relaxed">
          <span className="font-mono font-bold text-amber-300 uppercase tracking-wider block mb-0.5 text-[11px]">
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
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          }
        >
          <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-950/40">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono tracking-wider text-[11px] border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Model Identity</th>
                  <th className="p-3.5">Task Type</th>
                  <th className="p-3.5">Features In</th>
                  <th className="p-3.5">predict_proba</th>
                  <th className="p-3.5">Created Date</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredModels.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      No models matching &quot;{searchTerm}&quot;.
                    </td>
                  </tr>
                ) : (
                  filteredModels.map((m) => (
                    <tr key={m.model_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-3.5">
                        <div className="font-bold text-slate-100 text-sm">{m.model_name}</div>
                        <div className="flex items-center space-x-1.5 text-[11px] font-mono text-slate-400 mt-0.5">
                          <span>ID: {m.model_id.slice(0, 12)}...</span>
                          <CopyButton text={m.model_id} />
                        </div>
                      </td>
                      <td className="p-3.5 font-mono text-slate-300 capitalize">{m.task_type.replace("_", " ")}</td>
                      <td className="p-3.5 font-mono text-slate-300 font-semibold">{m.n_features_in ?? "N/A"}</td>
                      <td className="p-3.5">
                        {m.predict_proba_supported ? (
                          <span className="inline-flex items-center text-emerald-300 text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Supported
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-slate-500 text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                            <XCircle className="w-3.5 h-3.5 mr-1" /> Not Supported
                          </span>
                        )}
                      </td>
                      <td className="p-3.5 text-slate-400 font-mono text-[11px]">{new Date(m.created_at).toLocaleDateString()}</td>
                      <td className="p-3.5">
                        <StatusBadge status={m.status} />
                      </td>
                      <td className="p-3.5 text-right">
                        <Link
                          href={`/models/${m.model_id}`}
                          className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors border border-slate-700 inline-block"
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
          className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
          aria-modal="true"
          role="dialog"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-100">Register Scikit-Learn Model</h3>
              </div>
              <button
                onClick={() => setShowRegisterModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold p-1 rounded hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            {submitError && <ErrorState message={submitError} />}

            <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Model Name *</label>
                <input
                  type="text"
                  required
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. Production XGBoost Classifier"
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Task Type *</label>
                <select
                  value={taskType}
                  onChange={(e) => setTaskType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  <option value="binary_classification">Binary Classification</option>
                  <option value="multiclass_classification">Multiclass Classification</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Short operational notes or feature pipeline summary"
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 h-20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Model File (.joblib or .pkl) *</label>
                <input
                  type="file"
                  required
                  accept=".joblib,.pkl"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-lg px-3 py-2 text-slate-300 text-xs file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer font-mono"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow-md transition-colors disabled:opacity-50"
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

