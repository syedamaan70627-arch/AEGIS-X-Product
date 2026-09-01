import assert from "node:assert";
import { test, beforeEach, afterEach } from "node:test";
import { api, setAuthToken } from "../lib/api";

const originalFetch = globalThis.fetch;

beforeEach(() => {
  setAuthToken(null);
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  setAuthToken(null);
});

test("Scenario 7: Failure Prediction setup API call sends fit request to model endpoint", async () => {
  let targetUrl = "";
  let parsedBody: any = null;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    targetUrl = input.toString();
    parsedBody = JSON.parse((init?.body as string) || "{}");
    return new Response(
      JSON.stringify({
        model_id: "model-pred-123",
        status: "fitted",
        selected_predictor: "random_forest_dynamic",
        horizon_steps: 1,
        horizon_unit: "controlled_degradation_states",
        threshold: 0.45,
        fitted_at: "2026-09-02T00:00:00Z",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  const res = await api.fitFailurePrediction("model-pred-123", {});
  assert.ok(targetUrl.endsWith("/failure-prediction/model-pred-123/fit"));
  assert.strictEqual(res.status, "fitted");
  assert.strictEqual(res.horizon_unit, "controlled_degradation_states");
});

test("Scenario 8: Early Warning setup API call sends fit request to model endpoint", async () => {
  let targetUrl = "";
  let parsedBody: any = null;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    targetUrl = input.toString();
    parsedBody = JSON.parse((init?.body as string) || "{}");
    return new Response(
      JSON.stringify({
        model_id: "model-warn-456",
        status: "fitted",
        horizon_value: 3,
        horizon_unit: "controlled_degradation_states",
        warning_threshold: 0.46,
        fitted_at: "2026-09-02T00:00:00Z",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  const res = await api.fitEarlyWarning("model-warn-456", { horizon_val: 3 });
  assert.ok(targetUrl.endsWith("/early-warning/model-warn-456/fit"));
  assert.strictEqual(parsedBody.horizon_val, 3);
  assert.strictEqual(res.status, "fitted");
  assert.strictEqual(res.horizon_unit, "controlled_degradation_states");
});
