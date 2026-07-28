import type {
  AnalyzeResponse,
  ChatHistoryTurn,
  Connection,
  CopilotDraftContext,
  CopilotIntent,
  CopilotResponse,
  CreateEdgeRequest,
  CreateEdgeResponse,
  CreateNodeRequest,
  DeleteEdgeResponse,
  DeleteNodeResponse,
  CreateNodeResponse,
  CreateWorkstreamRequest,
  CreateWorkstreamResponse,
  CrossLinkDetail,
  CrossLinksResponse,
  DraftResponse,
  EdgeDetail,
  ExtractConceptsResponse,
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
  SSEEvent,
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

async function deleteJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { method: "DELETE" });
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

/** Create a node, optionally attaching the document to chunk.
 *
 *  With an `attachment` the request goes as `multipart/form-data` — a JSON
 *  `payload` part plus the file — because a file cannot ride in a JSON body.
 *  Without one it stays the plain-JSON shape the URL-ingest path uses. The
 *  Content-Type header is deliberately NOT set for FormData: the browser must
 *  add it itself so the multipart boundary is included.
 */
export async function createNode(
  workstreamId: string,
  body: CreateNodeRequest,
  attachment?: File | null,
): Promise<CreateNodeResponse> {
  const url = `${API_BASE}/api/workstreams/${workstreamId}/nodes`;
  if (!attachment) {
    return postJson<CreateNodeResponse>(url, body);
  }
  const form = new FormData();
  form.append("payload", JSON.stringify(body));
  form.append("attachment", attachment);
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) {
    return throwHttpError(res);
  }
  return (await res.json()) as CreateNodeResponse;
}

/** Derive a document's concepts from its passages. Synchronous on the server —
 *  the promise settles only when extraction finishes (or fails). */
export function extractConcepts(
  workstreamId: string,
  nodeId: string,
): Promise<ExtractConceptsResponse> {
  return postJson<ExtractConceptsResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/nodes/${nodeId}/extract-concepts`,
  );
}

/** Connect two nodes already on the canvas. Runs no analysis. */
export function createEdge(
  workstreamId: string,
  body: CreateEdgeRequest,
): Promise<CreateEdgeResponse> {
  return postJson<CreateEdgeResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges`,
    body,
  );
}

/** Remove a node, its linkages, and the artefacts that only existed for it. */
export function deleteNode(
  workstreamId: string,
  nodeId: string,
): Promise<DeleteNodeResponse> {
  return deleteJson<DeleteNodeResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/nodes/${nodeId}`,
  );
}

/** Remove one linkage. Both documents stay; only the relationship goes. */
export function deleteEdge(
  workstreamId: string,
  edgeId: string,
): Promise<DeleteEdgeResponse> {
  return deleteJson<DeleteEdgeResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}`,
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
  draftContext?: CopilotDraftContext,
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
      draft_html: draftContext?.draftHtml,
      draft_selection: draftContext?.selectionText,
    },
  );
}

function abortError(): DOMException {
  return new DOMException("The user aborted a request.", "AbortError");
}

/** Stream a Copilot reply via SSE. Yields typed events as they arrive.
 *  Pass an AbortSignal so the caller can cancel the in-flight stream when
 *  the component unmounts, the intent changes, or the user navigates away.
 *
 *  The signal is deliberately *not* forwarded via `fetch()`'s `RequestInit`.
 *  In a real browser that would be equivalent, but under Vitest's jsdom test
 *  environment, jsdom installs its own `AbortController`/`AbortSignal`
 *  classes, distinct from the ones Node's native `fetch` (undici) validates
 *  against internally — passing that signal straight through throws
 *  `RequestInit: Expected signal (...) to be an instance of AbortSignal` the
 *  moment MSW's fetch interceptor reconstructs the `Request`. Cancellation is
 *  handled instead by calling `reader.cancel()`, which the Streams spec also
 *  defines to abort the underlying fetch in a real browser, so behaviour is
 *  equivalent without threading an environment-specific class through
 *  `fetch()`. */
export async function* streamCopilotMessage(
  workstreamId: string,
  nodeId: string,
  intent: CopilotIntent,
  message: string,
  history: ChatHistoryTurn[],
  referencedFindingIds: string[],
  signal: AbortSignal,
  draftContext?: CopilotDraftContext,
): AsyncGenerator<SSEEvent> {
  if (signal.aborted) throw abortError();

  const res = await fetch(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/copilot/stream`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        intent,
        message,
        history,
        referenced_finding_ids: referencedFindingIds,
        draft_html: draftContext?.draftHtml,
        draft_selection: draftContext?.selectionText,
      }),
    },
  );

  if (signal.aborted) {
    // Cancelled while the connection was still being established — drop the
    // response rather than surface stale tokens from an abandoned turn.
    void res.body?.cancel();
    throw abortError();
  }

  if (!res.ok) {
    return throwHttpError(res);
  }

  // Parse the SSE stream from the response body.
  const reader = res.body!.getReader();
  const onAbort = () => {
    reader.cancel(abortError()).catch(() => {});
  };
  signal.addEventListener("abort", onAbort);

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        if (signal.aborted) throw abortError();
        break;
      }
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by "\n\n".
      const frames = buffer.split("\n\n");
      // The last element is either "" (complete) or a partial frame — keep it.
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        if (!frame.trim()) continue;
        const lines = frame.split("\n");
        const eventLine = lines.find((l) => l.startsWith("event: "));
        const dataLine = lines.find((l) => l.startsWith("data: "));
        if (!eventLine || !dataLine) continue;
        const event = eventLine
          .slice("event: ".length)
          .trim() as SSEEvent["event"];
        const data = JSON.parse(
          dataLine.slice("data: ".length),
        ) as SSEEvent["data"];
        yield { event, data } as SSEEvent;
      }
    }
  } finally {
    signal.removeEventListener("abort", onAbort);
  }
}

// --- New Workstream --------------------------------------------------------

export async function fetchReviewers(): Promise<Person[]> {
  // The server already excludes the owner, so the picker cannot offer a drafter
  // themselves — no client-side filtering to keep in step.
  const body = await getJson<{ reviewers: Person[] }>(
    `${API_BASE}/api/reviewers`,
  );
  return body.reviewers;
}

export function createWorkstream(
  body: CreateWorkstreamRequest,
): Promise<CreateWorkstreamResponse> {
  return postJson<CreateWorkstreamResponse>(
    `${API_BASE}/api/workstreams`,
    body,
  );
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
