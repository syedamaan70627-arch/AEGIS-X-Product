/**
 * AEGIS-X AI Reliability Platform - API Type Definitions
 */

export interface SystemStatus {
  api_status: string;
  api_version: string;
  auth_mode: "disabled" | "required";
  database_backend: "sqlite" | "supabase";
  storage_backend: "local" | "supabase";
  supported_model_formats: string[];
  supported_dataset_formats: string[];
  supported_task_types: string[];
  reliability_capabilities: string[];
}

export interface UserMe {
  user_id: string;
  email: string;
  authenticated: boolean;
}

export interface ReadinessResponse {
  status: "OK" | "DEGRADED";
  database: string;
  storage: string;
  auth: string;
}

export interface ModelRecord {
  model_id: string;
  model_name: string;
  task_type: string;
  description?: string | null;
  filename: string;
  predict_supported: boolean;
  predict_proba_supported: boolean;
  n_features_in?: number | null;
  classes?: (string | number)[] | null;
  feature_names?: string[] | null;
  created_at: string;
  status: string;
}

export interface ModelListResponse {
  total: number;
  models: ModelRecord[];
}

export interface DatasetRecord {
  dataset_id: string;
  model_id: string;
  dataset_type: "REFERENCE" | "EVALUATION" | "TEMPORAL_TRAJECTORY" | "PREDICTION_TRAJECTORY";
  filename: string;
  target_column?: string | null;
  num_samples: number;
  num_features: number;
  feature_names: string[];
  has_target: boolean;
  created_at: string;

  status: string;
}

export interface DatasetListResponse {
  total: number;
  datasets: DatasetRecord[];
}

export interface ReferenceFitResponse {
  model_id: string;
  dataset_id: string;
  status: "fitted";
  num_samples: number;
  feature_names: string[];
  fitted_at: string;
}

export interface CapabilityStatusDetail {
  status: "READY" | "REQUIRES_SETUP" | "NOT_AVAILABLE";
  reason?: string | null;
}

export interface ModelCapabilitiesResponse {
  model_id: string;
  capabilities: {
    core_analysis: CapabilityStatusDetail;
    stress_testing: CapabilityStatusDetail;
    fault_testing: CapabilityStatusDetail;
    failure_memory: CapabilityStatusDetail;
    failure_prediction: CapabilityStatusDetail;
    early_warning: CapabilityStatusDetail;
  };
}

export interface SignalDetail {
  status: string;
  aggregate_score?: number | null;
  scores?: number[] | null;
  details?: Record<string, any> | null;
  warnings: string[];
}

export interface FusionDetail {
  status: string;
  method: string;
  aggregate_fused_risk: number;
  fused_risk_scores?: number[] | null;
  threshold?: number | null;
  model_metadata?: Record<string, any> | null;
  warnings: string[];
  limitations: string[];
}

export interface DiagnosticDetail {
  accuracy: number;
  error_rate: number;
  num_failures: number;
  correlation_fused_risk_vs_error?: number | null;
  metrics: Record<string, any>;
}

export interface AnalysisResponse {
  analysis_id: string;
  model_id: string;
  reference_dataset_id: string;
  evaluation_dataset_id: string;
  created_at: string;
  status: string;
  model_capability_summary: Record<string, boolean>;
  ood: SignalDetail;
  uncertainty: SignalDetail;
  drift: SignalDetail;
  fusion: FusionDetail;
  warnings: string[];
  limitations: string[];
  diagnostics?: DiagnosticDetail | null;
}

export interface AnalysisSummary {
  analysis_id: string;
  model_id: string;
  reference_dataset_id: string;
  evaluation_dataset_id: string;
  status: string;
  fusion_method: string;
  has_labels: boolean;
  aggregate_ood_risk?: number | null;
  aggregate_uncertainty?: number | null;
  aggregate_drift_score?: number | null;
  aggregate_fused_risk?: number | null;
  created_at: string;
}

export interface AnalysisListResponse {
  total: number;
  analyses: AnalysisSummary[];
}

