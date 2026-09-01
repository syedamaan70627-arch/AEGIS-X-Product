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
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export const getApiServerRoot = (): string => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  try {
    const url = new URL(baseUrl);
    return url.origin;
  } catch (_) {
    return baseUrl.replace(/\/api\/v1\/?$/, "");
  }
};

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
  const headers = await buildHeaders(isMultipart);
  const fetchOptions: RequestInit = {
    ...options,
    headers: {
      ...(headers as Record<string, string>),
      ...((options.headers as Record<string, string>) || {}),
    },
  };

  const res = await fetch(url, fetchOptions);

  if (res.status === 401 && !isRetry && isSupabaseConfigured()) {
    try {
      const supabase = getSupabaseClient();
      const { data, error } = await supabase.auth.refreshSession();
      if (!error && data?.session?.access_token) {
        const newToken = data.session.access_token;
        setAuthToken(newToken);

        const newHeaders = await buildHeaders(isMultipart, newToken);
        const retryOptions: RequestInit = {
          ...options,
          headers: {
            ...(newHeaders as Record<string, string>),
            ...((options.headers as Record<string, string>) || {}),
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
    const res = await fetch(`${BASE_URL}/status`);
    return handleResponse<SystemStatus>(res);
  },

  getUserMe: async (): Promise<UserMe> => {
    return authenticatedFetch<UserMe>(`${BASE_URL}/me`);
  },

  // Model Registry
  listModels: async (): Promise<ModelListResponse> => {
    return authenticatedFetch<ModelListResponse>(`${BASE_URL}/models`);
  },

  getModel: async (modelId: string): Promise<ModelRecord> => {
    return authenticatedFetch<ModelRecord>(`${BASE_URL}/models/${modelId}`);
  },

  getModelCapabilities: async (modelId: string): Promise<ModelCapabilitiesResponse> => {
    return authenticatedFetch<ModelCapabilitiesResponse>(`${BASE_URL}/models/${modelId}/capabilities`);
  },

  registerModel: async (formData: FormData): Promise<ModelRecord> => {
    return authenticatedFetch<ModelRecord>(`${BASE_URL}/models`, {
      method: "POST",
      body: formData,
    }, true);
  },

  fitReferenceState: async (modelId: string, datasetId: string): Promise<ReferenceFitResponse> => {
    return authenticatedFetch<ReferenceFitResponse>(`${BASE_URL}/models/${modelId}/reference/${datasetId}/fit`, {
      method: "POST",
    });
  },

  // Dataset Registry
  listDatasets: async (modelId?: string): Promise<DatasetListResponse> => {
    const url = modelId ? `${BASE_URL}/datasets?model_id=${encodeURIComponent(modelId)}` : `${BASE_URL}/datasets`;
    return authenticatedFetch<DatasetListResponse>(url);
  },

  getDataset: async (datasetId: string): Promise<DatasetRecord> => {
    return authenticatedFetch<DatasetRecord>(`${BASE_URL}/datasets/${datasetId}`);
  },

  registerDataset: async (formData: FormData): Promise<DatasetRecord> => {
    return authenticatedFetch<DatasetRecord>(`${BASE_URL}/datasets`, {
      method: "POST",
      body: formData,
    }, true);
  },

  deleteDataset: async (datasetId: string): Promise<{ status: string; dataset_id: string }> => {
    return authenticatedFetch<{ status: string; dataset_id: string }>(`${BASE_URL}/datasets/${datasetId}`, {
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
    return authenticatedFetch<AnalysisResponse>(`${BASE_URL}/analysis`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getAnalysis: async (analysisId: string): Promise<any> => {
    return authenticatedFetch<any>(`${BASE_URL}/analysis/${analysisId}`);
  },

  listModelAnalyses: async (modelId: string): Promise<AnalysisListResponse> => {
    return authenticatedFetch<AnalysisListResponse>(`${BASE_URL}/models/${modelId}/analyses`);
  },

  // Stress Lab
  runStressTest: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
    stress_type: string;
    severity: number;
    random_state?: number;
  }): Promise<StressTestResponse> => {
    return authenticatedFetch<StressTestResponse>(`${BASE_URL}/stress-tests`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getStressTest: async (stressTestId: string): Promise<any> => {
    return authenticatedFetch<any>(`${BASE_URL}/stress-tests/${stressTestId}`);
  },

  listModelStressTests: async (modelId: string): Promise<StressTestListResponse> => {
    return authenticatedFetch<StressTestListResponse>(`${BASE_URL}/models/${modelId}/stress-tests`);
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
    return authenticatedFetch<FaultTestResponse>(`${BASE_URL}/fault-tests`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getFaultTest: async (faultTestId: string): Promise<any> => {
    return authenticatedFetch<any>(`${BASE_URL}/fault-tests/${faultTestId}`);
  },

  getFailureExplorerData: async (faultTestId: string): Promise<FailureExplorerResponse> => {
    return authenticatedFetch<FailureExplorerResponse>(`${BASE_URL}/fault-tests/${faultTestId}/failures`);
  },

  listModelFaultTests: async (modelId: string): Promise<FaultTestListResponse> => {
    return authenticatedFetch<FaultTestListResponse>(`${BASE_URL}/models/${modelId}/fault-tests`);
  },

  // Failure Memory
  buildFailureMemory: async (
    modelId: string,
    body: { fault_test_ids?: string[]; n_clusters?: number; random_state?: number }
  ): Promise<MemoryBuildResponse> => {
    return authenticatedFetch<MemoryBuildResponse>(`${BASE_URL}/failure-memory/${modelId}/build`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getFailureMemory: async (memoryId: string): Promise<any> => {
    return authenticatedFetch<any>(`${BASE_URL}/failure-memory/${memoryId}`);
  },

  matchFailureMemoryQuery: async (
    memoryId: string,
    body: { query_profile: Record<string, number> }
  ): Promise<MemoryMatchResponse> => {
    return authenticatedFetch<MemoryMatchResponse>(`${BASE_URL}/failure-memory/${memoryId}/match`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  listModelFailureMemories: async (modelId: string): Promise<MemoryListResponse> => {
    return authenticatedFetch<MemoryListResponse>(`${BASE_URL}/models/${modelId}/failure-memory`);
  },

  // Failure Prediction
  runFailurePrediction: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<PredictionResponse> => {
    return authenticatedFetch<PredictionResponse>(`${BASE_URL}/predictions/failure`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getPrediction: async (predictionId: string): Promise<any> => {
    return authenticatedFetch<any>(`${BASE_URL}/predictions/${predictionId}`);
  },

  // Early Warning
  queryEarlyWarning: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<WarningResponse> => {
    return authenticatedFetch<WarningResponse>(`${BASE_URL}/warnings`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  evaluateEarlyWarning: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<WarningEvaluationResponse> => {
    return authenticatedFetch<WarningEvaluationResponse>(`${BASE_URL}/warnings/evaluate`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getWarning: async (warningId: string): Promise<any> => {
    return authenticatedFetch<any>(`${BASE_URL}/warnings/${warningId}`);
  },
};
