import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowLeftRight, ScrollText } from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchGraph, fetchNodeDetail } from "@/lib/api";
import type { NodeDetail } from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { asList, conceptsOf } from "./intel";

/** A compact regulatory profile for a workstream — policy owner, applicability,
 *  legal basis, ISMP classification, key topics — read from its primary
 *  document's concept metadata. Surfaced in the graph rail so the intelligence
 *  profile lives beside the drafting canvas, and reusable elsewhere. */
export function RegulatoryProfileCard({ workstreamId }: { workstreamId: string }) {
  const { data: graph } = useQuery({
    queryKey: ["workstream", workstreamId, "graph"],
    queryFn: () => fetchGraph(workstreamId),
    enabled: Boolean(workstreamId),
  });
  const taskId = graph?.primary_task_id;
  const { data: detail } = useQuery<NodeDetail>({
    queryKey: ["node-detail", workstreamId, taskId],
    queryFn: () => fetchNodeDetail(workstreamId, taskId as string),
    enabled: Boolean(workstreamId && taskId),
  });

  const concepts = conceptsOf(detail?.concepts);

  return (
    <section className="rounded-xl border border-border/60 bg-card/40 p-3">
      <div className="flex items-center justify-between gap-2">
        <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-muted-foreground">
          <ScrollText className="h-3.5 w-3.5" /> Regulatory profile
        </h3>
        <Link
          to={`/intelligence/compare?a=${workstreamId}`}
          className="flex items-center gap-1 text-[11px] font-semibold text-cyan-300 hover:underline"
        >
          <ArrowLeftRight className="h-3 w-3" /> Compare
        </Link>
      </div>

      {!detail ? (
        <div className="mt-2 space-y-1.5">
          <Skeleton className="h-3.5 w-2/3" />
          <Skeleton className="h-3.5 w-1/2" />
        </div>
      ) : (
        <dl className="mt-2 space-y-1.5 text-xs">
          <Row label="Owner" value={concepts?.policy_owner} />
          <Row label="Applicability" value={concepts?.applicability} />
          <ChipRow label="Legal basis" values={asList(concepts?.legal_basis)} fallback={detail.pursuant_to} />
          <Row
            label="ISMP"
            value={concepts?.ismp_classification ?? detail.ismp_classification}
            pendingNote="pending RH form"
          />
          <ChipRow label="Topics" values={asList(concepts?.keywords)} />
        </dl>
      )}
    </section>
  );
}

function Row({
  label,
  value,
  pendingNote,
}: {
  label: string;
  value?: string | null;
  pendingNote?: string;
}) {
  return (
    <div className="grid grid-cols-[72px_1fr] gap-1.5">
      <dt className="font-semibold text-muted-foreground">{label}</dt>
      <dd className={cn(!value && "italic text-muted-foreground")}>
        {value || (pendingNote ? `— ${pendingNote}` : "—")}
      </dd>
    </div>
  );
}

function ChipRow({
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
    <div className="grid grid-cols-[72px_1fr] gap-1.5">
      <dt className="font-semibold text-muted-foreground">{label}</dt>
      <dd className="flex flex-wrap gap-1">
        {items.length === 0 ? (
          <span className="italic text-muted-foreground">—</span>
        ) : (
          items.map((v) => (
            <span key={v} className="rounded-full bg-accent/60 px-1.5 py-0.5 font-medium text-foreground/90">
              {v}
            </span>
          ))
        )}
      </dd>
    </div>
  );
}

export default RegulatoryProfileCard;
