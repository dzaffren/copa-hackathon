// "Why this changed" trail (spec-drafter-workspace.md · "The 'Why this changed'
// trail lists public supporting documents" / "An internal supporting document
// appears locked and content-withheld"; Test 9).
//
// Confidentiality-aware and client-side: the trail is read from the mock
// `provenance.ts` fixture (there are NO provenance edges in the engine graph),
// keyed by document id, and rendered only inside the detail panel — a supporting
// document NEVER becomes its own graph node. Public entries show their real
// title + date; internal entries are listed (so the trail stays complete) but
// locked, with their content withheld — the withheld notice is shown, never the
// document's actual content.

import type { ProvenanceEntry } from "../../fixtures/provenance";
import { getProvenance } from "../../fixtures/provenance";

export interface ProvenanceTrailProps {
  /** The document whose trail to render — only the editable draft has one. */
  documentId: string;
}

/** A public supporting document: real title, type + date, and a short note. */
function PublicEntry({ entry }: { entry: ProvenanceEntry }): JSX.Element {
  return (
    <div>
      <p className="font-medium text-slate-800">{entry.title}</p>
      <p className="text-xs text-slate-500">
        <span>{entry.documentType}</span>
        {entry.date !== "" && (
          <>
            {" · "}
            <time dateTime={entry.isoDate}>{entry.date}</time>
          </>
        )}
        <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 uppercase tracking-wide text-slate-500">
          public
        </span>
      </p>
      <p className="mt-1 text-sm text-slate-600">{entry.note}</p>
    </div>
  );
}

/** An internal supporting document: title shown so the trail is complete, but
 *  locked — access-controlled, with its content withheld (never revealed). */
function LockedEntry({ entry }: { entry: ProvenanceEntry }): JSX.Element {
  return (
    <div>
      <p className="font-medium text-slate-800">
        {entry.title} <span aria-hidden="true">🔒</span>
      </p>
      <p
        className="text-xs font-semibold uppercase tracking-wide text-amber-700"
        data-testid="locked-label"
      >
        Restricted · access-controlled · content withheld
      </p>
      <p className="mt-1 text-sm text-slate-600">{entry.note}</p>
    </div>
  );
}

export default function ProvenanceTrail({
  documentId,
}: ProvenanceTrailProps): JSX.Element | null {
  const entries = getProvenance(documentId);
  if (entries.length === 0) return null;

  return (
    <section
      data-testid="why-this-changed"
      aria-labelledby="why-this-changed-heading"
      className="mt-6 border-t border-slate-200 pt-4"
    >
      <h3
        id="why-this-changed-heading"
        className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500"
      >
        Why this changed
      </h3>
      <ul className="space-y-4">
        {entries.map((entry) => (
          <li key={entry.id} data-testid={`provenance-${entry.id}`}>
            {entry.restricted ? (
              <LockedEntry entry={entry} />
            ) : (
              <PublicEntry entry={entry} />
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
