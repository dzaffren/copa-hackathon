import type { ConceptsAvailable } from "@/lib/types";

/** One of the nine regulatory-profile fields. */
export type ConceptField = keyof Omit<ConceptsAvailable, "status">;

/** Display order + labels for the regulatory-profile fields. `legal_basis` and
 *  `ismp_classification` were added for Cross-Workstream Intelligence — a shared
 *  Act or classification is a strong overlap signal.
 *
 *  Shared by the panel's read mode and `NodeMetadataForm`'s edit mode so the two
 *  cannot drift: a drafter must fill in the field she thought she was reading. */
export const CONCEPT_FIELD_ORDER: [ConceptField, string][] = [
  ["policy_owner", "Policy owner"],
  ["applicability", "Applicability"],
  ["empowerment_framework", "Empowerment framework"],
  ["requirement", "Requirement"],
  ["issuance_date", "Issuance date"],
  ["effective_date", "Effective date"],
  ["keywords", "Keywords"],
  ["legal_basis", "Legal basis"],
  ["ismp_classification", "ISMP classification"],
];

/** The two fields that hold several values. They render as chips in read mode
 *  and as one comma-separated line in edit mode. */
export const LIST_FIELDS = new Set<ConceptField>(["keywords", "legal_basis"]);

/** ISMP classification has no offline source (its authority is CAS's RH
 *  publication form), so an empty one is honestly pending rather than merely
 *  unfilled. A drafter may still record one. */
export const ISMP_PENDING = "Pending — RH publication form";

/** Normalise a concept value to a display list (a list stays a list, a scalar
 *  becomes one item, null/undefined becomes empty). Lets `keywords` and
 *  `legal_basis` render as chips regardless of older scalar side-files. */
export function asList(value: string[] | string | null | undefined): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}
