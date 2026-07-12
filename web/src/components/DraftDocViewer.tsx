// Mock, POC-grade viewer of the single living draft (spec-drafter-workspace.md ·
// System Design → Components: "Word/SharePoint-style render of the living draft +
// tracked-change insertions from workflowState"). Shared later by #8 (alignment)
// and #9 (copilot); #7 only reads.
//
// Security guardrail (spec · Permissions & Security / Threat Model): the markdown
// is parsed IN-COMPONENT into React elements — text is placed as React children,
// so React escapes everything. There is **no** `dangerouslySetInnerHTML` here and
// **no** npm markdown dependency (`web/package.json` is frozen).

import { Fragment, useEffect, useMemo, useState } from "react";

import type { TrackedChange } from "../types";
import { getTrackedChanges } from "../lib/workflowState";

const DEFAULT_DOCUMENT_ID = "rmit-v2-2026-draft";

export interface DraftDocViewerProps {
  /** The document whose tracked changes overlay the render. */
  documentId?: string;
  /** Raw markdown of the draft (e.g. loaded from data/mock/rmit-v2-2026-draft.md). */
  markdown: string;
}

// ---------------------------------------------------------------------------
// Minimal, dependency-free markdown parsing
// ---------------------------------------------------------------------------
//
// Deliberately tiny: enough to give the draft a legible, document-like surface
// (headings, paragraphs, bullet lists) without pulling in a markdown library.
// Anything not recognised is rendered as plain paragraph text — never as HTML.

type ParsedBlock =
  | { kind: "h1"; text: string }
  | { kind: "h2"; text: string }
  | { kind: "p"; text: string }
  | { kind: "ul"; items: string[] };

function parseMarkdown(markdown: string): ParsedBlock[] {
  const blocks: ParsedBlock[] = [];
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");

  let paragraph: string[] = [];
  let list: string[] = [];

  const flushParagraph = (): void => {
    if (paragraph.length > 0) {
      blocks.push({ kind: "p", text: paragraph.join(" ").trim() });
      paragraph = [];
    }
  };
  const flushList = (): void => {
    if (list.length > 0) {
      blocks.push({ kind: "ul", items: list });
      list = [];
    }
  };

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();

    if (trimmed === "") {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(trimmed);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      blocks.push({ kind: level === 1 ? "h1" : "h2", text: heading[2].trim() });
      continue;
    }

    const listItem = /^[-*]\s+(.*)$/.exec(trimmed);
    if (listItem) {
      flushParagraph();
      list.push(listItem[1].trim());
      continue;
    }

    // A plain text line — joins the current paragraph.
    flushList();
    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();
  return blocks;
}

// ---------------------------------------------------------------------------
// Anchoring tracked changes to their clause
// ---------------------------------------------------------------------------

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function blockText(block: ParsedBlock): string {
  return block.kind === "ul" ? block.items.join(" ") : block.text;
}

/**
 * The index of the first parsed block that mentions `clauseNumber`, or -1 when
 * none does. Matches either the full label ("RMiT 17.1") or its bare number
 * ("17.1", as the draft prints it), guarding against partial hits like "117.1"
 * or "17.10".
 */
