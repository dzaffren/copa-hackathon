import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, PencilLine } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchTask, HttpError } from "@/lib/api";
import { SourceCard } from "./SourceCard";
import { NeighboursCard } from "./NeighboursCard";
import { PairwiseComparisonCard } from "./PairwiseComparisonCard";
import { AssignDialog } from "./AssignDialog";

export default function TaskScreenPage() {
  const { workstreamId = "", nodeId = "" } = useParams();

  const query = useQuery({
    queryKey: ["task", workstreamId, nodeId],
    queryFn: () => fetchTask(workstreamId, nodeId),
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
          className="mt-4 inline-block text-sm font-semibold text-indigo-600 hover:text-indigo-800"
        >
          ← Back to the workstream graph
        </Link>
      </div>
    );
  }

  const { task, neighbours, draft_empty } = query.data;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between gap-6">
          <div className="min-w-0">
            <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
              <Link to={graphHref} className="hover:text-indigo-600">
                ← Workstream graph
              </Link>
              <span className="text-gray-300">/</span>
              <span className="font-medium text-gray-700">Task</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-indigo-100 uppercase tracking-wider text-indigo-800 hover:bg-indigo-100">
                task
              </Badge>
              <h1 className="text-xl font-bold">{task.title}</h1>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {`${task.description} · ${neighbours.length} neighbour nodes defined at creation`}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <AssignDialog />
            <Button asChild className="bg-indigo-600 hover:bg-indigo-700">
              <Link to={`/workstreams/${workstreamId}/tasks/${nodeId}/draft`}>
                <PencilLine /> Open draft
              </Link>
            </Button>
          </div>
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
