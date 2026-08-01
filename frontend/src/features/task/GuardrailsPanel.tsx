import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fetchGuardrails, saveGuardrails } from "@/lib/api";
import type { GuardrailsResponse } from "@/lib/types";

interface Props {
  workstreamId: string;
}

/** The protection badge on the Recommendations card, and the guardrails behind it.
 *
 *  These are the rules the recommendations engine follows — four of the five
 *  defaults encode a specific way the tool has already been observed to get this
 *  wrong against a real BNM reviewer, and the fifth is the verbatim-citation
 *  rule. All five are editable: a rule the drafter cannot change is not
 *  accountable to her, which is the point of showing them at all.
 *
 *  Collapsed by default. The badge is the toggle, so the rules are one click from
 *  the recommendations they shaped rather than on another screen.
 */
export function GuardrailsPanel({ workstreamId }: Props) {
  const queryClient = useQueryClient();
  const queryKey = ["guardrails", workstreamId];
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey,
    queryFn: () => fetchGuardrails(workstreamId),
  });

  // Seed the textarea from the server once, then leave it alone: re-seeding on
  // every render would discard what the drafter is typing.
  useEffect(() => {
    if (query.data && draft === null) setDraft(query.data.body);
  }, [query.data, draft]);

  const mutation = useMutation({
    mutationFn: (body: string) => saveGuardrails(workstreamId, body),
    onMutate: () => setError(null),
    onSuccess: (saved: GuardrailsResponse) => {
      queryClient.setQueryData<GuardrailsResponse>(queryKey, saved);
      setDraft(saved.body);
    },
    // The drafter's edits stay on screen on failure — she may have typed a
    // paragraph, and losing it to a failed request would be worse than the
    // failure.
    onError: () => setError("We could not save your guardrails. Try again."),
  });

  const value = draft ?? "";
  const dirty = query.data != null && value !== query.data.body;

  return (
    <>
      <button
        type="button"
        data-testid="guardrails-badge"
        aria-expanded={open}
        aria-label="Guardrails — the rules recommendations follow"
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-semibold transition",
          open
            ? "border-primary/40 bg-primary/10 text-primary"
            : "border-border/60 text-muted-foreground hover:bg-accent hover:text-foreground",
        )}
      >
        <ShieldCheck className="h-3.5 w-3.5" />
        Guardrails
      </button>

      {open && (
        <div
          data-testid="guardrails-panel"
          className="mt-2 w-full rounded-lg border border-border/60 bg-muted/30 p-3"
        >
          <p className="mb-2 text-[11px] leading-relaxed text-muted-foreground">
            The rules every recommendation must follow. Edit them and the next
            generation reads what you saved.
          </p>

          {query.isPending && (
            <div
              role="status"
              className="flex items-center gap-2 py-2 text-xs text-muted-foreground"
            >
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading
              guardrails…
            </div>
          )}

          {query.isError && (
            <p className="py-2 text-xs text-muted-foreground">
              We could not load the guardrails.
            </p>
          )}

          {query.data && (
            <>
              <label htmlFor="guardrails-body" className="sr-only">
                Guardrails
              </label>
              <textarea
                id="guardrails-body"
                data-testid="guardrails-body"
                value={value}
                onChange={(event) => setDraft(event.target.value)}
                rows={12}
                className="w-full rounded-md border border-border/60 bg-card p-2 font-mono text-[11px] leading-relaxed outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
              />

              {/* An empty box is a real decision, so it is reported rather than
                  quietly overruled by reinstating the defaults. */}
              {value.trim() === "" && (
                <p
                  data-testid="guardrails-empty-warning"
                  className="mt-1.5 text-[11px] font-medium text-amber-800"
                >
                  Recommendations will be generated with no guardrails.
                </p>
              )}

              {error && (
                <p className="mt-1.5 text-[11px] text-destructive">{error}</p>
              )}

              <div className="mt-2 flex items-center gap-2">
                <Button
                  size="sm"
                  data-testid="guardrails-save"
                  disabled={!dirty || mutation.isPending}
                  onClick={() => mutation.mutate(value)}
                >
                  {mutation.isPending && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  )}
                  Save
                </Button>
                {query.data.updated_at && !dirty && (
                  <span className="text-[11px] text-muted-foreground">
                    Saved
                  </span>
                )}
                {query.data.is_default && (
                  <span className="text-[11px] text-muted-foreground">
                    Showing the shipped defaults
                  </span>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
