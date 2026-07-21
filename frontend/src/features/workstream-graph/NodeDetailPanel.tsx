import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  ChevronDown,
  ExternalLink,
  FileText,
  Loader2,
  ShieldCheck,
  Scale,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fetchNodeDetail } from "@/lib/api";
import type { ConceptsAvailable } from "@/lib/types";
import { nodeStyle } from "./legend";

function conceptsAvailable(
  concepts: ConceptsAvailable | { status: string; message: string },
): concepts is ConceptsAvailable {
  return concepts.status === "available";
}

/** Normalise a concept value to a display list (a list stays a list, a scalar
 *  becomes one item, null/undefined becomes empty). Lets `keywords` and
 *  `legal_basis` render as chips regardless of older scalar side-files. */
function asList(value: string[] | string | null | undefined): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

// Display order + labels for the regulatory-profile concept fields. `legal_basis`
// and `ismp_classification` were added for Cross-Workstream Intelligence — a
// shared Act or classification is a strong overlap signal.
const CONCEPT_FIELD_ORDER: [keyof Omit<ConceptsAvailable, "status">, string][] = [
  ["policy_owner", "Policy owner"],
  ["applicability", "Applicability"],
  ["empowerment_framework", "Empowerment framework"],
  ["requirement", "Requirement"],
  ["issuance_date", "Issuance date"],
  ["effective_date", "Effective date"],
  ["keywords", "Keywords"],
  ["legal_basis", "Legal basis"],
  ["ismp_classification", "ISMP classification"],
];

// Fields whose values render as chips rather than a single line.
const CHIP_FIELDS = new Set(["keywords", "legal_basis"]);

const ISMP_PENDING = "Pending — RH publication form";

interface NodeDetailPanelProps {
  workstreamId: string;
  nodeId: string;
  /** Refocus the panel on a neighbour when its chip is clicked. */
  onSelectNode: (id: string) => void;
  onClose?: () => void;
}

function openSource(url: string | null) {
  if (!url) return;
  // Only follow http(s) sources — guards against a stored `javascript:`/`data:`
  // URL on a user-created node turning "Open source" into an XSS vector.
  try {
    const parsed = new URL(url, window.location.origin);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      window.open(parsed.href, "_blank", "noopener,noreferrer");
    }
  } catch {
    // malformed URL — do nothing
  }
}

