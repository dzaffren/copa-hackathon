import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { createEdge, HttpError } from "@/lib/api";
import type { EdgeType, GraphNode } from "@/lib/types";

const EDGE_TYPE_OPTIONS: EdgeType[] = [
  "supersedes",
  "references",
  "contributes-to",
  "parallel-to",
];

/** Plain-language copy for the refusals this dialog can provoke. */
const ERROR_COPY: Record<string, string> = {
  SELF_LOOP: "A document cannot be connected to itself.",
  DUPLICATE_EDGE: "That connection already exists between these two documents.",
  NODE_NOT_FOUND: "One of those documents is no longer in this workstream.",
  INVALID_EDGE_TYPE: "Choose a connection type.",
  EDGE_REQUIRED: "Pick a document and a connection type.",
};

const fieldClass =
  "w-full rounded-md border border-border/70 bg-background/60 px-3 py-2 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/40";

interface AddEdgeDialogProps {
  workstreamId: string;
  /** The node the drafter is viewing — the connection is drawn from here. */
  sourceNodeId: string;
  /** Every node in this workstream; the viewed node is filtered out so a
   *  self-connection cannot even be selected. */
  nodes: GraphNode[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Connect the viewed node to another node already on the canvas. Mirrors
 * `AddNodeDialog`'s plain controlled-form approach (no form library). Drawing a
 * connection never runs analysis — that stays a separate, explicit action.
 */
export function AddEdgeDialog({
  workstreamId,
  sourceNodeId,
  nodes,
  open,
  onOpenChange,
}: AddEdgeDialogProps) {
  const queryClient = useQueryClient();
  const [targetNodeId, setTargetNodeId] = useState("");
  const [edgeType, setEdgeType] = useState("");

  const candidates = nodes.filter((n) => n.id !== sourceNodeId);
  const canSubmit = targetNodeId !== "" && edgeType !== "";

  function reset() {
    setTargetNodeId("");
    setEdgeType("");
  }

  const mutation = useMutation({
    mutationFn: () =>
      createEdge(workstreamId, {
        source_node_id: sourceNodeId,
        target_node_id: targetNodeId,
        edge_type: edgeType as EdgeType,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["workstream", workstreamId, "graph"],
      });
      queryClient.invalidateQueries({
        queryKey: ["node", workstreamId, sourceNodeId],
      });
      reset();
      onOpenChange(false);
    },
  });

  const error = mutation.error;
  const errorMessage = error
    ? ((error instanceof HttpError && ERROR_COPY[error.code]) ?? error.message)
    : null;

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      <DialogContent className="glass max-w-md">
        <DialogHeader>
          <DialogTitle>Add edge</DialogTitle>
          <DialogDescription>
            Connect this document to another one already in this workstream.
          </DialogDescription>
        </DialogHeader>

        {candidates.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            There are no other documents in this workstream to connect to.
          </p>
        ) : (
          <div className="space-y-4">
            <label className="block text-sm">
              <span className="mb-1 block font-medium">Connect to</span>
              <select
                className={fieldClass}
                value={targetNodeId}
                onChange={(e) => setTargetNodeId(e.target.value)}
                aria-label="Connect to"
              >
                <option value="">Select a document…</option>
                {candidates.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.title}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium">Connection type</span>
              <select
                className={fieldClass}
                value={edgeType}
                onChange={(e) => setEdgeType(e.target.value)}
                aria-label="Connection type"
              >
                <option value="">Type…</option>
                {EDGE_TYPE_OPTIONS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>

            {errorMessage && (
              <p role="alert" className="text-sm text-red-500">
                {errorMessage}
              </p>
            )}
          </div>
        )}

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
            {mutation.isPending ? "Connecting…" : "Add edge"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default AddEdgeDialog;
