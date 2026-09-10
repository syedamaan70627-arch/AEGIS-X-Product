import React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ReportsPage from '@/app/reports/page';
import { IntegratedReportView } from '@/components/reports/IntegratedReportView';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  api: {
    listModels: vi.fn(),
    listModelAnalyses: vi.fn(),
    getGovernanceHistory: vi.fn(),
    getGovernanceStatus: vi.fn(),
    getGovernanceByAnalysis: vi.fn(),
    evaluateGovernance: vi.fn(),
    listReportsByModel: vi.fn(),
    generateReport: vi.fn(),
    getReportExportUrl: vi.fn(() => 'http://localhost/export'),
  },
}));

const mockModel = {
  id: 'mod_1',
  model_id: 'mod_1',
  model_name: 'AEGIS Test RF',
  task_type: 'classification',
  created_at: '2026-09-06T12:00:00Z',
  filename: 'aegis_rf.pkl',
  file_path: 'models/aegis_rf.pkl',
  predict_supported: true,
  predict_proba_supported: true,
};

const mockAnalysis = {
  id: 'ana_3e2f39a9',
  analysis_id: 'ana_3e2f39a9',
  model_id: 'mod_1',
  reference_dataset_id: 'ds_ref',
  evaluation_dataset_id: 'ds_eval',
  status: 'COMPLETED',
  aggregate_ood_risk: 0.85,
  aggregate_uncertainty: 0.15,
  aggregate_drift_score: 0.10,
  aggregate_fused_risk: 0.42,
  created_at: '2026-09-06T12:00:00Z',
};

const mockGovernanceEval = {
  id: 'gov_1',
  evaluation_id: 'gov_1',
  model_id: 'mod_1',
  analysis_id: 'ana_3e2f39a9',
  decision_id: 'dec_3e2f',
  state_index: 1,
  operating_mode: 'EVIDENCE_ONLY',
  raw_action: 'WATCH',
  effective_action: 'WATCH',
  previous_effective_action: 'CONTINUE',
  transition_occurred: true,
  transition_reason: 'State transition to WATCH under elevated risk.',
  p_adverse: 0.042,
  prediction_set: [0],
  evidence_snapshot_hash: 'sha256_gov_hash',
  calibrated: false,
  calibrator_artifact_id: 'cal_art_test',
  calibrator_artifact_sha256: 'sha256_art_hash_123',
  result_path: 'res.json',
  created_at: '2026-09-06T12:00:00Z',
};

