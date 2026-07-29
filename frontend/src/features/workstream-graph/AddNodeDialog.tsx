import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { createNode, HttpError } from "@/lib/api";
import {
  TASK_TYPE_OPTIONS,
  type DocClass,
  type EdgeType,
  type GraphNode,
  type NodeType,
  type TaskTypeCode,
} from "@/lib/types";
import { NODE_LEGEND, NODE_LEGEND_ORDER } from "./legend";

const EDGE_TYPE_OPTIONS: EdgeType[] = [
  "supersedes",
  "references",
  "parallel-to",
];

/** The three segmenters, with the guidance a drafter needs to pick correctly.
 *  Getting this wrong is the difference between citable passages and rubble,
 *  which is why it is asked rather than inferred. */
const DOC_CLASS_OPTIONS: { value: DocClass; label: string; hint: string }[] = [
  {
    value: "semi-structured",
    label: "Semi-structured",
    hint: "Headings and numbered paragraphs — most standards and papers.",
  },
  {
    value: "prose",
    label: "Prose",
    hint: "Flowing text with no reliable numbering.",
  },
  {
    value: "structured-rules",
    label: "Structured rules",
    hint: "Numbered BNM policy documents only (e.g. RMiT).",
  },
];

/** Plain-language messages for the failures this form can provoke. The server's
 *  own message is shown when it carries more detail. */
const ERROR_COPY: Record<string, string> = {
  ATTACHMENT_REQUIRED: "Attach a document to add it to the graph.",
  INVALID_DOC_CLASS: "Choose how the document should be broken up.",
  INGEST_FAILED: "The document could not be read. Try a different file.",
  CHUNKING_FAILED:
    "This document can't be broken up that way. Try prose or semi-structured.",
  NO_PASSAGES: "The document produced no passages and can't be added.",
  EDGE_REQUIRED:
    "Connect the document to at least one node already on the canvas.",
};

interface EdgeRow {
  target_node_id: string;
  edge_type: string;
}

/** Seed the edge rows when the dialog opens.
 *
 *  A document must connect to at least one node already on the canvas, so on a
 *  brand-new workstream — where the focal node is the ONLY possible target —
 *  there is nothing to choose. Pre-filling that row means the first document can
 *  be added without the drafter hunting for the one legal answer; with several
 *  candidates the choice is theirs, so we seed nothing.
 */
function defaultEdges(nodes: GraphNode[]): EdgeRow[] {
  if (nodes.length !== 1) return [];
  return [{ target_node_id: nodes[0].id, edge_type: "references" }];
}

interface AddNodeDialogProps {
  workstreamId: string;
  nodes: GraphNode[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const fieldClass =
  "w-full rounded-md border border-border/70 bg-background/60 px-3 py-2 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/40";

/**
 * Add-node modal. A plain controlled form (consistent with the existing task
 * dialogs — no react-hook-form/zod dependency). The node type is chosen from a
 * colour-coded grid of the seven types. "Add to graph" stays disabled until a
 * title is set and at least one complete edge row (target + type) is declared,
 * mirroring the server's EDGE_REQUIRED rule.
 */
export function AddNodeDialog({
  workstreamId,
  nodes,
  open,
  onOpenChange,
}: AddNodeDialogProps) {
  const queryClient = useQueryClient();
  const [nodeType, setNodeType] = useState<NodeType>("international-standard");
  const [taskType, setTaskType] = useState<TaskTypeCode | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [autoIngest, setAutoIngest] = useState(true);
  const [edges, setEdges] = useState<EdgeRow[]>(() => defaultEdges(nodes));
  const [attachment, setAttachment] = useState<File | null>(null);
  const [docClass, setDocClass] = useState<DocClass>("semi-structured");

  const completeEdges = edges.filter((e) => e.target_node_id && e.edge_type);
  const canSubmit =
    title.trim().length > 0 && completeEdges.length > 0 && attachment !== null;

  function reset() {
    setNodeType("international-standard");
    setTitle("");
    setDescription("");
    setSourceUrl("");
    setAutoIngest(true);
    setEdges(defaultEdges(nodes));
    setAttachment(null);
    setDocClass("semi-structured");
  }

  const mutation = useMutation({
    mutationFn: () =>
      createNode(
        workstreamId,
        {
          node_type: nodeType,
          title: title.trim(),
          description: description.trim() || null,
          source_url: sourceUrl.trim() || null,
          doc_class: docClass,
          edges: completeEdges.map((e) => ({
            target_node_id: e.target_node_id,
            edge_type: e.edge_type as EdgeType,
          })),
          ...(autoIngest ? {} : { skip_ingest: true }),
        },
        attachment,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["workstream", workstreamId, "graph"],
      });
      reset();
      onOpenChange(false);
    },
  });

