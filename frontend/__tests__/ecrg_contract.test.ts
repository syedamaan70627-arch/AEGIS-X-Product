import assert from "node:assert";
import { test } from "node:test";
import { ECRGDecisionResponse, ECRGEvidenceContract } from "../types/ecrg";

test("ECRG Contract: Evidence Input Contract Schema Validation", () => {
  const mockEvidence: ECRGEvidenceContract = {
    model_id: "013245af-9a9a-4e59-9648-0bb135f604d7",
    dataset_id: "test-eval-id",
    trajectory_id: "unit_001",
    state_index: 25,
    timestamp: "2026-09-02T20:35:00Z",
    ood_score: 0.12,
    uncertainty_score: 0.25,
    drift_score: 0.35,
    fused_risk: 0.28,
    signal_disagreement: 0.08,
    ood_drift_redundancy: 0.05,
    stress_robustness: 0.95,
    fault_sensitivity: 0.10,
    memory_similarity: 0.42,
    temporal_failure_probability: 0.18,
    early_warning_state: "NORMAL",
    prediction_horizon: 5,
    eventual_failure: null,
    failure_within_horizon: null,
  };

  assert.strictEqual(mockEvidence.model_id, "013245af-9a9a-4e59-9648-0bb135f604d7");
  assert.strictEqual(mockEvidence.fused_risk, 0.28);
  assert.strictEqual(mockEvidence.eventual_failure, null);
});

test("ECRG Contract: Governance Decision Response Structure", () => {
  const mockResponse: ECRGDecisionResponse = {
    decision_id: "dec-101",
    mode: "EVIDENCE_ONLY",
    action: "CONTINUE",
    warning_severity: "LOW",
    certification_banner: "LABEL-FREE / NON-CERTIFIED",
    calibrated: false,
    primary_supporting_signal: "fused_risk",
    supporting_evidence: ["Fused risk 0.28 below threshold"],
    contradictory_evidence: [],
    signal_disagreement_index: 0.08,
    consecutive_state_count: 10,
    in_cooldown: false,
    state_transition_occurred: false,
  };

  assert.strictEqual(mockResponse.mode, "EVIDENCE_ONLY");
  assert.strictEqual(mockResponse.action, "CONTINUE");
  assert.strictEqual(mockResponse.certification_banner, "LABEL-FREE / NON-CERTIFIED");
  assert.strictEqual(mockResponse.calibrated, false);
});
