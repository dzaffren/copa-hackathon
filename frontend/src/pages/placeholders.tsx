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

// ReviewLinkagesPage is no longer a placeholder — see
// @/features/review-linkages/ReviewLinkagesPage.

export function NewWorkstreamPage() {
  return (
    <Shell eyebrow="New workstream" title="New workstream">
      <p>
        The new-workstream form is a separate story. This placeholder confirms
        the route resolves.
      </p>
    </Shell>
  );
}

export function InstitutionMapPage() {
  return (
    <Shell eyebrow="Institution map" title="Institution map">
      <p>
        The institution map is a separate epic. This placeholder confirms the
        route resolves.
      </p>
    </Shell>
  );
}
