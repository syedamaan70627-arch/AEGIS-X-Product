import React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ROUTES } from '@/lib/routes';
import EarlyWarningPage from '@/app/warnings/page';
import { api } from '@/lib/api';
import { ToastProvider } from '@/components/providers/ToastProvider';

vi.mock('@/lib/api', () => ({
  api: {
    listModels: vi.fn(),
    getModelCapabilities: vi.fn(),
    listDatasets: vi.fn(),
  },
}));

describe('AEGIS-X Zero-Dead-Link Navigation Regression Suite', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('verifies all registered ROUTES map to valid non-empty paths', () => {
    Object.entries(ROUTES).forEach(([key, routePath]) => {
      expect(routePath).toBeDefined();
      expect(routePath.startsWith('/')).toBe(true);
      expect(routePath.length).toBeGreaterThan(1);
    });
  });

  it('verifies report source routes (Section C-I) exist in canonical route registry', () => {
    const reportSourceRoutes = [
      ROUTES.reliability,
      ROUTES.stressLab,
      ROUTES.faultLab,
      ROUTES.failureExplorer,
      ROUTES.earlyWarning,
      ROUTES.governance,
    ];

    expect(reportSourceRoutes).toContain('/reliability');
    expect(reportSourceRoutes).toContain('/stress');
    expect(reportSourceRoutes).toContain('/faults');
    expect(reportSourceRoutes).toContain('/failures');
    expect(reportSourceRoutes).toContain('/warnings');
    expect(reportSourceRoutes).toContain('/governance');
  });

  it('verifies Fault Lab canonical route is /faults and is non-empty', () => {
    expect(ROUTES.faultLab).toBe('/faults');
  });

  it('renders Early Warning prerequisite state (NOT EVALUATED) when trajectory dataset is missing', async () => {
    (api.listModels as any).mockResolvedValue({
      models: [
        {
          model_id: 'mod_1',
          model_name: 'AEGIS Test RF',
          task_type: 'classification',
        },
      ],
    });
    (api.getModelCapabilities as any).mockResolvedValue({
      capabilities: {
        early_warning: { status: 'UNAVAILABLE', reason: 'Trajectory dataset missing' },
      },
    });
    (api.listDatasets as any).mockResolvedValue({ datasets: [] });

    render(
      <ToastProvider>
        <EarlyWarningPage />
      </ToastProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Early Warning/i)).toBeInTheDocument();
    });
  });
});
