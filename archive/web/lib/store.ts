// The one shared finding state (spec-upload-and-workspace.md → "Shared Technical Spine").
// A single Zustand store, persisted to localStorage under the "rr" key, imported as a
// `useStore` hook by every route. Persistence keeps state across reloads; Zustand's
// cross-tab sync keeps open tabs live — the honest MVP1 realisation of "one shared state".
// No backend writes: the engine is read-only; every drafter action lands here, client-side.
//
// SLICE OWNERSHIP (each story owns the slices + methods it writes):
//   sources, blocked            — Upload & workspace          (implemented here, Task 1)
//   verdicts, trail             — Connection reconciliation   (methods added by that story)
//   watch, setAside             — Cross-source insights       (methods added by that story)
//   draft, resolved, submitted  — Grounded redraft assistant  (methods added by that story)
//   driftSeen                   — Source drift monitor        (methods added by that story)
//
// This file (Task 1) ships the workspace slices and the shared scaffold (reset,
// connectionsFor). Downstream stories extend `RRState` and this creator with their own
// methods; they must not restructure the slices below.

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  Connection,
  ConnectionsResponse,
  Verdict,
  Verification,
} from "./types";

/** A source the drafter added that the curated library missed. */
export interface AddedSource {
  title: string;
  source_type: string;
  added_by: "drafter";
}

/** One entry in the decision trail (owned by reconciliation; typed here so all read it). */
export interface TrailEntry {
  connection_id: string;
  paragraph: string;
  verdict: Verdict;
  source: string;
  quote: {
    clause_number: string;
    text: string | null;
    verification: Verification;
  };
  note_type: string;
  why?: string | null;
}

export interface VerdictRecord {
  status: "confirmed" | "dismissed";
  verdict?: Verdict;
  reason?: string;
  why?: string | null;
}

export interface RRState {
  // ── Upload & workspace (this story) ─────────────────────────────────────
  sources: Record<string, AddedSource[]>;
  blocked: string[];
  addSource: (
    paragraph: string,
    src: { title: string; source_type: string },
  ) => void;
  supplyBlocked: (connectionId: string) => void;
  /** Merge the engine payload with any drafter-added sources for one paragraph. */
  connectionsFor: (
    paragraph: string,
    engine: ConnectionsResponse,
  ) => ConnectionsResponse;

  // ── Reconciliation (methods added by that story) ────────────────────────
  verdicts: Record<string, VerdictRecord>;
  trail: TrailEntry[];

  // ── Cross-source insights (methods added by that story) ─────────────────
  watch: { insight_id: string; source: string; added_at: string }[];
  setAside: string[];

  // ── Grounded redraft assistant (methods added by that story) ────────────
  draft: Record<string, { text: string; tracked_changes: unknown[] }>;
  resolved: Record<string, { kind: "edit" | "dismissal"; reason?: string }>;
  submitted: { submitted: true; trail: TrailEntry[] } | null;

  // ── Source drift monitor (methods added by that story) ──────────────────
  driftSeen: string[];

  // ── Shared scaffold ─────────────────────────────────────────────────────
  /** Clear every slice — a fresh upload is a fresh session. */
  reset: () => void;
}

const EMPTY: Pick<
  RRState,
  | "sources"
  | "blocked"
  | "verdicts"
  | "trail"
  | "watch"
  | "setAside"
  | "draft"
  | "resolved"
  | "submitted"
  | "driftSeen"
> = {
  sources: {},
  blocked: [],
  verdicts: {},
  trail: [],
  watch: [],
  setAside: [],
  draft: {},
  resolved: {},
  submitted: null,
  driftSeen: [],
};

/** Render a drafter-added source as a connection card (branch "uncited", no engine verdict). */
function addedToConnection(paragraph: string, src: AddedSource): Connection {
  return {
    id: `${paragraph}::added:${src.title}`,
    branch: "uncited",
    source: {
      document_id: `added:${src.title}`,
      title: src.title,
      // Added sources carry the drafter's chosen type; widen to the engine union at render.
      source_type: src.source_type as Connection["source"]["source_type"],
    },
    status: "could_not_retrieve",
    reason:
      "Added by you — the tool will link it to this paragraph and analyse the connection.",
    verdict: null,
    quote: null,
  };
}

export const useStore = create<RRState>()(
  persist(
    (set, get) => ({
      ...EMPTY,

      addSource: (paragraph, src) => {
        const title = src.title.trim().slice(0, 200);
        if (!title) return; // empty title is rejected (Validation rule)
        set((s) => {
          const existing = s.sources[paragraph] ?? [];
          // Idempotent: same title on the same paragraph is not re-added.
          if (existing.some((e) => e.title === title)) return s;
          return {
            sources: {
              ...s.sources,
              [paragraph]: [
                ...existing,
                { title, source_type: src.source_type, added_by: "drafter" },
              ],
            },
          };
        });
      },

      supplyBlocked: (connectionId) =>
        set((s) =>
          s.blocked.includes(connectionId)
            ? s // idempotent
            : { blocked: [...s.blocked, connectionId] },
        ),

      connectionsFor: (paragraph, engine) => {
        const added = get().sources[paragraph] ?? [];
        if (added.length === 0) return engine;
        return {
          ...engine,
          // Added sources are always a real result, so a paragraph with only
          // added sources is no longer "no matching source found".
          no_matching_source: false,
          connections: [
            ...engine.connections,
            ...added.map((src) => addedToConnection(paragraph, src)),
          ],
        };
      },

      reset: () => set({ ...EMPTY }),
    }),
    {
      name: "rr",
      // Persist only data slices; methods are recreated by the store on load.
      partialize: (s) => ({
        sources: s.sources,
        blocked: s.blocked,
        verdicts: s.verdicts,
        trail: s.trail,
        watch: s.watch,
        setAside: s.setAside,
        draft: s.draft,
        resolved: s.resolved,
        submitted: s.submitted,
        driftSeen: s.driftSeen,
      }),
    },
  ),
);
