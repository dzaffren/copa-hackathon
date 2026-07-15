import { Link, useParams } from "react-router-dom";

function Shell({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mx-auto max-w-3xl p-8">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {eyebrow}
      </p>
      <h1 className="mt-1 text-2xl font-bold">{title}</h1>
      <div className="mt-4 text-sm text-muted-foreground">{children}</div>
    </div>
  );
}

export function HomePage() {
  return (
    <Shell eyebrow="Workstream Brain" title="Workstream Brain">
      <Link
        className="font-semibold text-primary underline-offset-4 hover:underline"
        to="/workstreams/opres-v2/tasks/opres-pd-v0-3"
      >
        Open the OpRes PD v0.3 task screen →
      </Link>
    </Shell>
  );
}

export function WorkstreamGraphPage() {
  const { workstreamId } = useParams();
  return (
    <Shell eyebrow="Workstream graph" title={`Workstream ${workstreamId}`}>
      <p>
        The workstream graph canvas is not part of this build. This placeholder
        confirms the breadcrumb route resolves.
      </p>
    </Shell>
  );
}

export function DraftingWorkspacePage() {
  const { workstreamId, nodeId } = useParams();
  return (
    <Shell eyebrow="Drafting workspace" title="Drafting workspace">
      <p>
        Drafting workspace for task <code>{nodeId}</code> in workstream{" "}
        <code>{workstreamId}</code>. Placeholder for the drafting story.
      </p>
    </Shell>
  );
}

export function ReviewLinkagesPage() {
  const { workstreamId, edgeId } = useParams();
  return (
    <Shell eyebrow="Review linkages" title="Review linkages">
      <p>
        Review linkages for edge <code>{edgeId}</code> in workstream{" "}
        <code>{workstreamId}</code>. Placeholder for the review story.
      </p>
    </Shell>
  );
}
