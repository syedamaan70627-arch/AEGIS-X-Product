/**
 * AEGIS-X Centralized Typed API Client
 */

import { getStoredAuthToken, setStoredAuthToken } from "@/lib/auth";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase/client";
import {
  AnalysisListResponse,
  AnalysisResponse,
  DatasetListResponse,
  DatasetRecord,
  FailureExplorerResponse,
  FaultTestListResponse,
  FaultTestResponse,
  MemoryBuildResponse,
  MemoryListResponse,
  MemoryMatchResponse,
  ModelCapabilitiesResponse,
  ModelListResponse,
  ModelRecord,
  PredictionResponse,
  ReadinessResponse,
  ReferenceFitResponse,
  StressTestListResponse,
  StressTestResponse,
  SystemStatus,
  UserMe,
  WarningEvaluationResponse,
  WarningResponse,
  GovernanceEvaluationRequest,
  GovernanceEvaluationResponse,
  GovernanceStatusResponse,
  GovernanceHistoryResponse,
} from "@/types/api";


import { getEnvConfig } from "@/lib/config";

export const getApiBaseUrl = (): string => {
  const cfg = getEnvConfig();
  if (cfg.isVercel && (!cfg.apiBaseUrl || cfg.missingVars.includes("NEXT_PUBLIC_API_BASE_URL"))) {
    throw new ApiError(
      "Missing NEXT_PUBLIC_API_BASE_URL configuration on Vercel deployment.",
      "CONFIG_ERROR",
      500
    );
  }
  return cfg.apiBaseUrl || "http://127.0.0.1:8000/api/v1";
};

export const getApiServerRoot = (): string => {
  const baseUrl = getApiBaseUrl();
  try {
    const url = new URL(baseUrl);
    return url.origin;
  } catch (_) {
    return baseUrl.replace(/\/api\/v1\/?$/, "");
  }
};

const getBASE_URL = (): string => getApiBaseUrl();


export class ApiError extends Error {
  code: string;
  details?: any;
  status: number;

  constructor(message: string, code: string = "API_ERROR", status: number = 500, details?: any) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

let activeAuthToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  activeAuthToken = token;
  setStoredAuthToken(token);
};

export const getValidSessionToken = async (): Promise<string | null> => {
  if (isSupabaseConfigured()) {
    try {
      const supabase = getSupabaseClient();
      const { data } = await supabase.auth.getSession();
      if (data?.session?.access_token) {
        activeAuthToken = data.session.access_token;
        return data.session.access_token;
      }

      // Browser storage fallback when getSession() resolves null during initial hydration
      if (typeof window !== "undefined" && window.localStorage) {
        for (let i = 0; i < window.localStorage.length; i++) {
          const key = window.localStorage.key(i);
          if (key && /^sb-.*-auth-token$/.test(key)) {
            const raw = window.localStorage.getItem(key);
            if (raw) {
              try {
                const parsed = JSON.parse(raw);
                const token = parsed?.access_token || parsed?.currentSession?.access_token;
                const refreshToken = parsed?.refresh_token || parsed?.currentSession?.refresh_token;

                if (refreshToken) {
                  const { data: refreshData, error: refreshErr } = await supabase.auth.refreshSession({ refresh_token: refreshToken });
                  if (!refreshErr && refreshData?.session?.access_token) {
                    activeAuthToken = refreshData.session.access_token;
                    return refreshData.session.access_token;
                  }
                }

                if (token) {
                  activeAuthToken = token;
                  return token;
                }
              } catch (_) {}
            }
          }
        }
      }
    } catch (_) {}
  }
  return activeAuthToken || getStoredAuthToken();
};

async function buildHeaders(isMultipart: boolean = false, tokenOverride?: string | null): Promise<HeadersInit> {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }

  const token = tokenOverride !== undefined ? tokenOverride : await getValidSessionToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errCode = "UNKNOWN_ERROR";
    let errMsg = `Request failed with status ${res.status}`;
    let errDetails = null;

    try {
      const data = await res.json();
      if (data.error) {
        errCode = data.error.code || errCode;
        errMsg = data.error.message || errMsg;
        errDetails = data.error.details || null;
      } else if (data.detail) {
        errMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch (_) {}

    throw new ApiError(errMsg, errCode, res.status, errDetails);
  }
  return res.json() as Promise<T>;
}

