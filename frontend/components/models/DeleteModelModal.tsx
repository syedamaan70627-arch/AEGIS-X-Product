"use client";

import React, { useEffect, useState, useRef } from "react";
import { AlertTriangle, Trash2, X, Loader2, ShieldAlert } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { ModelRecord, ModelDependencySummary } from "@/types/api";

interface DeleteModelModalProps {
  isOpen: boolean;
  model: ModelRecord | null;
  onClose: () => void;
  onSuccess: (deletedModelId: string) => void;
}

export const DeleteModelModal: React.FC<DeleteModelModalProps> = ({
  isOpen,
  model,
  onClose,
  onSuccess,
}) => {
  const [confirmInput, setConfirmInput] = useState("");
  const [loadingDeps, setLoadingDeps] = useState(false);
  const [dependencies, setDependencies] = useState<ModelDependencySummary | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && model) {
      setConfirmInput("");
      setErrorMsg(null);
      setDependencies(null);
      setLoadingDeps(true);

      api.getModelDependencies(model.model_id)
        .then((deps) => setDependencies(deps))
        .catch((err) => {
          console.error("Failed to load model dependencies:", err);
          setErrorMsg(err.message || "Failed to inspect model dependencies.");
        })
        .finally(() => setLoadingDeps(false));

      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, model]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isDeleting) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isDeleting, onClose]);

  if (!isOpen || !model) return null;

  const isConfirmed = confirmInput.trim() === model.model_name.trim();

  const handleDelete = async () => {
    if (!isConfirmed || isDeleting) return;
    setIsDeleting(true);
    setErrorMsg(null);

    try {
      await api.deleteModel(model.model_id);
      onSuccess(model.model_id);
      onClose();
    } catch (err: any) {
      console.error("Failed to delete model:", err);
      const msg = err instanceof ApiError ? err.message : (err?.message || "Failed to delete model.");
      setErrorMsg(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      aria-modal="true"
      role="dialog"
      aria-labelledby="delete-model-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-red-500/30 bg-slate-900 shadow-2xl shadow-red-950/20 text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/60 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
              <Trash2 className="h-5 w-5" />
            </div>
            <div>
              <h2 id="delete-model-title" className="text-lg font-semibold text-slate-100">
                Delete model?
              </h2>
              <p className="text-xs text-slate-400">
                Remove executable model from active registry
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors disabled:opacity-50"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4 px-6 py-5">
          {/* Model Card */}
          <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-semibold text-slate-200">{model.model_name}</span>
              <span className="text-xs font-mono text-slate-400">{model.model_id.slice(0, 8)}...</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
              <span className="rounded bg-slate-800 px-2 py-0.5 text-slate-300">
                {model.n_features_in ? `${model.n_features_in} features` : "Unknown features"}
              </span>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-slate-300">
                {model.task_type === "binary_classification" ? "Binary Classification" : model.task_type}
              </span>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-slate-300 font-mono">
                {model.filename}
              </span>
            </div>
          </div>

          {/* Dependency Summary Pre-flight */}
          {loadingDeps ? (
            <div className="flex items-center justify-center gap-2 rounded-lg border border-slate-800 py-4 text-xs text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
              <span>Inspecting model dependencies...</span>
            </div>
          ) : dependencies ? (
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-slate-300">
              <div className="flex items-center gap-2 font-medium text-amber-400 mb-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Associated Operational Dependencies</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {dependencies.uploaded_datasets > 0 && (
                  <li>{dependencies.uploaded_datasets} evaluation dataset(s)</li>
                )}
                {dependencies.reliability_analyses > 0 && (
                  <li>{dependencies.reliability_analyses} reliability analysis run(s)</li>
                )}
                {dependencies.stress_tests > 0 && (
                  <li>{dependencies.stress_tests} stress test run(s)</li>
                )}
                {dependencies.fault_tests > 0 && (
                  <li>{dependencies.fault_tests} fault injection run(s)</li>
                )}
                {dependencies.governance_evaluations > 0 && (
                  <li>{dependencies.governance_evaluations} governance evaluation(s)</li>
                )}
                {dependencies.report_snapshots > 0 && (
                  <li>{dependencies.report_snapshots} immutable report snapshot(s)</li>
                )}
                {dependencies.uploaded_datasets === 0 &&
                  dependencies.reliability_analyses === 0 &&
                  dependencies.governance_evaluations === 0 && (
                    <li>No active operational analyses bound</li>
                  )}
              </ul>
              <p className="mt-2 text-[11px] text-slate-400">
                Deleting the active model prevents future analyses. Historical immutable report snapshots and audit evidence will be preserved.
              </p>
            </div>
          ) : null}

          {/* Error Message */}
          {errorMsg && (
            <div className="flex items-start gap-2.5 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-300">
              <ShieldAlert className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
              <div>
                <span className="font-semibold">Deletion Failed:</span> {errorMsg}
              </div>
            </div>
          )}

          {/* Safety Confirmation Prompt */}
          <div className="space-y-2">
            <label htmlFor="confirm-input" className="block text-xs text-slate-300">
              Type <span className="font-bold text-slate-100">{model.model_name}</span> to confirm permanent deletion:
            </label>
            <input
              id="confirm-input"
              ref={inputRef}
              type="text"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder={model.model_name}
              disabled={isDeleting}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-red-500/50 focus:outline-none focus:ring-1 focus:ring-red-500/50 disabled:opacity-50"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 border-t border-slate-800 bg-slate-950/60 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-slate-100 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={!isConfirmed || isDeleting}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-red-950/50 hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/50 disabled:cursor-not-allowed disabled:opacity-40 transition-all"
          >
            {isDeleting ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Deleting Model...</span>
              </>
            ) : (
              <>
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete Model</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
