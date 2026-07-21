import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Brain,
  Building2,
  ClipboardCheck,
  Layers,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Radar,
  Sun,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchWorkstreams } from "@/lib/api";
import { useTheme } from "@/lib/theme";
import { Skeleton } from "@/components/ui/skeleton";
import type { WorkstreamRole } from "@/lib/types";

// A coloured status dot per workstream role — own (active draft), review
// (someone else's, we comment), delivered (published).
const ROLE_DOT: Record<WorkstreamRole, string> = {
  own: "bg-cyan-400",
  review: "bg-amber-400",
  delivered: "bg-emerald-400",
};

const ROLE_LABEL: Record<WorkstreamRole, string> = {
  own: "Drafting",
  review: "Reviewing",
  delivered: "Delivered",
};

/**
 * The shared left rail, persistent across every screen. Lists the drafter's
 * workstreams with role status dots, a "+ New workstream" action and an
 * "Institution map" link, and collapses to an icon-only rail. The active
 * workstream is highlighted with a left accent bar.
 */
export function Sidebar({
  activeWorkstreamId,
}: {
  activeWorkstreamId?: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { pathname } = useLocation();
  const intelActive = pathname.startsWith("/intelligence");
  const queueActive = pathname.startsWith("/review-queue");
  const {
    data: workstreams = [],
    isLoading,
  } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-border/60 bg-card/40 backdrop-blur-xl transition-[width] duration-200",
        collapsed ? "w-16" : "w-64",
      )}
    >
      {/* Brand + collapse toggle */}
      <div className="flex items-center justify-between gap-2 border-b border-border/60 px-3 py-4">
        {!collapsed && (
          <Link to="/" className="flex min-w-0 items-center gap-2">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-cyan-500/30 to-indigo-500/30 ring-1 ring-cyan-400/40">
              <Brain className="h-4 w-4 text-cyan-300" />
            </span>
            <span className="flex min-w-0 flex-col leading-tight">
              <span className="truncate text-sm font-bold">Workstream Brain</span>
              <span className="truncate text-[10px] text-muted-foreground">
                Policy drafting intelligence
              </span>
            </span>
          </Link>
        )}
        <button
          type="button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setCollapsed((c) => !c)}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Workstream list */}
      <nav className="flex-1 overflow-y-auto p-2">
        {/* Cross-Workstream Intelligence — the primary product surface, kept
            above the workstream list so the early-warning view is one click
            from anywhere. */}
        <Link
          to="/intelligence"
          title="Cross-Workstream Intelligence"
          aria-current={intelActive ? "page" : undefined}
          className={cn(
            "group relative mb-2 flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-semibold transition-colors",
            intelActive
              ? "bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-400/30"
              : "text-foreground/80 hover:bg-accent/40 hover:text-foreground",
          )}
        >
          <Radar className="h-4 w-4 shrink-0 text-cyan-300" />
          {!collapsed && <span>Cross-Workstream Intel</span>}
        </Link>

        {/* Review Queue — the maker-checker backlog for detected linkages. */}
        <Link
          to="/review-queue"
          title="Review Queue"
          aria-current={queueActive ? "page" : undefined}
          className={cn(
            "group relative mb-2 flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-semibold transition-colors",
            queueActive
              ? "bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-400/30"
              : "text-foreground/80 hover:bg-accent/40 hover:text-foreground",
          )}
        >
          <ClipboardCheck className="h-4 w-4 shrink-0 text-cyan-300" />
          {!collapsed && <span>Review Queue</span>}
        </Link>

        <p
          className={cn(
            "px-2 pb-1.5 pt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground",
            collapsed && "sr-only",
          )}
        >
          Workstreams
        </p>

        {isLoading && !collapsed ? (
          <div className="space-y-1.5 px-1">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (
          <ul className="space-y-1">
            {workstreams.map((ws) => {
              const active = ws.id === activeWorkstreamId;
              return (
                <li key={ws.id}>
                  <Link
                    to={`/workstreams/${ws.id}`}
                    title={`${ws.name} · ${ROLE_LABEL[ws.role] ?? ws.role}`}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors",
                      active
                        ? "bg-accent/70 font-semibold text-foreground"
                        : "text-foreground/70 hover:bg-accent/40 hover:text-foreground",
                    )}
                  >
                    {active && (
                      <span className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-cyan-400" />
                    )}
                    <span
                      className={cn(
                        "h-2 w-2 shrink-0 rounded-full ring-2 ring-background",
                        ROLE_DOT[ws.role] ?? "bg-slate-400",
                      )}
                    />
                    {collapsed ? (
                      <Layers className="h-4 w-4 shrink-0 text-muted-foreground" />
                    ) : (
                      <span className="truncate">{ws.name}</span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        )}

        <Link
          to="/workstreams/new"
          title="New workstream"
          className="mt-2 flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium text-cyan-300 transition-colors hover:bg-accent/40"
        >
          <Plus className="h-4 w-4 shrink-0" />
          {!collapsed && <span>New workstream</span>}
        </Link>
      </nav>

      {/* Institution map + theme toggle */}
      <div className="space-y-1 border-t border-border/60 p-2">
        <Link
          to="/institution-map"
          title="Institution map"
          className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-foreground/70 transition-colors hover:bg-accent/40 hover:text-foreground"
        >
          <Building2 className="h-4 w-4 shrink-0 text-violet-300" />
          {!collapsed && <span>Institution map</span>}
        </Link>
        <button
          type="button"
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          aria-label={
            theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
          }
          className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent/40 hover:text-foreground"
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4 shrink-0" />
          ) : (
            <Moon className="h-4 w-4 shrink-0" />
          )}
          {!collapsed && (
            <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
          )}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