async function authenticatedFetch<T>(
  url: string,
  options: RequestInit = {},
  isMultipart: boolean = false,
  isRetry: boolean = false
): Promise<T> {
  const defaultHeaders = (await buildHeaders(isMultipart)) as Record<string, string>;
  const callerHeaders = (options.headers as Record<string, string>) || {};

  const mergedHeaders: Record<string, string> = {
    ...defaultHeaders,
    ...callerHeaders,
  };

  if (
    defaultHeaders["Authorization"] &&
    (!callerHeaders["Authorization"] ||
      callerHeaders["Authorization"] === "Bearer null" ||
      callerHeaders["Authorization"] === "Bearer undefined" ||
      callerHeaders["Authorization"] === "Bearer ")
  ) {
    mergedHeaders["Authorization"] = defaultHeaders["Authorization"];
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers: mergedHeaders,
  };

  const res = await fetch(url, fetchOptions);

  if (res.status === 401 && !isRetry && isSupabaseConfigured()) {
    try {
      const supabase = getSupabaseClient();
      let newToken: string | null = null;

      const { data, error } = await supabase.auth.refreshSession();
      if (!error && data?.session?.access_token) {
        newToken = data.session.access_token;
      } else {
        newToken = await getValidSessionToken();
      }

      if (newToken) {
        setAuthToken(newToken);
        const retryHeaders = (await buildHeaders(isMultipart, newToken)) as Record<string, string>;
        const retryOptions: RequestInit = {
          ...options,
          headers: {
            ...retryHeaders,
            ...callerHeaders,
            Authorization: `Bearer ${newToken}`,
          },
        };
        const retryRes = await fetch(url, retryOptions);
        return handleResponse<T>(retryRes);
      }
    } catch (_) {}

    setAuthToken(null);
  } else if (res.status === 401) {
    setAuthToken(null);
  }

  return handleResponse<T>(res);
}

