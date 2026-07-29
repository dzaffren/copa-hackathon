import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { saveNodeMetadata } from "@/lib/api";
import type { ConceptsAvailable, NodeMetadataRequest } from "@/lib/types";
import {
  asList,
  CONCEPT_FIELD_ORDER,
  LIST_FIELDS,
  type ConceptField,
} from "./metadata";

/** The two fields that hold clause-length text and so get a textarea. */
const MULTILINE_FIELDS = new Set<ConceptField>([
  "empowerment_framework",
  "requirement",
]);

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

/** Turn the edited strings back into the wire shape.
 *
 *  Blank, whitespace-only, and an emptied list all become `null`: "cleared" and
 *  "never set" are one state, which is what "blank means not set yet" requires.
 *  All nine keys are always present — the server replaces the profile whole, so
 *  an omitted key would silently clear a value the drafter did not touch. */
function toRequest(values: FormState): NodeMetadataRequest {
  const body = {} as Record<ConceptField, string | string[] | null>;
  for (const [field] of CONCEPT_FIELD_ORDER) {
    const raw = values[field];
    if (LIST_FIELDS.has(field)) {
      const members = raw
        .split(",")
        .map((m) => m.trim())
        .filter((m) => m.length > 0);
      body[field] = members.length > 0 ? members : null;
    } else {
      body[field] = raw.trim() || null;
    }
  }
  return body as unknown as NodeMetadataRequest;
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

  return (
    <div className="mt-2 space-y-3">
      {CONCEPT_FIELD_ORDER.map(([field, label]) => (
        <label key={field} className="block text-sm">
          <span className="mb-1 block text-xs font-medium text-muted-foreground">
            {label}
          </span>
          {MULTILINE_FIELDS.has(field) ? (
            <textarea
              className={fieldClass}
              rows={3}
              aria-label={label}
              value={values[field]}
              onChange={(e) => update(field, e.target.value)}
            />
          ) : (
            <input
              className={fieldClass}
              aria-label={label}
              value={values[field]}
              onChange={(e) => update(field, e.target.value)}
            />
          )}
          {field === "empowerment_framework" && (
            <span className="mt-1 block text-[11px] text-muted-foreground">
              Quote this word-for-word from the document.
            </span>
          )}
        </label>
      ))}

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
