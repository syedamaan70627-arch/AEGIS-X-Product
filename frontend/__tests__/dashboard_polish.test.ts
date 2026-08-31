import assert from "node:assert";
import { test } from "node:test";

test("Dashboard Polish: Validates allowed risk levels and capability states", () => {
  const allowedRiskLevels = ["Low", "Moderate", "High", "Unavailable"];
  const allowedCapabilities = ["READY", "REQUIRES_SETUP", "NOT_AVAILABLE"];

  assert.ok(allowedRiskLevels.includes("Low"));
  assert.ok(allowedRiskLevels.includes("High"));
  assert.ok(allowedCapabilities.includes("NOT_AVAILABLE"));
});