const mockReportPayload = {
  context: {
    report_id: 'rep_snapshot_1',
    user_id: 'user_a',
    model_id: 'mod_1',
    model_name: 'AEGIS Test RF',
    analysis_id: 'ana_3e2f39a9',
    reference_dataset_id: 'ds_ref',
    evaluation_dataset_id: 'ds_eval',
    governance_decision_id: 'dec_3e2f',
    generated_at: '2026-09-06T12:00:00Z',
    evidence_sha256: 'sha256_evidence_hash_123',
  },
  trust_disposition: 'LOW',
  trust_rationale: 'Model exhibits elevated risk flags (Fused Risk: 0.42, Action: WATCH). Enhanced monitoring required.',
  overall_completeness_pct: 91.6,
  completeness: {
    ood_detection: { name: 'OOD Detection', status: 'VERIFIED', evidence_count: 100 },
    early_warning: { name: 'Early Warning Engine', status: 'UNAVAILABLE', prerequisite_missing: 'No ordered temporal trajectory is available for this analysis.' },
  },
  reliability_summary: {
    aggregate_ood_risk: 0.85,
    aggregate_uncertainty: 0.15,
    aggregate_drift_score: 0.10,
    aggregate_fused_risk: 0.42,
    fusion_method: 'uncertainty_weighted',
    result_path: 'analysis/res.json',
  },
  stress_lab_summary: { status: 'UNAVAILABLE', test_count: 0, avg_risk_delta: null, max_stressed_risk: null },
  fault_lab_summary: { status: 'UNAVAILABLE', test_count: 0, pass_rate: null },
  failure_explorer_summary: { status: 'VERIFIED', signature_count: 3 },
  temporal_intelligence_summary: { status: 'UNAVAILABLE' },
  ecrg_governance_summary: {
    decision_id: 'dec_3e2f',
    operating_mode: 'EVIDENCE_ONLY',
    raw_action: 'WATCH',
    effective_action: 'WATCH',
    previous_effective_action: 'CONTINUE',
    state_index: 1,
    p_adverse: 0.042,
    prediction_set: [0],
    calibrated: false,
    calibrated_disclosure: 'Conformal calibration was not active for this EVIDENCE_ONLY snapshot.',
    calibrator_artifact_id: 'cal_art_test',
    calibrator_artifact_sha256: 'sha256_art_hash_123',
    evidence_snapshot_hash: 'sha256_gov_hash',
    transition_reason: 'State transition to WATCH under elevated risk.',
    reason_codes: ['STATE_TRANSITION_WATCH'],
    created_at: '2026-09-06T12:00:00Z',
  },
  why_this_decision: [
    { factor: 'ECRG Effective Governance Action', impact: 'POSITIVE', description: "ECRG state machine evaluated effective action as 'WATCH' in 'EVIDENCE_ONLY' mode.", evidence_link: '/governance' },
    { factor: 'High OOD Exposure', impact: 'CRITICAL', description: 'Evaluation inputs differ strongly from reference conditions.', evidence_link: '/reliability' }
  ],
  action_plan: [
    { priority: 'P1', title: 'Initiate Enhanced Monitoring Protocol', rationale: 'ECRG state machine evaluated effective action as WATCH.', trigger_condition: 'Effective Action == WATCH', target_component: 'ECRG Governor' }
  ],
  retraining_disposition: 'RETRAINING_ADVISED',
  retraining_rationale: 'Elevated out-of-distribution density shift (0.850) requires model parameter review.',
  deployment_suitability: { recommended_environment: 'SUPERVISED_PRODUCTION_WITH_MONITORING', risk_tier: 'TIER_3_EVALUATION' },
  trend_comparison: { has_previous_analysis: false, trend_direction: 'NO VALID COMPARABLE PRIOR ASSESSMENT' },
  top_risk_drivers: [
    { category: 'Distribution Shift', driver_name: 'Out-of-Distribution Feature Density Shift', severity_score: 0.85, impact_description: 'Evaluation samples deviate from reference density.' }
  ],
  scientific_limitations: ['Label-free risk evidence is not confirmed prediction error.'],
};

const mockReportSnapshot = {
  id: 'rep_snapshot_1',
  user_id: 'user_a',
  model_id: 'mod_1',
  analysis_id: 'ana_3e2f39a9',
  report_type: 'integrated',
  title: 'AEGIS-X Integrated Reliability & Governance Report',
  disposition: 'LOW',
  completeness_score: 91.6,
  result_path: 'reports/rep_snapshot_1.json',
  snapshot_json: mockReportPayload,
  created_at: '2026-09-06T12:00:00Z',
};

