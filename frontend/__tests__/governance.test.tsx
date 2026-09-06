import React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import GovernancePage from '@/app/governance/page';
import { GovernanceOverviewCard } from '@/components/governance/GovernanceOverviewCard';
import { GovernanceDetailsModal } from '@/components/governance/GovernanceDetailsModal';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  api: {
    listModels: vi.fn(),
    listModelAnalyses: vi.fn(),
    getGovernanceStatus: vi.fn(),
    evaluateGovernance: vi.fn(),
    getGovernanceHistory: vi.fn(),
  },
}));

vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => ({ loading: false, authenticated: true, user: { id: 'user_a' } }),
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

const mockGovStatusWatch = {
  model_id: 'mod_1',
  latest_action: 'WATCH',
  mode: 'EVIDENCE_ONLY',
  consecutive_state_count: 1,
  in_cooldown: false,
  total_evaluations: 1,
  last_evaluated_at: '2026-09-06T12:00:00Z',
};

const mockGovEvalWatch = {
  id: 'gov_1',
  evaluation_id: 'gov_1_eval_id_123',
  dataset_id: 'ds_eval',
  user_id: 'user_a',
  model_id: 'mod_1',
  analysis_id: 'ana_3e2f39a9',
  decision_id: 'dec_3e2f9999',
  state_index: 1,
  mode: 'EVIDENCE_ONLY',
  operating_mode: 'EVIDENCE_ONLY',
  raw_action: 'WATCH',
  effective_action: 'WATCH',
  action: 'WATCH',
  state_transition_occurred: true,
  previous_effective_action: 'CONTINUE',
  transition_occurred: true,
  transition_reason: 'State transition to WATCH due to elevated OOD risk',
  p_adverse: 0.42,
  ood_score: 0.85,
  uncertainty_score: 0.15,
  drift_score: 0.10,
  fused_risk: 0.42,
  signal_disagreement: 0.05,
  signal_disagreement_index: 0.05,
  primary_supporting_signal: 'OOD_DETECTOR',
  warning_severity: 'MODERATE',
  consecutive_state_count: 1,
  in_cooldown: false,
  stress_robustness: 0.95,
  fault_sensitivity: 0.05,
  temporal_failure_probability: 0.0,
  prediction_set_json: JSON.stringify([0, 1]),
  reason_codes: ['HIGH_OOD_RISK'],
  reason_codes_json: JSON.stringify(['HIGH_OOD_RISK']),
  calibrated: false,
  evidence_snapshot_hash: 'sha256_gov_hash_abc123',
  result_path: 'res.json',
  created_at: '2026-09-06T12:00:00Z',
};

const mockGovEvalDiffActions = {
  ...mockGovEvalWatch,
  id: 'gov_2',
  evaluation_id: 'gov_2_eval_id_456',
  decision_id: 'dec_diff_actions',
  raw_action: 'DEFER',
  effective_action: 'WATCH',
  transition_reason: 'Anti-flapping hysteresis delay active (step 1 of 2)',
};

const mockGovStatusDiffActions = {
  ...mockGovStatusWatch,
  latest_action: 'WATCH',
  total_evaluations: 2,
};

describe('AEGIS-X Governance Behavioral Test Suite', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (api.listModels as any).mockResolvedValue({ models: [mockModel] });
    (api.listModelAnalyses as any).mockResolvedValue({ analyses: [mockAnalysis] });
    (api.getGovernanceStatus as any).mockResolvedValue(mockGovStatusWatch);
    (api.getGovernanceHistory as any).mockResolvedValue({ total: 1, evaluations: [mockGovEvalWatch] });
  });

  // TEST 11 — Governance Page Renders Header, Selectors & Readiness Bar
  it('TEST 11: Renders Governance page with model selector, analysis selector, and readiness bar', async () => {
    render(<GovernancePage />);

    await waitFor(() => {
      expect(screen.getAllByText(/Evidence-Calibrated Reliability Governance/i).length).toBeGreaterThan(0);
    });

    expect(screen.getByText('Model Readiness:')).toBeInTheDocument();
    expect(screen.getByText('Analysis Readiness:')).toBeInTheDocument();
    expect(screen.getByText('Evidence Telemetry:')).toBeInTheDocument();
    expect(screen.getByText('Conformal Calibration:')).toBeInTheDocument();
  });

  // TEST 12 — NOT_EVALUATED State Rendering
  it('TEST 12: Displays NOT_EVALUATED when no governance decision exists without defaulting to CONTINUE', async () => {
    (api.getGovernanceStatus as any).mockResolvedValue(null);

    render(
      <GovernanceOverviewCard
        modelId="mod_1"
        selectedAnalysis={mockAnalysis as any}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/GOVERNANCE NOT EVALUATED/i)).toBeInTheDocument();
    });

    // Ensure it did NOT falsely default to CONTINUE
    expect(screen.queryByText(/effective action: continue/i)).not.toBeInTheDocument();
  });

  // TEST 13 — Existing Decision Rendering (EVIDENCE_ONLY, WATCH)
  it('TEST 13: Correctly renders persisted governance evaluation decision (Mode: EVIDENCE_ONLY, Effective Action: WATCH)', async () => {
    render(
      <GovernanceOverviewCard
        modelId="mod_1"
        selectedAnalysis={mockAnalysis as any}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('WATCH')).toBeInTheDocument();
    });

    expect(screen.getByText('EVIDENCE_ONLY')).toBeInTheDocument();
  });

  // TEST 14 — Recommended vs Effective Action Distinction
  it('TEST 14: Displays distinct recommended (raw) action vs effective action during anti-flapping hysteresis', async () => {
    (api.getGovernanceStatus as any).mockResolvedValue(mockGovStatusDiffActions);
    (api.evaluateGovernance as any).mockResolvedValue(mockGovEvalDiffActions);

    render(
      <GovernanceOverviewCard
        modelId="mod_1"
        selectedAnalysis={mockAnalysis as any}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('WATCH')).toBeInTheDocument(); // Effective Action
    });

    const evalBtn = screen.getByRole('button', { name: /evaluate governance/i });
    fireEvent.click(evalBtn);

    await waitFor(() => {
      expect(screen.getByText('Anti-flapping hysteresis delay active (step 1 of 2)')).toBeInTheDocument();
    });
  });

  // TEST 15 — Audit & Provenance Information Display
  it('TEST 15: Displays Decision ID, Evidence Hash, Operating Mode, and Reason Codes in details modal', () => {
    render(
      <GovernanceDetailsModal
        evaluation={mockGovEvalWatch as any}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText(/gov_1_eval_id_123/i)).toBeInTheDocument();
    expect(screen.getByText('sha256_gov_hash_abc123')).toBeInTheDocument();
    expect(screen.getByText(/EVIDENCE_ONLY/i)).toBeInTheDocument();
    expect(screen.getByText('HIGH_OOD_RISK')).toBeInTheDocument();
    expect(screen.getByText('State transition to WATCH due to elevated OOD risk')).toBeInTheDocument();
  });

  // TEST 16 — Governance History Timeline Integration
  it('TEST 16: Fetches and displays governance transition audit history for selected model', async () => {
    render(<GovernancePage />);

    await waitFor(() => {
      expect(api.getGovernanceHistory).toHaveBeenCalledWith('mod_1', expect.anything(), expect.anything());
    });

    expect(screen.getByText('Governance State Transition Audit History')).toBeInTheDocument();
  });
});