function PanelHeader({ onClose }: { onClose?: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 px-4 py-2.5">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        Node detail
      </span>
      {onClose && (
        <button
          type="button"
          aria-label="Close panel"
          onClick={onClose}
          className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

/**
 * Right-panel detail for a selected node: type + sub-badge, description,
 * governance badges (ISMP classification / "pursuant to" — shown only when the
 * node actually carries them, never invented), the clickable first-order
 * neighbour chips, recent activity, a collapsed Concepts disclosure, and an
 * Open task / Open source action keyed by node type.
 */
export function NodeDetailPanel({
  workstreamId,
  nodeId,
  onSelectNode,
  onClose,
}: NodeDetailPanelProps) {
  const navigate = useNavigate();
  const [conceptsOpen, setConceptsOpen] = useState(false);
  const query = useQuery({
    queryKey: ["node", workstreamId, nodeId],
    queryFn: () => fetchNodeDetail(workstreamId, nodeId),
  });

  if (query.isPending) {
    return (
      <div className="flex h-full flex-col">
        <PanelHeader onClose={onClose} />
        <div
          role="status"
          className="flex items-center gap-2 p-6 text-sm text-muted-foreground"
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading node…
        </div>
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="flex h-full flex-col">
        <PanelHeader onClose={onClose} />
        <div className="p-6 text-sm text-muted-foreground">
          Could not load this node.
        </div>
      </div>
    );
  }

  const node = query.data;
  const concepts = node.concepts;
  const enriched = conceptsAvailable(concepts);
  const style = nodeStyle(node.node_type);
  const isTask = node.node_type === "task";
  const subBadge = [node.issuer, node.short_type].filter(Boolean).join(" · ");

  // Legal basis: prefer the enriched `legal_basis` list, else the structural
  // `pursuant_to` on the node. ISMP: the enriched value, else the node field;
  // for a profiled document with no value yet, show the honest pending state
  // (its source, CAS's RH publication form, is not held offline).
  const legalBasis =
    enriched && asList(concepts.legal_basis).length > 0
      ? asList(concepts.legal_basis)
      : node.pursuant_to
        ? [node.pursuant_to]
        : [];
  const ismpValue =
    (enriched ? concepts.ismp_classification : null) ?? node.ismp_classification;
  const ismpBadge = ismpValue ?? (enriched ? ISMP_PENDING : null);

  return (
    <div className="flex h-full flex-col animate-in slide-in-from-right-4 duration-200">
      <PanelHeader onClose={onClose} />
      <div className="space-y-2 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className={cn("border uppercase tracking-wide", style.badge)}>
            {node.node_type}
          </Badge>
          {subBadge && (
            <span className="text-xs text-muted-foreground">{subBadge}</span>
          )}
        </div>
        <h2 className="text-lg font-bold leading-tight">{node.title}</h2>
        {node.description && (
          <p className="text-sm text-muted-foreground">{node.description}</p>
        )}
        {(legalBasis.length > 0 || ismpBadge) && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {ismpBadge && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium",
                  ismpValue
                    ? "border-cyan-400/30 bg-cyan-500/10 text-cyan-300"
                    : "border-slate-400/30 bg-slate-500/10 text-muted-foreground",
                )}
                title={ismpValue ? undefined : "ISMP classification not yet sourced"}
              >
                <ShieldCheck className="h-3 w-3" /> ISMP: {ismpBadge}
              </span>
            )}
            {legalBasis.length > 0 && (
              <span className="inline-flex items-center gap-1 rounded-md border border-amber-300/30 bg-amber-400/10 px-2 py-0.5 text-[11px] font-medium text-amber-300">
                <Scale className="h-3 w-3" /> Legal basis: {legalBasis.join(", ")}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-4 pb-4">
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            First-order neighbours
          </h3>
          {node.first_order_neighbours.length === 0 ? (
            <p className="text-sm text-muted-foreground">None</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {node.first_order_neighbours.map((nb) => (
                <button
                  key={nb.id}
                  type="button"
                  onClick={() => onSelectNode(nb.id)}
                  className={cn(
                    "rounded-md border px-2 py-1 text-xs font-medium transition hover:opacity-80",
                    nodeStyle(nb.node_type).badge,
                  )}
                >
                  {nb.title}
                </button>
              ))}
            </div>
          )}
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Second-order neighbours
          </h3>
          <p className="text-sm text-muted-foreground">
            {node.second_order_neighbours.message}
          </p>
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Recent activity
          </h3>
          {node.recent_activity.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent activity</p>
          ) : (
            <ul className="space-y-2">
              {node.recent_activity.map((a, i) => (
                <li key={i} className="text-sm">
                  <span className="font-medium">{a.author}</span>{" "}
                  <span className="text-muted-foreground">
                    · {a.kind} · {a.at.slice(0, 10)}
                  </span>
                  <p className="text-muted-foreground">{a.summary}</p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <button
            type="button"
            onClick={() => setConceptsOpen((o) => !o)}
            aria-expanded={conceptsOpen}
            className="flex w-full items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted-foreground"
          >
            <span>Concepts</span>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                conceptsOpen && "rotate-180",
              )}
            />
          </button>
          {conceptsOpen &&
            (conceptsAvailable(concepts) ? (
              <dl className="mt-2 space-y-2 text-sm">
                {CONCEPT_FIELD_ORDER.map(([field, label]) => {
                  const value = concepts[field];
                  const chips = CHIP_FIELDS.has(field) ? asList(value) : null;
                  const pending =
                    field === "ismp_classification" && value == null
                      ? ISMP_PENDING
                      : null;
                  return (
                    <div key={field}>
                      <dt className="text-xs font-medium text-muted-foreground">
                        {label}
                      </dt>
                      {chips ? (
                        chips.length > 0 ? (
                          <dd className="flex flex-wrap gap-1">
                            {chips.map((c) => (
                              <span
                                key={c}
                                className="rounded-full bg-accent/60 px-2 py-0.5 text-xs font-medium text-foreground/90"
                              >
                                {c}
                              </span>
                            ))}
                          </dd>
                        ) : (
                          <dd className="text-muted-foreground">Not available</dd>
                        )
                      ) : (
                        <dd className={cn((!value || pending) && "text-muted-foreground")}>
                          {value ?? pending ?? "Not available"}
                        </dd>
                      )}
                    </div>
                  );
                })}
              </dl>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">
                {concepts.message}
              </p>
            ))}
        </section>
      </div>

      <div className="border-t border-border/60 p-4">
        {isTask ? (
          <Button
            className="w-full bg-cyan-500 text-slate-950 hover:bg-cyan-400"
            onClick={() =>
              navigate(`/workstreams/${workstreamId}/tasks/${node.id}`)
            }
          >
            <FileText /> Open task
          </Button>
        ) : (
          <Button
            variant="outline"
            className="w-full"
            onClick={() => openSource(node.source_url)}
          >
            <ExternalLink /> Open source
          </Button>
        )}
      </div>
    </div>
  );
}

export default NodeDetailPanel;
