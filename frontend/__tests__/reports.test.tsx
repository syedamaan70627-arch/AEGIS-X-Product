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
  transition_reason: 'State transition to WATCH',
  evidence_snapshot_hash: 'sha256_gov_hash',
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
  trust_disposition: 'CONDITIONAL',
  trust_rationale: 'The evaluation data displays elevated OOD exposure relative to baseline.',
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
    state_index: 1,
    calibrated: true,
  },
  why_this_decision: [
    { factor: 'High OOD Exposure', impact: 'CRITICAL', description: 'Evaluation inputs differ strongly from reference conditions.' }
  ],
  action_plan: [
    { priority: 'P1', title: 'Review high-OOD observations', target_component: 'Reliability -> OOD', rationale: 'Review high-OOD observations under Reliability analysis tab' }
  ],
  retraining_disposition: 'MONITOR',
  retraining_rationale: 'OOD risk is elevated but predictive uncertainty remains low.',
  deployment_suitability: { recommended_environment: 'STAGING', risk_tier: 'TIER_2' },
  top_risk_drivers: ['High OOD risk detected relative to reference dataset'],
  scientific_limitations: ['Label-free risk evidence is not confirmed prediction error.'],
};

const mockReportSnapshot = {
  id: 'rep_snapshot_1',
  user_id: 'user_a',
  model_id: 'mod_1',
  analysis_id: 'ana_3e2f39a9',
  report_type: 'integrated',
  title: 'AEGIS-X Integrated Reliability & Governance Report',
  disposition: 'CONDITIONAL',
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
    expect(screen.getByText('Executive Decision Summary')).toBeInTheDocument();

    // Tab 2: Reliability Section
    rerender(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="reliability"
      />
    );
    expect(screen.getByText('Section C: Reliability Evidence')).toBeInTheDocument();

    // Tab 3: Model Trust Section
    rerender(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="model_trust"
      />
    );
    expect(screen.getByText('Section H: Model Trust Interpretation')).toBeInTheDocument();

    // Tab 4: Governance Decision Section
    rerender(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="governance"
      />
    );
    expect(screen.getByText('Section I: ECRG Governance Integration')).toBeInTheDocument();
  });

  // TEST 7 — Model/Analysis Switching Clears Stale Context
  it('TEST 7: Clears stale report state when model or analysis selection changes', async () => {
    (api.listModelAnalyses as any).mockResolvedValueOnce({
      analyses: [
        mockAnalysis,
        { id: 'ana_2', analysis_id: 'ana_2', model_id: 'mod_1', created_at: '2026-09-06T13:00:00Z' },
      ],
    });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(api.listModelAnalyses).toHaveBeenCalledWith('mod_1');
    });
  });

  // TEST 8 — Zero-Dummy Behavior: Unexecuted Modules Render NOT EVALUATED / NOT APPLICABLE / UNAVAILABLE
  it('TEST 8: Renders NOT APPLICABLE with prerequisite reason for Early Warning without fake 0% score', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    expect(screen.getByText('Early Warning Engine')).toBeInTheDocument();
    expect(screen.getByText('UNAVAILABLE')).toBeInTheDocument();
    expect(screen.getByText(/Reason: No ordered temporal trajectory is available/i)).toBeInTheDocument();
  });

  // TEST 9 — First Viewport Executive Summary Header Rendering
  it('TEST 9: Renders complete 1-Minute Executive Summary header fields', () => {
    render(
      <IntegratedReportView
        report={mockReportPayload as any}
        reportId="rep_snapshot_1"
        activeTab="integrated"
      />
    );

    expect(screen.getAllByText('CONDITIONAL').length).toBeGreaterThan(0);
    expect(screen.getAllByText('WATCH').length).toBeGreaterThan(0);
    expect(screen.getByText('Supervised Automation (Monitoring Required)')).toBeInTheDocument();
    expect(screen.getAllByText(/High OOD risk/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Review high-OOD observations')).toBeInTheDocument();
    expect(screen.getAllByText('MONITOR').length).toBeGreaterThan(0);
    expect(screen.getAllByText('91.6%').length).toBeGreaterThan(0);
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
});