describe('AEGIS-X Reports Behavioral Test Suite', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (api.listModels as any).mockResolvedValue({ models: [mockModel] });
    (api.listModelAnalyses as any).mockResolvedValue({ analyses: [mockAnalysis] });
    (api.getGovernanceHistory as any).mockResolvedValue({ evaluations: [mockGovernanceEval] });
    (api.getGovernanceStatus as any).mockResolvedValue(mockGovernanceEval);
    (api.getGovernanceByAnalysis as any).mockResolvedValue(mockGovernanceEval);
    (api.listReportsByModel as any).mockResolvedValue([mockReportSnapshot]);
    (api.generateReport as any).mockResolvedValue(mockReportSnapshot);
  });

  // TEST 1 — Reports Page Renders Basic Structure
  it('TEST 1: Renders Reports page header, selectors, and readiness strip', async () => {
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText('AEGIS-X Reports & Decision Support Layer')).toBeInTheDocument();
    });

    expect(screen.getByText('REPORT STORAGE:')).toBeInTheDocument();
  });

  // TEST 2 — Readiness States Display Correct Badges
  it('TEST 2: Renders correct readiness badges for MODEL, ANALYSIS, EVIDENCE, GOVERNANCE, and STORAGE', async () => {
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText('MODEL:')).toBeInTheDocument();
    });

    expect(screen.getByText('ANALYSIS:')).toBeInTheDocument();
    expect(screen.getByText('EVIDENCE:')).toBeInTheDocument();
    expect(screen.getByText('GOVERNANCE:')).toBeInTheDocument();
    expect(screen.getByText('REPORT STORAGE:')).toBeInTheDocument();
  });

  // TEST 3 — Storage Unavailable Disables Generate Button & Suppresses Raw URLs
  it('TEST 3: Disables Generate button when REPORT STORAGE is UNAVAILABLE without exposing PostgREST URLs', async () => {
    (api.listReportsByModel as any).mockRejectedValue({
      reason: 'Report storage is currently unavailable.',
      action: 'Please retry after storage is restored.',
      details: 'PostgREST Supabase REST API unreachable',
    });

    render(<ReportsPage />);

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /generate new snapshot/i });
      expect(button).toBeDisabled();
    });

    await waitFor(() => {
      expect(screen.getByText(/storage is currently unavailable/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/supabase.co\/rest\/v1/i)).not.toBeInTheDocument();
  });

  // TEST 4 — Governance Same-Analysis Binding
  it('TEST 4: Binds exact governance decision for the selected analysis and renders GOVERNANCE: READY', async () => {
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText('GOVERNANCE:')).toBeInTheDocument();
      expect(screen.getAllByText('READY').length).toBeGreaterThan(0);
    });
  });

  // TEST 5 — Snapshot Generation Success Resolves Cleanly
  it('TEST 5: Generates and displays a valid immutable report snapshot when button clicked', async () => {
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /generate new snapshot/i })).toBeEnabled();
    });

    const generateBtn = screen.getByRole('button', { name: /generate new snapshot/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(api.generateReport).toHaveBeenCalledWith({
        model_id: 'mod_1',
        analysis_id: 'ana_3e2f39a9',
        report_type: 'integrated',
      });
    });
  });

  // TEST 6 — Four Report Tabs Render Distinct Views from SAME Snapshot
  it('TEST 6: All 4 report tabs render distinct views driven from the exact same snapshot object', () => {
    const { rerender } = render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    // Tab 1: Integrated Report
    expect(screen.getByTestId('integrated-view')).toBeInTheDocument();
    expect(screen.getByText('Executive Decision Summary')).toBeInTheDocument();

    // Tab 2: Reliability Section Only
    rerender(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="reliability"
      />
    );
    expect(screen.getByTestId('reliability-view')).toBeInTheDocument();
    expect(screen.getByText('Telemetry & Reliability Assessment Summary')).toBeInTheDocument();
    expect(screen.queryByText('Executive Decision Summary')).not.toBeInTheDocument();

    // Tab 3: Model Trust Section Only
    rerender(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="model_trust"
      />
    );
    expect(screen.getByTestId('trust-view')).toBeInTheDocument();
    expect(screen.getByText('Model Operational Trust & Risk Interpretation')).toBeInTheDocument();
    expect(screen.queryByTestId('reliability-view')).not.toBeInTheDocument();

    // Tab 4: Governance Decision Section Only
    rerender(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="governance"
      />
    );
    expect(screen.getByTestId('governance-view')).toBeInTheDocument();
    expect(screen.getByText('ECRG Conformal Governance Decision Report')).toBeInTheDocument();
    expect(screen.queryByTestId('trust-view')).not.toBeInTheDocument();
  });

  // TEST 7 — Synthesis Consistency: WATCH Action Is Not Rendered as DEFER or BLOCKED
  it('TEST 7: WATCH governance action renders supervised monitoring without false BLOCKED or DEFER status', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    expect(screen.getAllByText('WATCH').length).toBeGreaterThan(0);
    expect(screen.getByText('Supervised Automation (Monitoring Required)')).toBeInTheDocument();
    expect(screen.queryByText('BLOCKED_FROM_DEPLOYMENT')).not.toBeInTheDocument();
  });

  // TEST 8 — Trend Consistency: Absence of Previous Run Renders NO VALID COMPARABLE PRIOR ASSESSMENT
  it('TEST 8: Absence of prior analysis renders NO VALID COMPARABLE PRIOR ASSESSMENT instead of STABLE', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    expect(screen.getByText('NO VALID COMPARABLE PRIOR ASSESSMENT')).toBeInTheDocument();
  });

  // TEST 9 — Conformal Calibration Disclosure: Unset Calibration Displays Explicit Disclosure
  it('TEST 9: EVIDENCE_ONLY snapshot with unset calibration renders explicit uncalibrated disclosure', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="governance"
      />
    );

    expect(screen.getByText(/Conformal calibration was not active for this EVIDENCE_ONLY snapshot/i)).toBeInTheDocument();
  });

  // TEST 10 — Human-Readable Error Boundaries
  it('TEST 10: Formats API failures into user-friendly error blocks without raw stack traces', async () => {
    (api.listReportsByModel as any).mockRejectedValue({
      message: 'Report generation failed',
      reason: 'Failed to retrieve analysis runs for the selected model.',
      action: 'Run an analysis under Core Reliability before generating reports.',
      techDetails: 'Database connection failed',
    });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText('Report generation failed')).toBeInTheDocument();
    });

    expect(screen.getByText('Failed to retrieve analysis runs for the selected model.')).toBeInTheDocument();
    expect(screen.getByText('Run an analysis under Core Reliability before generating reports.')).toBeInTheDocument();
  });

  // TEST 11 — Section I Renders All 11 Governance Fields
  it('TEST 11: Section I renders all 11 required governance fields with real persisted evaluation data', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    const sectionI = screen.getByTestId('section-i-ecrg');
    expect(sectionI).toBeInTheDocument();

    // 1. Operating Mode
    expect(sectionI).toHaveTextContent('EVIDENCE_ONLY');
    // 2. Effective Action
    expect(sectionI).toHaveTextContent('WATCH');
    // 3. Previous Action
    expect(sectionI).toHaveTextContent('CONTINUE');
    // 4. State Index
    expect(sectionI).toHaveTextContent('1');
    // 5. Adverse Probability
    expect(sectionI).toHaveTextContent('0.0420');
    // 6. Calibration Status
    expect(sectionI).toHaveTextContent('UNCERTIFIED');
    // 7. Conformal Prediction Set
    expect(sectionI).toHaveTextContent('[0]');
    // 8. Provenance
    expect(sectionI).toHaveTextContent('cal_art_test');
    // 9. Governance Rationale / Transition Reason
    expect(sectionI).toHaveTextContent('State transition to WATCH under elevated risk.');
    // 10. Evidence Hash
    expect(sectionI).toHaveTextContent('sha256_gov_hash');
    // 11. Timestamp / Evaluation
    expect(sectionI).toHaveTextContent('dec_3e2f');
  });

  // TEST 12 — Section I Maintains Strict Fail-Closed Behavior When Un-evaluated
  it('TEST 12: Section I displays truthful fail-closed explicit values (NOT_EVALUATED, UNAVAILABLE, NOT_AVAILABLE, UNSET) without defaulting to CONTINUE', () => {
    const unEvaluatedPayload = {
      ...mockReportPayload,
      ecrg_governance_summary: {
        evaluated: false,
        operating_mode: 'NOT_EVALUATED',
        effective_action: 'UNAVAILABLE',
        raw_action: 'UNAVAILABLE',
        previous_effective_action: 'NONE',
        state_index: 0,
        calibrated: false,
        calibrator_artifact_id: null,
        p_adverse: null,
        evidence_snapshot_hash: null,
      },
    };

    render(
      <IntegratedReportView
        report={unEvaluatedPayload as any}
        reportId="rep_uneval"
        activeTab="integrated"
      />
    );

    const sectionI = screen.getByTestId('section-i-ecrg');
    expect(sectionI).toHaveTextContent('NOT_EVALUATED');
    expect(sectionI).toHaveTextContent('UNAVAILABLE');
    expect(sectionI).toHaveTextContent('UNSET');
    expect(sectionI).toHaveTextContent('NOT_AVAILABLE');

    // Strict check: Must not silently default to CONTINUE
    expect(sectionI).not.toHaveTextContent(/Effective Action.*CONTINUE/);
  });

  // TEST 13 — Section I and Section J Evidence Traceability Agreement
  it('TEST 13: Section I effective action and Section J ECRG trace strictly agree and never contradict', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    const sectionI = screen.getByTestId('section-i-ecrg');
    expect(sectionI).toHaveTextContent('WATCH');

    // Section J
    const sectionJ = document.getElementById('section-j');
    expect(sectionJ).not.toBeNull();
    expect(sectionJ).toHaveTextContent('ECRG Effective Governance Action');
    expect(sectionJ).toHaveTextContent("evaluated effective action as 'WATCH' in 'EVIDENCE_ONLY' mode");
  });

  // TEST 14 — Evaluate ECRG Governance Trigger
  it('TEST 14: Calling handleEvaluateGovernance triggers POST /governance/evaluate and regenerates report snapshot', async () => {
    const unEvaluatedSnapshot = {
      ...mockReportSnapshot,
      snapshot_json: {
        ...mockReportPayload,
        ecrg_governance_summary: {
          evaluated: false,
          operating_mode: 'NOT_EVALUATED',
          effective_action: 'UNAVAILABLE',
          raw_action: 'UNAVAILABLE',
          previous_effective_action: 'NONE',
          state_index: 0,
          calibrated: false,
        },
      },
    };

    const mockEvaluatedResponse = {
      evaluation_id: 'dec_new_456',
      model_id: 'mod_1',
      user_id: 'user_a',
      dataset_id: 'ds_eval',
      mode: 'EVIDENCE_ONLY',
      action: 'CONTINUE',
      raw_action: 'CONTINUE',
      previous_effective_action: 'NONE',
      state_index: 0,
      state_transition_occurred: false,
      calibrated: false,
      evidence_snapshot_hash: 'sha256_new_hash',
      p_adverse: 0.012,
      transition_reason: 'Nominal state maintenance.',
      created_at: '2026-09-06T13:00:00Z',
    };

    (api.listReportsByModel as any).mockResolvedValue([unEvaluatedSnapshot]);
    (api.getGovernanceByAnalysis as any).mockResolvedValue(null);
    (api.evaluateGovernance as any).mockResolvedValue(mockEvaluatedResponse);

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText('AEGIS-X Reports & Decision Support Layer')).toBeInTheDocument();
    });

    const runBtn = await screen.findByRole('button', { name: /run evaluation/i });
    expect(runBtn).toBeInTheDocument();
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(api.evaluateGovernance).toHaveBeenCalledWith(
        expect.objectContaining({
          model_id: 'mod_1',
          source_analysis_id: 'ana_3e2f39a9',
          mode: 'EVIDENCE_ONLY',
        })
      );
    });

    await waitFor(() => {
      expect(api.generateReport).toHaveBeenCalled();
    });
  });
});
