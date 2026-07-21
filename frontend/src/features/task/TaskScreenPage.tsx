import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  GitBranch,
  Link2,
  Loader2,
  PencilLine,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fetchTask, setTaskWorkflow, HttpError } from "@/lib/api";
import type { TaskWorkflowStatus } from "@/lib/types";
import { SourceCard } from "./SourceCard";
import { NeighboursCard } from "./NeighboursCard";
import { PairwiseComparisonCard } from "./PairwiseComparisonCard";
import { AssignDialog } from "./AssignDialog";
import { ApproveDialog } from "./ApproveDialog";

const STATUS_LABEL: Record<TaskWorkflowStatus, string> = {
  draft: "Draft",
  pending_review: "Pending Review",
  approved: "Approved",
};

const STATUS_BADGE: Record<TaskWorkflowStatus, string> = {
  draft: "bg-slate-500/15 text-slate-300 border border-slate-400/30",
  pending_review: "bg-amber-400/15 text-amber-300 border border-amber-300/30",
  approved: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/30",
};

function formatApprovedAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function MetricTile({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
}) {
  return (
    <div className="glass flex items-center gap-3 rounded-xl px-4 py-3">
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

export default function TaskScreenPage() {
  const { workstreamId = "", nodeId = "" } = useParams();
  const queryClient = useQueryClient();
  const queryKey = ["task", workstreamId, nodeId];

  const query = useQuery({
    queryKey,
    queryFn: () => fetchTask(workstreamId, nodeId),
  });

  const workflowMutation = useMutation({
    mutationFn: (vars: { status: TaskWorkflowStatus; actorId: string }) =>
      setTaskWorkflow(workstreamId, nodeId, vars.status, vars.actorId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });

  const graphHref = `/workstreams/${workstreamId}`;

  if (query.isPending) {
    return (
      <div
        role="status"
        className="flex items-center gap-2 p-10 text-sm text-muted-foreground"
      >
        <Loader2 className="h-4 w-4 animate-spin" /> Loading task…
      </div>
    );
  }

  if (query.isError) {
    const err = query.error;
    const code = err instanceof HttpError ? err.code : "INTERNAL_ERROR";
    const message =
      code === "NOT_A_TASK"
        ? "This node is not a task, so it has no task screen."
        : "We could not load this task.";
    return (
      <div className="mx-auto max-w-lg p-10 text-center">
        <p className="text-sm font-semibold">{message}</p>
        <p className="mt-1 text-xs text-muted-foreground">{code}</p>
        <Link
          to={graphHref}
          className="mt-4 inline-block text-sm font-semibold text-cyan-300 hover:text-cyan-200"
        >
          ← Back to the workstream graph
        </Link>
      </div>
    );
  }

  const { task, workflow, neighbours, draft_empty } = query.data;
  const currentStatus = workflow.status;
  const analysedCount = neighbours.filter((n) => n.analysed).length;
  const findingsTotal = neighbours.reduce(
    (sum, n) => sum + (n.findings_count ?? 0),
    0,
  );

  return (
    <div className="h-full overflow-y-auto bg-background">
      <header className="border-b border-border/60 bg-card/30 px-6 py-4 backdrop-blur">
        <div className="flex items-center justify-between gap-6">
          <div className="min-w-0">
            <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
              <Link to={graphHref} className="hover:text-cyan-300">
                ← Workstream graph
              </Link>
              <span>/</span>
              <span className="font-medium text-foreground">Task</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border border-cyan-400/30 bg-cyan-500/15 uppercase tracking-wider text-cyan-300 hover:bg-cyan-500/15">
                task
              </Badge>
              <h1 className="text-xl font-bold">{task.title}</h1>
              <Badge
                className={cn(
                  "uppercase tracking-wide",
                  STATUS_BADGE[currentStatus],
                )}
              >
                {STATUS_LABEL[currentStatus]}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {task.owner.name} · {task.format} · {neighbours.length} neighbour
              nodes
            </p>
            {currentStatus === "approved" && workflow.approved_by && (
              <p className="mt-0.5 text-xs text-emerald-300">
                Approved by {workflow.approved_by.name}
                {workflow.approved_at &&
                  ` · ${formatApprovedAt(workflow.approved_at)}`}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {currentStatus === "draft" && (
              <AssignDialog
                members={task.reviewers}
                onAssigned={(member) =>
                  workflowMutation.mutate({
                    status: "pending_review",
                    actorId: member.id,
                  })
                }
              />
            )}
            {currentStatus === "pending_review" && workflow.checker && (
              <ApproveDialog
                checker={workflow.checker}
                onApproved={(approver) =>
                  workflowMutation.mutate({
                    status: "approved",
                    actorId: approver.id,
                  })
                }
              />
            )}
            <Button
              asChild
              className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
            >
              <Link to={`/workstreams/${workstreamId}/tasks/${nodeId}/draft`}>
                <PencilLine /> Open draft
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3 sm:max-w-xl">
          <MetricTile
            icon={<GitBranch className="h-4 w-4" />}
            value={neighbours.length}
            label="Neighbours"
          />
          <MetricTile
            icon={<Sparkles className="h-4 w-4" />}
            value={analysedCount}
            label="Analysed"
          />
          <MetricTile
            icon={<Link2 className="h-4 w-4" />}
            value={findingsTotal}
            label="Findings"
          />
        </div>
      </header>

      <div className="grid grid-cols-12 gap-4 p-6">
        <section className="col-span-12 space-y-4 lg:col-span-4">
          <SourceCard task={task} />
          <NeighboursCard neighbours={neighbours} />
        </section>
        <section className="col-span-12 lg:col-span-8">
          <PairwiseComparisonCard
            workstreamId={workstreamId}
            nodeId={nodeId}
            neighbours={neighbours}
            draftEmpty={draft_empty}
          />
        </section>
      </div>
    </div>
  );
}
