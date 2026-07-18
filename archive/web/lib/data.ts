// The single read seam over the engine's analysis data (spec-upload-and-workspace.md →
// "Shared Technical Spine" / "API Design"). Two sources, one interface:
//
//   NEXT_PUBLIC_API_BASE unset  → fetch the bundled JSON snapshot in /public/data
//                                 (default; deploy-safe, no backend at demo time)
//   NEXT_PUBLIC_API_BASE = URL  → call the live FastAPI engine
//                                 (enables the live "analyse any paragraph" moment)
//
// Every consuming route/component reads through here — it never talks to the engine or
// the snapshot directly, so the snapshot-vs-live switch stays in one place.

import type { ConnectionsResponse, ParagraphsResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ?? "";

/** The one demo vehicle (see the epic — BNM AI Discussion Paper). */
export const DOCUMENT_ID = "ai-dp-2025";

/** True when reads come from the bundled snapshot rather than a live engine. */
export const isSnapshot = API_BASE === "";

/** Raised when the snapshot/live source cannot be read; callers render a retry state. */
export class DataUnavailableError extends Error {
  constructor(
    message: string,
    readonly cause_status?: number,
  ) {
    super(message);
    this.name = "DataUnavailableError";
  }
}

async function getJson<T>(url: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, { cache: "no-store" });
  } catch (e) {
    throw new DataUnavailableError(`Could not reach ${url}: ${String(e)}`);
  }
  if (!res.ok) {
    throw new DataUnavailableError(`${url} returned ${res.status}`, res.status);
  }
  return (await res.json()) as T;
}

/** Canvas paragraphs + per-paragraph analysis state. */
export async function fetchParagraphs(): Promise<ParagraphsResponse> {
  const url = isSnapshot
    ? "/data/paragraphs.json"
    : `${API_BASE}/documents/${DOCUMENT_ID}/paragraphs`;
  return getJson<ParagraphsResponse>(url);
}

/**
 * Every connection the right rail needs for one paragraph. In snapshot mode a
 * missing file means the paragraph was never pre-analysed — surface it as a
 * clean "analysed, nothing bears on it" result rather than an error, so the UI
 * shows "No matching source found" instead of a crash.
 */
export async function fetchConnections(
  paragraph: string,
): Promise<ConnectionsResponse> {
  if (isSnapshot) {
    try {
      return await getJson<ConnectionsResponse>(
        `/data/connections/${paragraph}.json`,
      );
    } catch (e) {
      if (e instanceof DataUnavailableError && e.cause_status === 404) {
        return {
          paragraph: { number: paragraph, title: "" },
          state: "not_analysed",
          no_matching_source: false,
          connections: [],
        };
      }
      throw e;
    }
  }
  return getJson<ConnectionsResponse>(
    `${API_BASE}/documents/${DOCUMENT_ID}/paragraphs/${paragraph}/connections`,
  );
}

/**
 * Live "Analyse this paragraph". Only meaningful against a live engine; in
 * snapshot mode it degrades to a snapshot read (the demo's pre-analysed
 * paragraphs are unaffected). A 503 from the engine is surfaced so the caller
 * can show the graceful "live analysis temporarily unavailable" message.
 */
export async function analyse(paragraph: string): Promise<ConnectionsResponse> {
  if (isSnapshot) {
    return fetchConnections(paragraph);
  }
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE}/documents/${DOCUMENT_ID}/paragraphs/${paragraph}/analyse`,
      { method: "POST", cache: "no-store" },
    );
  } catch (e) {
    throw new DataUnavailableError(`Analyse request failed: ${String(e)}`);
  }
  if (res.status === 503) {
    throw new DataUnavailableError(
      "Live analysis is temporarily unavailable; pre-analysed paragraphs are unaffected.",
      503,
    );
  }
  if (!res.ok) {
    throw new DataUnavailableError(
      `Analyse returned ${res.status}`,
      res.status,
    );
  }
  return (await res.json()) as ConnectionsResponse;
}
