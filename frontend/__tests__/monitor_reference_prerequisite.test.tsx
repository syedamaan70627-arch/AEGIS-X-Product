import React from "react";
import "@testing-library/jest-dom/vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import BatchMonitorPage from "@/app/monitor/page";
import { api } from "@/lib/api";
import { ToastProvider } from "@/components/providers/ToastProvider";

vi.mock("@/lib/api", () => ({
  api: {
    listModels: vi.fn(),
    listDatasets: vi.fn(),
    runAnalysis: vi.fn(),
    getModelCapabilities: vi.fn(),
    fitReferenceState: vi.fn(),
  },
}));

describe("Batch Monitor Reference State Prerequisite Suite", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("detects un-fitted reference state and renders REFERENCE STATE REQUIRED panel", async () => {
    (api.listModels as any).mockResolvedValue({
      models: [{ model_id: "test1", model_name: "test1", n_features_in: 64 }],
    });
    (api.getModelCapabilities as any).mockResolvedValue({
      model_id: "test1",
      capabilities: {
        core_analysis: { status: "REQUIRES_SETUP", reason: "Reference state not fitted" },
      },
    });
    (api.listDatasets as any).mockResolvedValue({
      datasets: [
        { dataset_id: "ref_1", model_id: "test1", filename: "reference_dataset.csv", dataset_type: "REFERENCE", num_samples: 50, num_features: 64 },
        { dataset_id: "eval_1", model_id: "test1", filename: "evaluation_100pct_ood.csv", dataset_type: "EVALUATION", num_samples: 100, num_features: 64 },
      ],
    });

    render(
      <ToastProvider>
        <BatchMonitorPage />
      </ToastProvider>
    );

    // Verify REFERENCE STATE REQUIRED panel appears
    await waitFor(() => {
      expect(screen.getByText("REFERENCE STATE REQUIRED")).toBeInTheDocument();
      expect(screen.getByText("AEGIS-X needs a fitted reference dataset before operational reliability analysis can be executed.")).toBeInTheDocument();
    });

    // Execute Analysis button must be disabled
    const executeBtn = screen.getByRole("button", { name: /Execute Analysis/i }) as HTMLButtonElement;
    expect(executeBtn.disabled).toBe(true);
    expect(screen.getByText("Fit a reference state before running analysis.")).toBeInTheDocument();
  });

  it("allows one-click reference fit and enables Execute Analysis upon success", async () => {
    (api.listModels as any).mockResolvedValue({
      models: [{ model_id: "test1", model_name: "test1", n_features_in: 64 }],
    });
    (api.getModelCapabilities as any).mockResolvedValue({
      model_id: "test1",
      capabilities: {
        core_analysis: { status: "REQUIRES_SETUP", reason: "Reference state not fitted" },
      },
    });
    (api.listDatasets as any).mockResolvedValue({
      datasets: [
        { dataset_id: "ref_1", model_id: "test1", filename: "reference_dataset.csv", dataset_type: "REFERENCE", num_samples: 50, num_features: 64 },
        { dataset_id: "eval_1", model_id: "test1", filename: "evaluation_100pct_ood.csv", dataset_type: "EVALUATION", num_samples: 100, num_features: 64 },
      ],
    });
    (api.fitReferenceState as any).mockResolvedValue({
      model_id: "test1",
      dataset_id: "ref_1",
      status: "fitted",
      num_samples: 50,
      feature_names: [],
      fitted_at: "2026-09-07T00:00:00Z",
    });

    render(
      <ToastProvider>
        <BatchMonitorPage />
      </ToastProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Fit Reference State/i })).toBeInTheDocument();
    });

    const fitBtn = screen.getByRole("button", { name: /Fit Reference State/i });
    fireEvent.click(fitBtn);

    await waitFor(() => {
      expect(api.fitReferenceState).toHaveBeenCalledWith("test1", "ref_1");
    });

    // Execute button becomes enabled after successful reference fit
    await waitFor(() => {
      const executeBtn = screen.getByRole("button", { name: /Execute Analysis/i }) as HTMLButtonElement;
      expect(executeBtn.disabled).toBe(false);
    });
  });

  it("detects feature count mismatch and displays REFERENCE DATASET INCOMPATIBLE alert", async () => {
    (api.listModels as any).mockResolvedValue({
      models: [{ model_id: "test1", model_name: "test1", n_features_in: 64 }],
    });
    (api.getModelCapabilities as any).mockResolvedValue({
      model_id: "test1",
      capabilities: {
        core_analysis: { status: "REQUIRES_SETUP", reason: "Reference state not fitted" },
      },
    });
    (api.listDatasets as any).mockResolvedValue({
      datasets: [
        { dataset_id: "ref_bad", model_id: "test1", filename: "incompatible_ref.csv", dataset_type: "REFERENCE", num_samples: 50, num_features: 10 },
      ],
    });

    render(
      <ToastProvider>
        <BatchMonitorPage />
      </ToastProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("REFERENCE DATASET INCOMPATIBLE")).toBeInTheDocument();
      expect(screen.getByText(/Expected: 64 features \| Received: 10 features/i)).toBeInTheDocument();
    });

    const fitBtn = screen.getByRole("button", { name: /Fit Reference State/i }) as HTMLButtonElement;
    expect(fitBtn.disabled).toBe(true);
  });
});
