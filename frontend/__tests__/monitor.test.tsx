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

describe("Batch Monitor UI & Fusion Engine Selector Suite", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (api.getModelCapabilities as any).mockResolvedValue({
      model_id: "mod_1",
      capabilities: {
        core_analysis: { status: "READY", reason: null },
      },
    });
  });

  it("renders Execution Setup form with clear Fusion Engine selector and separate Execute Analysis button", async () => {
    (api.listModels as any).mockResolvedValue({
      models: [
        {
          model_id: "mod_1",
          model_name: "AEGIS Test RF",
          task_type: "binary_classification",
        },
      ],
    });
    (api.listDatasets as any).mockResolvedValue({
      datasets: [
        {
          dataset_id: "ds_1",
          model_id: "mod_1",
          filename: "eval_batch.csv",
          dataset_type: "EVALUATION",
          num_samples: 100,
          num_features: 30,
        },
      ],
    });

    render(
      <ToastProvider>
        <BatchMonitorPage />
      </ToastProvider>
    );

    // Verify Labels
    await waitFor(() => {
      expect(screen.getByText("Target Model *")).toBeInTheDocument();
      expect(screen.getByText("Evaluation Dataset *")).toBeInTheDocument();
      expect(screen.getByText("Fusion Engine *")).toBeInTheDocument();
    });

    // Verify Fusion Engine select control and default value
    const fusionSelect = screen.getByLabelText("Fusion Engine *") as HTMLSelectElement;
    expect(fusionSelect).toBeInTheDocument();
    expect(fusionSelect.value).toBe("stress_robust");

    // Verify Options
    const options = Array.from(fusionSelect.options).map((o) => o.text);
    expect(options).toEqual([
      "StressRobust Fusion (Recommended)",
      "Original Fusion",
    ]);

    // Verify Execute Analysis Button is present below
    const executeBtn = screen.getByRole("button", { name: /Execute Analysis/i });
    expect(executeBtn).toBeInTheDocument();

    // Change option to Original Fusion
    fireEvent.change(fusionSelect, { target: { value: "original" } });
    expect(fusionSelect.value).toBe("original");

    // Switch back to StressRobust Fusion
    fireEvent.change(fusionSelect, { target: { value: "stress_robust" } });
    expect(fusionSelect.value).toBe("stress_robust");
  });

  it("triggers analysis with selected fusion method when Execute Analysis button is clicked", async () => {
    (api.listModels as any).mockResolvedValue({
      models: [{ model_id: "mod_1", model_name: "AEGIS Test RF", task_type: "binary_classification" }],
    });
    (api.listDatasets as any).mockResolvedValue({
      datasets: [{ dataset_id: "ds_1", model_id: "mod_1", filename: "eval.csv", dataset_type: "EVALUATION", num_samples: 50, num_features: 10 }],
    });
    (api.runAnalysis as any).mockResolvedValue({
      analysis_id: "an_123",
      status: "COMPLETED",
      ood: { aggregate_score: 0.1 },
      uncertainty: { aggregate_score: 0.2 },
      drift: { aggregate_score: 0.15 },
      fusion: { aggregate_fused_risk: 0.18 },
    });

    render(
      <ToastProvider>
        <BatchMonitorPage />
      </ToastProvider>
    );

    await waitFor(() => {
      const btn = screen.getByRole("button", { name: /Execute Analysis/i });
      expect(btn).not.toBeDisabled();
    });

    const executeBtn = screen.getByRole("button", { name: /Execute Analysis/i });
    fireEvent.submit(executeBtn.closest("form")!);

    await waitFor(() => {
      expect(api.runAnalysis).toHaveBeenCalledWith({
        model_id: "mod_1",
        evaluation_dataset_id: "ds_1",
        fusion_method: "stress_robust",
      });
    });
  });
});
