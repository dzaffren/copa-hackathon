import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, FileText, History, User, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { HttpError, fetchLinkageReview, transitionLinkageReview } from "@/lib/api";
import { CROSS_STORE, type Person, type ReviewQueueItem } from "@/lib/types";
import { labelStyle, labelText } from "@/lib/labels";
import { Skeleton } from "@/components/ui/skeleton";
import { ACTION_LABELS, NEXT_ACTIONS, statusStyle } from "./reviewStatus";

/** The maker-checker control surface for one linkage: current status, maker,
 *  checker, timestamps, contextual action buttons (with an actor + optional
 *  comment), and the full append-only audit history. */
export function LinkageReviewPanel({
  item,
  actors,
  onClose,
}: {
  item: ReviewQueueItem;
  actors: Person[];
  onClose?: () => void;
}) {
  const queryClient = useQueryClient();
  const [actorId, setActorId] = useState(actors[0]?.id ?? "");
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["linkage-review", item.workstream_id, item.edge_id],
    queryFn: () => fetchLinkageReview(item.workstream_id, item.edge_id),
  });

  const row = useMemo(
    () => data?.linkages.find((l) => l.finding_id === item.finding_id),
    [data, item.finding_id],
  );
  const record = row?.review;

  const mutation = useMutation({
    mutationFn: (action: string) =>
      transitionLinkageReview(item.workstream_id, item.edge_id, item.finding_id, {
        action: action as never,
        actor_id: actorId,
        comment: comment.trim() || undefined,
      }),
    onSuccess: () => {
      setComment("");
      setError(null);
      queryClient.invalidateQueries({
        queryKey: ["linkage-review", item.workstream_id, item.edge_id],
      });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    },
    onError: (err) => {
      setError(
        err instanceof HttpError ? err.message : "Could not apply that action.",
      );
    },
  });

  const style = record ? statusStyle(record.status) : statusStyle("ai_detected");
  const actions = record ? NEXT_ACTIONS[record.status] : [];

  return (
    <div className="flex h-full min-h-0 flex-col" data-testid="linkage-review-panel">
      {/* Header */}
      <header className="border-b border-border/60 bg-card/40 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {item.near.workstream_name ?? item.near.workstream_id}
              <span className="px-1">↔</span>
              {item.far.workstream_name ?? item.far.workstream_id}
            </p>
            <p className="mt-1 text-sm font-medium leading-snug">{item.summary}</p>
          </div>
          {onClose && (
            <button
              type="button"
              aria-label="Close"
              onClick={onClose}
              className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] font-semibold">
          <span className={cn("rounded-full px-2 py-0.5", style.pill)}>{style.label}</span>
          <span
            className={cn(
              "rounded-full px-1.5 py-0.5",
              labelStyle(item.label).pill,
            )}
          >
            {labelText(item.label, item.sentiment)}
          </span>
        </div>
      </header>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {/* Maker / checker */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <Party label="Maker" person={record?.maker} at={record?.created_at} />
          <Party label="Checker" person={record?.checker} at={record?.checked_at} />
        </div>

        {/* Actions */}
        <section className="rounded-lg border border-border/60 bg-card/40 p-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Take action
          </h3>
          {isLoading ? (
            <Skeleton className="mt-2 h-8 w-full" />
          ) : actions.length === 0 ? (
            <p className="mt-2 text-sm text-muted-foreground">
              This linkage is {record ? statusStyle(record.status).label.toLowerCase() : "closed"} — no further action.
            </p>
          ) : (
            <div className="mt-2 space-y-2">
              <label className="flex items-center gap-2 text-xs">
                <span className="font-semibold text-muted-foreground">Acting as</span>
                <select
                  value={actorId}
                  onChange={(e) => setActorId(e.target.value)}
                  className="rounded-md border border-border/60 bg-background/60 px-2 py-1 text-sm outline-none focus:border-cyan-400/50"
                >
                  {actors.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </select>
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a comment (optional)…"
                rows={2}
                className="w-full resize-none rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-cyan-400/50"
              />
              <div className="flex flex-wrap gap-2">
                {actions.map((a) => (
                  <button
                    key={a.action}
                    type="button"
                    disabled={mutation.isPending || !actorId}
                    onClick={() => mutation.mutate(a.action)}
                    className={cn(
                      "rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors disabled:opacity-50",
                      a.tone === "primary" &&
                        "bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-400/30 hover:bg-cyan-500/25",
                      a.tone === "neutral" && "bg-accent/60 text-foreground/90 hover:bg-accent",
                      a.tone === "danger" &&
                        "bg-red-500/15 text-red-300 ring-1 ring-red-400/30 hover:bg-red-500/25",
                    )}
                  >
                    {a.label}
                  </button>
                ))}
              </div>
              {error && <p className="text-xs font-medium text-red-300">{error}</p>}
            </div>
          )}
        </section>

        {/* Audit trail */}
        <section>
          <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-muted-foreground">
            <History className="h-3.5 w-3.5" /> Audit history
          </h3>
          {isLoading ? (
            <Skeleton className="mt-2 h-16 w-full" />
          ) : !record || record.audit.length === 0 ? (
            <p className="mt-2 text-sm text-muted-foreground">
              No actions yet — this linkage was surfaced by the AI and awaits a maker.
            </p>
          ) : (
            <ol className="mt-2 space-y-2" data-testid="audit-trail">
              {record.audit.map((entry, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                  <div>
                    <span className="font-medium">{entry.actor.name}</span>{" "}
                    <span className="text-muted-foreground">
                      {ACTION_LABELS[entry.action]} · {entry.at.slice(0, 16).replace("T", " ")}
                    </span>
                    {entry.comment && (
                      <p className="text-xs italic text-muted-foreground">
                        “{entry.comment}”
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>

      {/* Footer: jump to the clause-level evidence */}
      <footer className="border-t border-border/60 bg-card/40 p-3">
        <Link
          to={`/workstreams/${CROSS_STORE}/edges/${item.edge_id}/review`}
          className="flex items-center justify-center gap-1.5 rounded-lg bg-accent/60 px-3 py-2 text-sm font-semibold text-foreground/90 transition-colors hover:bg-accent"
        >
          <FileText className="h-4 w-4" /> View clause evidence
        </Link>
      </footer>
    </div>
  );
}

function Party({
  label,
  person,
  at,
}: {
  label: string;
  person: Person | null | undefined;
  at: string | null | undefined;
}) {
  return (
    <div className="rounded-lg border border-border/50 bg-background/40 p-2">
      <p className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        <User className="h-3 w-3" /> {label}
      </p>
      <p className={cn("text-sm font-medium", !person && "italic text-muted-foreground")}>
        {person?.name ?? "Unassigned"}
      </p>
      {at && (
        <p className="text-[10px] text-muted-foreground">{at.slice(0, 10)}</p>
      )}
    </div>
  );
}

export default LinkageReviewPanel;
