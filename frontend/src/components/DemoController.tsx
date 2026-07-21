import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Minimize2, Play } from "lucide-react";

import { cn } from "@/lib/utils";

// The 6-step demo path, in presentation order. Paths must match the routes
// registered in App.tsx exactly, since this navigates by literal pathname.
interface DemoStep {
  label: string;
  path: string;
}

const DEMO_STEPS: DemoStep[] = [
  { label: "Dashboard", path: "/" },
  { label: "Workstream Graph", path: "/workstreams/opres-v2" },
  {
    label: "Review Linkages",
    path: "/workstreams/opres-v2/edges/e-opres_v0_3--bcbs_opres_2021/review",
  },
  { label: "Task Screen", path: "/workstreams/opres-v2/tasks/opres-pd-v0-3" },
  {
    label: "Drafting Workspace",
    path: "/workstreams/opres-v2/tasks/opres-pd-v0-3/draft",
  },
  { label: "Institution Map", path: "/institution-map" },
];

const STORAGE_KEY = "wsb-demo-controller-minimized";

/**
 * Floating presenter control for stepping through the 6-screen demo path.
 * Purely a navigation aid — it holds no product state, just pushes routes.
 *
 * The active step is derived from the URL (not local state) so it stays in
 * sync when the presenter clicks through the app manually instead of using
 * the controller, and survives a page refresh.
 */
export function DemoController() {
  const navigate = useNavigate();
  const location = useLocation();

  const [minimized, setMinimized] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem(STORAGE_KEY) === "1";
  });

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, minimized ? "1" : "0");
  }, [minimized]);

  // The active step matches the longest path prefix, so a sub-route (e.g. a
  // different edge's review screen) still highlights the closest demo step
  // rather than showing no selection at all.
  const activeIndex = useMemo(() => {
    let best = -1;
    let bestLen = -1;
    DEMO_STEPS.forEach((step, i) => {
      const isRoot = step.path === "/";
      const matches = isRoot
        ? location.pathname === "/"
        : location.pathname === step.path ||
          location.pathname.startsWith(`${step.path}/`);
      if (matches && step.path.length > bestLen) {
        best = i;
        bestLen = step.path.length;
      }
    });
    return best;
  }, [location.pathname]);

  function goTo(index: number) {
    const clamped = Math.max(0, Math.min(DEMO_STEPS.length - 1, index));
    navigate(DEMO_STEPS[clamped].path);
  }

  function goPrev() {
    goTo((activeIndex === -1 ? 0 : activeIndex) - 1);
  }
  function goNext() {
    goTo((activeIndex === -1 ? -1 : activeIndex) + 1);
  }

  // Alt+Left / Alt+Right (or Shift+Left / Shift+Right) advance the demo from
  // anywhere in the app, so a presenter never has to reach for the mouse.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!e.altKey && !e.shiftKey) return;
      if (e.key === "ArrowRight") {
        e.preventDefault();
        goNext();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        goPrev();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex]);

  if (minimized) {
    return (
      <button
        type="button"
        aria-label="Expand demo walkthrough panel"
        onClick={() => setMinimized(false)}
        className="fixed bottom-4 left-1/2 z-50 grid h-11 w-11 -translate-x-1/2 place-items-center rounded-full border border-border/60 bg-card/80 text-cyan-300 shadow-lg shadow-black/30 backdrop-blur-xl transition hover:bg-accent"
      >
        <Play className="h-4 w-4" />
      </button>
    );
  }

  return (
    <div
      role="toolbar"
      aria-label="Demo walkthrough"
      className="fixed bottom-4 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-2xl border border-border/60 bg-card/80 px-3 py-2 text-sm shadow-lg shadow-black/30 backdrop-blur-xl"
    >
      <button
        type="button"
        aria-label="Previous step"
        onClick={goPrev}
        disabled={activeIndex <= 0}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      <ol className="flex items-center gap-1.5">
        {DEMO_STEPS.map((step, i) => {
          const active = i === activeIndex;
          return (
            <li key={step.path}>
              <button
                type="button"
                title={step.label}
                aria-label={`Step ${i + 1}: ${step.label}`}
                aria-current={active ? "step" : undefined}
                onClick={() => goTo(i)}
                className={cn(
                  "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition",
                  active
                    ? "border-cyan-400/50 bg-cyan-500/15 text-cyan-300"
                    : "border-transparent text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "grid h-4 w-4 shrink-0 place-items-center rounded-full text-[10px] font-bold",
                    active
                      ? "bg-cyan-400 text-slate-950"
                      : "bg-accent text-muted-foreground",
                  )}
                >
                  {i + 1}
                </span>
                <span className="hidden sm:inline">{step.label}</span>
              </button>
            </li>
          );
        })}
      </ol>

      <button
        type="button"
        aria-label="Next step"
        onClick={goNext}
        disabled={activeIndex >= DEMO_STEPS.length - 1}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
      >
        <ChevronRight className="h-4 w-4" />
      </button>

      <div className="mx-1 h-5 w-px shrink-0 bg-border/60" />

      <button
        type="button"
        aria-label="Minimize demo walkthrough panel"
        onClick={() => setMinimized(true)}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition hover:bg-accent hover:text-foreground"
      >
        <Minimize2 className="h-4 w-4" />
      </button>
    </div>
  );
}

export default DemoController;
