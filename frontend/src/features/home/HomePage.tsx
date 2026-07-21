import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Building2, FileText, Layers, Plus } from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchWorkstreams } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { OverlapAlertsCard } from "@/features/home/OverlapAlertsCard";
import type { WorkstreamRole, WorkstreamSummary } from "@/lib/types";

const ROLE_STYLE: Record<
  WorkstreamRole,
  { dot: string; label: string; chip: string; glow: string }
> = {
  own: {
    dot: "bg-cyan-400",
    label: "Drafting",
    chip: "bg-cyan-500/15 text-cyan-300 border border-cyan-400/30",
    glow: "from-cyan-500/40",
  },
  review: {
    dot: "bg-amber-400",
    label: "Reviewing",
    chip: "bg-amber-400/15 text-amber-300 border border-amber-300/30",
    glow: "from-amber-400/40",
  },
  delivered: {
    dot: "bg-emerald-400",
    label: "Delivered",
    chip: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/30",
    glow: "from-emerald-500/40",
  },
};

function roleStyle(role: WorkstreamRole) {
  return ROLE_STYLE[role] ?? ROLE_STYLE.own;
}

function WorkstreamCard({ ws }: { ws: WorkstreamSummary }) {
  const style = roleStyle(ws.role);
  return (
    <Link
      to={`/workstreams/${ws.id}`}
      className="group glass relative flex flex-col overflow-hidden rounded-2xl p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-400/50 hover:shadow-lg hover:shadow-cyan-500/5"
    >
      {/* Corner glow accent, tinted by role */}
      <span
        className={cn(
          "pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-gradient-to-br to-transparent opacity-60 blur-2xl",
          style.glow,
        )}
      />
      <div className="flex items-start justify-between gap-3">
        <span className="flex items-center gap-2">
          <span className={cn("h-2.5 w-2.5 rounded-full", style.dot)} />
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
              style.chip,
            )}
          >
            {style.label}
          </span>
        </span>
        <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-cyan-300" />
      </div>

      <h3 className="mt-4 text-base font-semibold leading-snug">{ws.name}</h3>
      <p className="mt-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
        <FileText className="h-3.5 w-3.5" />
        {ws.deliverable_type ?? "Workstream"}
      </p>
    </Link>
  );
}

function StatTile({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode;
  value: number | string;
  label: string;
}) {
  return (
    <div className="glass flex items-center gap-3 rounded-2xl px-4 py-3">
      <span className="grid h-9 w-9 place-items-center rounded-lg bg-accent/60 text-cyan-300">
        {icon}
      </span>
      <div className="leading-tight">
        <div className="text-lg font-bold">{value}</div>
        <div className="text-[11px] text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

/**
 * The landing dashboard. A hero header, at-a-glance stat tiles, and a card per
 * workstream the drafter belongs to — plus the two primitives that create new
 * work: New Workstream and the cross-workstream Institution Map.
 */
export function HomePage() {
  const { data: workstreams, isPending, isError } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });

  const counts = {
    total: workstreams?.length ?? 0,
    own: workstreams?.filter((w) => w.role === "own").length ?? 0,
    review: workstreams?.filter((w) => w.role === "review").length ?? 0,
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl p-8">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-cyan-300/80">
              Workstream Brain
            </p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight">
              Your workstreams
            </h1>
            <p className="mt-1.5 max-w-xl text-sm text-muted-foreground">
              Each workstream is a knowledge graph of policy documents joined by
              structural edges. Open one to review AI-found linkages before you
              draft.
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              to="/institution-map"
              className="inline-flex items-center gap-2 rounded-lg border border-border/70 bg-card/40 px-3.5 py-2 text-sm font-medium backdrop-blur transition hover:bg-accent"
            >
              <Building2 className="h-4 w-4 text-violet-300" /> Institution map
            </Link>
            <Link
              to="/workstreams/new"
              className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 shadow-sm transition hover:bg-cyan-400"
            >
              <Plus className="h-4 w-4" /> New workstream
            </Link>
          </div>
        </header>

        <div className="mt-6">
          <OverlapAlertsCard />
        </div>

        {!isPending && !isError && workstreams.length > 0 && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatTile
              icon={<Layers className="h-4 w-4" />}
              value={counts.total}
              label="Workstreams"
            />
            <StatTile
              icon={<FileText className="h-4 w-4" />}
              value={counts.own}
              label="Drafting"
            />
            <StatTile
              icon={<Building2 className="h-4 w-4" />}
              value={counts.review}
              label="Reviewing"
            />
          </div>
        )}

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {isPending ? (
            [0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="glass flex flex-col gap-3 rounded-2xl p-5">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ))
          ) : isError ? (
            <p className="col-span-full text-sm text-muted-foreground">
              Could not load your workstreams.
            </p>
          ) : workstreams.length === 0 ? (
            <p className="col-span-full text-sm text-muted-foreground">
              No workstreams yet. Create one to get started.
            </p>
          ) : (
            workstreams.map((ws) => <WorkstreamCard key={ws.id} ws={ws} />)
          )}
        </div>
      </div>
    </div>
  );
}

export default HomePage;
