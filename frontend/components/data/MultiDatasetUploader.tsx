"use client";

import React, { useState, useRef } from "react";
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, X, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { DatasetRecord } from "@/types/api";

interface FileQueueItem {
  id: string;
  file: File;
  status: "pending" | "uploading" | "success" | "error";
  record?: DatasetRecord;
  error?: string;
}

interface MultiDatasetUploaderProps {
  modelId: string;
  datasetType: "EVALUATION" | "REFERENCE";
  onComplete: () => void;
}

export const MultiDatasetUploader: React.FC<MultiDatasetUploaderProps> = ({
  modelId,
  datasetType,
  onComplete,
}) => {
  const [queue, setQueue] = useState<FileQueueItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFilesToQueue = (files: FileList | File[]) => {
    const newItems: FileQueueItem[] = Array.from(files)
      .filter((f) => f.name.endsWith(".csv"))
      .map((f, idx) => ({
        id: `${f.name}-${Date.now()}-${idx}`,
        file: f,
        status: "pending",
      }));

    if (newItems.length > 0) {
      setQueue((prev) => [...prev, ...newItems]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToQueue(e.target.files);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToQueue(e.dataTransfer.files);
    }
  };

  const removeItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const startUpload = async () => {
    if (!modelId || queue.length === 0 || isUploading) return;
    setIsUploading(true);

    const updatedQueue = [...queue];

    for (let i = 0; i < updatedQueue.length; i++) {
      const item = updatedQueue[i];
      if (item.status === "success") continue;

      // Mark uploading
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, status: "uploading", error: undefined } : q))
      );

      try {
        const formData = new FormData();
        formData.append("model_id", modelId);
        formData.append("dataset_type", datasetType);
        formData.append("file", item.file);

        const record = await api.registerDataset(formData);

        setQueue((prev) =>
          prev.map((q) => (q.id === item.id ? { ...q, status: "success", record } : q))
        );
      } catch (err: any) {
        console.error(`Upload error for ${item.file.name}:`, err);
        const errorMsg = err instanceof ApiError ? err.message : (err?.message || "Upload failed.");
        setQueue((prev) =>
          prev.map((q) => (q.id === item.id ? { ...q, status: "error", error: errorMsg } : q))
        );
      }
    }

    setIsUploading(false);
    onComplete();
  };

  const pendingCount = queue.filter((q) => q.status === "pending" || q.status === "error").length;
  const successCount = queue.filter((q) => q.status === "success").length;

  return (
    <div className="space-y-4 font-sans text-xs">
      {/* Drag and Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
          isDragOver
            ? "border-[#3B82F6] bg-[#3B82F6]/10"
            : "border-[#26303D] bg-[#0F141B] hover:border-[#3B82F6]/50 hover:bg-[#151B23]"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".csv"
          onChange={handleFileSelect}
          className="hidden"
        />
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#1A222C] text-[#3B82F6] mb-3">
          <Upload className="h-6 w-6" />
        </div>
        <p className="text-sm font-semibold text-[#F3F4F6]">
          Click or Drag & Drop multiple evaluation CSV files here
        </p>
        <p className="mt-1 text-xs text-[#9CA3AF]">
          Select 1 to 10+ CSV dataset files (e.g. evaluation_00pct_ood.csv, evaluation_100pct_ood.csv)
        </p>
      </div>

      {/* Queue List */}
      {queue.length > 0 && (
        <div className="space-y-2 rounded-xl border border-[#26303D] bg-[#151B23] p-4">
          <div className="flex items-center justify-between border-b border-[#26303D] pb-2 text-xs font-semibold text-[#F3F4F6]">
            <span>Upload Queue ({queue.length} file{queue.length > 1 ? "s" : ""})</span>
            <div className="flex items-center space-x-3">
              {successCount > 0 && (
                <span className="text-[#22C55E]">{successCount} Ready</span>
              )}
              {pendingCount > 0 && (
                <button
                  type="button"
                  onClick={startUpload}
                  disabled={isUploading}
                  className="px-3 py-1 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded font-medium shadow-sm disabled:opacity-50 transition-colors"
                >
                  {isUploading ? "Uploading Queue..." : `Upload ${pendingCount} File(s)`}
                </button>
              )}
            </div>
          </div>

          <div className="divide-y divide-[#26303D]/60 max-h-60 overflow-y-auto">
            {queue.map((item) => (
              <div key={item.id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3 truncate mr-3">
                  <FileText className="w-4 h-4 text-[#9CA3AF] shrink-0" />
                  <div className="truncate">
                    <div className="font-semibold text-[#F3F4F6] truncate">{item.file.name}</div>
                    <div className="text-[11px] text-[#6B7280] font-mono">
                      {(item.file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  {item.status === "pending" && (
                    <span className="text-[#9CA3AF] text-[11px] font-medium bg-[#1A222C] px-2 py-0.5 rounded border border-[#26303D]">
                      Ready to upload
                    </span>
                  )}
                  {item.status === "uploading" && (
                    <span className="inline-flex items-center text-[#3B82F6] text-[11px] font-medium bg-[#3B82F6]/10 px-2 py-0.5 rounded border border-[#3B82F6]/30">
                      <Loader2 className="w-3 h-3 animate-spin mr-1" /> Uploading...
                    </span>
                  )}
                  {item.status === "success" && (
                    <span className="inline-flex items-center text-[#22C55E] text-[11px] font-medium bg-[#22C55E]/10 px-2 py-0.5 rounded border border-[#22C55E]/30">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Ready ({item.record?.num_samples} samples)
                    </span>
                  )}
                  {item.status === "error" && (
                    <span className="inline-flex items-center text-red-400 text-[11px] font-medium bg-red-500/10 px-2 py-0.5 rounded border border-red-500/30 max-w-xs truncate" title={item.error}>
                      <AlertCircle className="w-3 h-3 mr-1 shrink-0" /> {item.error}
                    </span>
                  )}

                  {!isUploading && item.status !== "uploading" && (
                    <button
                      type="button"
                      onClick={() => removeItem(item.id)}
                      className="text-[#6B7280] hover:text-red-400 p-1 rounded"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
