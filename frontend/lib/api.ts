/**
 * AEGIS-X Centralized Typed API Client
 */

import { getStoredAuthToken, setStoredAuthToken } from "@/lib/auth";
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

const getHeaders = (isMultipart: boolean = false): HeadersInit => {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }

  const token = activeAuthToken || getStoredAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

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

export const api = {
  // System & Health
  getHealth: async () => {
    const res = await fetch("http://127.0.0.1:8000/health");
    return handleResponse<{ status: string; service: string; api_version: string; engine_available: boolean }>(res);
  },

  getReadiness: async (): Promise<ReadinessResponse> => {
    const res = await fetch("http://127.0.0.1:8000/ready");
    return handleResponse<ReadinessResponse>(res);
  },

  getStatus: async (): Promise<SystemStatus> => {
    const res = await fetch(`${BASE_URL}/status`);
    return handleResponse<SystemStatus>(res);
  },

  getUserMe: async (): Promise<UserMe> => {
    const res = await fetch(`${BASE_URL}/me`, { headers: getHeaders() });
    return handleResponse<UserMe>(res);
  },

  // Model Registry
  listModels: async (): Promise<ModelListResponse> => {
    const res = await fetch(`${BASE_URL}/models`, { headers: getHeaders() });
    return handleResponse<ModelListResponse>(res);
  },

  getModel: async (modelId: string): Promise<ModelRecord> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}`, { headers: getHeaders() });
    return handleResponse<ModelRecord>(res);
  },

  getModelCapabilities: async (modelId: string): Promise<ModelCapabilitiesResponse> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}/capabilities`, { headers: getHeaders() });
    return handleResponse<ModelCapabilitiesResponse>(res);
  },

  registerModel: async (formData: FormData): Promise<ModelRecord> => {
    const res = await fetch(`${BASE_URL}/models`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData,
    });
    return handleResponse<ModelRecord>(res);
  },

  fitReferenceState: async (modelId: string, datasetId: string): Promise<ReferenceFitResponse> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}/reference/${datasetId}/fit`, {
      method: "POST",
      headers: getHeaders(),
    });
    return handleResponse<ReferenceFitResponse>(res);
  },

  // Dataset Registry
  listDatasets: async (modelId?: string): Promise<DatasetListResponse> => {
    const url = modelId ? `${BASE_URL}/datasets?model_id=${encodeURIComponent(modelId)}` : `${BASE_URL}/datasets`;
    const res = await fetch(url, { headers: getHeaders() });
    return handleResponse<DatasetListResponse>(res);
  },

  getDataset: async (datasetId: string): Promise<DatasetRecord> => {
    const res = await fetch(`${BASE_URL}/datasets/${datasetId}`, { headers: getHeaders() });
    return handleResponse<DatasetRecord>(res);
  },

  registerDataset: async (formData: FormData): Promise<DatasetRecord> => {
    const res = await fetch(`${BASE_URL}/datasets`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData,
    });
    return handleResponse<DatasetRecord>(res);
  },

  // Analysis Engine
  runAnalysis: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
    reference_dataset_id?: string;
    fusion_method?: string;
  }): Promise<AnalysisResponse> => {
    const res = await fetch(`${BASE_URL}/analysis`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<AnalysisResponse>(res);
  },

  getAnalysis: async (analysisId: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/analysis/${analysisId}`, { headers: getHeaders() });
    return handleResponse<any>(res);
  },

  listModelAnalyses: async (modelId: string): Promise<AnalysisListResponse> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}/analyses`, { headers: getHeaders() });
    return handleResponse<AnalysisListResponse>(res);
  },

  // Stress Lab
  runStressTest: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
    stress_type: string;
    severity: number;
    random_state?: number;
  }): Promise<StressTestResponse> => {
    const res = await fetch(`${BASE_URL}/stress-tests`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<StressTestResponse>(res);
  },

  getStressTest: async (stressTestId: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/stress-tests/${stressTestId}`, { headers: getHeaders() });
    return handleResponse<any>(res);
  },

  listModelStressTests: async (modelId: string): Promise<StressTestListResponse> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}/stress-tests`, { headers: getHeaders() });
    return handleResponse<StressTestListResponse>(res);
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
    const res = await fetch(`${BASE_URL}/fault-tests`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<FaultTestResponse>(res);
  },

  getFaultTest: async (faultTestId: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/fault-tests/${faultTestId}`, { headers: getHeaders() });
    return handleResponse<any>(res);
  },

  getFailureExplorerData: async (faultTestId: string): Promise<FailureExplorerResponse> => {
    const res = await fetch(`${BASE_URL}/fault-tests/${faultTestId}/failures`, { headers: getHeaders() });
    return handleResponse<FailureExplorerResponse>(res);
  },

  listModelFaultTests: async (modelId: string): Promise<FaultTestListResponse> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}/fault-tests`, { headers: getHeaders() });
    return handleResponse<FaultTestListResponse>(res);
  },

  // Failure Memory
  buildFailureMemory: async (
    modelId: string,
    body: { fault_test_ids?: string[]; n_clusters?: number; random_state?: number }
  ): Promise<MemoryBuildResponse> => {
    const res = await fetch(`${BASE_URL}/failure-memory/${modelId}/build`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<MemoryBuildResponse>(res);
  },

  getFailureMemory: async (memoryId: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/failure-memory/${memoryId}`, { headers: getHeaders() });
    return handleResponse<any>(res);
  },

  matchFailureMemoryQuery: async (
    memoryId: string,
    body: { query_profile: Record<string, number> }
  ): Promise<MemoryMatchResponse> => {
    const res = await fetch(`${BASE_URL}/failure-memory/${memoryId}/match`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<MemoryMatchResponse>(res);
  },

  listModelFailureMemories: async (modelId: string): Promise<MemoryListResponse> => {
    const res = await fetch(`${BASE_URL}/models/${modelId}/failure-memory`, { headers: getHeaders() });
    return handleResponse<MemoryListResponse>(res);
  },

  // Failure Prediction
  runFailurePrediction: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<PredictionResponse> => {
    const res = await fetch(`${BASE_URL}/predictions/failure`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<PredictionResponse>(res);
  },

  getPrediction: async (predictionId: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/predictions/${predictionId}`, { headers: getHeaders() });
    return handleResponse<any>(res);
  },

  // Early Warning
  queryEarlyWarning: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<WarningResponse> => {
    const res = await fetch(`${BASE_URL}/warnings`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<WarningResponse>(res);
  },

  evaluateEarlyWarning: async (body: {
    model_id: string;
    evaluation_dataset_id: string;
  }): Promise<WarningEvaluationResponse> => {
    const res = await fetch(`${BASE_URL}/warnings/evaluate`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<WarningEvaluationResponse>(res);
  },

  getWarning: async (warningId: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/warnings/${warningId}`, { headers: getHeaders() });
    return handleResponse<any>(res);
  },
};
