import type {
  AnalyzeResponse,
  Connection,
  CopilotIntent,
  CopilotResponse,
  CreateNodeRequest,
  CreateNodeResponse,
  DraftResponse,
  EdgeDetail,
  LinkagesResponse,
  NodeDetail,
  PatchReviewStateResponse,
  ReviewResponse,
  ReviewState,
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

async function patchJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
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

// --- Review Linkages -------------------------------------------------------

export function fetchReview(
  workstreamId: string,
  edgeId: string,
): Promise<ReviewResponse> {
  return getJson<ReviewResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/review`,
  );
}

export function setReviewState(
  workstreamId: string,
  edgeId: string,
  findingId: string,
  reviewState: ReviewState,
): Promise<PatchReviewStateResponse> {
  // Finding ids carry a `~` separator, which is unreserved in a path segment —
  // encoded anyway so any future id shape survives the round-trip.
  return patchJson<PatchReviewStateResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/findings/` +
      encodeURIComponent(findingId),
    { review_state: reviewState },
  );
}

// --- Drafting Workspace ----------------------------------------------------

async function putJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    return throwHttpError(res);
  }
  return (await res.json()) as T;
}

export function fetchReviewedLinkages(
  workstreamId: string,
  nodeId: string,
): Promise<LinkagesResponse> {
  return getJson<LinkagesResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/reviewed-linkages`,
  );
}

export function fetchRelatedLinkages(
  workstreamId: string,
  nodeId: string,
): Promise<LinkagesResponse> {
  // hops is fixed at 1 and sent explicitly: the server rejects anything else,
  // and naming it here keeps the bound visible at the call site.
  return getJson<LinkagesResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/related-linkages?hops=1`,
  );
}

export function fetchDraft(
  workstreamId: string,
  nodeId: string,
): Promise<DraftResponse> {
  return getJson<DraftResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/draft`,
  );
}

export function saveDraft(
  workstreamId: string,
  nodeId: string,
  contentHtml: string,
): Promise<DraftResponse> {
  return putJson<DraftResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/draft`,
    { content_html: contentHtml },
  );
}

export function sendCopilotMessage(
  workstreamId: string,
  nodeId: string,
  intent: CopilotIntent,
  message: string,
  turn: number,
): Promise<CopilotResponse> {
  // `turn` is client-owned: the chat is deliberately not persisted, so the
  // server holds no conversation state to count from.
  return postJson<CopilotResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/copilot`,
    { intent, message, turn },
  );
}

export { HttpError };
