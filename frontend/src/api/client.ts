import type {
  ApiErrorPayload,
  ApiResponse,
  AssistantResult,
  CrackResult,
  HealthResult,
  KnowledgeResult,
  PlanningResult,
  SafetyResult,
  ValuationResult,
  WeatherResult,
} from './types';
import { apiKeyStore } from '../lib/apiKeyStore';

const BASE_URL = ((import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || '/api';
const TIMEOUT_MS = 90_000;

export class ApiRequestError extends Error {
  code: string;
  status: number;
  details: { field?: string | null; message: string }[];
  requestId?: string;

  constructor(
    message: string,
    options: {
      code?: string;
      status?: number;
      details?: { field?: string | null; message: string }[];
      requestId?: string;
    } = {},
  ) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = options.code || 'request_failed';
    this.status = options.status || 0;
    this.details = options.details || [];
    this.requestId = options.requestId;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiResponse<T>> {
  const extraHeaders: Record<string, string> = {};
  if (apiKeyStore.apiKey) extraHeaders['x-ai-api-key'] = apiKeyStore.apiKey;
  if (apiKeyStore.provider) extraHeaders['x-ai-provider'] = apiKeyStore.provider;
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { ...(init?.headers as Record<string, string> | undefined), ...extraHeaders },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === 'TimeoutError';
    throw new ApiRequestError(
      timedOut
        ? 'The request timed out. The AI provider may be busy — please try again.'
        : 'Cannot reach the ConstructIQ API. Make sure the FastAPI backend is running on port 8000.',
      { code: timedOut ? 'timeout' : 'network_error' },
    );
  }

  if (!response.ok) {
    let payload: ApiErrorPayload | null = null;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = null;
    }
    throw new ApiRequestError(payload?.error?.message || `Request failed with status ${response.status}.`, {
      code: payload?.error?.code,
      status: response.status,
      details: payload?.error?.details,
      requestId: payload?.error?.request_id,
    });
  }
  return (await response.json()) as ApiResponse<T>;
}

function jsonBody(value: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(value),
  };
}

export const api = {
  baseUrl: BASE_URL,

  health: () => request<HealthResult>('/health'),

  analyzeSafety: (form: FormData) =>
    request<SafetyResult>('/safety/analyze', { method: 'POST', body: form }),

  analyzeCrack: (form: FormData) =>
    request<CrackResult>('/crack/analyze', { method: 'POST', body: form }),

  createPlan: (payload: Record<string, unknown>) =>
    request<PlanningResult>('/planning/plan', jsonBody(payload)),

  estimateValuation: (payload: Record<string, unknown>) =>
    request<ValuationResult>('/valuation/estimate', jsonBody(payload)),

  chat: (payload: Record<string, unknown>) =>
    request<AssistantResult>('/assistant/chat', jsonBody(payload)),

  askKnowledge: (payload: Record<string, unknown>) =>
    request<KnowledgeResult>('/knowledge/ask', jsonBody(payload)),

  weather: (params: { city?: string; lat?: number; lon?: number }) => {
    const query = new URLSearchParams();
    if (params.city) query.set('city', params.city);
    if (params.lat !== undefined) query.set('lat', String(params.lat));
    if (params.lon !== undefined) query.set('lon', String(params.lon));
    return request<WeatherResult>(`/weather/advisory?${query.toString()}`);
  },
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.details.length) {
      return `${error.message} (${error.details.map((detail) => detail.message).join('; ')})`;
    }
    return error.message;
  }
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}
