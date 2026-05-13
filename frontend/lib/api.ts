const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface Trial {
  id: string;
  title: string;
  status?: string;
  phase?: string;
  sponsor?: string;
  condition?: string;
  therapeutic_area?: string;
  start_date?: string;
  completion_date?: string;
  enrollment?: number;
}

export interface SearchResult {
  trial: Trial;
  score: number;
  chunk_text: string;
  rank: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface RAGResponse {
  question: string;
  answer: string;
  sources: Trial[];
  faithfulness_score?: number;
  eval_id?: number;
}

export interface EvalResult {
  id: number;
  query: string;
  faithfulness?: number;
  answer_relevance?: number;
  context_recall?: number;
  judge_score?: number;
  created_at: string;
}

export interface EvalSummary {
  avg_faithfulness: number;
  avg_answer_relevance: number;
  avg_context_recall: number;
  avg_judge_score: number;
  total_evals: number;
  below_threshold: number;
  threshold: number;
}

export interface IngestLog {
  id: number;
  run_at: string;
  trials_fetched: number;
  trials_new: number;
  trials_updated: number;
  trials_skipped: number;
  errors: number;
  duration_seconds?: number;
  status: string;
}

export interface TrialsResponse {
  total: number;
  items: Trial[];
  skip: number;
  limit: number;
}

async function apiFetch<T>(path: string, options?: RequestInit, token?: string, timeoutMs = 90000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers,
      signal: controller.signal,
      ...options,
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  } catch (e: any) {
    if (e.name === "AbortError") throw new Error("Request timed out. The server is taking too long — please try again.");
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  search: (query: string, filters?: { phase?: string; status?: string; therapeutic_area?: string }, token?: string) =>
    apiFetch<SearchResponse>("/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: 10, ...filters }),
    }, token),

  rag: (question: string, token?: string) =>
    apiFetch<RAGResponse>("/rag", {
      method: "POST",
      body: JSON.stringify({ question, top_k: 20 }),
    }, token),

  evalSummary: () => apiFetch<EvalSummary>("/evals/summary"),

  evalList: (limit = 50) => apiFetch<EvalResult[]>(`/evals?limit=${limit}`),

  ingestLogs: () => apiFetch<IngestLog[]>("/ingest/logs"),

  triggerIngest: (query = "") =>
    apiFetch("/ingest/trigger", { method: "POST", body: JSON.stringify({ query }) }),
    
  trialsList: (skip = 0, limit = 20, phase?: string, status?: string) => {
    let url = `/trials?skip=${skip}&limit=${limit}`;
    if (phase) url += `&phase=${encodeURIComponent(phase)}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    return apiFetch<TrialsResponse>(url);
  },

  health: () => fetch(`${API_BASE.replace("/api", "")}/health`).then((r) => r.json()),
};