  const error = mutation.error;
  const errorCode = error instanceof HttpError ? error.code : undefined;
  const errorField = error instanceof HttpError ? error.field : undefined;
  const errorMessage = error
    ? ((errorCode && ERROR_COPY[errorCode]) ?? error.message)
    : null;

  const addRow = () =>
    setEdges((rows) => [...rows, { target_node_id: "", edge_type: "" }]);
  const removeRow = (i: number) =>
    setEdges((rows) => rows.filter((_, idx) => idx !== i));
  const updateRow = (i: number, patch: Partial<EdgeRow>) =>
    setEdges((rows) =>
      rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)),
    );

  // Seed the pre-filled edge row when the dialog OPENS, not at mount: the page
  // keeps this dialog mounted permanently, so at mount the graph query has not
  // resolved and `nodes` is still empty. `seededFor` makes it fire once per
  // opening without clobbering rows the drafter has since edited.
  const [seededFor, setSeededFor] = useState<string | null>(null);
  if (open && seededFor !== workstreamId) {
    setSeededFor(workstreamId);
    if (edges.length === 0) setEdges(defaultEdges(nodes));
  }
  if (!open && seededFor !== null) setSeededFor(null);

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      {/* The dialog is a column: header and footer stay put while only the body
          scrolls. Scrolling the whole DialogContent let a tall form (node type
          grid + method picker + edge rows) push its own footer out of the box. */}
      <DialogContent className="glass flex max-h-[90vh] max-w-lg flex-col overflow-hidden">
        <DialogHeader>
          <DialogTitle>Add node</DialogTitle>
          <DialogDescription>
            Add a new anchor to the workstream. At least one edge to an existing
            node is required.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
          <div>
            <span className="mb-1.5 block text-sm font-medium">Node type</span>
            <div
              role="radiogroup"
              aria-label="Node type"
              className="grid grid-cols-2 gap-1.5 sm:grid-cols-3"
            >
              {NODE_LEGEND_ORDER.map((t) => {
                const selected = t === nodeType;
                return (
                  <button
                    key={t}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    aria-label={t}
                    onClick={() => {
                      setNodeType(t);
                      // A deliverable kind belongs to a working draft only, so
                      // switching away discards it — a stale pick must never
                      // reach the server, which refuses it (TASK_TYPE_NOT_ALLOWED).
                      if (t !== "task") setTaskType(null);
                    }}
                    className={cn(
                      "flex items-center gap-1.5 rounded-lg border px-2 py-1.5 text-left text-[11px] font-medium transition",
                      selected
                        ? "border-primary/60 bg-primary/10 ring-1 ring-primary/40"
                        : "border-border/60 hover:bg-accent/50",
                    )}
                  >
                    <span
                      className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{
                        backgroundColor: NODE_LEGEND[t].fill,
                        boxShadow: `0 0 5px ${NODE_LEGEND[t].stroke}`,
                      }}
                    />
                    <span className="truncate">{t}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Asked of a working draft only: a standard, act, or industry paper
              is not a deliverable Aisyah is producing. No colour dots here —
              those encode node type. */}
          {nodeType === "task" && (
            <div>
              <span className="mb-1.5 block text-sm font-medium">
                Task type
              </span>
              <div
                role="radiogroup"
                aria-label="Task type"
                className={cn(
                  "grid grid-cols-2 gap-1.5 sm:grid-cols-3",
                  errorField === "task_type" &&
                    "rounded-lg ring-1 ring-red-400",
                )}
              >
                {TASK_TYPE_OPTIONS.map((option) => {
                  const selected = option.code === taskType;
                  return (
                    <button
                      key={option.code}
                      type="button"
                      role="radio"
                      aria-checked={selected}
                      aria-label={option.code}
                      onClick={() => setTaskType(option.code)}
                      className={cn(
                        "flex items-center rounded-lg border px-2 py-1.5 text-left text-[11px] font-medium transition",
                        selected
                          ? "border-primary/60 bg-primary/10 ring-1 ring-primary/40"
                          : "border-border/60 hover:bg-accent/50",
                      )}
                    >
                      <span className="truncate">{option.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <label className="block text-sm">
            <span className="mb-1 block font-medium">Title</span>
            <input
              className={fieldClass}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-label="Title"
              placeholder="e.g. BCBS OpRes 2021 Companion Guide"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium">Description</span>
            <textarea
              className={fieldClass}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              aria-label="Description"
              rows={2}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium">Source URL</span>
            <input
              className={fieldClass}
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              aria-label="Source URL"
              placeholder="https://…"
            />
          </label>

          <label
            className={cn(
              "flex items-center gap-2 text-sm",
              sourceUrl.trim() ? "" : "text-muted-foreground",
            )}
          >
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-border/70 accent-primary"
              checked={autoIngest}
              disabled={!sourceUrl.trim()}
              onChange={(e) => setAutoIngest(e.target.checked)}
              aria-label="Auto-ingest document from URL"
            />
            <span>Auto-ingest document from URL</span>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium">Attachment</span>
            <input
              type="file"
              className={cn(
                "block text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-sm file:text-foreground",
                errorField === "attachment" && "text-red-500",
              )}
              aria-label="Attachment"
              accept=".pdf,.docx"
              onChange={(e) => setAttachment(e.target.files?.[0] ?? null)}
            />
          </label>

          <div>
            <span className="mb-1.5 block text-sm font-medium">
              Breaking-up method
            </span>
            <div
              role="radiogroup"
              aria-label="Breaking-up method"
              className={cn(
                "space-y-1.5",
                errorField === "doc_class" && "rounded-lg ring-1 ring-red-400",
              )}
            >
              {DOC_CLASS_OPTIONS.map((option) => {
                const selected = option.value === docClass;
                return (
                  <button
                    key={option.value}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    aria-label={option.value}
                    onClick={() => setDocClass(option.value)}
                    className={cn(
                      "block w-full rounded-lg border px-3 py-2 text-left transition",
                      selected
                        ? "border-primary/60 bg-primary/10 ring-1 ring-primary/40"
                        : "border-border/60 hover:bg-accent/50",
                    )}
                  >
                    <span className="block text-xs font-medium">
                      {option.label}
                    </span>
                    <span className="block text-[11px] text-muted-foreground">
                      {option.hint}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-sm font-medium">Edges</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addRow}
              >
                <Plus /> Add edge
              </Button>
            </div>
            {edges.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                At least one edge to an existing node is required.
              </p>
            ) : (
              <ul className="space-y-2">
                {edges.map((row, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <select
                      className={fieldClass}
                      value={row.target_node_id}
                      onChange={(e) =>
                        updateRow(i, { target_node_id: e.target.value })
                      }
                      aria-label={`Edge ${i + 1} target`}
                    >
                      <option value="">Select target…</option>
                      {nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.title}
                        </option>
                      ))}
                    </select>
                    <select
                      className={fieldClass}
                      value={row.edge_type}
                      onChange={(e) =>
                        updateRow(i, { edge_type: e.target.value })
                      }
                      aria-label={`Edge ${i + 1} type`}
                    >
                      <option value="">Type…</option>
                      {EDGE_TYPE_OPTIONS.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      aria-label={`Remove edge ${i + 1}`}
                      onClick={() => removeRow(i)}
                      className="rounded p-1 text-muted-foreground hover:text-red-400"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {errorMessage && (
            <p role="alert" className="text-sm text-red-500">
              {errorMessage}
            </p>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              reset();
              onOpenChange(false);
            }}
          >
            Cancel
          </Button>
          <Button
            type="button"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={!canSubmit || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "Chunking…" : "Add to graph"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default AddNodeDialog;
