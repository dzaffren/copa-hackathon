// Connection detail (spec-drafter-workspace.md · "Understanding the core cluster
// connection", "A different connection shows a different real overlap", "Each
// reference connection carries an at-a-glance 'why this reference matters'";
// Tests 3–5). Given a selected edge it explains, in plain language, WHY the two
// nodes connect (the engine `reason`) and then hydrates the cited clauses
// VERBATIM by number via `getClause`.
//
// Verbatim-citation guardrail (Product rule): a clause is only ever shown as the
// text the engine returns for its number. If a cited clause does not resolve
// (404 CLAUSE_NOT_FOUND → typed `EngineNotFound`), the panel shows "No matching
// clause found" — it never invents text and never crashes.
//
// Reference / cross-cluster deferral (#26): a `references` or `cross-cluster`
// edge shows only the "why it matters" note (and, for references, a hand-off to
// the Reference Radar). The verbatim, clause-by-clause passages of what an
// external reference SAYS are #26's job — so those edges fetch NO clause text.

import { useEffect, useState } from "react";

import type { GraphEdge } from "../../types";
import { EngineNotFound, getClause } from "../../lib/engineApi";

export interface EdgeDetailProps {
  edge: GraphEdge;
}

/** Edge types whose deep content is deferred (references) or not-yet-built
 *  (cross-cluster) — these must NOT fetch verbatim clause text. */
const NO_CLAUSE_HYDRATION = new Set(["references", "cross-cluster"]);

type ClauseStatus = "loading" | "resolved" | "missing" | "error";

interface ClauseResult {
  clauseNumber: string;
  status: ClauseStatus;
  text?: string;
}

/** The clauses this edge cites, deduped, draft-side (source) first. */
function citedClauses(edge: GraphEdge): string[] {
  const all = [...(edge.source_clauses ?? []), ...(edge.target_clauses ?? [])];
  return Array.from(new Set(all));
}

function headingFor(type: string): string {
  if (type === "references") return "Why this reference matters";
  if (type === "cross-cluster") return "Why this surfaced";
  return "Why these are connected";
}

/** One cited clause, quoted verbatim — or the guardrail message when it is
 *  missing, or a neutral notice on any other transient failure. */
function ClausePassage({ result }: { result: ClauseResult }): JSX.Element {
  return (
    <blockquote
      data-testid="clause-passage"
      className="border-l-4 border-slate-300 pl-3"
    >
      <cite className="block text-xs font-semibold not-italic text-slate-500">
        {result.clauseNumber}
      </cite>
      {result.status === "loading" && (
        <p className="text-sm text-slate-400">Loading clause…</p>
      )}
      {result.status === "resolved" && (
        <p className="text-sm text-slate-800">{result.text}</p>
      )}
      {result.status === "missing" && (
        <p className="text-sm font-medium text-amber-700">
          No matching clause found
        </p>
      )}
      {result.status === "error" && (
        <p className="text-sm text-slate-400">
          Clause text is unavailable right now.
        </p>
      )}
    </blockquote>
  );
}

export default function EdgeDetail({ edge }: EdgeDetailProps): JSX.Element {
  const isReference = edge.type === "references";
  const isCrossCluster = edge.type === "cross-cluster";
  const hydrates = !NO_CLAUSE_HYDRATION.has(edge.type);

  const [results, setResults] = useState<ClauseResult[]>(() =>
    hydrates
      ? citedClauses(edge).map((clauseNumber) => ({
          clauseNumber,
          status: "loading" as const,
        }))
      : [],
  );

  useEffect(() => {
    if (NO_CLAUSE_HYDRATION.has(edge.type)) {
      setResults([]);
      return;
    }
    const clauses = citedClauses(edge);
    if (clauses.length === 0) {
      setResults([]);
      return;
    }

    let cancelled = false;
    setResults(
      clauses.map((clauseNumber) => ({
        clauseNumber,
        status: "loading" as const,
      })),
    );

    Promise.all(
      clauses.map(async (clauseNumber): Promise<ClauseResult> => {
        try {
          const clause = await getClause(clauseNumber);
          return { clauseNumber, status: "resolved", text: clause.text };
        } catch (err) {
          // Only a genuine "not found" becomes the guardrail message; any other
          // failure is a neutral notice, never invented clause text.
          if (err instanceof EngineNotFound) {
            return { clauseNumber, status: "missing" };
          }
          return { clauseNumber, status: "error" };
        }
      }),
    ).then((next) => {
      if (!cancelled) setResults(next);
    });

    return () => {
      cancelled = true;
    };
  }, [edge]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900">
          {headingFor(edge.type)}
        </h2>
        <p className="mt-1 text-sm leading-relaxed text-slate-700">
          {edge.reason}
        </p>
      </div>

      {isReference && (
        <div className="rounded-md bg-sky-50 p-3 text-sm text-sky-900">
          <p>
            The verbatim, clause-by-clause detail lives in the Reference Radar —
            it is not shown here.
          </p>
          <button
            type="button"
            className="mt-2 rounded border border-sky-300 bg-white px-3 py-1.5 text-sm font-medium text-sky-800"
          >
            See in the Reference Radar
          </button>
        </div>
      )}

      {isCrossCluster && (
        <p className="rounded-md bg-slate-100 p-3 text-sm text-slate-600">
          Full cross-cluster mapping is a future phase.
        </p>
      )}

      {hydrates && results.length > 0 && (
        <section aria-label="Cited clauses" className="space-y-3">
          {results.map((result) => (
            <ClausePassage key={result.clauseNumber} result={result} />
          ))}
        </section>
      )}
    </div>
  );
}
