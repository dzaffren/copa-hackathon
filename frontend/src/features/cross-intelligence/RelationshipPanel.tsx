import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeftRight,
  Check,
  FileText,
  Scale,
  Tag,
  User,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchCrossLinkDetail } from "@/lib/api";
import { CROSS_STORE, type ReviewFinding } from "@/lib/types";
import { labelStyle, labelText } from "@/lib/labels";
import { Skeleton } from "@/components/ui/skeleton";
import { classStyle, riskStyle } from "./intel";

/** The relationship-detail panel: why the overlap was flagged, what the two
 *  documents share, the verbatim clause evidence on every linkage, and the
 *  actions a drafter can take. Answers the product's seven questions for one
 *  relationship (what / why / evidence / who / action). */
export function RelationshipPanel({
  edgeId,
  onClose,
}: {
  edgeId: string;
  onClose?: () => void;
}) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["cross-link-detail", edgeId],
    queryFn: () => fetchCrossLinkDetail(edgeId),
  });

  if (isLoading) {
    return (
      <div className="space-y-3 p-5">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div className="p-5 text-sm text-muted-foreground">
        Could not load this relationship.
      </div>
    );
  }

  const cls = classStyle(data.classification);
  const risk = riskStyle(data.risk_level);
  const shared = data.shared_attributes;
  const comparePath =
    data.near.workstream_id && data.far.workstream_id
      ? `/intelligence/compare?a=${data.near.workstream_id}&b=${data.far.workstream_id}`
      : null;

  return (
    <div className="flex h-full min-h-0 flex-col" data-testid="relationship-panel">
      {/* Header */}
      <header className="border-b border-border/60 bg-card/40 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-rose-300/80">
              Potential overlap detected
            </p>
            <h2 className="mt-1 text-base font-bold leading-snug">
              {data.near.workstream_name ?? data.near.workstream_id}
              <span className="px-1.5 text-muted-foreground">↔</span>
              {data.far.workstream_name ?? data.far.workstream_id}
            </h2>
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {data.near.title} ↔ {data.far.title}
            </p>
          </div>
          {onClose && (
            <button
              type="button"
              aria-label="Close relationship"
              onClick={onClose}
              className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] font-semibold">
          <span className={cn("rounded-full px-2 py-0.5", cls.pill)}>{cls.label}</span>
          <span className={cn("rounded-full px-2 py-0.5", risk.pill)}>{risk.label}</span>
          <span className="rounded-full border border-border/60 px-2 py-0.5 text-muted-foreground">
            {data.findings.length} linkages
          </span>
          {data.detected_at && (
            <span className="text-muted-foreground">Detected {data.detected_at}</span>
          )}
        </div>
      </header>

      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-5">
        {/* Why detected */}
        <section>
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Why this was detected
          </h3>
          <ul className="mt-2 space-y-1.5">
            {data.reasons.length === 0 && (
              <li className="text-sm text-muted-foreground">
                No shared attributes derivable — flagged on clause linkages alone.
              </li>
            )}
            {data.reasons.map((reason) => (
              <li key={reason} className="flex items-start gap-2 text-sm">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Shared attributes */}
        <section className="grid gap-2">
          <SharedRow icon={<Scale className="h-3.5 w-3.5" />} label="Legal basis" values={shared.legal_basis} />
          <SharedRow icon={<User className="h-3.5 w-3.5" />} label="Applicability" values={shared.applicability} />
          <SharedRow icon={<Tag className="h-3.5 w-3.5" />} label="Shared topics" values={shared.keywords} />
          {shared.policy_owner && (
            <SharedRow icon={<User className="h-3.5 w-3.5" />} label="Policy owner" values={[shared.policy_owner]} />
          )}
        </section>

        {/* Evidence */}
        <section>
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Clause evidence
          </h3>
          <div className="mt-2 space-y-3">
            {data.findings.map((f) => (
              <EvidenceCard key={f.id} finding={f} nearTitle={data.near.title} farTitle={data.far.title} />
            ))}
          </div>
        </section>
      </div>

      {/* Actions */}
      <footer className="grid grid-cols-2 gap-2 border-t border-border/60 bg-card/40 p-3">
        <Link
          to={`/workstreams/${CROSS_STORE}/edges/${data.id}/review`}
          className="flex items-center justify-center gap-1.5 rounded-lg bg-cyan-500/15 px-3 py-2 text-sm font-semibold text-cyan-300 ring-1 ring-cyan-400/30 transition-colors hover:bg-cyan-500/25"
        >
          <FileText className="h-4 w-4" /> View clause linkage
        </Link>
        {comparePath ? (
          <Link
            to={comparePath}
            className="flex items-center justify-center gap-1.5 rounded-lg bg-accent/60 px-3 py-2 text-sm font-semibold text-foreground/90 transition-colors hover:bg-accent"
          >
            <ArrowLeftRight className="h-4 w-4" /> Compare workstreams
          </Link>
        ) : (
          <span className="rounded-lg bg-accent/30 px-3 py-2 text-center text-sm text-muted-foreground">
            Compare unavailable
          </span>
        )}
        <p className="col-span-2 text-center text-[11px] text-muted-foreground">
          Create review task · Assign owner · Mark reviewed arrive with the Review
          Queue (Phase 3).
        </p>
      </footer>
    </div>
  );
}

function SharedRow({
  icon,
  label,
  values,
}: {
  icon: ReactNode;
  label: string;
  values: string[];
}) {
  if (values.length === 0) return null;
  return (
    <div className="flex items-start gap-2 text-sm">
      <span className="mt-0.5 flex items-center gap-1 text-xs font-semibold text-muted-foreground">
        {icon}
        {label}
      </span>
      <span className="flex flex-1 flex-wrap gap-1">
        {values.map((v) => (
          <span
            key={v}
            className="rounded-full bg-accent/60 px-2 py-0.5 text-xs font-medium text-foreground/90"
          >
            {v}
          </span>
        ))}
      </span>
    </div>
  );
}

const NO_CLAUSE = "No matching clause found";

function EvidenceCard({
  finding,
  nearTitle,
  farTitle,
}: {
  finding: ReviewFinding;
  nearTitle: string | null;
  farTitle: string | null;
}) {
  const style = labelStyle(finding.label);
  return (
    <div className={cn("rounded-lg border border-border/60 border-l-2 bg-card/40 p-3", style.accent)}>
      <div className="flex items-center justify-between gap-2">
        <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", style.pill)}>
          {labelText(finding.label, finding.sentiment)}
        </span>
      </div>
      <p className="mt-1.5 text-sm font-medium leading-snug">{finding.summary}</p>
      {finding.scope_note && (
        <p className="mt-1 text-xs italic text-muted-foreground">{finding.scope_note}</p>
      )}
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <ClauseColumn title={nearTitle} clauses={finding.source_clauses} />
        <ClauseColumn title={farTitle} clauses={finding.target_clauses} />
      </div>
    </div>
  );
}

function ClauseColumn({
  title,
  clauses,
}: {
  title: string | null;
  clauses: { clause_number: string; text: string }[];
}) {
  return (
    <div className="rounded-md bg-background/40 p-2">
      <p className="truncate text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {title ?? "—"}
      </p>
      {clauses.length === 0 ? (
        <p className="mt-1 text-xs italic text-muted-foreground">{NO_CLAUSE}</p>
      ) : (
        <ul className="mt-1 space-y-1.5">
          {clauses.map((c, i) => (
            <li key={`${c.clause_number}-${i}`} className="text-xs">
              <span className="font-mono font-semibold text-foreground/80">
                {c.clause_number}
              </span>
              <span
                className={cn(
                  "mt-0.5 block leading-snug",
                  c.text === NO_CLAUSE ? "italic text-muted-foreground" : "text-foreground/70",
                )}
              >
                {c.text}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default RelationshipPanel;
