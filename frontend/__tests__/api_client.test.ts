import assert from "node:assert";
import { test } from "node:test";
import { api } from "../lib/api";

test("API Client: Module exports expected API methods", () => {
  assert.strictEqual(typeof api.getHealth, "function");
  assert.strictEqual(typeof api.getReadiness, "function");
  assert.strictEqual(typeof api.getStatus, "function");
  assert.strictEqual(typeof api.listModels, "function");
  assert.strictEqual(typeof api.getModelCapabilities, "function");
  assert.strictEqual(typeof api.registerModel, "function");
  assert.strictEqual(typeof api.fitReferenceState, "function");
  assert.strictEqual(typeof api.runAnalysis, "function");
  assert.strictEqual(typeof api.runStressTest, "function");
  assert.strictEqual(typeof api.runFaultTest, "function");
  assert.strictEqual(typeof api.buildFailureMemory, "function");
  assert.strictEqual(typeof api.matchFailureMemoryQuery, "function");
  assert.strictEqual(typeof api.runFailurePrediction, "function");
  assert.strictEqual(typeof api.queryEarlyWarning, "function");
});
