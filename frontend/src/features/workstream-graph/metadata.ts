import type { ConceptsAvailable } from "@/lib/types";

/** One of the seven regulatory-profile fields. */
export type ConceptField = keyof Omit<ConceptsAvailable, "status">;

/** Display order + labels for the regulatory-profile fields.
 *
 *  `keywords` and `requirement` were removed on 30 Jul 2026: the extracted axes
 *  (the Concepts section) now carry a document's topics, derived from the
 *  document itself rather than typed by hand, and the obligation a document
 *  imposes is the whole draft rather than one field.
 *
 *  Shared by the panel's read mode and `NodeMetadataForm`'s edit mode so the two
 *  cannot drift: a drafter must fill in the field she thought she was reading. */
export const CONCEPT_FIELD_ORDER: [ConceptField, string][] = [
  ["policy_owner", "Policy owner"],
  ["applicability", "Applicability"],
  ["empowerment_framework", "Empowerment framework"],
  ["issuance_date", "Issuance date"],
  ["effective_date", "Effective date"],
  ["legal_basis", "Legal basis"],
  ["ismp_classification", "ISMP classification"],
];

/** The one field that holds several values. It renders as chips in read mode and
 *  as one comma-separated line in edit mode. */
export const LIST_FIELDS = new Set<ConceptField>(["legal_basis"]);

/** The four BNM security classifications, ascending in sensitivity. Offered as a
 *  closed dropdown rather than free text — these are handling categories with
 *  real consequences, not a label a drafter should be able to invent. */
export const ISMP_CLASSIFICATIONS = [
  "UMUM",
  "TERHAD",
  "SULIT",
  "RAHSIA",
] as const;

/** ISMP classification has no offline source (its authority is CAS's RH
 *  publication form), so an empty one is honestly pending rather than merely
 *  unfilled. A drafter may still record one. */
export const ISMP_PENDING = "Pending — RH publication form";

/** Normalise a concept value to a display list (a list stays a list, a scalar
 *  becomes one item, null/undefined becomes empty). Lets `legal_basis` render as
 *  chips regardless of older scalar side-files. */
export function asList(value: string[] | string | null | undefined): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}
