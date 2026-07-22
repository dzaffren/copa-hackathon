import type {
  AnalyzeResponse,
  ChatHistoryTurn,
  Connection,
  CopilotIntent,
  CopilotResponse,
  CreateNodeRequest,
  CreateNodeResponse,
  CreateWorkstreamRequest,
  CreateWorkstreamResponse,
  CrossLinkDetail,
  CrossLinksResponse,
  DraftResponse,
  EdgeDetail,
  LinkageReviewResponse,
  LinkageTransitionRequest,
  LinkageTransitionResponse,
  LinkagesResponse,
  Person,
  ReviewQueueResponse,
  NodeDetail,
  PatchReviewStateResponse,
  ReviewResponse,
  ReviewState,
  TaskResponse,
  TaskWorkflow,
  TaskWorkflowStatus,
  WorkstreamGraph,
  WorkstreamSummary,
} from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ApiError {
  code: string;
  message: string;
  /** Which input the error belongs to, when the route names one. Lets a form
   *  flag the offending field instead of showing a banner. */
  field?: string;
}

class HttpError extends Error {
  code: string;
  status: number;
  field?: string;
  constructor(status: number, code: string, message: string, field?: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
    this.field = field;
  }
}

async function throwHttpError(res: Response): Promise<never> {
  let code = "INTERNAL_ERROR";
  let message = `Request failed with status ${res.status}`;
  let field: string | undefined;
  try {
    const body = (await res.json()) as Partial<ApiError>;
    if (body.code) code = body.code;
    if (body.message) message = body.message;
    if (body.field) field = body.field;
  } catch {
    // non-JSON error body — keep defaults
  }
  throw new HttpError(res.status, code, message, field);
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

export function setTaskWorkflow(
  workstreamId: string,
  nodeId: string,
  status: TaskWorkflowStatus,
  actorId: string,
): Promise<{ workflow: TaskWorkflow }> {
  return patchJson<{ workflow: TaskWorkflow }>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/workflow`,
    { status, actor_id: actorId },
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
  history: ChatHistoryTurn[],
  referencedFindingIds: string[],
): Promise<CopilotResponse> {
  // The server holds no conversation state (deliberately not persisted across
  // sessions), so the client sends the full prior history on every call.
  return postJson<CopilotResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/copilot`,
    {
      intent,
      message,
      history,
      referenced_finding_ids: referencedFindingIds,
    },
  );
}

// --- New Workstream --------------------------------------------------------

export async function fetchReviewers(): Promise<Person[]> {
  // The server already excludes the owner, so the picker cannot offer a drafter
  // themselves — no client-side filtering to keep in step.
  const body = await getJson<{ reviewers: Person[] }>(`${API_BASE}/api/reviewers`);
  return body.reviewers;
}

export function createWorkstream(
  body: CreateWorkstreamRequest,
): Promise<CreateWorkstreamResponse> {
  return postJson<CreateWorkstreamResponse>(`${API_BASE}/api/workstreams`, body);
}

// --- Cross-workstream linkage ----------------------------------------------

export async function fetchCrossLinks(workstreamId: string) {
  const body = await getJson<CrossLinksResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/cross-links`,
  );
  return body.links;
}

/** Every cross-workstream link in the corpus, regardless of workstream —
 *  backs the Home dashboard's Overlap Alerts card and the Cross-Workstream
 *  Intelligence page's metrics + relationship list. */
export async function fetchAllCrossLinks() {
  const body = await getJson<CrossLinksResponse>(`${API_BASE}/api/cross-links`);
  return body.links;
}

/** One cross-workstream relationship in full: both regulatory profiles, what
 *  they share, why it was flagged, and the verbatim clause evidence on every
 *  linkage. Backs the Cross-Workstream Intelligence relationship panel. */
export function fetchCrossLinkDetail(edgeId: string): Promise<CrossLinkDetail> {
  return getJson<CrossLinkDetail>(`${API_BASE}/api/cross-links/${edgeId}`);
}

// --- Per-linkage Maker-Checker workflow ------------------------------------

/** The Review Queue: every cross-workstream linkage with its maker-checker
 *  status, plus a tally by status. */
export function fetchReviewQueue(): Promise<ReviewQueueResponse> {
  return getJson<ReviewQueueResponse>(`${API_BASE}/api/review-queue`);
}

/** Every linkage on an edge with its maker-checker record. */
export function fetchLinkageReview(
  workstreamId: string,
  edgeId: string,
): Promise<LinkageReviewResponse> {
  return getJson<LinkageReviewResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/linkage-review`,
  );
}

/** Apply a maker-checker action to one linkage (claim / submit / pick_up /
 *  approve / reject / request_changes). The server enforces valid transitions
 *  and the maker≠checker rule. */
export function transitionLinkageReview(
  workstreamId: string,
  edgeId: string,
  findingId: string,
  body: LinkageTransitionRequest,
): Promise<LinkageTransitionResponse> {
  return patchJson<LinkageTransitionResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/findings/${findingId}/linkage-review`,
    body,
  );
}

export { HttpError };
