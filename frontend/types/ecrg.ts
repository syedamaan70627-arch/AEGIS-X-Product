/**
 * AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
 * Typed TypeScript Contracts for Frontend Integration.
 */

export type ECRGOperatingMode = "EVIDENCE_ONLY" | "CALIBRATED_GOVERNANCE";

export type ECRGGovernanceAction = "CONTINUE" | "WATCH" | "DEFER" | "ESCALATE";

export interface ECRGEvidenceContract {
  model_id: string;
  dataset_id: string;
  trajectory_id?: string;
  state_index: number;
  timestamp: string;
  source_analysis_id?: string;
  ood_score: number;
  uncertainty_score: number;
  drift_score: number;
  fused_risk: number;
  signal_disagreement: number;
  ood_drift_redundancy: number;
  stress_robustness: number;
  fault_sensitivity: number;
  memory_similarity: number;
  temporal_failure_probability: number;
  early_warning_state: string;
  prediction_horizon: number;
  eventual_failure?: boolean | null;
  failure_within_horizon?: boolean | null;
}

export interface ECRGCalibrationConfig {
  target_risk_alpha: number;
  calibration_set_size: number;
  calibrated_quantile_threshold?: number | null;
  calibration_method: string;
  risk_quantity_controlled: string;
  stated_assumptions: string[];
}

export interface ECRGDecisionResponse {
  decision_id: string;
  mode: ECRGOperatingMode;
  action: ECRGGovernanceAction;
  warning_severity: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  certification_banner: string;
  calibrated: boolean;
  calibration_config?: ECRGCalibrationConfig | null;
  population_risk?: number | null;
  selective_risk?: number | null;
  coverage?: number | null;
  primary_supporting_signal: string;
  supporting_evidence: string[];
  contradictory_evidence: string[];
  signal_disagreement_index: number;
  consecutive_state_count: number;
  in_cooldown: boolean;
  state_transition_occurred: boolean;
}
