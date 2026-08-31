import assert from "node:assert";
import { test } from "node:test";
import { ModelCapabilitiesResponse } from "../types/api";

test("Capability UX: Capability states map exclusively to allowed statuses", () => {
  const mockCap: ModelCapabilitiesResponse = {
    model_id: "test-id-123",
    capabilities: {
      core_analysis: { status: "READY" },
      stress_testing: { status: "READY" },
      fault_testing: { status: "READY" },
      failure_memory: { status: "REQUIRES_SETUP", reason: "Fault runs exist." },
      failure_prediction: { status: "NOT_AVAILABLE", reason: "Artifact not fitted." },
      early_warning: { status: "NOT_AVAILABLE", reason: "Artifact not fitted." },
    },
  };

  const allowedStatuses = new Set(["READY", "REQUIRES_SETUP", "NOT_AVAILABLE"]);

  Object.values(mockCap.capabilities).forEach((cap) => {
    assert.strictEqual(allowedStatuses.has(cap.status), true);
  });
});
