// "Why this changed" provenance trail (spec-drafter-workspace.md · Test 9 +
// scenarios "The 'Why this changed' trail lists public supporting documents" /
// "An internal supporting document appears locked and content-withheld").
//
// This is a CLIENT-SIDE mock, keyed by document id — provenance is deliberately
// NOT in the engine graph (there are no provenance edges in `graph.json`), and
// these supporting documents NEVER appear as their own graph nodes; they show
// only inside the detail panel's "Why this changed" trail when the draft is
// selected.
//
// Confidentiality-aware: public documents are shown with their real title and
// date; internal documents are listed (so the trail stays complete) but marked
// restricted with their content withheld — the panel renders a locked entry, it
// does not reveal the note-as-content.

/** Whether a supporting document's content may be shown, or is withheld. */
export type ProvenanceAccess = "public" | "internal";

/** One entry in a document's "Why this changed" trail. */
export interface ProvenanceEntry {
  /** Stable id for React keys. */
  id: string;
  /** Real title — shown for public entries; still shown (only) for internal so
   *  the trail stays complete. */
  title: string;
  /** Kind of supporting document, e.g. "Discussion Paper" | "FAQ". */
  documentType: string;
  /** Human-readable date, e.g. "19 Dec 2025". Empty when withheld. */
  date: string;
  /** ISO date for ordering/machine use. Empty when withheld. */
  isoDate: string;
  /** `"public"` → title + date + note shown; `"internal"` → locked/withheld. */
  access: ProvenanceAccess;
  /** True when the content is access-controlled and must not be rendered. */
  restricted: boolean;
  /** Public: a short why-it-changed note. Internal: a withheld-notice string
   *  (never the document's actual content). */
  note: string;
}

/**
 * Trails keyed by document id. Only the single editable draft carries a trail
 * in MVP1 (spec: the "Why this changed" trail is rendered only for
 * `rmit-v2-2026-draft`).
 */
export const provenanceByDocument: Record<string, ProvenanceEntry[]> = {
  "rmit-v2-2026-draft": [
    {
      id: "prov-opres-discussion-paper-2025",
      title: "Operational Resilience — Discussion Paper",
      documentType: "Discussion Paper",
      date: "19 Dec 2025",
      isoDate: "2025-12-19",
      access: "public",
      restricted: false,
      note:
        "BNM's Operational Resilience discussion paper reframed continuity of " +
        "critical financial services around deeper third-party and cloud " +
        "dependencies — the context for RMiT v2's cloud changes.",
    },
    {
      id: "prov-rmit-faqs-2026",
      title: "RMiT FAQs (updated)",
      documentType: "FAQ",
      date: "1 Jul 2026",
      isoDate: "2026-07-01",
      access: "public",
      restricted: false,
      note:
        "The updated RMiT FAQs clarified the cloud consultation / notification " +
        "expectation that RMiT 17.1 is being revised to reflect.",
    },
    {
      id: "prov-jpp-minutes-cloud-review",
      title: "JPP Committee minutes — cloud policy review",
      documentType: "Committee minutes",
      // Withheld: an internal, access-controlled document. Title is shown so the
      // trail stays complete; the date and content are not revealed.
      date: "",
      isoDate: "",
      access: "internal",
      restricted: true,
      note:
        "Restricted — internal committee minutes, access-controlled. Listed so " +
        "the trail stays complete; its content is not shown here.",
    },
  ],
};

/** The "Why this changed" trail for a document id (empty when none applies). */
export function getProvenance(documentId: string): ProvenanceEntry[] {
  return provenanceByDocument[documentId] ?? [];
}
