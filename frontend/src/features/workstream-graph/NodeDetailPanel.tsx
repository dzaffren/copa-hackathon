import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ChevronDown, ExternalLink, FileText, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { fetchNodeDetail } from "@/lib/api";
import { nodeStyle } from "./legend";

interface NodeDetailPanelProps {
  workstreamId: string;
  nodeId: string;
  /** Refocus the panel on a neighbour when its chip is clicked. */
  onSelectNode: (id: string) => void;
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

/**
 * Right-panel detail for a selected node: type + sub-badge, description, the
 * clickable first-order neighbour chips, a "N/A in demo" second-order block,
 * recent activity, a collapsed Concepts placeholder, and an Open task / Open
 * source action keyed by node type.
 */
export function NodeDetailPanel({
  workstreamId,
  nodeId,
  onSelectNode,
}: NodeDetailPanelProps) {
  const navigate = useNavigate();
  const [conceptsOpen, setConceptsOpen] = useState(false);
  const query = useQuery({
    queryKey: ["node", workstreamId, nodeId],
    queryFn: () => fetchNodeDetail(workstreamId, nodeId),
  });

  if (query.isPending) {
    return (
      <div
        role="status"
        className="flex items-center gap-2 p-6 text-sm text-muted-foreground"
      >
        <Loader2 className="h-4 w-4 animate-spin" /> Loading node…
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Could not load this node.
      </div>
    );
  }

  const node = query.data;
  const style = nodeStyle(node.node_type);
  const isTask = node.node_type === "task";
  const subBadge = [node.issuer, node.short_type].filter(Boolean).join(" · ");

  return (
    <Card className="flex h-full flex-col rounded-none border-0 border-l">
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className={cn("border uppercase tracking-wide", style.badge)}>
            {node.node_type}
          </Badge>
          {subBadge && (
            <span className="text-xs text-muted-foreground">{subBadge}</span>
          )}
        </div>
        <h2 className="text-lg font-bold leading-tight">{node.title}</h2>
        {node.description && (
          <p className="text-sm text-muted-foreground">{node.description}</p>
        )}
      </CardHeader>

      <CardContent className="flex-1 space-y-5 overflow-y-auto">
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
                    "rounded-md border px-2 py-1 text-xs font-medium hover:opacity-80",
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
          <button
            type="button"
            onClick={() => setConceptsOpen((o) => !o)}
            aria-expanded={conceptsOpen}
            className="flex w-full items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted-foreground"
          >
            <span>Concepts</span>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                conceptsOpen && "rotate-180",
              )}
            />
          </button>
          {conceptsOpen && (
            <p className="mt-2 text-sm text-muted-foreground">
              {node.concepts.message}
            </p>
          )}
        </section>
      </CardContent>

      <div className="border-t p-4">
        {isTask ? (
          <Button
            className="w-full bg-indigo-600 hover:bg-indigo-700"
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
    </Card>
  );
}

export default NodeDetailPanel;
