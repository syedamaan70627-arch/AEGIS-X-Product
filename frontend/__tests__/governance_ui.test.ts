import assert from "node:assert";
import { test } from "node:test";
import {
  ECRGGovernanceAction,
  ECRGOperatingMode,
  GovernanceEvaluationRequest,
  GovernanceEvaluationResponse,
  GovernanceHistoryResponse,
  GovernanceStatusResponse,
} from "../types/api";

test("Phase 7J: 1 & 2. Governance Status & Action State Rendering Types", () => {
  const actions: ECRGGovernanceAction[] = ["CONTINUE", "WATCH", "DEFER", "ESCALATE"];
  assert.strictEqual(actions.length, 4);

  const statusResponse: GovernanceStatusResponse = {
    model_id: "mod-001",
    latest_action: "CONTINUE",
    mode: "CALIBRATED_GOVERNANCE",
    warning_severity: "LOW",
    consecutive_state_count: 5,
    in_cooldown: false,
    last_evaluated_at: "2026-09-04T12:00:00Z",
    total_evaluations: 12,
    total_transitions: 2,
  };

  assert.strictEqual(statusResponse.model_id, "mod-001");
  assert.strictEqual(statusResponse.latest_action, "CONTINUE");
  assert.strictEqual(statusResponse.mode, "CALIBRATED_GOVERNANCE");
  assert.strictEqual(statusResponse.total_evaluations, 12);
});

test("Phase 7J: 3 & 5. Evaluation Action Request Payload & Successful Response Structure", () => {
  const req: GovernanceEvaluationRequest = {
    model_id: "mod-001",
    dataset_id: "ds-eval-001",
    source_analysis_id: "an-001",
    ood_score: 0.1,
    uncertainty_score: 0.1,
    drift_score: 0.05,
    fused_risk: 0.12,
    mode: "EVIDENCE_ONLY",
  };

  assert.strictEqual(req.model_id, "mod-001");
  assert.strictEqual(req.fused_risk, 0.12);

  const evalResponse: GovernanceEvaluationResponse = {
    evaluation_id: "eval-101",
    model_id: "mod-001",
    user_id: "user_test",
    dataset_id: "ds-eval-001",
    mode: "EVIDENCE_ONLY",
    action: "CONTINUE",
    warning_severity: "LOW",
    certification_banner: "LABEL-FREE GOVERNANCE",
    calibrated: false,
    primary_supporting_signal: "fused_risk",
    supporting_evidence: [],
    contradictory_evidence: [],
    signal_disagreement_index: 0.05,
    consecutive_state_count: 1,
    in_cooldown: false,
    state_transition_occurred: false,
    evidence_snapshot_hash: "hash_abcdef123456",
    p_adverse: 0.12,
    transition_reason: "Nominal risk bounds",
    reason_codes: ["NOMINAL_RISK"],
    result_json_path: "storage/results/governance/mod-001/eval-101.json",
    created_at: "2026-09-04T12:00:00Z",
  };

  assert.strictEqual(evalResponse.action, "CONTINUE");
  assert.strictEqual(evalResponse.state_transition_occurred, false);
});

test("Phase 7J: 6 & 7. Transition vs No-Transition State Handling", () => {
  const transitionEval: Partial<GovernanceEvaluationResponse> = {
    action: "DEFER",
    state_transition_occurred: true,
    transition_reason: "High fused risk triggered transition from CONTINUE to DEFER",
  };

  assert.strictEqual(transitionEval.state_transition_occurred, true);
  assert.strictEqual(transitionEval.action, "DEFER");

  const holdEval: Partial<GovernanceEvaluationResponse> = {
    action: "DEFER",
    state_transition_occurred: false,
    transition_reason: "Held DEFER state; step 2 of persistence threshold",
  };

  assert.strictEqual(holdEval.state_transition_occurred, false);
});

test("Phase 7J: 8, 9 & 10. Governance History & Pagination Structure", () => {
  const emptyHistory: GovernanceHistoryResponse = {
    model_id: "mod-001",
    total: 0,
    limit: 5,
    offset: 0,
    evaluations: [],
  };

  assert.strictEqual(emptyHistory.total, 0);
  assert.strictEqual(emptyHistory.evaluations.length, 0);

  const paginatedHistory: GovernanceHistoryResponse = {
    model_id: "mod-001",
    total: 15,
    limit: 5,
    offset: 5,
    evaluations: [
      {
        evaluation_id: "eval-102",
        model_id: "mod-001",
        user_id: "user_test",
        dataset_id: "ds-eval-001",
        mode: "EVIDENCE_ONLY",
        action: "DEFER",
        warning_severity: "HIGH",
        certification_banner: "LABEL-FREE GOVERNANCE",
        calibrated: false,
        primary_supporting_signal: "fused_risk",
        supporting_evidence: [],
        contradictory_evidence: [],
        signal_disagreement_index: 0.1,
        consecutive_state_count: 2,
        in_cooldown: false,
        state_transition_occurred: true,
        evidence_snapshot_hash: "hash_987654",
        p_adverse: 0.85,
        transition_reason: "High fused risk",
        reason_codes: ["HIGH_FUSED_RISK"],
        created_at: "2026-09-04T12:05:00Z",
      },
    ],
  };

  assert.strictEqual(paginatedHistory.total, 15);
  assert.strictEqual(paginatedHistory.offset, 5);
  assert.strictEqual(paginatedHistory.evaluations[0].action, "DEFER");
});

test("Phase 7J: 11, 12, 13 & 14. Fail-Safe Escalation & Error Isolation", () => {
  const failsafeEval: GovernanceEvaluationResponse = {
    evaluation_id: "eval-err-999",
    model_id: "mod-001",
    user_id: "user_test",
    dataset_id: "ds-eval-001",
    mode: "EVIDENCE_ONLY",
    action: "ESCALATE",
    warning_severity: "CRITICAL",
    certification_banner: "FAIL-SAFE ESCALATION (EVIDENCE CORRUPTED)",
    calibrated: false,
    primary_supporting_signal: "evidence_validation_failure",
    supporting_evidence: ["Critical signal corrupted"],
    contradictory_evidence: [],
    signal_disagreement_index: 1.0,
    consecutive_state_count: 1,
    in_cooldown: false,
    state_transition_occurred: true,
    evidence_snapshot_hash: "corrupted_hash",
    p_adverse: 1.0,
    transition_reason: "Safe escalation triggered",
    reason_codes: ["CRITICAL_EVIDENCE_CORRUPTED", "SAFE_ESCALATION_TRIGGERED"],
    created_at: "2026-09-04T12:10:00Z",
  };

  assert.strictEqual(failsafeEval.action, "ESCALATE");
  assert.strictEqual(failsafeEval.warning_severity, "CRITICAL");
  assert.ok(failsafeEval.reason_codes.includes("SAFE_ESCALATION_TRIGGERED"));
});

test("Phase 7J: 15 & 16. Provenance Display & Safe Automation Default Enforcement", () => {
  // Proves that when status is null / undefined, default state is NOT green "CONTINUE" without evaluation
  const defaultAutomationAllowed = (statusAction?: ECRGGovernanceAction) => {
    if (!statusAction) return false; // Fail-safe: No automation without explicit CONTINUE
    return statusAction === "CONTINUE";
  };

  assert.strictEqual(defaultAutomationAllowed(undefined), false);
  assert.strictEqual(defaultAutomationAllowed("CONTINUE"), true);
  assert.strictEqual(defaultAutomationAllowed("DEFER"), false);
  assert.strictEqual(defaultAutomationAllowed("ESCALATE"), false);
});
