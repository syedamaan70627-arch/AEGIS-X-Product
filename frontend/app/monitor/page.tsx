"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { AnalysisResponse, DatasetRecord, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { Activity, AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Play } from "lucide-react";

export default function BatchMonitorPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Registry & Selection State
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  
  // Datasets for selected model
  const [referenceDatasets, setReferenceDatasets] = useState<DatasetRecord[]>([]);
  const [selectedRefDatasetId, setSelectedRefDatasetId] = useState<string>("");
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [fusionMethod, setFusionMethod] = useState<string>("stress_robust");

  // Reference State Readiness State
  const [referenceStateStatus, setReferenceStateStatus] = useState<"READY" | "NOT_FITTED" | "CHECKING" | "UNAVAILABLE">("CHECKING");
  const [fittingReference, setFittingReference] = useState(false);
  const [fittingError, setFittingError] = useState<string | null>(null);
  const [fitSuccessMsg, setFitSuccessMsg] = useState<string | null>(null);

  // Analysis Execution State
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Initial Load: Models
  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listModels();
        const loadedModels = res.models || [];
        setModels(loadedModels);

        if (loadedModels.length > 0) {
          const activeId = selectedModelId || loadedModels[0].model_id;
          setSelectedModelId(activeId);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load models.");
      } finally {
        setLoading(false);
      }
    }
    loadModels();
  }, []);

  // When selectedModelId changes: Query readiness & load datasets
  useEffect(() => {
    async function loadModelResources() {
      if (!selectedModelId) return;

      setReferenceStateStatus("CHECKING");
      setAnalysisResult(null);
      setAnalysisError(null);
      setFitSuccessMsg(null);
      setFittingError(null);

      try {
        // 1. Query model capabilities to detect reference state readiness
        const capsRes = await api.getModelCapabilities(selectedModelId);
        const coreStatus = capsRes.capabilities?.core_analysis?.status;
        if (coreStatus === "READY") {
          setReferenceStateStatus("READY");
        } else {
          setReferenceStateStatus("NOT_FITTED");
        }
      } catch (_) {
        setReferenceStateStatus("UNAVAILABLE");
      }

      try {
        // 2. Fetch datasets for selected model and categorize by type
        const res = await api.listDatasets(selectedModelId);
        const allDatasets = res.datasets || [];

        const refDs = allDatasets.filter((d) => d.dataset_type === "REFERENCE");
        const evalDs = allDatasets.filter((d) => d.dataset_type === "EVALUATION");

        setReferenceDatasets(refDs);
        setDatasets(evalDs);

        if (refDs.length > 0) {
          setSelectedRefDatasetId(refDs[0].dataset_id);
        } else {
          setSelectedRefDatasetId("");
        }

        if (evalDs.length > 0) {
          setSelectedDatasetId(evalDs[0].dataset_id);
        } else {
          setSelectedDatasetId("");
        }
      } catch (_) {}
    }

    loadModelResources();
  }, [selectedModelId]);

  // Handle Reference Fit
  const handleFitReference = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedRefDatasetId) return;

    setFittingReference(true);
    setFittingError(null);
    setFitSuccessMsg(null);

    try {
      await api.fitReferenceState(selectedModelId, selectedRefDatasetId);
      setReferenceStateStatus("READY");
      setFitSuccessMsg("Reference baseline fitted successfully. Operational analysis execution is now ready.");
      toast.success("Reference State Fitted", "AEGIS-X baseline reference state established.");
    } catch (err: any) {
      setFittingError(err.message || "Failed to fit reference baseline state.");
      toast.error("Reference Fit Error", err.message || "Could not fit reference state.");
    } finally {
      setFittingReference(false);
    }
  };

  // Handle Analysis Run
  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !selectedDatasetId) {
      setAnalysisError("Please select both a model and an evaluation dataset.");
      return;
    }

    if (referenceStateStatus !== "READY") {
      setAnalysisError("Reference State Required: Fit a reference baseline dataset before running operational analysis.");
      return;
    }

    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await api.runAnalysis({
        model_id: selectedModelId,
        evaluation_dataset_id: selectedDatasetId,
        fusion_method: fusionMethod,
      });
      setAnalysisResult(res);
      toast.success("Analysis Complete", `Fused risk score: ${(res.fusion.aggregate_fused_risk * 100).toFixed(1)}%`);
    } catch (err: any) {
      const msg = err.message || "Operational analysis execution failed.";
      if (msg.includes("has no fitted reference state") || msg.includes("REFERENCE_STATE_NOT_FITTED")) {
        setReferenceStateStatus("NOT_FITTED");
        setAnalysisError("Reference State Required: AEGIS-X needs a fitted reference dataset before operational reliability analysis can be executed.");
      } else {
        setAnalysisError(msg);
      }
      toast.error("Analysis Failed", msg);
    } finally {
      setAnalyzing(false);
    }
  };

  // Feature contract validation for selected reference dataset
  const activeModel = models.find((m) => m.model_id === selectedModelId);
  const selectedRefDs = referenceDatasets.find((d) => d.dataset_id === selectedRefDatasetId);
  const hasFeatureMismatch =
    activeModel?.n_features_in != null &&
    selectedRefDs?.num_features != null &&
    activeModel.n_features_in !== selectedRefDs.num_features;

  const canExecute = !!selectedModelId && referenceStateStatus === "READY" && !!selectedDatasetId && !analyzing;

  const steps = [
    { num: 1, label: "Active Model", state: selectedModelId ? "COMPLETE" : "REQUIRED" },
    { num: 2, label: "Reference State", state: referenceStateStatus === "READY" ? "COMPLETE" : "REQUIRED" },
    { num: 3, label: "Evaluation Batch", state: selectedDatasetId ? "READY" : "REQUIRED" },
    { num: 4, label: "Fusion Engine", state: fusionMethod ? "READY" : "REQUIRED" },
    { num: 5, label: "Execute", state: canExecute ? "READY" : "LOCKED" },
    { num: 6, label: "Inspect Results", state: analysisResult ? "COMPLETE" : "WAITING" },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Batch Operational Monitor"
        description="Execute AEGIS-X multi-signal operational analysis across OOD, Uncertainty, Drift, and Fusion detectors."
        icon={<Activity className="w-6 h-6 text-[#3B82F6]" />}
        breadcrumbs={[{ label: "Operations" }, { label: "Batch Monitor" }]}
      />

      {/* State-Aware 6-Step Workflow Stepper */}
      <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 shadow-sm font-sans">
        <div className="flex items-center justify-between overflow-x-auto gap-2 text-xs font-sans py-1">
          {steps.map((s, idx) => {
            const isComplete = s.state === "COMPLETE";
            const isReady = s.state === "READY";
            const isRequired = s.state === "REQUIRED";
            return (
              <React.Fragment key={s.num}>
                <div className="flex items-center space-x-2 shrink-0">
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold ${
                      isComplete
                        ? "bg-[#22C55E] text-slate-950"
                        : isReady
                        ? "bg-[#3B82F6] text-white"
                        : isRequired
                        ? "bg-amber-500/20 border border-amber-500/60 text-amber-400"
                        : "bg-[#0F141B] border border-[#26303D] text-[#6B7280]"
                    }`}
                  >
                    {s.num}
                  </span>
                  <div className="flex flex-col">
                    <span className={isComplete || isReady ? "text-[#F3F4F6] font-semibold" : "text-[#6B7280]"}>
                      {s.label}
                    </span>
                    <span
                      className={`text-[9px] font-mono uppercase ${
                        isComplete
                          ? "text-[#22C55E]"
                          : isReady
                          ? "text-[#60A5FA]"
                          : isRequired
                          ? "text-amber-400 font-bold"
                          : "text-[#6B7280]"
                      }`}
                    >
                      {s.state}
                    </span>
                  </div>
                </div>
                {idx < steps.length - 1 && <ChevronRight className="w-4 h-4 text-[#26303D] shrink-0" />}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {loading ? (
        <LoadingState message="Initializing batch monitor..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="space-y-8">
          {/* REFERENCE STATE PREREQUISITE PANEL */}
          {referenceStateStatus === "NOT_FITTED" && (
            <div className="bg-[#151B23] border border-amber-500/40 rounded-xl p-5 shadow-md space-y-4 font-sans text-xs">
              <div className="flex items-center justify-between border-b border-[#26303D] pb-3">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                  <div>
                    <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                      REFERENCE STATE REQUIRED
                    </h3>
                    <p className="text-xs text-slate-300 mt-0.5">
                      AEGIS-X needs a fitted reference dataset before operational reliability analysis can be executed.
                    </p>
                  </div>
                </div>
                <StatusBadge status="NOT_FITTED" />
              </div>

              {fittingError && <ErrorState message={fittingError} />}

              {referenceDatasets.length === 0 ? (
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-lg text-slate-400 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-sans">
                  <span>No REFERENCE datasets registered for this model. Upload a baseline CSV first.</span>
                  <Link
                    href="/data"
                    className="px-3.5 py-1.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold rounded-lg shrink-0 transition-colors font-sans text-xs"
                  >
                    Upload Reference Dataset in Data Setup →
                  </Link>
                </div>
              ) : (
                <form onSubmit={handleFitReference} className="space-y-4 max-w-xl">
                  <div>
                    <label htmlFor="ref-dataset-select" className="block font-bold text-slate-200 mb-1.5 text-xs">
                      Reference Dataset *
                    </label>
                    <div className="relative">
                      <select
                        id="ref-dataset-select"
                        value={selectedRefDatasetId}
                        onChange={(e) => setSelectedRefDatasetId(e.target.value)}
                        className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3.5 py-2.5 text-xs text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono appearance-none pr-10 cursor-pointer shadow-sm transition-colors"
                      >
                        {referenceDatasets.map((d) => (
                          <option key={d.dataset_id} value={d.dataset_id}>
                            {d.filename} ({d.num_samples} samples, {d.num_features} features)
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="w-4 h-4 text-[#9CA3AF] absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  {hasFeatureMismatch && activeModel && selectedRefDs && (
                    <div className="p-3 bg-rose-950/40 border border-rose-800/80 rounded-lg text-rose-300 font-mono text-[11px]">
                      <strong className="block font-bold mb-0.5 font-sans uppercase">
                        REFERENCE DATASET INCOMPATIBLE
                      </strong>
                      Expected: {activeModel.n_features_in} features | Received: {selectedRefDs.num_features} features
                    </div>
                  )}

                  <div className="flex items-center space-x-3 pt-1">
                    <button
                      type="submit"
                      disabled={fittingReference || hasFeatureMismatch || !selectedRefDatasetId}
                      className="px-5 py-2.5 bg-[#22C55E] hover:bg-[#16A34A] text-slate-950 font-bold rounded-lg text-xs shadow-sm transition-all disabled:opacity-50 inline-flex items-center space-x-2 cursor-pointer font-sans"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>{fittingReference ? "Fitting Reference State..." : "Fit Reference State"}</span>
                    </button>

                    <Link href="/data" className="text-slate-400 hover:text-slate-200 text-xs font-medium font-sans">
                      Go to Data Setup →
                    </Link>
                  </div>
                </form>
              )}
            </div>
          )}

          {fitSuccessMsg && (
            <div className="p-4 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-xl flex items-center justify-between shadow-sm">
              <div className="text-xs font-bold text-[#22C55E] flex items-center gap-1.5 font-sans">
                <CheckCircle2 className="w-4 h-4 text-[#22C55E]" /> {fitSuccessMsg}
              </div>
              <StatusBadge status="READY" />
            </div>
          )}

          {/* Analysis Form Configuration */}
          <SectionCard title="Execution Setup" subtitle="Configure operational analysis parameter options">
            {analysisError && <ErrorState message={analysisError} />}

            <form onSubmit={handleRunAnalysis} className="space-y-5 max-w-2xl w-full text-xs font-sans">
              <div>
                <label htmlFor="target-model-select" className="block font-bold text-[#F3F4F6] mb-1.5 text-xs font-sans">
                  Target Model *
                </label>
                <div className="relative">
                  <select
                    id="target-model-select"
                    value={selectedModelId}
                    onChange={(e) => setSelectedModelId(e.target.value)}
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3.5 py-2.5 text-xs text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono appearance-none pr-10 cursor-pointer shadow-sm transition-colors"
                  >
                    {models.length === 0 ? (
                      <option value="">No registered models available</option>
                    ) : (
                      models.map((m) => (
                        <option key={m.model_id} value={m.model_id}>
                          {m.model_name}
                        </option>
                      ))
                    )}
                  </select>
                  <ChevronDown className="w-4 h-4 text-[#9CA3AF] absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              <div>
                <label htmlFor="eval-dataset-select" className="block font-bold text-[#F3F4F6] mb-1.5 text-xs font-sans">
                  Evaluation Dataset *
                </label>
                <div className="relative">
                  <select
                    id="eval-dataset-select"
                    value={selectedDatasetId}
                    onChange={(e) => setSelectedDatasetId(e.target.value)}
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3.5 py-2.5 text-xs text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-mono appearance-none pr-10 cursor-pointer shadow-sm transition-colors"
                  >
                    {datasets.length === 0 ? (
                      <option value="">No EVALUATION datasets available</option>
                    ) : (
                      datasets.map((d) => (
                        <option key={d.dataset_id} value={d.dataset_id}>
                          {d.filename} ({d.num_samples} samples)
                        </option>
                      ))
                    )}
                  </select>
                  <ChevronDown className="w-4 h-4 text-[#9CA3AF] absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              <div>
                <label htmlFor="fusion-engine-select" className="block font-bold text-[#F3F4F6] mb-1.5 text-xs font-sans">
                  Fusion Engine *
                </label>
                <div className="relative">
                  <select
                    id="fusion-engine-select"
                    value={fusionMethod}
                    onChange={(e) => setFusionMethod(e.target.value)}
                    className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3.5 py-2.5 text-xs text-[#F3F4F6] focus:outline-none focus:border-[#3B82F6] font-sans appearance-none pr-10 cursor-pointer shadow-sm transition-colors"
                  >
                    <option value="stress_robust">StressRobust Fusion (Recommended)</option>
                    <option value="original">Original Fusion</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-[#9CA3AF] absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              <div className="pt-2 space-y-2">
                <button
                  type="submit"
                  disabled={!canExecute}
                  className="px-6 py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-lg font-semibold text-xs shadow-sm transition-all disabled:opacity-50 inline-flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{analyzing ? "Running Analysis..." : "Execute Analysis"}</span>
                </button>

                {referenceStateStatus === "NOT_FITTED" && (
                  <p className="text-[11px] text-amber-400 font-mono flex items-center space-x-1">
                    <span>Fit a reference state before running analysis.</span>
                  </p>
                )}
              </div>
            </form>
          </SectionCard>

          {/* Analysis Results View */}
          {analyzing && <LoadingState message="Running OOD, Uncertainty, Drift, and Fusion detectors..." />}

          {analysisResult && (
            <div className="space-y-8 animate-fadeIn">
              {/* Separate Reliability Signals Display */}
              <SectionCard
                title="Operational Reliability Signals"
                subtitle={`Evaluation Batch: ${datasets.find((d) => d.dataset_id === selectedDatasetId)?.filename || "evaluation_batch.csv"} | Analysis ID: ${analysisResult.analysis_id}`}
                action={
                  <div className="flex items-center space-x-3">
                    <CopyButton text={analysisResult.analysis_id} label="Copy Analysis ID" />
                    <StatusBadge status={analysisResult.status} />
                  </div>
                }
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <RiskIndicator label="OOD Risk" value={analysisResult.ood.aggregate_score} />
                  <RiskIndicator label="Uncertainty Risk" value={analysisResult.uncertainty.aggregate_score} />
                  <RiskIndicator label="Feature Drift Prevalence" value={analysisResult.drift.aggregate_score} />
                  <RiskIndicator label="Fused Risk Score" value={analysisResult.fusion.aggregate_fused_risk} />
                </div>

                <div className="mt-4 p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl text-[11px] font-sans text-slate-400 flex items-center justify-between">
                  <span>
                    <strong className="text-slate-300">Scientific Scope Notice:</strong> Individual reliability signals (OOD, Uncertainty, Drift) are preserved independently because their operational usefulness varies by deployment context.
                  </span>
                  <Link href="/reliability" className="text-[#3B82F6] hover:text-[#2563EB] font-semibold inline-flex items-center shrink-0 ml-4 font-sans">
                    Inspect Diagnostics →
                  </Link>
                </div>
              </SectionCard>

              {/* Separate Label-Aware Retrospective Diagnostics Section */}
              {analysisResult.diagnostics ? (
                <div className="p-6 bg-slate-900/90 border border-slate-800/80 rounded-2xl space-y-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      <div>
                        <h3 className="text-sm font-bold text-slate-100">Retrospective Diagnostics</h3>
                        <p className="text-xs text-slate-400">
                          Computed using ground-truth target labels present in evaluation dataset.
                        </p>
                      </div>
                    </div>
                    <StatusBadge status="LABEL_VERIFIED" />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Accuracy</div>
                      <div className="text-xl font-bold text-emerald-400 mt-1">
                        {(analysisResult.diagnostics.accuracy * 100).toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Error Rate</div>
                      <div className="text-xl font-bold text-amber-400 mt-1">
                        {(analysisResult.diagnostics.error_rate * 100).toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Total Failures</div>
                      <div className="text-xl font-bold text-rose-400 mt-1">
                        {analysisResult.diagnostics.num_failures} / {analysisResult.diagnostics.metrics.total_evaluation_samples}
                      </div>
                    </div>

                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 shadow-md">
                      <div className="text-slate-400 uppercase font-semibold text-[11px]">Spearman Correlation</div>
                      <div className="text-xl font-bold text-[#3B82F6] mt-1">
                        {analysisResult.diagnostics.correlation_fused_risk_vs_error ?? "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 flex items-center justify-between shadow-md">
                  <span>Target labels absent: Evaluation dataset is processed label-free for operational risk.</span>
                  <StatusBadge status="LABEL_FREE" />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
