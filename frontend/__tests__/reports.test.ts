import { describe, it, expect } from "vitest";
import { ReportPayload } from "../types/api";

describe("AEGIS-X Reports Frontend Data Models", () => {
  it("validates report payload structure and trust disposition", () => {
    const mockPayload: ReportPayload = {
      context: {
        report_id: "rep_1",
        user_id: "usr_1",
        model_id: "mod_1",
        model_name: "TestModel",
        analysis_id: "ana_1",
        generated_at: "2026-09-06T12:00:00Z",
        reference_dataset_id: "ds_ref",
        evaluation_dataset_id: "ds_eval",
        task_type: "classification",
      },
      report_type: "integrated",
      trust_disposition: "HIGH",
      trust_rationale: "Nominal reliability with ECRG action CONTINUE",
      completeness: {
        model_inventory: {
          name: "Model Inventory",
          status: "VERIFIED",
          evidence_count: 1,
          details: {},
        },
      },
      overall_completeness_pct: 100.0,
      reliability_summary: { aggregate_fused_risk: 0.05 },
      stress_lab_summary: { status: "VERIFIED" },
      fault_lab_summary: { status: "VERIFIED" },
      failure_explorer_summary: { status: "VERIFIED" },
      temporal_intelligence_summary: { status: "VERIFIED" },
      ecrg_governance_summary: { effective_action: "CONTINUE" },
      why_this_decision: [],
      action_plan: [],
      retraining_disposition: "NOT INDICATED",
      retraining_rationale: "Nominal bounds",
      deployment_suitability: { recommended_environment: "PRODUCTION" },
      trend_comparison: { has_previous_analysis: false },
      top_risk_drivers: [],
      scientific_limitations: ["Sample bounds apply"],
    };

    expect(mockPayload.trust_disposition).toBe("HIGH");
    expect(mockPayload.overall_completeness_pct).toBe(100.0);
    expect(mockPayload.context.model_name).toBe("TestModel");
  });
});
