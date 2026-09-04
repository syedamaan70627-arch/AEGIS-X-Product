"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DatasetRecord, ModelRecord, ReferenceFitResponse } from "@/types/api";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { Activity, CheckCircle2, Database, FileSpreadsheet, Layers, Play, Trash2, Upload } from "lucide-react";

export default function DataSetupPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);

  // Upload Dataset State
  const [datasetType, setDatasetType] = useState<"REFERENCE" | "EVALUATION" | "TEMPORAL_TRAJECTORY">("REFERENCE");
  const [targetColumn, setTargetColumn] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Reference Fit State
  const [fittingDatasetId, setFittingDatasetId] = useState<string | null>(null);
  const [fitResult, setFitResult] = useState<ReferenceFitResponse | null>(null);
  const [fitError, setFitError] = useState<string | null>(null);

  // Delete Confirmation State
  const [deletingDatasetId, setDeletingDatasetId] = useState<string | null>(null);

  const loadData = async (targetModelId?: string) => {
    setLoading(true);
    setError(null);
    try {
      const modelsRes = await api.listModels();
      const loadedModels = modelsRes.models || [];
      setModels(loadedModels);

      if (loadedModels.length > 0) {
        const activeId = targetModelId || selectedModelId || loadedModels[0].model_id;
        if (!selectedModelId) {
          setSelectedModelId(activeId);
        }
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
    loadData(selectedModelId);
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
      toast.success("Dataset Uploaded", `Successfully registered ${selectedFile.name} as ${datasetType}`);
      setSelectedFile(null);
      setTargetColumn("");
      await loadData();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload dataset.");
      toast.error("Upload Failed", err.message || "Could not register dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleFitReference = async (refDatasetId: string) => {
    if (!selectedModelId || fittingDatasetId !== null) return;
    setFittingDatasetId(refDatasetId);
    setFitError(null);
    try {
      const res = await api.fitReferenceState(selectedModelId, refDatasetId);
      setFitResult(res);
      toast.success("Baseline State Fitted", `Fitted reference baseline over ${res.num_samples} samples`);
      await loadData();
    } catch (err: any) {
      setFitError(err.message || "Failed to fit reference baseline state.");
      toast.error("Reference Fit Error", err.message || "Could not fit baseline.");
    } finally {
      setFittingDatasetId(null);
    }
  };

  const confirmDeleteDataset = async () => {
    if (!deletingDatasetId) return;
    const targetId = deletingDatasetId;
    setDeletingDatasetId(null);
    try {
      await api.deleteDataset(targetId);
      toast.success("Dataset Deleted", "Dataset removed from registry.");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to delete dataset.");
      toast.error("Delete Failed", err.message || "Could not remove dataset.");
    }
  };

  const referenceDatasets = datasets.filter((d) => d.dataset_type === "REFERENCE");
  const evaluationDatasets = datasets.filter((d) => d.dataset_type === "EVALUATION");
  const temporalDatasets = datasets.filter(
    (d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY"
  );

  return (
    <div className="space-y-8">
      <PageHeader
        title="Data Setup & Reference Fitting"
        description="Configure baseline REFERENCE data distributions, EVALUATION batches, and TEMPORAL TRAJECTORY degradation sequences."
        icon={<Database className="w-6 h-6 text-[#3B82F6]" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Data Setup" }]}
      />

      {/* Concept Explanation Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-sans">
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 border-l-4 border-l-[#22C55E] shadow-sm">
          <h4 className="font-bold text-[#F3F4F6] uppercase tracking-wider mb-1 flex items-center gap-2 font-sans text-[11px]">
            <Database className="w-4 h-4 text-[#22C55E]" /> Reference Data
          </h4>
          <p className="text-[#9CA3AF] leading-relaxed">
            Known clean operating baseline distribution used to compute distance statistics for OOD, Drift, and Fusion.
          </p>
        </div>
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 border-l-4 border-l-[#3B82F6] shadow-sm">
          <h4 className="font-bold text-[#F3F4F6] uppercase tracking-wider mb-1 flex items-center gap-2 font-sans text-[11px]">
            <FileSpreadsheet className="w-4 h-4 text-[#3B82F6]" /> Evaluation Data
          </h4>
          <p className="text-[#9CA3AF] leading-relaxed">
            New production or test batch data evaluated against the fitted baseline state to measure operational risk.
          </p>
        </div>
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 border-l-4 border-l-[#64748B] shadow-sm">
          <h4 className="font-bold text-[#F3F4F6] uppercase tracking-wider mb-1 flex items-center gap-2 font-sans text-[11px]">
            <Activity className="w-4 h-4 text-[#64748B]" /> Temporal Trajectory
          </h4>
          <p className="text-[#9CA3AF] leading-relaxed">
            Sequential degradation state sequences containing reliability signals used to fit Failure Prediction and Early Warning.
          </p>
        </div>
      </div>

      {/* Model Selector Bar */}
      {models.length > 0 && (
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center space-x-3 text-xs">
            <Layers className="w-4 h-4 text-[#3B82F6] shrink-0" />
            <span className="font-semibold text-[#F3F4F6] font-sans">Active Model Context:</span>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-1.5 text-[#F3F4F6] font-mono focus:outline-none focus:border-[#3B82F6] text-xs"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name} ({m.model_id.slice(0, 8)}...)
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center space-x-1 text-[11px] font-mono text-[#9CA3AF]">
            <span>ID: {selectedModelId}</span>
            <CopyButton text={selectedModelId} />
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

              <form onSubmit={handleDatasetUpload} className="space-y-4 text-xs font-sans">
                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1.5">Dataset Category *</label>
                  <div className="grid grid-cols-1 gap-2">
                    <button
                      type="button"
                      onClick={() => setDatasetType("REFERENCE")}
                      className={`py-2 px-3 rounded-lg font-semibold text-left border transition-all flex items-center justify-between ${
                        datasetType === "REFERENCE"
                          ? "bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/40 shadow-sm"
                          : "bg-[#0F141B] text-[#9CA3AF] border-[#26303D] hover:bg-[#1A222C]"
                      }`}
                    >
                      <span className="font-mono text-xs">REFERENCE</span>
                      <span className="text-[10px] text-[#6B7280] font-sans">Baseline Distribution</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setDatasetType("EVALUATION")}
                      className={`py-2 px-3 rounded-lg font-semibold text-left border transition-all flex items-center justify-between ${
                        datasetType === "EVALUATION"
                          ? "bg-[#3B82F6]/10 text-[#60A5FA] border-[#3B82F6]/40 shadow-sm"
                          : "bg-[#0F141B] text-[#9CA3AF] border-[#26303D] hover:bg-[#1A222C]"
                      }`}
                    >
                      <span className="font-mono text-xs">EVALUATION</span>
                      <span className="text-[10px] text-[#6B7280] font-sans">Test Batch</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setDatasetType("TEMPORAL_TRAJECTORY")}
                      className={`py-2 px-3 rounded-lg font-semibold text-left border transition-all flex items-center justify-between ${
                        datasetType === "TEMPORAL_TRAJECTORY"
                          ? "bg-[#64748B]/20 text-[#F3F4F6] border-[#64748B]/50 shadow-sm"
                          : "bg-[#0F141B] text-[#9CA3AF] border-[#26303D] hover:bg-[#1A222C]"
                      }`}
                    >
                      <span className="font-mono text-xs">TEMPORAL TRAJECTORY</span>
                      <span className="text-[10px] text-[#6B7280] font-sans">Degradation Sequences</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1">Target Label Column (Optional)</label>
                  <input
                    type="text"
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    placeholder="e.g. target, Failure_Onset_Next"
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] font-mono"
                  />
                  <p className="mt-1 text-[11px] text-[#6B7280]">
                    Required for supervised training or ground-truth verification.
                  </p>
                </div>

                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1">CSV File *</label>
                  <input
                    type="file"
                    required
                    accept=".csv"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-[#9CA3AF] text-xs file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#3B82F6] file:text-white hover:file:bg-[#2563EB] cursor-pointer font-mono"
                  />
                </div>

                <button
                  type="submit"
                  disabled={uploading || !selectedModelId}
                  className="w-full py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg font-semibold shadow-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
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
              <div className="p-4 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-xl flex items-center justify-between shadow-sm">
                <div>
                  <div className="text-xs font-bold text-[#22C55E] flex items-center gap-1.5 font-sans">
                    <CheckCircle2 className="w-4 h-4 text-[#22C55E]" /> Reference Baseline Fitted Successfully
                  </div>
                  <div className="text-[11px] font-mono text-[#22C55E]/80 mt-1">
                    Baseline fitted on {fitResult.num_samples} samples across {fitResult.feature_names.length} features.
                  </div>
                </div>
                <StatusBadge status="FITTED" />
              </div>
            )}

            {/* Reference Datasets */}
            <SectionCard title="Reference Datasets (Baseline)" subtitle="Select a reference dataset to fit baseline state">
              {referenceDatasets.length === 0 ? (
                <p className="text-xs text-[#6B7280] py-4">No reference datasets registered for this model.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-[#26303D] bg-[#0F141B]">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-[#0F141B] text-[#9CA3AF] uppercase font-sans tracking-wider text-[11px] border-b border-[#26303D]">
                      <tr>
                        <th className="p-3.5">Filename</th>
                        <th className="p-3.5">Samples</th>
                        <th className="p-3.5">Features</th>
                        <th className="p-3.5">Target</th>
                        <th className="p-3.5 text-right">Reference Fit Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#26303D]">
                      {referenceDatasets.map((d) => (
                        <tr key={d.dataset_id} className="bg-[#151B23] hover:bg-[#1A222C] transition-colors">
                          <td className="p-3.5 font-bold text-[#22C55E]">
                            <div className="flex items-center space-x-1.5">
                              <span>{d.filename}</span>
                              <CopyButton text={d.dataset_id} />
                            </div>
                          </td>
                          <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold">{d.num_samples}</td>
                          <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold">{d.num_features}</td>
                          <td className="p-3.5 font-mono text-[#9CA3AF]">{d.target_column || "Label-Free"}</td>
                          <td className="p-3.5 text-right space-x-2">
                            <button
                              type="button"
                              onClick={() => handleFitReference(d.dataset_id)}
                              disabled={fittingDatasetId !== null}
                              className="px-3 py-1.5 text-xs font-semibold bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg transition-colors disabled:opacity-50 inline-flex items-center space-x-1 shadow-sm font-sans"
                            >
                              <Play className="w-3 h-3 fill-current mr-1" />
                              <span>{fittingDatasetId === d.dataset_id ? "Fitting..." : "FIT REFERENCE STATE"}</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => setDeletingDatasetId(d.dataset_id)}
                              title="Delete Dataset"
                              className="p-1.5 text-[#9CA3AF] hover:text-[#EF4444] bg-[#0F141B] hover:bg-[#1A222C] border border-[#26303D] rounded-lg transition-colors inline-flex items-center"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
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
                <p className="text-xs text-[#6B7280] py-4">No evaluation datasets registered for this model.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-[#26303D] bg-[#0F141B]">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-[#0F141B] text-[#9CA3AF] uppercase font-sans tracking-wider text-[11px] border-b border-[#26303D]">
                      <tr>
                        <th className="p-3.5">Filename</th>
                        <th className="p-3.5">Samples</th>
                        <th className="p-3.5">Features</th>
                        <th className="p-3.5">Target</th>
                        <th className="p-3.5">Uploaded</th>
                        <th className="p-3.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#26303D]">
                      {evaluationDatasets.map((d) => (
                        <tr key={d.dataset_id} className="bg-[#151B23] hover:bg-[#1A222C] transition-colors">
                          <td className="p-3.5 font-bold text-[#60A5FA]">
                            <div className="flex items-center space-x-1.5">
                              <span>{d.filename}</span>
                              <CopyButton text={d.dataset_id} />
                            </div>
                          </td>
                          <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold">{d.num_samples}</td>
                          <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold">{d.num_features}</td>
                          <td className="p-3.5 font-mono text-[#9CA3AF]">{d.target_column || "Label-Free"}</td>
                          <td className="p-3.5 text-[#9CA3AF] font-mono text-[11px]">{new Date(d.created_at).toLocaleDateString()}</td>
                          <td className="p-3.5 text-right">
                            <button
                              type="button"
                              onClick={() => setDeletingDatasetId(d.dataset_id)}
                              title="Delete Dataset"
                              className="p-1.5 text-[#9CA3AF] hover:text-[#EF4444] bg-[#0F141B] hover:bg-[#1A222C] border border-[#26303D] rounded-lg transition-colors inline-flex items-center"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>

            {/* Temporal Trajectory Datasets */}
            <SectionCard
              title="Temporal Trajectory Datasets"
              subtitle="Registered degradation state sequences for Failure Prediction and Early Warning model setup"
            >
              {temporalDatasets.length === 0 ? (
                <p className="text-xs text-[#6B7280] py-4">No temporal trajectory datasets registered for this model.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-[#26303D] bg-[#0F141B]">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-[#0F141B] text-[#9CA3AF] uppercase font-sans tracking-wider text-[11px] border-b border-[#26303D]">
                      <tr>
                        <th className="p-3.5">Filename</th>
                        <th className="p-3.5">Samples</th>
                        <th className="p-3.5">Features</th>
                        <th className="p-3.5">Target</th>
                        <th className="p-3.5">Uploaded</th>
                        <th className="p-3.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#26303D]">
                      {temporalDatasets.map((d) => (
                        <tr key={d.dataset_id} className="bg-[#151B23] hover:bg-[#1A222C] transition-colors">
                          <td className="p-3.5 font-bold text-[#9CA3AF]">
                            <div className="flex items-center space-x-1.5">
                              <span>{d.filename}</span>
                              <CopyButton text={d.dataset_id} />
                            </div>
                          </td>
                          <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold">{d.num_samples}</td>
                          <td className="p-3.5 font-mono text-[#F3F4F6] font-semibold">{d.num_features}</td>
                          <td className="p-3.5 font-mono text-[#9CA3AF]">{d.target_column || "Failure_Onset_Next"}</td>
                          <td className="p-3.5 text-[#9CA3AF] font-mono text-[11px]">{new Date(d.created_at).toLocaleDateString()}</td>
                          <td className="p-3.5 text-right">
                            <button
                              type="button"
                              onClick={() => setDeletingDatasetId(d.dataset_id)}
                              title="Delete Dataset"
                              className="p-1.5 text-[#9CA3AF] hover:text-[#EF4444] bg-[#0F141B] hover:bg-[#1A222C] border border-[#26303D] rounded-lg transition-colors inline-flex items-center"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
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

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deletingDatasetId !== null}
        title="Confirm Dataset Deletion"
        message="Are you sure you want to delete this dataset? This action cannot be undone."
        confirmText="Delete Dataset"
        cancelText="Cancel"
        onConfirm={confirmDeleteDataset}
        onCancel={() => setDeletingDatasetId(null)}
      />
    </div>
  );
}

