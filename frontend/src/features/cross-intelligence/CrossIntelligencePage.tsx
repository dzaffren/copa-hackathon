import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Map, Radar, Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchAllCrossLinks, fetchWorkstreams } from "@/lib/api";
import type { CrossLink, RelationshipClassification } from "@/lib/types";
import { labelStyle } from "@/lib/labels";
import { Skeleton } from "@/components/ui/skeleton";
import {
  classStyle,
  intelMetrics,
  riskStyle,
  unreviewedCount,
} from "./intel";
import { RelationshipPanel } from "./RelationshipPanel";

const CLASS_FILTERS: { value: RelationshipClassification | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "conflict", label: "Conflicts" },
  { value: "divergent", label: "Divergent" },
  { value: "overlap", label: "Overlap" },
  { value: "aligned", label: "Aligned" },
];

/** Cross-Workstream Intelligence — the early-warning surface. Which other
 *  active workstreams may overlap with a given one, and why, with the evidence
 *  and actions to resolve it before FPWG. Primary product area. */
export function CrossIntelligencePage() {
  const { data: links = [], isLoading } = useQuery({
    queryKey: ["cross-links", "all"],
    queryFn: fetchAllCrossLinks,
  });
  const { data: workstreams = [] } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });

  const [query, setQuery] = useState("");
  const [classFilter, setClassFilter] = useState<RelationshipClassification | "all">("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const metrics = useMemo(
    () => intelMetrics(links, workstreams.length),
    [links, workstreams.length],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return links
      .filter((l) => classFilter === "all" || l.classification === classFilter)
      .filter((l) => {
        if (!q) return true;
        const hay = [
          l.near.workstream_name,
          l.far.workstream_name,
          l.near.title,
          l.far.title,
          ...l.reasons,
          ...l.shared_attributes.keywords,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .sort((a, b) => riskRank(b) - riskRank(a));
  }, [links, query, classFilter]);

  // Default the detail panel to the highest-risk relationship once loaded.
  const activeId = selectedId ?? filtered[0]?.id ?? null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* Header */}
      <header className="border-b border-border/60 bg-card/30 px-6 py-4 backdrop-blur">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-cyan-300/80">
              <Radar className="h-3.5 w-3.5" /> Cross-Workstream Intelligence
            </p>
            <h1 className="mt-1 text-lg font-bold">
              Overlap, duplication &amp; conflict across active policy workstreams
            </h1>
            <p className="mt-0.5 max-w-2xl text-sm text-muted-foreground">
              An early-warning system: the moment two teams draft policies that
              touch the same requirements, entities or legal basis, it surfaces
              here — with the evidence to resolve it before FPWG, not after.
            </p>
          </div>
          <Link
            to="/institution-map"
            className="flex shrink-0 items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5 text-xs font-semibold text-muted-foreground transition-colors hover:border-violet-400/50 hover:text-violet-200"
          >
            <Map className="h-4 w-4" /> Map view
          </Link>
        </div>

        {/* Metrics */}
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
          <Metric label="Active workstreams" value={metrics.activeWorkstreams} loading={isLoading} />
          <Metric label="Potential overlaps" value={metrics.potentialOverlaps} loading={isLoading} />
          <Metric
            label="High-risk conflicts"
            value={metrics.highRiskConflicts}
            tone={metrics.highRiskConflicts > 0 ? "danger" : "neutral"}
            loading={isLoading}
          />
          <Metric
            label="Unreviewed linkages"
            value={metrics.unreviewedLinkages}
            tone={metrics.unreviewedLinkages > 0 ? "warn" : "neutral"}
            loading={isLoading}
          />
          <Metric
            label="Recently detected"
            value={metrics.recentlyDetected}
            hint={metrics.latestDetectedAt ?? undefined}
            loading={isLoading}
          />
        </div>
      </header>

      {/* Body: relationship list + detail panel */}
      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        {/* List column */}
        <div className="flex min-h-0 flex-col border-r border-border/60">
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2 border-b border-border/60 px-4 py-2.5">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search workstreams, topics, reasons…"
                className="w-full rounded-lg border border-border/60 bg-background/60 py-1.5 pl-8 pr-3 text-sm outline-none focus:border-cyan-400/50"
              />
            </div>
            <div className="flex gap-1">
              {CLASS_FILTERS.map((f) => (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => setClassFilter(f.value)}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
                    classFilter === f.value
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:bg-accent/50",
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-3">
            {isLoading ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <EmptyState hasLinks={links.length > 0} />
            ) : (
              <ul className="space-y-2">
                {filtered.map((link) => (
                  <li key={link.id}>
                    <RelationshipCard
                      link={link}
                      active={link.id === activeId}
                      onClick={() => setSelectedId(link.id)}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Detail column */}
        <div className="hidden min-h-0 lg:block">
          {activeId ? (
            <RelationshipPanel key={activeId} edgeId={activeId} />
          ) : (
            <div className="grid h-full place-items-center p-8 text-center text-sm text-muted-foreground">
              Select a relationship to see why it was detected and the evidence
              behind it.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function riskRank(link: CrossLink): number {
  const byRisk = { high: 300, medium: 200, low: 100 }[link.risk_level] ?? 0;
  return byRisk + unreviewedCount(link);
}

function Metric({
  label,
  value,
  hint,
  tone = "neutral",
  loading,
}: {
  label: string;
  value: number;
  hint?: string;
  tone?: "neutral" | "warn" | "danger";
  loading?: boolean;
}) {
  const toneClass =
    tone === "danger"
      ? "text-red-300"
      : tone === "warn"
        ? "text-amber-300"
        : "text-foreground";
  return (
    <div className="glass rounded-xl px-3 py-2.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      {loading ? (
        <Skeleton className="mt-1 h-7 w-10" />
      ) : (
        <p className={cn("mt-0.5 text-2xl font-bold tabular-nums", toneClass)}>{value}</p>
      )}
      {hint && <p className="text-[10px] text-muted-foreground">latest {hint}</p>}
    </div>
  );
}

function RelationshipCard({
  link,
  active,
  onClick,
}: {
  link: CrossLink;
  active: boolean;
  onClick: () => void;
}) {
  const cls = classStyle(link.classification);
  const risk = riskStyle(link.risk_level);
  const unreviewed = unreviewedCount(link);
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="relationship-card"
      className={cn(
        "w-full rounded-xl border p-3 text-left transition-colors",
        active
          ? "border-cyan-400/50 bg-accent/50"
          : "border-border/60 bg-card/40 hover:border-border hover:bg-accent/30",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 text-sm font-semibold">
          <span className={cn("h-2 w-2 shrink-0 rounded-full", cls.dot)} />
          <span className="truncate">
            {link.near.workstream_name ?? link.near.workstream_id}
          </span>
          <span className="text-muted-foreground">↔</span>
          <span className="truncate">
            {link.far.workstream_name ?? link.far.workstream_id}
          </span>
        </span>
        <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold", risk.pill)}>
          {risk.label}
        </span>
      </div>

      {link.reasons[0] && (
        <p className="mt-1.5 line-clamp-2 text-xs text-muted-foreground">
          {link.reasons.slice(0, 2).join(" · ")}
        </p>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-1">
        <span className={cn("rounded-full px-1.5 py-0.5 text-[10px] font-semibold", cls.pill)}>
          {cls.label}
        </span>
        {(Object.entries(link.labels) as [keyof typeof link.labels, number][]).map(
          ([label, count]) => (
            <span
              key={label as string}
              className={cn(
                "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                labelStyle(label as never).pill,
              )}
            >
              {count} {label}
            </span>
          ),
        )}
        {unreviewed > 0 && (
          <span className="ml-auto text-[10px] font-medium text-amber-300">
            {unreviewed} unreviewed
          </span>
        )}
      </div>
    </button>
  );
}

function EmptyState({ hasLinks }: { hasLinks: boolean }) {
  return (
    <div className="grid h-full place-items-center p-8 text-center">
      <div className="max-w-xs">
        <Radar className="mx-auto h-8 w-8 text-muted-foreground/60" />
        <p className="mt-3 text-sm font-medium">
          {hasLinks ? "No relationships match your filter" : "No overlaps detected"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {hasLinks
            ? "Clear the search or class filter to see every detected relationship."
            : "As active workstreams accumulate overlapping requirements, detected relationships appear here."}
        </p>
      </div>
    </div>
  );
}

export default CrossIntelligencePage;
