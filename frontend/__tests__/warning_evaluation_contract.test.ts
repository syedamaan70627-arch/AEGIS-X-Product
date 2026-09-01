import assert from "node:assert";
import { test, beforeEach, afterEach } from "node:test";
import { api, setAuthToken } from "../lib/api";
import { WarningEvaluationResponse, TrajectoryLevelMetrics, TrajectoryWarningResultItem } from "../types/api";

const originalFetch = globalThis.fetch;

beforeEach(() => {
  setAuthToken(null);
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  setAuthToken(null);
});

test("Early Warning Evaluation API contract matches backend response structure", async () => {
  let targetUrl = "";

  const mockResponse: WarningEvaluationResponse = {
    warning_id: "warn-eval-123",
    model_id: "model-456",
    status: "AVAILABLE",
    horizon_value: 3,
    horizon_unit: "controlled_degradation_states",
    warning_threshold: 0.46,
    state_level_metrics: { precision: 0.9, recall: 0.85 },
    trajectory_level_metrics: {
      failing_trajectories: 4,
      warned_failing_trajectories: 4,
      early_warning_coverage: 1.0,
      mean_lead_steps: 2.5,
      median_lead_steps: 2.0,
      non_failing_trajectories: 2,
      false_trajectory_warnings: 0,
      false_trajectory_warning_rate: 0.0,
      lead_time_unit: "controlled_degradation_states",
    },
    trajectory_results: [
      {
        trajectory_id: 0,
        eventually_fails: true,
        first_warning_state_index: 1,
        failure_state_index: 3,
        lead_steps: 2,
        is_early_warning: true,
        is_false_trajectory_warning: false,
      },
      {
        trajectory_id: 1,
        eventually_fails: false,
        first_warning_state_index: null,
        failure_state_index: null,
        lead_steps: null,
        is_early_warning: false,
        is_false_trajectory_warning: false,
      },
    ],
    warnings: [],
    limitations: [],
    created_at: "2026-09-02T00:00:00Z",
  };

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    targetUrl = input.toString();
    return new Response(JSON.stringify(mockResponse), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  const res = await api.evaluateEarlyWarning({ model_id: "model-456", evaluation_dataset_id: "ds-traj-999" });
  assert.ok(targetUrl.endsWith("/warnings/evaluate"));
  assert.strictEqual(res.warning_id, "warn-eval-123");
  assert.strictEqual(res.horizon_unit, "controlled_degradation_states");

  const metrics: TrajectoryLevelMetrics = res.trajectory_level_metrics;
  assert.strictEqual(metrics.failing_trajectories, 4);
  assert.strictEqual(metrics.warned_failing_trajectories, 4);
  assert.strictEqual(metrics.early_warning_coverage, 1.0);
  assert.strictEqual(metrics.mean_lead_steps, 2.5);
  assert.strictEqual(metrics.median_lead_steps, 2.0);
  assert.strictEqual(metrics.non_failing_trajectories, 2);
  assert.strictEqual(metrics.false_trajectory_warnings, 0);
  assert.strictEqual(metrics.false_trajectory_warning_rate, 0.0);
  assert.strictEqual(metrics.lead_time_unit, "controlled_degradation_states");

  const results: TrajectoryWarningResultItem[] = res.trajectory_results;
  assert.strictEqual(results.length, 2);
  assert.strictEqual(results[0].lead_steps, 2);
  assert.strictEqual(results[1].first_warning_state_index, null);
  assert.strictEqual(results[1].lead_steps, null);
});

test("Query Early Warning contract remains unchanged", async () => {
  let targetUrl = "";

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    targetUrl = input.toString();
    return new Response(
      JSON.stringify({
        warning_id: "warn-query-789",
        model_id: "model-456",
        status: "AVAILABLE",
        is_warning_triggered: true,
        warning_score: 0.82,
        threshold: 0.46,
        horizon_value: 3,
        horizon_unit: "controlled_degradation_states",
        warnings: [],
        limitations: [],
        created_at: "2026-09-02T00:00:00Z",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  const res = await api.queryEarlyWarning({ model_id: "model-456", evaluation_dataset_id: "ds-traj-999" });
  assert.ok(targetUrl.endsWith("/warnings"));
  assert.strictEqual(res.warning_id, "warn-query-789");
  assert.strictEqual(res.is_warning_triggered, true);
  assert.strictEqual(res.warning_score, 0.82);
  assert.strictEqual(res.horizon_unit, "controlled_degradation_states");
});
