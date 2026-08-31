"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DatasetRecord, ModelRecord, ReferenceFitResponse } from "@/types/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CheckCircle2, Database, FileSpreadsheet, Layers, Play, Plus, Upload } from "lucide-react";

export default function DataSetupPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);

  // Upload Dataset State
  const [datasetType, setDatasetType] = useState<"REFERENCE" | "EVALUATION">("REFERENCE");
  const [targetColumn, setTargetColumn] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Reference Fit State
  const [fitting, setFitting] = useState(false);
  const [fitResult, setFitResult] = useState<ReferenceFitResponse | null>(null);
  const [fitError, setFitError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const modelsRes = await api.listModels();
      const loadedModels = modelsRes.models || [];
      setModels(loadedModels);

      if (loadedModels.length > 0) {
        const activeId = selectedModelId || loadedModels[0].model_id;
        setSelectedModelId(activeId);
        const dsRes = await api.listDatasets(activeId);
        setDatasets(dsRes.datasets || []);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load datasets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedModelId]);

  const handleDatasetUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedFile) {
      setUploadError("Please select a target model and CSV file.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("model_id", selectedModelId);
      formData.append("dataset_type", datasetType);
      if (targetColumn) formData.append("target_column", targetColumn);
      formData.append("file", selectedFile);

      await api.registerDataset(formData);
      setSelectedFile(null);
      setTargetColumn("");
      await loadData();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleFitReference = async (refDatasetId: string) => {
    if (!selectedModelId) return;
    setFitting(true);
    setFitError(null);
    try {
      const res = await api.fitReferenceState(selectedModelId, refDatasetId);
      setFitResult(res);
      await loadData();
    } catch (err: any) {
      setFitError(err.message || "Failed to fit reference baseline state.");
    } finally {
      setFitting(false);
    }
  };

  const referenceDatasets = datasets.filter((d) => d.dataset_type === "REFERENCE");
  const evaluationDatasets = datasets.filter((d) => d.dataset_type === "EVALUATION");

  return (
    <div className="space-y-8">
      <PageHeader
        title="Data Setup & Reference Fitting"
        description="Configure baseline REFERENCE data distributions and current EVALUATION batches for AEGIS-X."
      />

      {/* Concept Explanation Header */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 border-l-4 border-l-indigo-500">
          <h4 className="font-bold text-slate-100 uppercase tracking-wider mb-1 flex items-center gap-2">
            <Database className="w-4 h-4 text-indigo-400" /> Reference Data (Baseline)
          </h4>
          <p className="text-slate-400 leading-relaxed">
            Represents known, clean operating data distribution used to compute baseline distance statistics for OOD, Drift, and Calibration.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 border-l-4 border-l-emerald-500">
          <h4 className="font-bold text-slate-100 uppercase tracking-wider mb-1 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" /> Evaluation Data (Batch)
          </h4>
          <p className="text-slate-400 leading-relaxed">
            New production or test batch data evaluated against the fitted baseline state to measure operational risk signals.
          </p>
        </div>
      </div>

      {/* Model Selector Bar */}
      {models.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3 text-xs">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-slate-200">Active Model Context:</span>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name} ({m.model_id.slice(0, 8)}...)
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {loading ? (
        <LoadingState message="Loading datasets for selected model..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Form */}
          <div className="lg:col-span-1">
            <SectionCard title="Upload Dataset CSV" subtitle="Add tabular dataset file">
              {uploadError && <ErrorState message={uploadError} />}

              <form onSubmit={handleDatasetUpload} className="space-y-4 text-xs">
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Dataset Category *</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setDatasetType("REFERENCE")}
                      className={`py-2 rounded-lg font-semibold border transition-all ${
                        datasetType === "REFERENCE"
                          ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/50"
                          : "bg-slate-950 text-slate-400 border-slate-800"
                      }`}
                    >
                      REFERENCE
                    </button>
                    <button
                      type="button"
                      onClick={() => setDatasetType("EVALUATION")}
                      className={`py-2 rounded-lg font-semibold border transition-all ${
                        datasetType === "EVALUATION"
                          ? "bg-emerald-600/20 text-emerald-300 border-emerald-500/50"
                          : "bg-slate-950 text-slate-400 border-slate-800"
                      }`}
                    >
                      EVALUATION
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-slate-300 mb-1">Target Label Column (Optional)</label>
                  <input
                    type="text"
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    placeholder="e.g. target or label"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">
                    If omitted, dataset is treated as label-free operational data.
                  </p>
                </div>

                <div>
                  <label className="block font-medium text-slate-300 mb-1">CSV File *</label>
                  <input
                    type="file"
                    required
                    accept=".csv"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 text-xs file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                  />
                </div>

                <button
                  type="submit"
                  disabled={uploading || !selectedModelId}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow-md transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Upload className="w-4 h-4" />
                  <span>{uploading ? "Uploading CSV..." : "Upload Dataset"}</span>
                </button>
              </form>
            </SectionCard>
          </div>

          {/* Dataset Tables & Reference Fit */}
          <div className="lg:col-span-2 space-y-6">
            {fitError && <ErrorState message={fitError} />}
            {fitResult && (
              <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded-xl flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Reference Baseline Fitted Successfully
                  </div>
                  <div className="text-[11px] text-emerald-200/80 mt-1">
                    Baseline fitted on {fitResult.num_samples} samples across {fitResult.feature_names.length} features.
                  </div>
                </div>
                <StatusBadge status="FITTED" />
              </div>
            )}

            {/* Reference Datasets */}
            <SectionCard title="Reference Datasets (Baseline)" subtitle="Select a reference dataset to fit baseline state">
              {referenceDatasets.length === 0 ? (
                <p className="text-xs text-slate-500 py-4">No reference datasets registered for this model.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono border-b border-slate-800">
                      <tr>
                        <th className="p-3">Filename</th>
                        <th className="p-3">Samples</th>
                        <th className="p-3">Features</th>
                        <th className="p-3">Target</th>
                        <th className="p-3 text-right">Reference Fit Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {referenceDatasets.map((d) => (
                        <tr key={d.dataset_id} className="hover:bg-slate-800/40">
                          <td className="p-3 font-semibold text-slate-200">{d.filename}</td>
                          <td className="p-3 font-mono text-slate-300">{d.num_samples}</td>
                          <td className="p-3 font-mono text-slate-300">{d.num_features}</td>
                          <td className="p-3 font-mono text-slate-400">{d.target_column || "Label-Free"}</td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => handleFitReference(d.dataset_id)}
                              disabled={fitting}
                              className="px-3 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-md transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
                            >
                              <Play className="w-3 h-3 fill-current mr-1" />
                              <span>{fitting ? "Fitting..." : "FIT REFERENCE STATE"}</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>

            {/* Evaluation Datasets */}
            <SectionCard title="Evaluation Datasets (Batches)" subtitle="Registered test and operational evaluation batches">
              {evaluationDatasets.length === 0 ? (
                <p className="text-xs text-slate-500 py-4">No evaluation datasets registered for this model.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono border-b border-slate-800">
                      <tr>
                        <th className="p-3">Filename</th>
                        <th className="p-3">Samples</th>
                        <th className="p-3">Features</th>
                        <th className="p-3">Target</th>
                        <th className="p-3">Uploaded</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {evaluationDatasets.map((d) => (
                        <tr key={d.dataset_id} className="hover:bg-slate-800/40">
                          <td className="p-3 font-semibold text-slate-200">{d.filename}</td>
                          <td className="p-3 font-mono text-slate-300">{d.num_samples}</td>
                          <td className="p-3 font-mono text-slate-300">{d.num_features}</td>
                          <td className="p-3 font-mono text-slate-400">{d.target_column || "Label-Free"}</td>
                          <td className="p-3 text-slate-400">{new Date(d.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>
          </div>
        </div>
      )}
    </div>
  );
}