export interface StressTestResponse {
  stress_test_id: string;
  model_id: string;
  evaluation_dataset_id: string;
  stress_type: string;
  severity: number;
  random_state: number;
  status: string;
  original_risk?: number | null;
  stressed_risk?: number | null;
  risk_delta?: number | null;
  accuracy_delta?: number | null;
  original_accuracy?: number | null;
  stressed_accuracy?: number | null;
  details?: Record<string, any> | null;
  warnings: string[];
  limitations: string[];
  created_at: string;
}

export interface StressTestListResponse {
  total: number;
  stress_tests: Record<string, any>[];
}

export interface FaultTestResponse {
  fault_test_id: string;
  model_id: string;
  evaluation_dataset_id: string;
  fault_type: string;
  severity: number;
  affected_features: string[];
  status: string;
  transformation_metadata?: Record<string, any> | null;
  warnings: string[];
  limitations: string[];
  created_at: string;
}

export interface FaultTestListResponse {
  total: number;
  fault_tests: Record<string, any>[];
}

export interface FailureEventDetail {
  sample_id: number;
  ood_risk: number;
  uncertainty_risk: number;
  drift_risk: number;
  fused_risk: number;
  is_high_risk_warning: boolean;
  fault_type?: string | null;
  severity?: number | null;
  has_actual_failure?: boolean | null;
  is_silent_failure?: boolean | null;
}

export interface FailureExplorerResponse {
  fault_test_id: string;
  is_label_aware: boolean;
  total_samples: number;
  total_warnings: number;
  total_failures: number;
  silent_failures: number;
  silent_failure_rate: number;
  silent_failure_status: "AVAILABLE" | "NOT_AVAILABLE";
  failure_events: FailureEventDetail[];
  summary_by_fault: Record<string, any>;
  warnings: string[];
  limitations: string[];
}

export interface SignatureDetail {
  signature_id: number;
  centroid_profile: Record<string, number>;
  feature_names: string[];
  sample_count: number;
  distance_threshold: number;
  confidence: number;
}

export interface MemoryBuildResponse {
  memory_id: string;
  model_id: string;
  status: string;
  n_signatures: number;
  signatures: SignatureDetail[];
  silhouette_score?: number | null;
  stability_ari?: number | null;
  quality_summary: Record<string, any>;
  warnings: string[];
  limitations: string[];
  fitted_at: string;
}

export interface MemoryMatchResponse {
  matched_signature_id?: number | null;
  signature_distance?: number | null;
  distance_threshold?: number | null;
  is_known_pattern: boolean;
  centroid_profile?: Record<string, number> | null;
  associated_fault_distribution?: Record<string, number> | null;
  warnings: string[];
  limitations: string[];
}

export interface MemoryListResponse {
  total: number;
  memories: Record<string, any>[];
}

export interface PredictionEventDetail {
  sample_id: number;
  predicted_failure_prob: number;
  is_failure_warning: boolean;
  threshold: number;
  actual_failure_onset?: boolean | null;
}

export interface PredictionResponse {
  prediction_id: string;
  model_id: string;
  status: "AVAILABLE" | "NOT_AVAILABLE" | "ERROR";
  reason?: string | null;
  horizon_steps: number;
  horizon_unit: "controlled_degradation_states";
  selected_predictor?: string | null;
  threshold?: number | null;
  aggregate_onset_warning_rate?: number | null;
  mean_predicted_probability?: number | null;
  predictions?: PredictionEventDetail[] | null;
  heldout_metrics?: Record<string, any> | null;
  warnings: string[];
  limitations: string[];
  created_at: string;
}

export interface WarningResponse {
  warning_id: string;
  model_id: string;
  status: "AVAILABLE" | "NOT_AVAILABLE" | "ERROR";
  reason?: string | null;
  warning_score?: number | null;
  is_warning_triggered: boolean;
  threshold: number;
  horizon_value: number;
  horizon_unit: "controlled_degradation_states";
  signals?: Record<string, any> | null;
  warnings: string[];
  limitations: string[];
  created_at: string;
}

export interface WarningEvaluationResponse {
  warning_id: string;
  model_id: string;
  status: string;
  horizon_value: number;
  horizon_unit: "controlled_degradation_states";
  warning_threshold: number;
  state_level_metrics: Record<string, any>;
  trajectory_level_metrics: Record<string, any>;
  trajectory_results: any[];
  warnings: string[];
  limitations: string[];
  created_at: string;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, any> | null;
  };
}
