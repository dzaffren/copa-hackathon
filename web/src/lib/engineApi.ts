// Typed, read-mostly client for the Rulebook Radar engine (engine/api.py).
//
// Binds to the FastAPI read service: `GET /graph`, `GET /nodes/{id}`,
// `GET /clauses/{clause_number}?version=`, and `POST /connections/find`. The
// workspace (#7) uses only the three GETs; `findConnections` exists for the
// alignment story (#8) that reuses this client.
//
// Contract guarantees (spec-drafter-workspace.md · API Design / Permissions):
//   • The base URL comes from `VITE_ENGINE_BASE_URL`; a missing/empty value is a
//     configuration error, surfaced as a typed `EngineConfigError` (never a
//     silent request to `undefined/...`).
//   • Every path segment (clause numbers, node ids) is `encodeURIComponent`-
//     encoded, matching the engine's `:path` + `unquote` handling — so
//     `getClause("Outsourcing 12.1")` hits `/clauses/Outsourcing%2012.1`.
//   • A `404` with the uniform `{error, message}` body becomes a typed
//     `EngineNotFound` carrying the `error` code (so the UI can show
//     "No matching clause found" for `CLAUSE_NOT_FOUND`); any other non-2xx
//     becomes a generic `EngineRequestError`.

import type { Clause, ConnectionResult, Graph, NodeDetail } from "../types";

/** Thrown when `VITE_ENGINE_BASE_URL` is missing or empty at request time. */
export class EngineConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineConfigError";
    // Restore the prototype chain (TS + transpiled `extends Error`).
    Object.setPrototypeOf(this, EngineConfigError.prototype);
  }
}

/** Thrown on a `404` — carries the engine's `{error}` code and message. */
export class EngineNotFound extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status = 404) {
    super(message);
    this.name = "EngineNotFound";
    this.code = code;
    this.status = status;
    Object.setPrototypeOf(this, EngineNotFound.prototype);
  }
}

/** Thrown on any other non-2xx response (or a network/transport failure). */
export class EngineRequestError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = "EngineRequestError";
    this.status = status;
    this.code = code;
    Object.setPrototypeOf(this, EngineRequestError.prototype);
  }
}

/** The engine's uniform error body `{error, message}`. */
interface EngineErrorBody {
  error: string;
  message: string;
}

function isEngineErrorBody(body: unknown): body is EngineErrorBody {
  return (
    typeof body === "object" &&
    body !== null &&
    "error" in body &&
    typeof (body as Record<string, unknown>).error === "string"
  );
}

/**
 * Resolve the engine base URL from the build-time env, throwing a typed
 * `EngineConfigError` when it is missing/empty. Resolved lazily per request (not
 * at module load) so tests can drive both the configured and missing states via
 * `vi.stubEnv`, and so a runtime-injected URL is honoured. Any trailing slash is
 * stripped to keep `${base}${path}` joins clean.
 */
function resolveBaseUrl(): string {
  const raw = import.meta.env.VITE_ENGINE_BASE_URL;
  if (typeof raw !== "string" || raw.trim() === "") {
    throw new EngineConfigError(
      "VITE_ENGINE_BASE_URL is not set. Copy web/.env.example to web/.env and " +
        "point it at the engine read API (e.g. http://127.0.0.1:8000).",
    );
  }
  return raw.replace(/\/+$/, "");
}

/** Map a non-ok `Response` to the right typed error, reading the `{error,
 *  message}` body when present. */
async function toEngineError(response: Response): Promise<Error> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  const code = isEngineErrorBody(body) ? body.error : undefined;
  const message = isEngineErrorBody(body)
    ? body.message
    : response.statusText || `Engine request failed (${response.status})`;

  if (response.status === 404) {
    return new EngineNotFound(code ?? "NOT_FOUND", message, 404);
  }
  return new EngineRequestError(response.status, message, code);
}

/** Issue a request against the engine and decode its JSON body, translating
 *  transport + HTTP failures into the typed error hierarchy above. */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = resolveBaseUrl();

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, init);
  } catch (cause) {
    throw new EngineRequestError(
      0,
      `Network error requesting ${path}: ${String(cause)}`,
    );
  }

  if (!response.ok) {
    throw await toEngineError(response);
  }
  return (await response.json()) as T;
}

/** `GET /graph` — the whole knowledge graph (nodes + full edges). */
export function getGraph(): Promise<Graph> {
  return requestJson<Graph>("/graph");
}

/** `GET /nodes/{id}` — a node's derived status + outgoing edges (no clause
 *  anchors). The id is URL-encoded. `404` → `EngineNotFound("NODE_NOT_FOUND")`. */
export function getNode(id: string): Promise<NodeDetail> {
  return requestJson<NodeDetail>(`/nodes/${encodeURIComponent(id)}`);
}

/** `GET /clauses/{clause_number}?version=` — one verbatim clause. The clause
 *  number is URL-encoded (`"Outsourcing 12.1"` → `Outsourcing%2012.1`). A
 *  `404` → `EngineNotFound` (`CLAUSE_NOT_FOUND` / `CLAUSE_VERSION_NOT_FOUND`). */
export function getClause(
  clauseNumber: string,
  version?: string,
): Promise<Clause> {
  const path = `/clauses/${encodeURIComponent(clauseNumber)}`;
  const query = version ? `?version=${encodeURIComponent(version)}` : "";
  return requestJson<Clause>(`${path}${query}`);
}

/** `POST /connections/find` — the pairwise finder (owned by #8, not called by
 *  the #7 read-only workspace; the client contract lives here for reuse). */
export function findConnections(
  idA: string,
  idB: string,
): Promise<ConnectionResult> {
  return requestJson<ConnectionResult>("/connections/find", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: [idA, idB] }),
  });
}
