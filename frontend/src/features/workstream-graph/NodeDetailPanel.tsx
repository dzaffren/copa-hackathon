import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  ChevronDown,
  ExternalLink,
  FileText,
  Link2,
  Trash2,
  Loader2,
  Sparkles,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { deleteNode, extractConcepts, fetchNodeDetail } from "@/lib/api";
import {
  TASK_TYPE_OPTIONS,
  type NodeMetadata,
  type GraphNode,
} from "@/lib/types";
import { AddEdgeDialog } from "./AddEdgeDialog";
import { nodeStyle } from "./legend";
import {
  asList,
  CONCEPT_FIELD_ORDER,
  ISMP_PENDING,
  LIST_FIELDS,
} from "./metadata";
import { NodeMetadataForm } from "./NodeMetadataForm";

function conceptsAvailable(
  concepts: NodeMetadata | { status: string; message: string },
): concepts is NodeMetadata {
  return concepts.status === "available";
}

interface NodeDetailPanelProps {
  workstreamId: string;
  nodeId: string;
  /** Refocus the panel on a neighbour when its chip is clicked. */
  onSelectNode: (id: string) => void;
  onClose?: () => void;
  /** Every node in this workstream — the Add-edge dialog's target choices.
   *  Defaults to empty so callers that do not offer edge creation still work. */
  nodes?: GraphNode[];
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
  nodes = [],
}: NodeDetailPanelProps) {
  const navigate = useNavigate();
  const [conceptsOpen, setConceptsOpen] = useState(false);
  // The profile is read-only until Edit is pressed: several fields hold
  // word-for-word quotations, so a stray keystroke must not be able to alter one.
  const [metadataEditing, setMetadataEditing] = useState(false);
  const [addEdgeOpen, setAddEdgeOpen] = useState(false);
  // Two-step delete: the first click arms it, the second commits. Deletion
  // cascades (linkages, findings, passages, concepts) and cannot be undone, so
  // a single click must never be enough.
  const [confirmDelete, setConfirmDelete] = useState(false);
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["node", workstreamId, nodeId],
    queryFn: () => fetchNodeDetail(workstreamId, nodeId),
  });
  // Synchronous on the server: the mutation stays pending for the whole
  // extraction, then the node refetches so the pills and the new activity
  // entry appear together.
  const extract = useMutation({
    mutationFn: () => extractConcepts(workstreamId, nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["node", workstreamId, nodeId],
      });
    },
  });
  const remove = useMutation({
    mutationFn: () => deleteNode(workstreamId, nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["workstream", workstreamId, "graph"],
      });
      // The node this panel describes no longer exists — close it.
      onClose?.();
    },
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
  // The nine-field regulatory profile moved to `metadata`; `concepts` now
  // carries the extracted axis pills rendered in its own section below.
  const concepts = node.metadata;
  const enriched = conceptsAvailable(concepts);
  // `null` when the node has no side-file yet. The placeholder shape stays in the
  // response for the cross-workstream consumers that read it; the panel simply
  // renders an empty-but-fillable profile from it instead of its message.
  const profile = enriched ? concepts : null;
  const style = nodeStyle(node.node_type);
  const isTask = node.node_type === "task";
  const subBadge = [node.issuer, node.short_type].filter(Boolean).join(" · ");

  // Legal provision and ISMP classification used to repeat as badges under the
  // title. Both are rows in the Metadata disclosure below, so the badges were a
  // second copy of the same values — and the one a drafter could not edit where
  // she read it. The disclosure is now the only place either appears.

  // The chip reads the drafter-facing label, never the stored code — "DECK" is
  // a title suffix, not something to show as a badge. Absent for a context
  // document, which is never asked what kind of deliverable it is.
  const taskTypeLabel =
    TASK_TYPE_OPTIONS.find((o) => o.code === node.task_type)?.label ?? null;

  // First row of the profile on a working draft, and static text in edit mode
  // too: the deliverable kind is set once at creation and is never an input.
  // A context document is never asked what kind of deliverable it is, so it gets
  // no such row at all.
  const taskTypeRow = taskTypeLabel && (
    <div className="mt-2 text-sm">
      <span className="block text-xs font-medium text-muted-foreground">
        Task type
      </span>
      <span className="block">{taskTypeLabel}</span>
    </div>
  );

  return (
    <div className="flex h-full flex-col animate-in slide-in-from-right-4 duration-200">
      <PanelHeader onClose={onClose} />
      <div className="space-y-2 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className={cn("border uppercase tracking-wide", style.badge)}>
            {node.node_type}
          </Badge>
          {taskTypeLabel && (
            <span
              data-testid="task-type-chip"
              className="inline-flex items-center rounded-md border border-primary/30 bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary"
            >
              {taskTypeLabel}
            </span>
          )}
          {subBadge && (
            <span className="text-xs text-muted-foreground">{subBadge}</span>
          )}
        </div>
        <h2 className="text-lg font-bold leading-tight">{node.title}</h2>
        {node.description && (
          <p className="text-sm text-muted-foreground">{node.description}</p>
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
          {/* The Edit button is a SIBLING of the disclosure toggle, not nested
              inside it — a button within a button is invalid HTML and breaks
              keyboard activation of both. */}
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={() => setConceptsOpen((o) => !o)}
              aria-expanded={conceptsOpen}
              className="flex flex-1 items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted-foreground"
            >
              <span>Metadata</span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 transition-transform",
                  conceptsOpen && "rotate-180",
                )}
              />
            </button>
            {/* Offered on every node type: the prepared profiles already cover
                context documents, so restricting editing to working drafts would
                leave those uncorrectable. */}
            {!metadataEditing && (
              <Button
                variant="outline"
                size="sm"
                className="h-6 px-2 text-[11px]"
                onClick={() => {
                  setConceptsOpen(true);
                  setMetadataEditing(true);
                }}
              >
                Edit
              </Button>
            )}
          </div>
          {conceptsOpen &&
            (metadataEditing ? (
              <>
                {taskTypeRow}
                <NodeMetadataForm
                  workstreamId={workstreamId}
                  nodeId={node.id}
                  initial={profile}
                  onDone={() => setMetadataEditing(false)}
                />
              </>
            ) : (
              <>
                {taskTypeRow}
                <dl className="mt-2 space-y-2 text-sm">
                  {CONCEPT_FIELD_ORDER.map(([field, label]) => {
                    // A node with no side-file yet reads as nine empty fields
                    // rather than an apology: every one of them is fillable.
                    const value = profile?.[field] ?? null;
                    const chips = LIST_FIELDS.has(field) ? asList(value) : null;
                    const pending =
                      field === "ismp_classification" && value == null
                        ? ISMP_PENDING
                        : null;
                    return (
                      <div key={field}>
                        <dt className="text-xs font-medium text-muted-foreground">
                          {label}
                        </dt>
                        {chips && chips.length > 0 ? (
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
                          <dd
                            className={cn(
                              (!value || pending) && "text-muted-foreground",
                            )}
                          >
                            {/* "Not set" is a state a drafter can change, unlike
                              the old "not available". */}
                            {(typeof value === "string" ? value : null) ??
                              pending ??
                              "Not set"}
                          </dd>
                        )}
                      </div>
                    );
                  })}
                </dl>
              </>
            ))}
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Concepts
          </h3>
          {node.concepts.axes.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {node.concepts.axes.map((axis) => (
                <span
                  key={axis}
                  data-testid="concept-pill"
                  className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
                >
                  {axis}
                </span>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                No concepts extracted yet.
              </p>
              <Button
                variant="outline"
                size="sm"
                disabled={extract.isPending}
                onClick={() => extract.mutate()}
              >
                {extract.isPending ? (
                  <>
                    <Loader2 className="animate-spin" /> Extracting…
                  </>
                ) : (
                  <>
                    <Sparkles /> Extract concepts
                  </>
                )}
              </Button>
              {extract.isError && (
                <p role="alert" className="text-sm text-red-500">
                  Concept extraction failed. Try again.
                </p>
              )}
            </div>
          )}
        </section>
      </div>

      <div className="space-y-2 border-t border-border/60 p-4">
        <Button
          variant="outline"
          className="w-full"
          onClick={() => setAddEdgeOpen(true)}
        >
          <Link2 /> Add edge
        </Button>
        <AddEdgeDialog
          workstreamId={workstreamId}
          sourceNodeId={node.id}
          nodes={nodes}
          open={addEdgeOpen}
          onOpenChange={setAddEdgeOpen}
        />

        {/* The focal working draft is the workstream's anchor — the server
            refuses to delete it, so the action is not offered for a task. */}
        {!isTask &&
          (confirmDelete ? (
            <div className="space-y-1.5 rounded-lg border border-red-300/60 bg-red-50/60 p-2">
              <p className="text-xs text-red-700">
                Delete this document, its {node.first_order_neighbours.length}{" "}
                linkage
                {node.first_order_neighbours.length === 1 ? "" : "s"} and any
                findings on them? Its passages and concepts go too. This cannot
                be undone.
              </p>
              <div className="flex gap-1.5">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => setConfirmDelete(false)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="flex-1 bg-red-600 text-white hover:bg-red-700"
                  disabled={remove.isPending}
                  onClick={() => remove.mutate()}
                >
                  {remove.isPending ? "Deleting…" : "Delete"}
                </Button>
              </div>
              {remove.isError && (
                <p role="alert" className="text-xs text-red-700">
                  Could not delete this node.
                </p>
              )}
            </div>
          ) : (
            <Button
              variant="outline"
              className="w-full border-red-300/60 text-red-700 hover:bg-red-50"
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 /> Delete node
            </Button>
          ))}

        {isTask ? (
          <Button
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
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
