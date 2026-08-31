import assert from "node:assert";
import { test } from "node:test";

test("Reports V1: Report payload structure validation", () => {
  const mockReportPayload = {
    analysis_id: "test-analysis-id",
    model_id: "test-model-id",
    evaluation_dataset_id: "test-eval-id",
    reference_dataset_id: "test-ref-id",
    status: "completed",
    ood: { aggregate_score: 0.12 },
    uncertainty: { aggregate_score: 0.25 },
    drift: { aggregate_score: 0.35 },
    fusion: { aggregate_fused_risk: 0.28, method: "stress_robust" },
    limitations: ["Multi-signal fusion is domain context dependent."],
  };

  assert.strictEqual(mockReportPayload.status, "completed");
  assert.strictEqual(mockReportPayload.fusion.method, "stress_robust");
  assert.ok(mockReportPayload.limitations.length > 0);
});
