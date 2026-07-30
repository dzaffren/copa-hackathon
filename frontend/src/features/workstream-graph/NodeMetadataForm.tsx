import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { HttpError, saveNodeMetadata } from "@/lib/api";
import type { ConceptsAvailable, NodeMetadataRequest } from "@/lib/types";
import {
  asList,
  CONCEPT_FIELD_ORDER,
  ISMP_CLASSIFICATIONS,
  LIST_FIELDS,
  type ConceptField,
} from "./metadata";

/** The one field that holds clause-length text and so gets a textarea. */
const MULTILINE_FIELDS = new Set<ConceptField>(["empowerment_framework"]);

/** Plain-language copy for the refusals a save can provoke. Most of these should
 *  be unreachable from this form — it sends exactly the nine known keys and never
 *  `task_type` — but a refusal the drafter cannot read is worse than a verbose
 *  map, and the server's own message is the fallback. */
const ERROR_COPY: Record<string, string> = {
  METADATA_TOO_LARGE: "That value is too long — shorten it and try again.",
  INVALID_ISMP_CLASSIFICATION:
    "Choose one of the four classifications, or leave it unset.",
  INVALID_METADATA: "That value could not be saved. Check it and try again.",
  UNKNOWN_METADATA_FIELD: "That field is not part of the profile.",
  TASK_TYPE_IMMUTABLE:
    "A deliverable kind is set when the document is created and cannot be changed.",
  WORKSTREAM_NOT_FOUND: "This workstream is no longer available.",
  NODE_NOT_FOUND: "This document is no longer in the workstream.",
};

const fieldClass =
  "w-full rounded-md border border-border/70 bg-background/60 px-3 py-2 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/40";

/** Every field's editing value is a string — a list field holds its members
 *  comma-separated on one line, which is how a drafter enters several. */
type FormState = Record<ConceptField, string>;

/** Seed the form from the stored profile: a list joins into one editable line, a
 *  missing or null value becomes an empty input (never the text "null"). */
function toFormState(initial: ConceptsAvailable | null): FormState {
  const state = {} as FormState;
  for (const [field] of CONCEPT_FIELD_ORDER) {
    const value = initial?.[field] ?? null;
    state[field] = LIST_FIELDS.has(field)
      ? asList(value).join(", ")
      : typeof value === "string"
        ? value
        : "";
  }
  return state;
}

/** One typed value, or `null` when the drafter left it blank. Whitespace is not
 *  a value: "cleared" and "never set" are one state on disk, which is what
 *  "blank means not set yet" requires. */
function text(raw: string): string | null {
  return raw.trim() || null;
}

/** A comma-separated line as its members: trimmed, with empty ones dropped so a
 *  stray or trailing comma cannot store a blank keyword. An empty result is
 *  `null` rather than `[]`, matching `text`'s treatment of a cleared field. */
function list(raw: string): string[] | null {
  const members = raw
    .split(",")
    .map((m) => m.trim())
    .filter((m) => m.length > 0);
  return members.length > 0 ? members : null;
}

/** Turn the edited strings back into the wire shape.
 *
 *  Written out field by field rather than looped: the server replaces the profile
 *  whole, so an omitted key silently clears a value the drafter never touched.
 *  Spelling the seven out means the compiler catches a missing one, which a loop
 *  over `CONCEPT_FIELD_ORDER` could only do behind a cast. */
function toRequest(values: FormState): NodeMetadataRequest {
  return {
    policy_owner: text(values.policy_owner),
    applicability: text(values.applicability),
    empowerment_framework: text(values.empowerment_framework),
    issuance_date: text(values.issuance_date),
    effective_date: text(values.effective_date),
    legal_basis: list(values.legal_basis),
    ismp_classification: text(values.ismp_classification),
  };
}

interface NodeMetadataFormProps {
  workstreamId: string;
  nodeId: string;
  /** Current values, or null when the node has no profile yet. */
  initial: ConceptsAvailable | null;
  onDone: () => void;
}

/**
 * Edit mode for the Metadata disclosure: nine controlled inputs, Save and
 * Cancel. A plain controlled form, consistent with `AddNodeDialog` and
 * `AddEdgeDialog` — no form library.
 *
 * Its own file rather than inlined because `NodeDetailPanel.tsx` is already
 * ~500 lines carrying the header, five sections, the delete flow, and the footer
 * actions; a nine-field form inline would make it the largest file in the
 * feature.
 */
export function NodeMetadataForm({
  workstreamId,
  nodeId,
  initial,
  onDone,
}: NodeMetadataFormProps) {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<FormState>(() => toFormState(initial));

  const update = (field: ConceptField, value: string) =>
    setValues((v) => ({ ...v, [field]: value }));

  // The form is NOT reset or unmounted on failure — a drafter who typed a date
  // and lost the connection must be able to press Save again, not retype it.
  const mutation = useMutation({
    mutationFn: () => saveNodeMetadata(workstreamId, nodeId, toRequest(values)),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["node", workstreamId, nodeId],
      });
      onDone();
    },
  });

  const error = mutation.error;
  const errorCode = error instanceof HttpError ? error.code : undefined;
  const errorField = error instanceof HttpError ? error.field : undefined;
  const errorMessage = error
    ? ((errorCode && ERROR_COPY[errorCode]) ?? error.message)
    : null;

  return (
    <div className="mt-2 space-y-3">
      {CONCEPT_FIELD_ORDER.map(([field, label]) => {
        // The server names the field at fault, so the offending input is ringed
        // rather than leaving the drafter to guess which of nine it means.
        const inputClass = cn(
          fieldClass,
          errorField === field && "border-red-400 ring-1 ring-red-400",
        );
        return (
          <label key={field} className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-muted-foreground">
              {label}
            </span>
            {field === "ismp_classification" ? (
              // A closed vocabulary, not free text: these are BNM handling
              // categories with real consequences. The blank option is kept and
              // listed first so leaving it unset stays available — the panel then
              // renders the honest "pending" state rather than a guess.
              <select
                className={inputClass}
                aria-label={label}
                value={values[field]}
                onChange={(e) => update(field, e.target.value)}
              >
                <option value="">Not set</option>
                {ISMP_CLASSIFICATIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            ) : MULTILINE_FIELDS.has(field) ? (
              <textarea
                className={inputClass}
                rows={3}
                aria-label={label}
                value={values[field]}
                onChange={(e) => update(field, e.target.value)}
              />
            ) : (
              <input
                className={inputClass}
                aria-label={label}
                value={values[field]}
                onChange={(e) => update(field, e.target.value)}
              />
            )}
          </label>
        );
      })}

      {errorMessage && (
        <p role="alert" className="text-sm text-red-500">
          {errorMessage}
        </p>
      )}

      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={mutation.isPending}
          onClick={onDone}
        >
          Cancel
        </Button>
        <Button
          type="button"
          size="sm"
          className="bg-primary text-primary-foreground hover:bg-primary/90"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </div>
  );
}

export default NodeMetadataForm;
