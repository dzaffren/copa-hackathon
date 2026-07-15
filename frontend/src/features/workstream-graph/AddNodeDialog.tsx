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
import { createNode } from "@/lib/api";
import type { EdgeType, GraphNode, NodeType } from "@/lib/types";

const NODE_TYPE_OPTIONS: NodeType[] = [
  "task",
  "internal-published",
  "international-standard",
  "peer-regulator",
  "act-law",
  "industry-input",
  "others",
];

const EDGE_TYPE_OPTIONS: EdgeType[] = [
  "supersedes",
  "references",
  "contributes-to",
  "parallel-to",
];

interface EdgeRow {
  target_node_id: string;
  edge_type: string;
}

interface AddNodeDialogProps {
  workstreamId: string;
  nodes: GraphNode[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const fieldClass = "w-full rounded-md border px-3 py-2 text-sm";

/**
 * Add-node modal. A plain controlled form (consistent with the existing task
 * dialogs — no react-hook-form/zod dependency). "Add to graph" stays disabled
 * until a title is set and at least one complete edge row (target + type) is
 * declared, mirroring the server's EDGE_REQUIRED rule.
 */
export function AddNodeDialog({
  workstreamId,
  nodes,
  open,
  onOpenChange,
}: AddNodeDialogProps) {
  const queryClient = useQueryClient();
  const [nodeType, setNodeType] = useState<NodeType>("international-standard");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [edges, setEdges] = useState<EdgeRow[]>([]);

  const completeEdges = edges.filter((e) => e.target_node_id && e.edge_type);
  const canSubmit = title.trim().length > 0 && completeEdges.length > 0;

  function reset() {
    setNodeType("international-standard");
    setTitle("");
    setDescription("");
    setSourceUrl("");
    setEdges([]);
  }

  const mutation = useMutation({
    mutationFn: () =>
      createNode(workstreamId, {
        node_type: nodeType,
        title: title.trim(),
        description: description.trim() || null,
        source_url: sourceUrl.trim() || null,
        edges: completeEdges.map((e) => ({
          target_node_id: e.target_node_id,
          edge_type: e.edge_type as EdgeType,
        })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["workstream", workstreamId, "graph"],
      });
      reset();
      onOpenChange(false);
    },
  });

  const addRow = () =>
    setEdges((rows) => [...rows, { target_node_id: "", edge_type: "" }]);
  const removeRow = (i: number) =>
    setEdges((rows) => rows.filter((_, idx) => idx !== i));
  const updateRow = (i: number, patch: Partial<EdgeRow>) =>
    setEdges((rows) =>
      rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)),
    );

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add node</DialogTitle>
          <DialogDescription>
            Add a new anchor to the workstream. At least one edge to an existing
            node is required.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium">Node type</span>
            <select
              className={fieldClass}
              value={nodeType}
              onChange={(e) => setNodeType(e.target.value as NodeType)}
              aria-label="Node type"
            >
              {NODE_TYPE_OPTIONS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

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

          <label className="block text-sm">
            <span className="mb-1 block font-medium">Attachment</span>
            <input
              type="file"
              className="block text-sm"
              aria-label="Attachment"
              accept=".pdf,.docx"
            />
          </label>

          <div>
            <div className="mb-1 flex items-center justify-between">
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
                      className="rounded p-1 text-gray-400 hover:text-red-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
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
            className="bg-indigo-600 hover:bg-indigo-700"
            disabled={!canSubmit || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "Adding…" : "Add to graph"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default AddNodeDialog;
