"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ModelRecord } from "@/types/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AlertOctagon, CheckCircle2, Layers, Plus, ShieldAlert, XCircle } from "lucide-react";

export default function ModelsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);

  // Registration modal state
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [modelName, setModelName] = useState("");
  const [taskType, setTaskType] = useState("binary_classification");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

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

  useEffect(() => {
    fetchModels();
  }, []);

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
      setShowRegisterModal(false);
      setModelName("");
      setDescription("");
      setSelectedFile(null);
      await fetchModels();
    } catch (err: any) {
      setSubmitError(err.message || "Failed to register model.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Model Registry"
        description="Register and inspect classification models (.joblib or .pkl) for AEGIS-X operational reliability evaluation."
        actions={
          <button
            onClick={() => setShowRegisterModal(true)}
            className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-md transition-colors"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Register Model
          </button>
        }
      />

      {/* Security Warning Callout */}
      <div className="p-4 bg-amber-950/40 border border-amber-800/60 rounded-xl flex items-start space-x-3">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200/90">
          <span className="font-semibold text-amber-300 uppercase tracking-wider block mb-0.5">
            Deserialization Security Warning
          </span>
          Only upload trusted scikit-learn model files (.joblib or .pkl). Deserializing untrusted python pickle files can lead to security vulnerabilities.
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
        <SectionCard title="Registered Classification Models" subtitle={`Total Models: ${models.length}`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="p-3">Model Name</th>
                  <th className="p-3">Task Type</th>
                  <th className="p-3">Features In</th>
                  <th className="p-3">predict_proba</th>
                  <th className="p-3">Created</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {models.map((m) => (
                  <tr key={m.model_id} className="hover:bg-slate-800/40">
                    <td className="p-3">
                      <div className="font-semibold text-slate-200">{m.model_name}</div>
                      <div className="text-[11px] font-mono text-slate-400">{m.model_id}</div>
                    </td>
                    <td className="p-3 font-mono text-slate-300">{m.task_type}</td>
                    <td className="p-3 font-mono text-slate-300">{m.n_features_in ?? "N/A"}</td>
                    <td className="p-3">
                      {m.predict_proba_supported ? (
                        <span className="inline-flex items-center text-emerald-400 text-[11px] font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Supported
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-slate-500 text-[11px] font-medium">
                          <XCircle className="w-3.5 h-3.5 mr-1" /> Not Supported
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-slate-400">{new Date(m.created_at).toLocaleDateString()}</td>
                    <td className="p-3">
                      <StatusBadge status={m.status} />
                    </td>
                    <td className="p-3 text-right space-x-2">
                      <Link
                        href={`/models/${m.model_id}`}
                        className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md transition-colors"
                      >
                        Inspect Capabilities →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      {/* Register Model Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-lg w-full shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">Register Scikit-Learn Model</h3>
              <button
                onClick={() => setShowRegisterModal(false)}
                className="text-slate-400 hover:text-slate-200 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            {submitError && <ErrorState message={submitError} />}

            <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">Model Name *</label>
                <input
                  type="text"
                  required
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. Production XGBoost Classifier"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Task Type *</label>
                <select
                  value={taskType}
                  onChange={(e) => setTaskType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  <option value="binary_classification">Binary Classification</option>
                  <option value="multiclass_classification">Multiclass Classification</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Short operational notes or feature pipeline summary"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 h-20"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Model File (.joblib or .pkl) *</label>
                <input
                  type="file"
                  required
                  accept=".joblib,.pkl"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 text-xs file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors"
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