export const api = {
  // System & Health
  getHealth: async () => {
    const res = await fetch(`${getApiServerRoot()}/health`);
    return handleResponse<{ status: string; service: string; api_version: string; engine_available: boolean }>(res);
  },

  getReadiness: async (): Promise<ReadinessResponse> => {
    const res = await fetch(`${getApiServerRoot()}/ready`);
    return handleResponse<ReadinessResponse>(res);
  },

  getStatus: async (): Promise<SystemStatus> => {
    const res = await fetch(`${getBASE_URL()}/status`);
    return handleResponse<SystemStatus>(res);
  },

  getUserMe: async (): Promise<UserMe> => {
    return authenticatedFetch<UserMe>(`${getBASE_URL()}/me`);
  },

  // Model Registry
  listModels: async (): Promise<ModelListResponse> => {
    return authenticatedFetch<ModelListResponse>(`${getBASE_URL()}/models`);
  },

  getModel: async (modelId: string): Promise<ModelRecord> => {
    return authenticatedFetch<ModelRecord>(`${getBASE_URL()}/models/${modelId}`);
  },

  getModelCapabilities: async (modelId: string): Promise<ModelCapabilitiesResponse> => {
    return authenticatedFetch<ModelCapabilitiesResponse>(`${getBASE_URL()}/models/${modelId}/capabilities`);
  },

  registerModel: async (formData: FormData): Promise<ModelRecord> => {
    return authenticatedFetch<ModelRecord>(`${getBASE_URL()}/models`, {
      method: "POST",
      body: formData,
    }, true);
  },

  fitReferenceState: async (modelId: string, datasetId: string): Promise<ReferenceFitResponse> => {
    return authenticatedFetch<ReferenceFitResponse>(`${getBASE_URL()}/models/${modelId}/reference/${datasetId}/fit`, {
      method: "POST",
    });
  },

  // Dataset Registry
  listDatasets: async (modelId?: string): Promise<DatasetListResponse> => {
    const url = modelId ? `${getBASE_URL()}/datasets?model_id=${encodeURIComponent(modelId)}` : `${getBASE_URL()}/datasets`;
    return authenticatedFetch<DatasetListResponse>(url);
  },

  getDataset: async (datasetId: string): Promise<DatasetRecord> => {
    return authenticatedFetch<DatasetRecord>(`${getBASE_URL()}/datasets/${datasetId}`);
  },

  registerDataset: async (formData: FormData): Promise<DatasetRecord> => {
    return authenticatedFetch<DatasetRecord>(`${getBASE_URL()}/datasets`, {
      method: "POST",
      body: formData,
    }, true);
  },

  deleteDataset: async (datasetId: string): Promise<{ status: string; dataset_id: string }> => {
    return authenticatedFetch<{ status: string; dataset_id: string }>(`${getBASE_URL()}/datasets/${datasetId}`, {
      method: "DELETE",
    });
  },

  // Analysis Engine
  runAnalysis: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
    reference_dataset_id?: string;
    fusion_method?: string;
  }): Promise<AnalysisResponse> => {
    return authenticatedFetch<AnalysisResponse>(`${getBASE_URL()}/analysis`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getAnalysis: async (analysisId: string): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/analysis/${analysisId}`);
  },

  listModelAnalyses: async (modelId: string): Promise<AnalysisListResponse> => {
    return authenticatedFetch<AnalysisListResponse>(`${getBASE_URL()}/models/${modelId}/analyses`);
  },

  // Stress Lab
  runStressTest: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
    stress_type: string;
    severity: number;
    random_state?: number;
  }): Promise<StressTestResponse> => {
    return authenticatedFetch<StressTestResponse>(`${getBASE_URL()}/stress-tests`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getStressTest: async (stressTestId: string): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/stress-tests/${stressTestId}`);
  },

  listModelStressTests: async (modelId: string): Promise<StressTestListResponse> => {
    return authenticatedFetch<StressTestListResponse>(`${getBASE_URL()}/models/${modelId}/stress-tests`);
  },

  // Fault Lab & Failure Explorer
  runFaultTest: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
    fault_type: string;
    severity: number;
    affected_features?: string[];
    stuck_value?: number;
    feature_pair?: string[];
    random_state?: number;
  }): Promise<FaultTestResponse> => {
    return authenticatedFetch<FaultTestResponse>(`${getBASE_URL()}/fault-tests`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getFaultTest: async (faultTestId: string): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/fault-tests/${faultTestId}`);
  },

  getFailureExplorerData: async (faultTestId: string): Promise<FailureExplorerResponse> => {
    return authenticatedFetch<FailureExplorerResponse>(`${getBASE_URL()}/fault-tests/${faultTestId}/failures`);
  },

  listModelFaultTests: async (modelId: string): Promise<FaultTestListResponse> => {
    return authenticatedFetch<FaultTestListResponse>(`${getBASE_URL()}/models/${modelId}/fault-tests`);
  },

  // Failure Memory
  buildFailureMemory: async (
    modelId: string,
    body: { fault_test_ids?: string[]; n_clusters?: number; random_state?: number }
  ): Promise<MemoryBuildResponse> => {
    return authenticatedFetch<MemoryBuildResponse>(`${getBASE_URL()}/failure-memory/${modelId}/build`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getFailureMemory: async (memoryId: string): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/failure-memory/${memoryId}`);
  },

  matchFailureMemoryQuery: async (
    memoryId: string,
    body: { query_profile: Record<string, number> }
  ): Promise<MemoryMatchResponse> => {
    return authenticatedFetch<MemoryMatchResponse>(`${getBASE_URL()}/failure-memory/${memoryId}/match`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  listModelFailureMemories: async (modelId: string): Promise<MemoryListResponse> => {
    return authenticatedFetch<MemoryListResponse>(`${getBASE_URL()}/models/${modelId}/failure-memory`);
  },

  // Failure Prediction
  runFailurePrediction: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<PredictionResponse> => {
    return authenticatedFetch<PredictionResponse>(`${getBASE_URL()}/predictions/failure`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getPrediction: async (predictionId: string): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/predictions/${predictionId}`);
  },

  // Early Warning
  queryEarlyWarning: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<WarningResponse> => {
    return authenticatedFetch<WarningResponse>(`${getBASE_URL()}/warnings`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  evaluateEarlyWarning: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<WarningEvaluationResponse> => {
    return authenticatedFetch<WarningEvaluationResponse>(`${getBASE_URL()}/warnings/evaluate`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getWarning: async (warningId: string): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/warnings/${warningId}`);
  },

  fitFailurePrediction: async (
    modelId: string,
    body?: { trajectory_dataset_id?: string; feature_set_type?: string; model_type?: string; random_state?: number }
  ): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/failure-prediction/${modelId}/fit`, {
      method: "POST",
      body: JSON.stringify(body || {}),
    });
  },

  fitEarlyWarning: async (
    modelId: string,
    body?: { trajectory_dataset_id?: string; horizon_val?: number; max_false_warning_rate?: number; random_state?: number }
  ): Promise<any> => {
    return authenticatedFetch<any>(`${getBASE_URL()}/early-warning/${modelId}/fit`, {
      method: "POST",
      body: JSON.stringify(body || {}),
    });
  },

  // Reliability Governance
  evaluateGovernance: async (body: GovernanceEvaluationRequest): Promise<GovernanceEvaluationResponse> => {
    return authenticatedFetch<GovernanceEvaluationResponse>(`${getBASE_URL()}/governance/evaluate`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getGovernanceStatus: async (modelId: string): Promise<GovernanceStatusResponse> => {
    return authenticatedFetch<GovernanceStatusResponse>(`${getBASE_URL()}/governance/${modelId}/status`);
  },

  getGovernanceHistory: async (
    modelId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<GovernanceHistoryResponse> => {
    return authenticatedFetch<GovernanceHistoryResponse>(
      `${getBASE_URL()}/governance/${modelId}/history?limit=${limit}&offset=${offset}`
    );
  },
};


