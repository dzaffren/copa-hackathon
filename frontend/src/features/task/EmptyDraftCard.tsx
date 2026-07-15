import { Link } from "react-router-dom";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  workstreamId: string;
  nodeId: string;
}

export function EmptyDraftCard({ workstreamId, nodeId }: Props) {
  return (
    <div
      data-testid="empty-draft-card"
      className="flex flex-col items-center gap-3 p-10 text-center"
    >
      <div className="grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
        <FileText className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-semibold">No findings yet</p>
        <p className="mx-auto mt-1 max-w-sm text-xs text-muted-foreground">
          No pairwise findings can exist until the draft has content. Add
          clauses in the drafting workspace to surface linkages against the
          declared neighbours.
        </p>
      </div>
      <Button asChild className="bg-indigo-600 hover:bg-indigo-700">
        <Link to={`/workstreams/${workstreamId}/tasks/${nodeId}/draft`}>
          <FileText /> Open draft
        </Link>
      </Button>
    </div>
  );
}
