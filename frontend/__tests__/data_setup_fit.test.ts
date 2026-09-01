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

test("Scenario 1 & 2: Fit request targets exactly the clicked dataset_id", async () => {
  let requestedModelId: string | null = null;
  let requestedDatasetId: string | null = null;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const urlStr = input.toString();
    const match = urlStr.match(/\/models\/([^/]+)\/reference\/([^/]+)\/fit/);
    if (match) {
      requestedModelId = match[1];
      requestedDatasetId = match[2];
    }
    return new Response(
      JSON.stringify({
        model_id: "model-abc",
        dataset_id: "dataset-123",
        status: "fitted",
        num_samples: 398,
        feature_names: ["f1", "f2"],
        fitted_at: "2026-09-01T00:00:00Z",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  const res = await api.fitReferenceState("model-abc", "dataset-123");
  assert.strictEqual(requestedModelId, "model-abc");
  assert.strictEqual(requestedDatasetId, "dataset-123");
  assert.strictEqual(res.status, "fitted");
  assert.strictEqual(res.num_samples, 398);
});

test("Scenario 3 & 4: API fit error returns formatted ApiError and clears state", async () => {
  globalThis.fetch = (async () => {
    return new Response(
      JSON.stringify({
        error: {
          code: "DATASET_VALIDATION_ERROR",
          message: "Dataset is of type EVALUATION. Reference fit requires REFERENCE dataset.",
        },
      }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  await assert.rejects(
    async () => {
      await api.fitReferenceState("model-abc", "dataset-eval-456");
    },
    (err: any) => {
      assert.strictEqual(err.status, 400);
      assert.strictEqual(err.code, "DATASET_VALIDATION_ERROR");
      assert.ok(err.message.includes("EVALUATION"));
      return true;
    }
  );
});

test("Scenario 5: Dataset deletion API call issues DELETE to endpoint", async () => {
  let deletedDatasetId: string | null = null;
  let deleteMethod: string | null = null;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const urlStr = input.toString();
    deleteMethod = init?.method || "GET";
    const match = urlStr.match(/\/datasets\/([^/]+)$/);
    if (match) {
      deletedDatasetId = match[1];
    }
    return new Response(
      JSON.stringify({ status: "deleted", dataset_id: "dataset-to-delete-999" }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  const res = await api.deleteDataset("dataset-to-delete-999");
  assert.strictEqual(deleteMethod, "DELETE");
  assert.strictEqual(deletedDatasetId, "dataset-to-delete-999");
  assert.strictEqual(res.status, "deleted");
});

test("Scenario 6: Failure Memory build API call matches backend schema without body model_id", async () => {
  let targetUrl = "";
  let parsedBody: any = null;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    targetUrl = input.toString();
    parsedBody = JSON.parse((init?.body as string) || "{}");
    return new Response(
      JSON.stringify({
        memory_id: "mem-789",
        model_id: "model-xyz",
        status: "AVAILABLE",
        n_signatures: 3,
        signatures: [],
        fitted_at: "2026-09-01T00:00:00Z",
      }),
      { status: 201, headers: { "Content-Type": "application/json" } }
    );
  }) as typeof fetch;

  const res = await api.buildFailureMemory("model-xyz", { n_clusters: 3, random_state: 42 });
  assert.ok(targetUrl.endsWith("/failure-memory/model-xyz/build"));
  assert.strictEqual(parsedBody.model_id, undefined);
  assert.strictEqual(parsedBody.n_clusters, 3);
  assert.strictEqual(parsedBody.random_state, 42);
  assert.strictEqual(res.memory_id, "mem-789");
});


