import type { ConceptsAvailable } from "@/lib/types";

/** One of the seven regulatory-profile fields. */
export type ConceptField = keyof Omit<ConceptsAvailable, "status">;

/** Display order + labels for the regulatory-profile fields.
 *
 *  `keywords` went on 30 Jul 2026 (the extracted axes carry a document's topics
 *  from the document itself) and `empowerment_framework` on 31 Jul 2026. On
 *  1 Aug 2026 "Legal basis" became "Legal provision" and `requirement` returned
 *  as "Policy requirement" — this time earning its row, because it is the axis
 *  list Recommendations reasons over rather than a restatement of the draft.
 *
 *  Shared by the panel's read mode and `NodeMetadataForm`'s edit mode so the two
 *  cannot drift: a drafter must fill in the field she thought she was reading. */
export const CONCEPT_FIELD_ORDER: [ConceptField, string][] = [
  ["policy_owner", "Policy owner"],
  ["applicability", "Applicability"],
  ["legal_provision", "Legal provision"],
  ["issuance_date", "Issuance date"],
  ["effective_date", "Effective date"],
  ["policy_requirement", "Policy requirement"],
  ["ismp_classification", "ISMP classification"],
];

/** The fields that hold several values. Each renders as chips in read mode and
 *  as one comma-separated line in edit mode.
 *
 *  `asList` tolerates a bare string on every one of them, which matters: the
 *  three retired workstreams still store `applicability` as a single sentence,
 *  and they render as one chip rather than breaking. */
export const LIST_FIELDS = new Set<ConceptField>([
  "applicability",
  "legal_provision",
  "policy_requirement",
]);

/** Helper text shown under a field in edit mode. Only `policy_requirement`
 *  carries one: what a drafter types there is not just a profile row, it is the
 *  input Recommendations is formulated from, and nothing else on the form says
 *  so. */
export const FIELD_NOTES: Partial<Record<ConceptField, string>> = {
  policy_requirement:
    "These become the dimensions the Recommendations feature is formulated on.",
};

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
 *  becomes one item, null/undefined becomes empty). Lets `legal_provision` render as
 *  chips regardless of older scalar side-files. */
export function asList(value: string[] | string | null | undefined): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}