function anchorIndex(blocks: ParsedBlock[], clauseNumber: string): number {
  const full = clauseNumber.trim();
  const numeric = full.match(/\d[\d.]*\d|\d/)?.[0] ?? "";
  const numericRe = numeric
    ? new RegExp(`(^|[^\\d.])${escapeRegExp(numeric)}(?![\\d.])`)
    : null;

  return blocks.findIndex((block) => {
    const text = blockText(block);
    if (full && text.includes(full)) return true;
    return numericRe ? numericRe.test(text) : false;
  });
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

/** A single tracked-change insertion, visually + accessibly distinct. */
function TrackedInsertion({ change }: { change: TrackedChange }): JSX.Element {
  const acceptedDate = change.acceptedAt.slice(0, 10);
  return (
    <ins
      data-testid="tracked-change"
      data-finding-id={change.findingId}
      aria-label={`Tracked-change insertion at ${change.clauseNumber}, accepted ${acceptedDate}`}
      className="my-2 block rounded border-l-4 border-emerald-500 bg-emerald-50 px-3 py-2 no-underline"
    >
      <span className="mb-1 flex flex-wrap items-center gap-x-2 text-xs font-semibold uppercase tracking-wide text-emerald-700">
        <span aria-hidden="true">✎</span>
        <span>Tracked change · {change.clauseNumber}</span>
        <time
          dateTime={change.acceptedAt}
          className="font-normal normal-case text-emerald-600"
        >
          accepted {acceptedDate}
        </time>
      </span>
      <span className="text-emerald-900 underline decoration-emerald-500 decoration-2 underline-offset-2">
        {change.insertedText}
      </span>
    </ins>
  );
}

function renderBlock(block: ParsedBlock, key: number): JSX.Element {
  switch (block.kind) {
    case "h1":
      return (
        <h1 key={key} className="mb-4 mt-2 text-2xl font-bold text-slate-900">
          {block.text}
        </h1>
      );
    case "h2":
      return (
        <h2
          key={key}
          className="mb-3 mt-6 text-lg font-semibold text-slate-800"
        >
          {block.text}
        </h2>
      );
    case "ul":
      return (
        <ul key={key} className="my-3 list-disc space-y-1 pl-6 text-slate-700">
          {block.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
    case "p":
    default:
      return (
        <p key={key} className="my-3 leading-relaxed text-slate-700">
          {block.text}
        </p>
      );
  }
}

export default function DraftDocViewer({
  documentId = DEFAULT_DOCUMENT_ID,
  markdown,
}: DraftDocViewerProps): JSX.Element {
  // Render-on-mount read of the shared store (sufficient for #7, which only
  // reads). A lightweight `storage` listener also refreshes on a cross-tab write
  // — a nice-to-have that goes through the public reader and never rebuilds the
  // store's key contract (owned by workflowState.ts).
  const [changes, setChanges] = useState<TrackedChange[]>(() =>
    getTrackedChanges(documentId),
  );

  useEffect(() => {
    setChanges(getTrackedChanges(documentId));

    const refresh = (event: StorageEvent): void => {
      if (event.key === null || event.key.includes(documentId)) {
        setChanges(getTrackedChanges(documentId));
      }
    };
    window.addEventListener("storage", refresh);
    return () => window.removeEventListener("storage", refresh);
  }, [documentId]);

  const { blocks, anchored, orphans } = useMemo(() => {
    const parsed = parseMarkdown(markdown);
    const anchoredMap = new Map<number, TrackedChange[]>();
    const orphanList: TrackedChange[] = [];

    for (const change of changes) {
      const index = anchorIndex(parsed, change.clauseNumber);
      if (index >= 0) {
        const bucket = anchoredMap.get(index) ?? [];
        bucket.push(change);
        anchoredMap.set(index, bucket);
      } else {
        orphanList.push(change);
      }
    }

    return { blocks: parsed, anchored: anchoredMap, orphans: orphanList };
  }, [markdown, changes]);

  return (
    <article className="mx-auto max-w-3xl">
      {/* Word/SharePoint-style chrome above the page surface. */}
      <div className="flex items-center justify-between rounded-t-md border border-b-0 border-slate-200 bg-slate-100 px-6 py-2 text-xs text-slate-500">
        <span className="font-medium text-slate-600">{documentId}</span>
        <span>
          {changes.length} tracked {changes.length === 1 ? "change" : "changes"}
        </span>
      </div>

      <div className="rounded-b-md border border-slate-200 bg-white px-8 py-10 shadow-sm sm:px-12">
        {blocks.map((block, index) => (
          <Fragment key={index}>
            {renderBlock(block, index)}
            {(anchored.get(index) ?? []).map((change) => (
              <TrackedInsertion key={change.id} change={change} />
            ))}
          </Fragment>
        ))}

        {orphans.length > 0 && (
          <section
            aria-labelledby="proposed-insertions-heading"
            className="mt-8 border-t border-dashed border-slate-300 pt-6"
          >
            <h2
              id="proposed-insertions-heading"
              className="mb-2 text-lg font-semibold text-slate-800"
            >
              Proposed insertions
            </h2>
            <p className="mb-3 text-sm text-slate-500">
              Accepted changes whose anchor clause was not found in this draft.
            </p>
            {orphans.map((change) => (
              <TrackedInsertion key={change.id} change={change} />
            ))}
          </section>
        )}
      </div>
    </article>
  );
}
