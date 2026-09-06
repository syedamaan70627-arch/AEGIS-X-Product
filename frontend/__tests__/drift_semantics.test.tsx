import React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ReliabilitySummary } from '@/components/ui/ReliabilitySummary';
import { RiskIndicator } from '@/components/ui/RiskIndicator';
import { IntegratedReportView } from '@/components/reports/IntegratedReportView';

vi.mock('@/lib/api', () => ({
  api: {
    getReportExportUrl: vi.fn(() => 'http://localhost/export'),
  },
}));

describe('Feature Drift Semantics & Terminology Tests', () => {
  it('ReliabilitySummary renders Feature Drift Prevalence label', () => {
    render(
      <ReliabilitySummary
        oodRisk={0.5694}
        uncertaintyRisk={0.4865}
        driftRisk={0.953125}
        fusedRisk={0.6804}
      />
    );

    expect(screen.getByText(/Feature Drift Prevalence/i)).toBeInTheDocument();
    expect(screen.queryByText(/Drift Risk/i)).not.toBeInTheDocument();
  });

  it('RiskIndicator renders High Prevalence badge for score 0.953125 on drift label', () => {
    render(
      <RiskIndicator
        label="Feature Drift Prevalence"
        value={0.953125}
      />
    );

    expect(screen.getByText(/High Prevalence/i)).toBeInTheDocument();
    expect(screen.getByText('95.3%')).toBeInTheDocument();
    expect(screen.queryByText(/High Risk/i)).not.toBeInTheDocument();
  });

  it('IntegratedReportView renders Feature Drift Prevalence with percentage and disclosure text', () => {
    const mockReport = {
      context: {
        report_id: 'rep_test123',
        user_id: 'usr_test',
        model_id: 'mod_1',
        model_name: 'AEGIS Test RF',
        task_type: 'classification',
        analysis_id: 'ana_1',
        reference_dataset_id: 'ds_ref',
        evaluation_dataset_id: 'ds_eval',
        governance_decision_id: 'dec_1',
        generated_at: '2026-09-06T12:00:00Z',
        evidence_sha256: 'sha256_123',
      },
      report_type: 'integrated' as const,
      trust_disposition: 'CONDITIONAL' as const,
      trust_rationale: 'Conditional execution due to high drift prevalence.',
      overall_completeness_pct: 91.7,
      completeness: {},
      reliability_summary: {
        status: 'COMPLETED',
        aggregate_fused_risk: 0.6804,
        aggregate_ood_risk: 0.5694,
        aggregate_uncertainty: 0.4865,
        aggregate_drift_score: 0.953125,
        drifted_feature_count: 61,
        total_feature_count: 64,
        fusion_method: 'uncertainty_weighted',
        result_path: 'analysis/res.json',
      },
      stress_lab_summary: { status: 'UNAVAILABLE', test_count: 0 },
      fault_lab_summary: { status: 'UNAVAILABLE', test_count: 0 },
      failure_explorer_summary: { status: 'VERIFIED' },
      temporal_intelligence_summary: { status: 'UNAVAILABLE' },
      ecrg_governance_summary: {
        operating_mode: 'EVIDENCE_ONLY',
        effective_action: 'WATCH',
        raw_action: 'WATCH',
        state_index: 1,
        calibrated: false,
      },
      why_this_decision: [
        {
          factor: 'Feature Drift Prevalence',
          impact: 'NEGATIVE' as const,
          description: 'Widespread feature distribution shift detected: 61 of 64 monitored features (95.3%) exhibited statistically significant marginal shift under two-sample KS test (α = 0.05).',
          evidence_link: '/reliability',
        },
      ],
      action_plan: [],
      retraining_disposition: 'URGENT MODEL REVIEW' as const,
      retraining_rationale: 'Urgent Model Review Mandated — Primary Adverse Evidence: Widespread Feature Drift (0.953).',
      deployment_suitability: { recommended_environment: 'SUPERVISED_PRODUCTION_WITH_MONITORING', risk_tier: 'TIER_3_EVALUATION' },
      trend_comparison: { has_previous_analysis: false, trend_direction: 'NO VALID COMPARABLE PRIOR ASSESSMENT' },
      top_risk_drivers: [],
      scientific_limitations: [],
    };

    render(
      <IntegratedReportView
        report={mockReport}
        reportId="rep_test123"
        activeTab="reliability"
      />
    );

    expect(screen.getByText('Feature Drift Prevalence')).toBeInTheDocument();
    expect(screen.getByText('HIGH PREVALENCE')).toBeInTheDocument();
    expect(screen.getByText('95.3%')).toBeInTheDocument();
    expect(screen.getByText(/Feature Drift Prevalence is the fraction of monitored features/i)).toBeInTheDocument();
    expect(screen.queryByText('Severe Feature Drift')).not.toBeInTheDocument();
  });
});
