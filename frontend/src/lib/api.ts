import type {
  AnalyzeResponse,
  Connection,
  CreateNodeRequest,
  CreateNodeResponse,
  EdgeDetail,
  NodeDetail,
  TaskResponse,
  WorkstreamGraph,
  WorkstreamSummary,
} from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ApiError {
  code: string;
  message: string;
}

class HttpError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
  }
}

async function throwHttpError(res: Response): Promise<never> {
  let code = "INTERNAL_ERROR";
  let message = `Request failed with status ${res.status}`;
  try {
    const body = (await res.json()) as Partial<ApiError>;
    if (body.code) code = body.code;
    if (body.message) message = body.message;
  } catch {
    // non-JSON error body — keep defaults
  }
  throw new HttpError(res.status, code, message);
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    return throwHttpError(res);
  }
  return (await res.json()) as T;
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    return throwHttpError(res);
  }
  return (await res.json()) as T;
}

// --- Task Screen -----------------------------------------------------------

export function fetchTask(
  workstreamId: string,
  nodeId: string,
): Promise<TaskResponse> {
  return getJson<TaskResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}`,
  );
}

export function fetchEdgeFindings(
  workstreamId: string,
  edgeId: string,
): Promise<Connection[]> {
  return getJson<Connection[]>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/findings`,
  );
}

// --- Graph Screen ----------------------------------------------------------

export async function fetchWorkstreams(): Promise<WorkstreamSummary[]> {
  const body = await getJson<{ workstreams: WorkstreamSummary[] }>(
    `${API_BASE}/api/workstreams`,
  );
  return body.workstreams;
}

export function fetchGraph(workstreamId: string): Promise<WorkstreamGraph> {
  return getJson<WorkstreamGraph>(
    `${API_BASE}/api/workstreams/${workstreamId}/graph`,
  );
}

export function fetchNodeDetail(
  workstreamId: string,
  nodeId: string,
): Promise<NodeDetail> {
  return getJson<NodeDetail>(
    `${API_BASE}/api/workstreams/${workstreamId}/nodes/${nodeId}`,
  );
}

export function fetchEdgeDetail(
  workstreamId: string,
  edgeId: string,
): Promise<EdgeDetail> {
  return getJson<EdgeDetail>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}`,
  );
}

export function createNode(
  workstreamId: string,
  body: CreateNodeRequest,
): Promise<CreateNodeResponse> {
  return postJson<CreateNodeResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/nodes`,
    body,
  );
}

export function analyzeEdge(
  workstreamId: string,
  edgeId: string,
): Promise<AnalyzeResponse> {
  return postJson<AnalyzeResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/analyze`,
  );
}

export { HttpError };
