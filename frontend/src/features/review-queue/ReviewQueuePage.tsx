import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ClipboardCheck, Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchReviewQueue, fetchReviewers } from "@/lib/api";
import type { LinkageStatus, ReviewQueueItem } from "@/lib/types";
import { labelStyle } from "@/lib/labels";
import { Skeleton } from "@/components/ui/skeleton";
import { STATUS_ORDER, statusStyle } from "./reviewStatus";
import { LinkageReviewPanel } from "./LinkageReviewPanel";

const OPEN_STATUSES: LinkageStatus[] = [
  "ai_detected",
  "maker_review",
  "submitted_for_check",
  "checker_review",
  "changes_requested",
];

/** Review Queue — the maker-checker backlog of cross-workstream linkages. Every
 *  AI-detected overlap that still needs a human, with a real audit trail behind
 *  each. The point of the early-warning system: clear these before FPWG. */
export function ReviewQueuePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["review-queue"],
    queryFn: fetchReviewQueue,
  });
  const { data: actors = [] } = useQuery({
    queryKey: ["reviewers"],
    queryFn: fetchReviewers,
  });

  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<LinkageStatus | "open" | "all">("open");
  const [selected, setSelected] = useState<string | null>(null);

  const items = data?.items ?? [];
  const counts = data?.counts_by_status;

  const openCount = OPEN_STATUSES.reduce((n, s) => n + (counts?.[s] ?? 0), 0);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items
      .filter((it) => {
        if (statusFilter === "all") return true;
        if (statusFilter === "open") return OPEN_STATUSES.includes(it.status);
        return it.status === statusFilter;
      })
      .filter((it) => {
        if (!q) return true;
        return [it.summary, it.near.workstream_name, it.far.workstream_name]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(q);
      });
  }, [items, statusFilter, query]);

  const activeKey = selected ?? (filtered[0] ? keyOf(filtered[0]) : null);
  const activeItem = filtered.find((it) => keyOf(it) === activeKey) ?? filtered[0] ?? null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-border/60 bg-card/30 px-6 py-4 backdrop-blur">
        <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-cyan-300/80">
          <ClipboardCheck className="h-3.5 w-3.5" /> Review Queue
        </p>
        <h1 className="mt-1 text-lg font-bold">
          Maker-checker review of cross-workstream linkages
        </h1>
        <p className="mt-0.5 max-w-2xl text-sm text-muted-foreground">
          Every AI-detected overlap runs through a maker and an independent
          checker before it is accepted — a full audit trail, cleared before a
          workstream reaches FPWG.
        </p>

        {/* Status metrics */}
        <div className="mt-4 flex flex-wrap gap-2">
          <MetricPill label="Open" value={openCount} tone="warn" loading={isLoading} />
          {STATUS_ORDER.map((s) => (
            <MetricPill
              key={s}
              label={statusStyle(s).label}
              value={counts?.[s] ?? 0}
              dot={statusStyle(s).dot}
              loading={isLoading}
            />
          ))}
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        {/* Queue list */}
        <div className="flex min-h-0 flex-col border-r border-border/60">
          <div className="flex flex-wrap items-center gap-2 border-b border-border/60 px-4 py-2.5">
            <div className="relative min-w-[160px] flex-1">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search linkages…"
                className="w-full rounded-lg border border-border/60 bg-background/60 py-1.5 pl-8 pr-3 text-sm outline-none focus:border-cyan-400/50"
              />
            </div>
            <div className="flex flex-wrap gap-1">
              {(["open", "all", ...STATUS_ORDER] as const).map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setStatusFilter(f)}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-xs font-medium capitalize transition-colors",
                    statusFilter === f
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:bg-accent/50",
                  )}
                >
                  {f === "open" || f === "all" ? f : statusStyle(f).label}
                </button>
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-3">
            {isLoading ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <div className="grid h-full place-items-center p-8 text-center text-sm text-muted-foreground">
                No linkages match this filter.
              </div>
            ) : (
              <ul className="space-y-2">
                {filtered.map((it) => (
                  <li key={keyOf(it)}>
                    <QueueRow
                      item={it}
                      active={keyOf(it) === activeKey}
                      onClick={() => setSelected(keyOf(it))}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="hidden min-h-0 lg:block">
          {activeItem ? (
            <LinkageReviewPanel
              key={keyOf(activeItem)}
              item={activeItem}
              actors={actors}
            />
          ) : (
            <div className="grid h-full place-items-center p-8 text-center text-sm text-muted-foreground">
              Select a linkage to review it.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function keyOf(item: ReviewQueueItem): string {
  return `${item.edge_id}::${item.finding_id}`;
}

function MetricPill({
  label,
  value,
  dot,
  tone,
  loading,
}: {
  label: string;
  value: number;
  dot?: string;
  tone?: "warn";
  loading?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold",
        tone === "warn"
          ? "border-amber-300/30 bg-amber-400/10 text-amber-300"
          : "border-border/60 bg-card/40 text-foreground/80",
      )}
    >
      {dot && <span className={cn("h-2 w-2 rounded-full", dot)} />}
      {label}
      <span className="tabular-nums">{loading ? "·" : value}</span>
    </span>
  );
}

function QueueRow({
  item,
  active,
  onClick,
}: {
  item: ReviewQueueItem;
  active: boolean;
  onClick: () => void;
}) {
  const style = statusStyle(item.status);
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="queue-row"
      className={cn(
        "w-full rounded-xl border p-3 text-left transition-colors",
        active
          ? "border-cyan-400/50 bg-accent/50"
          : "border-border/60 bg-card/40 hover:border-border hover:bg-accent/30",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs font-semibold text-muted-foreground">
          <span>{item.near.workstream_name ?? item.near.workstream_id}</span>
          <span className="px-1">↔</span>
          <span>{item.far.workstream_name ?? item.far.workstream_id}</span>
        </span>
        <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold", style.pill)}>
          {style.label}
        </span>
      </div>
      <p className="mt-1 line-clamp-2 text-sm">{item.summary}</p>
      <div className="mt-1.5 flex items-center gap-2">
        <span className={cn("rounded-full px-1.5 py-0.5 text-[10px] font-semibold", labelStyle(item.label).pill)}>
          {item.label}
        </span>
        {item.maker && (
          <span className="text-[10px] text-muted-foreground">maker {item.maker.name}</span>
        )}
        {item.checker && (
          <span className="text-[10px] text-muted-foreground">· checker {item.checker.name}</span>
        )}
      </div>
    </button>
  );
}

export default ReviewQueuePage;
