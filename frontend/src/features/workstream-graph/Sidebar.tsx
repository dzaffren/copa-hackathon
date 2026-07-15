import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  Layers,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchWorkstreams } from "@/lib/api";
import type { WorkstreamRole } from "@/lib/types";

const ROLE_BADGE: Record<WorkstreamRole, string> = {
  own: "bg-indigo-100 text-indigo-700",
  review: "bg-amber-100 text-amber-700",
  delivered: "bg-emerald-100 text-emerald-700",
};

function RoleBadge({ role }: { role: WorkstreamRole }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        ROLE_BADGE[role] ?? "bg-gray-100 text-gray-600",
      )}
    >
      {role}
    </span>
  );
}

/**
 * The shared left rail. Lists the drafter's workstreams with role badges, a
 * "+ New workstream" action and an "Institution map" link, and collapses to an
 * icon-only rail. The active workstream is highlighted.
 */
export function Sidebar({
  activeWorkstreamId,
}: {
  activeWorkstreamId?: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const { data: workstreams = [] } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r bg-white transition-[width]",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex items-center justify-between gap-2 border-b px-3 py-4">
        {!collapsed && (
          <span className="truncate text-sm font-bold">Workstream Brain</span>
        )}
        <button
          type="button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setCollapsed((c) => !c)}
          className="rounded p-1 text-gray-500 hover:bg-gray-100"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        <p
          className={cn(
            "px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground",
            collapsed && "sr-only",
          )}
        >
          Workstreams
        </p>
        <ul className="space-y-1">
          {workstreams.map((ws) => (
            <li key={ws.id}>
              <Link
                to={`/workstreams/${ws.id}`}
                title={ws.name}
                aria-current={ws.id === activeWorkstreamId ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2 rounded px-2 py-2 text-sm hover:bg-indigo-50",
                  ws.id === activeWorkstreamId
                    ? "bg-indigo-50 font-semibold text-indigo-700"
                    : "text-gray-700",
                )}
              >
                <Layers className="h-4 w-4 shrink-0" />
                {!collapsed && (
                  <span className="flex min-w-0 flex-1 items-center justify-between gap-2">
                    <span className="truncate">{ws.name}</span>
                    <RoleBadge role={ws.role} />
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>

        <Link
          to="/workstreams/new"
          title="New workstream"
          className="mt-2 flex items-center gap-2 rounded px-2 py-2 text-sm font-semibold text-indigo-600 hover:bg-indigo-50"
        >
          <Plus className="h-4 w-4 shrink-0" />
          {!collapsed && <span>New workstream</span>}
        </Link>
      </nav>

      <div className="border-t p-2">
        <Link
          to="/institution-map"
          title="Institution map"
          className="flex items-center gap-2 rounded px-2 py-2 text-xs text-gray-500 hover:bg-indigo-50 hover:text-indigo-600"
        >
          <Building2 className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Institution map</span>}
        </Link>
      </div>
    </aside>
  );
}

export default Sidebar;
