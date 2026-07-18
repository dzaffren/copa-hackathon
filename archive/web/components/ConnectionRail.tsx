import Link from "next/link";
import { BRANCH_LABEL, SOURCE_TYPE_LABEL } from "@/lib/labels";
import type { Connection, ConnectionsResponse } from "@/lib/types";
import { isBlocked } from "@/lib/types";
import { QuoteBlock } from "./QuoteBlock";
import { SourceTypeDot } from "./SourceTypeDot";
import { VerdictBadge } from "./VerdictBadge";

interface RailProps {
  /** null → nothing selected yet. */
  data: ConnectionsResponse | null;
  /** True while the selected paragraph's connections are loading. */
  loading?: boolean;
  /** Non-null → the snapshot/API read failed for the selection. */
  error?: string | null;
  /** Whether the drafter has supplied this (otherwise blocked) source. */
  isSupplied: (connectionId: string) => boolean;
  onSupply: (connectionId: string) => void;
  onAnalyse: () => void;
}

/**
 * The right rail for one paragraph. Renders exactly four mutually-exclusive,
 * visually-distinct states (spec-upload-and-workspace.md):
 *   1. analysed with connections   → the connection cards
 *   2. analysed, no bearing source → "No matching source found"
 *   3. not analysed                → the "Analyse this paragraph" prompt
 *   4. a blocked (could_not_retrieve) card lives INSIDE state 1
 * Plus loading / error / nothing-selected framing states.
 */
export function ConnectionRail({
  data,
  loading,
  error,
  isSupplied,
  onSupply,
  onAnalyse,
}: RailProps) {
  if (loading) {
    return (
      <div className="space-y-3" data-testid="rail-loading">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p
        className="rounded-lg bg-red-50 p-4 text-sm text-red-700"
        data-testid="rail-error"
      >
        Couldn’t load the analysis — {error}{" "}
        <button className="underline" onClick={onAnalyse}>
          retry
        </button>
      </p>
    );
  }

  if (!data) {
    return (
      <p className="p-4 text-sm text-slate-500" data-testid="rail-empty">
        Select a paragraph on the left.
      </p>
    );
  }

  if (data.state === "not_analysed") {
    return (
      <div
        className="rounded-lg border border-dashed border-slate-300 p-4"
        data-testid="rail-not-analysed"
      >
        <p className="text-sm text-slate-500">
          This paragraph is not yet analysed.
        </p>
        <button
          className="mt-3 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          onClick={onAnalyse}
          data-testid="analyse-paragraph"
        >
          Analyse this paragraph
        </button>
      </div>
    );
  }

  if (data.no_matching_source || data.connections.length === 0) {
    return (
      <p
        className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600"
        data-testid="rail-no-source"
      >
        No matching source found. This paragraph was analysed, but no source in
        the curated library bears on it.
      </p>
    );
  }

  return (
    <ul className="space-y-3" data-testid="rail-connections">
      {data.connections.map((c) => (
        <li key={c.id}>
          <ConnectionCard
            connection={c}
            supplied={isSupplied(c.id)}
            onSupply={() => onSupply(c.id)}
          />
        </li>
      ))}
    </ul>
  );
}

function ConnectionCard({
  connection,
  supplied,
  onSupply,
}: {
  connection: Connection;
  supplied: boolean;
  onSupply: () => void;
}) {
  const { source, branch } = connection;

  return (
    <div
      className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm"
      data-testid={`conn-${connection.id}`}
    >
      <div className="flex items-center gap-2">
        <SourceTypeDot type={source.source_type} />
        <span className="text-sm font-medium text-slate-800">
          {source.title}
        </span>
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span className="rounded bg-slate-100 px-1.5 py-0.5">
          {BRANCH_LABEL[branch]}
        </span>
        <span>{SOURCE_TYPE_LABEL[source.source_type]}</span>
        {source.stance && <span>· feedback: {source.stance}</span>}
      </div>

      {isBlocked(connection) ? (
        <BlockedBody
          reason={connection.reason}
          supplied={supplied}
          onSupply={onSupply}
        />
      ) : (
        <div className="mt-2">
          <VerdictBadge verdict={connection.verdict} />
          <p className="mt-2 text-sm text-slate-600">{connection.rationale}</p>
          <QuoteBlock quote={connection.quote} />
          <Link
            href={`/connections/${encodeURIComponent(connection.id)}`}
            className="mt-3 inline-block text-sm font-medium text-indigo-600 hover:underline"
            data-testid="open-connection"
          >
            Open connection &amp; act →
          </Link>
        </div>
      )}
    </div>
  );
}

function BlockedBody({
  reason,
  supplied,
  onSupply,
}: {
  reason: string;
  supplied: boolean;
  onSupply: () => void;
}) {
  if (supplied) {
    return (
      <p
        className="mt-2 rounded bg-emerald-50 p-2 text-sm text-emerald-700"
        data-testid="blocked-supplied"
      >
        You supplied it — the tool can now quote it verbatim and analyse this
        connection like any other source.
      </p>
    );
  }
  return (
    <div className="mt-2 rounded bg-amber-50 p-2" data-testid="blocked-card">
      <p className="text-xs font-medium text-amber-800">couldn’t retrieve</p>
      <p className="mt-1 text-sm text-amber-700">{reason}</p>
      <button
        className="mt-2 rounded-md border border-amber-300 px-2.5 py-1 text-xs font-medium text-amber-800 hover:bg-amber-100"
        onClick={onSupply}
        data-testid="supply-source"
      >
        Upload this source
      </button>
    </div>
  );
}
