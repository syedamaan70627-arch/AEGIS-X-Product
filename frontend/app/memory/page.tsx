"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { MemoryBuildResponse, MemoryMatchResponse, ModelRecord } from "@/types/api";
import { CopyButton } from "@/components/ui/CopyButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/providers/ToastProvider";
import { BrainCircuit, CheckCircle2, Layers, Play, Search } from "lucide-react";

export default function FailureMemoryPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [memories, setMemories] = useState<any[]>([]);
  const [selectedMemoryId, setSelectedMemoryId] = useState<string>("");

  // Build state
  const [building, setBuilding] = useState(false);
  const [buildResult, setBuildResult] = useState<MemoryBuildResponse | null>(null);
  const [buildError, setBuildError] = useState<string | null>(null);

  // Match Query state
  const [queryInput, setQueryInput] = useState<string>('{"ood_risk": 0.8, "uncertainty_risk": 0.6, "drift_risk": 0.4}');
  const [matching, setMatching] = useState(false);
  const [matchResult, setMatchResult] = useState<MemoryMatchResponse | null>(null);
  const [matchError, setMatchError] = useState<string | null>(null);

  useEffect(() => {
    async function loadModels() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listModels();
        const loaded = res.models || [];
        setModels(loaded);
        if (loaded.length > 0) {
          const activeId = selectedModelId || loaded[0].model_id;
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

  useEffect(() => {
    async function loadMemories() {
      if (!selectedModelId) return;
      try {
        const res = await api.listModelFailureMemories(selectedModelId);
        const mems = res.memories || [];
        setMemories(mems);
        if (mems.length > 0) {
          setSelectedMemoryId(mems[0].memory_id);
        } else {
          setSelectedMemoryId("");
        }
      } catch (_) {}
    }
    loadMemories();
  }, [selectedModelId]);

  const handleBuildMemory = async () => {
    if (!selectedModelId) return;
    setBuilding(true);
    setBuildError(null);
    try {
      const res = await api.buildFailureMemory(selectedModelId, { n_clusters: 3, random_state: 42 });
      setBuildResult(res);
      toast.success("Failure Memory Built", `Fitted ${res.signatures.length} signature centroids`);
      const memsRes = await api.listModelFailureMemories(selectedModelId);
      setMemories(memsRes.memories || []);
      if (memsRes.memories && memsRes.memories.length > 0) {
        setSelectedMemoryId(memsRes.memories[0].memory_id);
      }
    } catch (err: any) {
      setBuildError(err.message || "Failure Memory building failed.");
      toast.error("Build Failed", err.message || "Could not fit signature centroids.");
    } finally {
      setBuilding(false);
    }
  };

  const handleMatchQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMemoryId) {
      setMatchError("Please select or fit a Failure Memory instance first.");
      return;
    }

    setMatching(true);
    setMatchError(null);
    try {
      const parsedProfile = JSON.parse(queryInput);
      const res = await api.matchFailureMemoryQuery(selectedMemoryId, { query_profile: parsedProfile });
      setMatchResult(res);
      toast.success("Query Match Complete", res.is_known_pattern ? `Matched Signature #${res.matched_signature_id}` : "Unmatched Pattern");
    } catch (err: any) {
      setMatchError(err.message || "Invalid query profile JSON format or query match error.");
      toast.error("Query Error", err.message || "Execution failed.");
    } finally {
      setMatching(false);
    }
  };

  if (loading) return <LoadingState message="Initializing Failure Memory..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Failure Memory Engine"
        description="Fits unsupervised reliability signature centroids from aggregated condition profiles and matches incoming query condition profiles."
        icon={<BrainCircuit className="w-6 h-6 text-[#3B82F6]" />}
        breadcrumbs={[{ label: "Intelligence" }, { label: "Failure Memory" }]}
      />

      {/* Model Selector Bar */}
      {models.length > 0 && (
        <div className="bg-[#151B23] border border-[#26303D] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-sans shadow-sm">
          <div className="flex items-center space-x-3">
            <Layers className="w-4 h-4 text-[#3B82F6] shrink-0" />
            <span className="font-semibold text-[#F3F4F6]">Active Model:</span>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-1.5 text-[#F3F4F6] font-mono focus:outline-none focus:border-[#3B82F6] text-xs"
            >
              {models.map((m) => (
                <option key={m.model_id} value={m.model_id}>
                  {m.model_name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleBuildMemory}
            disabled={building || !selectedModelId}
            className="px-4 py-2 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 inline-flex items-center space-x-1.5 shrink-0 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
          >
            <BrainCircuit className="w-4 h-4" />
            <span>{building ? "Fitting Signatures..." : "Build Failure Memory"}</span>
          </button>
        </div>
      )}

      {buildError && <ErrorState message={buildError} />}

      {/* Concept Note */}
      <div className="p-4 bg-[#151B23] border border-[#26303D] rounded-xl text-xs text-[#9CA3AF] shadow-sm font-sans">
        <span className="font-sans font-bold text-[#F3F4F6] uppercase tracking-wider block mb-0.5 text-[11px]">Non-Causal Pattern Matching</span>
        Failure Memory stores recurring <strong>Reliability Signatures</strong> (Condition Profiles). Matches indicate topological similarity to historical fault condition profiles and are associative, not confirmed root causes.
      </div>

      {memories.length === 0 && !buildResult ? (
        <EmptyState
          title="Failure Memory Requires Setup"
          description="Execute fault injection runs in the Fault Lab, then click 'Build Failure Memory' to extract unsupervised signature centroids."
          actionText="Go to Fault Lab"
          actionHref="/faults"
          icon={<BrainCircuit className="w-8 h-8" />}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Fitted Signatures View */}
          <SectionCard
            title="Fitted Reliability Signatures"
            subtitle={`Fitted Memory ID: ${selectedMemoryId || buildResult?.memory_id || "N/A"}`}
            action={
              <div className="flex items-center space-x-2 font-mono text-xs">
                {(selectedMemoryId || buildResult?.memory_id) && (
                  <CopyButton text={selectedMemoryId || buildResult?.memory_id || ""} />
                )}
                <StatusBadge status="FITTED" />
              </div>
            }
          >
            {buildResult?.signatures ? (
              <div className="space-y-4">
                {buildResult.signatures.map((sig) => (
                  <div key={sig.signature_id} className="p-4 bg-[#0F141B] border border-[#26303D] rounded-xl space-y-2 text-xs shadow-sm font-sans">
                    <div className="flex items-center justify-between font-sans">
                      <span className="font-bold text-[#3B82F6] font-mono">Signature #{sig.signature_id}</span>
                      <span className="text-[#9CA3AF] font-mono">Samples: {sig.sample_count}</span>
                    </div>
                    <div className="text-[#9CA3AF] font-semibold font-sans">Centroid Profile:</div>
                    <pre className="p-3 bg-[#151B23] rounded-lg border border-[#26303D] font-mono text-[11px] text-[#F3F4F6] overflow-x-auto">
                      {JSON.stringify(sig.centroid_profile, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#6B7280] py-4 font-sans">Select a fitted memory instance to inspect signature centroids.</p>
            )}
          </SectionCard>

          {/* Match Query Profile */}
          <SectionCard title="Match Query Condition Profile" subtitle="Evaluate incoming condition profile against fitted centroids">
            {matchError && <ErrorState message={matchError} />}

            <form onSubmit={handleMatchQuery} className="space-y-4 text-xs font-sans">
              <div>
                <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Query Condition Profile (JSON) *</label>
                <textarea
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg p-3 text-[#F3F4F6] font-mono h-24 focus:outline-none focus:border-[#3B82F6]"
                />
              </div>

              <button
                type="submit"
                disabled={matching || !selectedMemoryId}
                className="w-full py-2.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] font-sans"
              >
                <Search className="w-4 h-4" />
                <span>{matching ? "Matching Query..." : "Match Query Profile"}</span>
              </button>
            </form>

            {matchResult && (
              <div className="mt-6 p-4 bg-slate-950/80 border border-slate-800/80 rounded-xl space-y-3 text-xs shadow-md">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <span className="font-bold text-slate-200">Query Match Result</span>
                  <StatusBadge status={matchResult.is_known_pattern ? "MATCHED_PATTERN" : "UNMATCHED"} />
                </div>

                <div className="grid grid-cols-2 gap-2 text-slate-300 font-mono">
                  <div>
                    <span className="text-slate-400">Matched Signature ID:</span>{" "}
                    <span className="font-bold">{matchResult.matched_signature_id ?? "None"}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Centroid Distance:</span>{" "}
                    <span className="font-bold">
                      {matchResult.signature_distance != null ? matchResult.signature_distance.toFixed(4) : "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </SectionCard>
        </div>
      )}
    </div>
  );
}

