/**
 * AEGIS-X Canonical Route Registry
 * Centralizes all internal routes across sidebar, reports, dashboards, and pages.
 */
export const ROUTES = {
  dashboard: "/dashboard",
  models: "/models",
  dataSetup: "/data",
  batchMonitor: "/monitor",
  reliability: "/reliability",
  analysis: "/reliability",
  stressLab: "/stress",
  faultLab: "/faults",
  failureExplorer: "/failures",
  failureMemory: "/memory",
  failurePrediction: "/prediction",
  earlyWarning: "/warnings",
  governance: "/governance",
  reports: "/reports",
  settings: "/settings",
  login: "/login",
  signup: "/signup",
} as const;

export type RouteKey = keyof typeof ROUTES;
