import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQueries, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowLeftRight } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  fetchAllCrossLinks,
  fetchGraph,
  fetchNodeDetail,
  fetchWorkstreams,
} from "@/lib/api";
import { CROSS_STORE, type NodeDetail, type WorkstreamSummary } from "@/lib/types";
import { labelStyle } from "@/lib/labels";
import { LABEL_ORDER } from "@/lib/labels";
import { Skeleton } from "@/components/ui/skeleton";
import { asList, classStyle, conceptsOf } from "./intel";

/** Side-by-side comparison of two workstreams: their regulatory profiles plus
 *  the detected relationships between them, grouped by semantic label. Answers
 *  "what overlaps, why, is it a real conflict, who owns it, what to do". */
export function CompareWorkstreamsPage() {
  const [params, setParams] = useSearchParams();
  const { data: workstreams = [] } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });

  // Default to the flagship pair (BCM vs Resolution & Recovery) when present.
  const fallbackA = pick(workstreams, ["bcm", "opres-v2"]);
  const fallbackB = pick(workstreams, ["resolution-recovery", "open-finance-ed"]);
  const aId = params.get("a") ?? fallbackA;
  const bId = params.get("b") ?? fallbackB;

  const setSide = (side: "a" | "b", id: string) => {
    const next = new URLSearchParams(params);
    next.set(side, id);
    if (!next.get(side === "a" ? "b" : "a")) {
      next.set(side === "a" ? "b" : "a", side === "a" ? bId ?? "" : aId ?? "");
    }
    setParams(next);
  };

  const { data: allLinks = [] } = useQuery({
    queryKey: ["cross-links", "all"],
    queryFn: fetchAllCrossLinks,
  });
  const link = useMemo(
    () =>
      allLinks.find(
        (l) =>
          (l.near.workstream_id === aId && l.far.workstream_id === bId) ||
          (l.near.workstream_id === bId && l.far.workstream_id === aId),
      ),
    [allLinks, aId, bId],
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-border/60 bg-card/30 px-6 py-4 backdrop-blur">
        <Link
          to="/intelligence"
          className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Cross-Workstream Intelligence
        </Link>
        <h1 className="mt-1 flex items-center gap-2 text-lg font-bold">
          <ArrowLeftRight className="h-5 w-5 text-cyan-300" /> Compare workstreams
        </h1>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <SidePicker
            label="A"
            value={aId}
            workstreams={workstreams}
            exclude={bId}
            onChange={(id) => setSide("a", id)}
          />
          <span className="text-muted-foreground">vs</span>
          <SidePicker
            label="B"
            value={bId}
            workstreams={workstreams}
            exclude={aId}
            onChange={(id) => setSide("b", id)}
          />
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto p-6">
        <div className="grid gap-4 lg:grid-cols-2">
          <ProfileColumn workstreamId={aId} workstreams={workstreams} accent="cyan" />
          <ProfileColumn workstreamId={bId} workstreams={workstreams} accent="violet" />
        </div>

        {/* Detected relationships */}
        <section className="mt-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Detected relationships
          </h2>
          {!link ? (
            <p className="mt-2 text-sm text-muted-foreground">
              No cross-workstream linkages detected between these two workstreams
              yet.
            </p>
          ) : (
            <div className="glass mt-2 rounded-xl p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[11px] font-semibold",
                    classStyle(link.classification).pill,
                  )}
                >
                  {classStyle(link.classification).label}
                </span>
                <span className="text-sm text-muted-foreground">
                  {link.findings_count} linkages across the five-label taxonomy
                </span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5">
                {LABEL_ORDER.map((label) => {
                  const count = link.labels[label] ?? 0;
                  return (
                    <div
                      key={label}
                      className={cn(
                        "rounded-lg border border-border/50 p-2 text-center",
                        count === 0 && "opacity-40",
                      )}
                    >
                      <p className="text-lg font-bold tabular-nums">{count}</p>
                      <span
                        className={cn(
                          "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                          labelStyle(label).pill,
                        )}
                      >
                        {label}
                      </span>
                    </div>
                  );
                })}
              </div>
              <Link
                to={`/workstreams/${CROSS_STORE}/edges/${link.id}/review`}
                className="mt-3 inline-block text-sm font-semibold text-cyan-300 hover:underline"
              >
                View clause-level evidence &amp; review →
              </Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function pick(workstreams: WorkstreamSummary[], preferred: string[]): string {
  for (const id of preferred) {
    if (workstreams.some((w) => w.id === id)) return id;
  }
  return workstreams[0]?.id ?? "";
}

function SidePicker({
  label,
  value,
  workstreams,
  exclude,
  onChange,
}: {
  label: string;
  value: string;
  workstreams: WorkstreamSummary[];
  exclude: string;
  onChange: (id: string) => void;
}) {
  return (
    <label className="flex items-center gap-1.5 text-sm">
      <span className="text-[10px] font-bold uppercase text-muted-foreground">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-cyan-400/50"
      >
        {workstreams
          .filter((w) => w.id !== exclude)
          .map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
      </select>
    </label>
  );
}

function ProfileColumn({
  workstreamId,
  workstreams,
  accent,
}: {
  workstreamId: string;
  workstreams: WorkstreamSummary[];
  accent: "cyan" | "violet";
}) {
  const meta = workstreams.find((w) => w.id === workstreamId);
  const { data: graph } = useQuery({
    queryKey: ["workstream", workstreamId, "graph"],
    queryFn: () => fetchGraph(workstreamId),
    enabled: Boolean(workstreamId),
  });
  const taskId = graph?.primary_task_id;
  const [detailQuery] = useQueries({
    queries: [
      {
        queryKey: ["node-detail", workstreamId, taskId],
        queryFn: () => fetchNodeDetail(workstreamId, taskId as string),
        enabled: Boolean(workstreamId && taskId),
      },
    ],
  });
  const detail = detailQuery.data as NodeDetail | undefined;
  const concepts = conceptsOf(detail?.concepts);
  const accentBar = accent === "cyan" ? "border-t-cyan-400/60" : "border-t-violet-400/60";

  return (
    <div className={cn("glass rounded-xl border-t-2 p-4", accentBar)}>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {meta ? roleLabel(meta) : "Workstream"}
      </p>
      <h3 className="text-base font-bold">{meta?.name ?? workstreamId}</h3>
      <p className="truncate text-xs text-muted-foreground">
        {detail?.title ?? graph?.primary_task_id ?? "—"}
      </p>

      {!detail ? (
        <div className="mt-3 space-y-2">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ) : (
        <dl className="mt-3 space-y-2 text-sm">
          <Field label="Policy owner" value={concepts?.policy_owner} />
          <Field label="Applicability" value={concepts?.applicability} />
          <ListField label="Legal basis" values={asList(concepts?.legal_basis) } fallback={detail.pursuant_to} />
          <Field
            label="ISMP classification"
            value={concepts?.ismp_classification}
            pendingNote="pending RH publication form"
          />
          <ListField label="Key topics" values={asList(concepts?.keywords)} />
          <Field label="Key requirement" value={concepts?.requirement} />
          <Field label="Empowerment" value={concepts?.empowerment_framework} />
          <Field label="Issued" value={concepts?.issuance_date} />
        </dl>
      )}
    </div>
  );
}

function roleLabel(w: WorkstreamSummary): string {
  const map: Record<string, string> = {
    own: "Drafting",
    review: "Reviewing",
    delivered: "Delivered",
  };
  return `${w.deliverable_type} · ${map[w.role] ?? w.role}`;
}

function Field({
  label,
  value,
  pendingNote,
}: {
  label: string;
  value?: string | null;
  pendingNote?: string;
}) {
  return (
    <div className="grid grid-cols-[110px_1fr] gap-2">
      <dt className="text-xs font-semibold text-muted-foreground">{label}</dt>
      <dd className={cn("text-sm", !value && "italic text-muted-foreground")}>
        {value || (pendingNote ? `Not available — ${pendingNote}` : "Not available")}
      </dd>
    </div>
  );
}

function ListField({
  label,
  values,
  fallback,
}: {
  label: string;
  values: string[];
  fallback?: string | null;
}) {
  const items = values.length > 0 ? values : fallback ? [fallback] : [];
  return (
    <div className="grid grid-cols-[110px_1fr] gap-2">
      <dt className="text-xs font-semibold text-muted-foreground">{label}</dt>
      <dd className="flex flex-wrap gap-1">
        {items.length === 0 ? (
          <span className="text-sm italic text-muted-foreground">Not available</span>
        ) : (
          items.map((v) => (
            <span
              key={v}
              className="rounded-full bg-accent/60 px-2 py-0.5 text-xs font-medium text-foreground/90"
            >
              {v}
            </span>
          ))
        )}
      </dd>
    </div>
  );
}

export default CompareWorkstreamsPage;
