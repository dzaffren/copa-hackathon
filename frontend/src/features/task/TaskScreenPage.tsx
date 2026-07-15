import { useParams } from "react-router-dom";

// Scaffold stub — replaced by the full Task Screen in Phase 2.
export default function TaskScreenPage() {
  const { workstreamId, nodeId } = useParams();
  return (
    <div className="p-8">
      <h1 className="text-xl font-bold">Task screen</h1>
      <p className="text-sm text-muted-foreground">
        {workstreamId} / {nodeId}
      </p>
    </div>
  );
}
