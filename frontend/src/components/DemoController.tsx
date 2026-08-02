import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  GripVertical,
  Minimize2,
  Play,
} from "lucide-react";

import { cn } from "@/lib/utils";

// The 5-step demo path, in presentation order. Paths must match the routes
// registered in App.tsx exactly, since this navigates by literal pathname.
//
// Runs on open-finance-pd-2026, the live demo workstream — every id below is
// read off its committed fixture (`graph.json` + `findings/`), so the walkthrough
// never lands on an unanalysed pair.
interface DemoStep {
  label: string;
  path: string;
  /** Marks a step that shares its `path` with another. Steps 1 and 2 are the
   *  same screen — the graph, then the analyse action on a selected edge — and
   *  two identical targets would strand the presenter: `activeIndex` is derived
   *  from the URL, so "Next" onto a path already matched would leave the index
   *  where it was and stop advancing. The param disambiguates the two without
   *  the page having to read it (the graph screen keys off `useParams` only). */
  query?: string;
}

const WS = "open-finance-pd-2026";
const TASK = "open-finance-pd-2026-pd";
// The HKMA ↔ ED pair: analysed, and the richest of the three findings files.
const EDGE = "e-hkma_open_api_framework--ed_open_finance_2025";

const DEMO_STEPS: DemoStep[] = [
  { label: "Workstream Graph", path: `/workstreams/${WS}` },
  {
    label: "Analyze Linkage",
    path: `/workstreams/${WS}`,
    query: "demo=analyze",
  },
  { label: "Task Workspace", path: `/workstreams/${WS}/tasks/${TASK}` },
  {
    label: "Review Linkage",
    path: `/workstreams/${WS}/edges/${EDGE}/review`,
  },
  {
    label: "Draft Workspace",
    path: `/workstreams/${WS}/tasks/${TASK}/draft`,
  },
];

/** A step's full navigation target, query string included. */
function stepHref(step: DemoStep): string {
  return step.query ? `${step.path}?${step.query}` : step.path;
}

const STORAGE_KEY = "wsb-demo-controller-minimized";
const POSITION_KEY = "wsb-demo-controller-position";

interface Position {
  left: number;
  top: number;
}

/** Keeps the dragged bar fully on-screen — a position saved from a wider
 *  viewport must not strand it off the edge after a resize. The minimized
 *  pill always returns to its fixed corner, so it never needs this. */
function clampToViewport(pos: Position, rect: DOMRect): Position {
  const maxLeft = Math.max(0, window.innerWidth - rect.width);
  const maxTop = Math.max(0, window.innerHeight - rect.height);
  return {
    left: Math.min(Math.max(pos.left, 0), maxLeft),
    top: Math.min(Math.max(pos.top, 0), maxTop),
  };
}

function readStoredPosition(): Position | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(POSITION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed?.left === "number" && typeof parsed?.top === "number") {
      return parsed;
    }
  } catch {
    // malformed value — fall back to the default corner
  }
  return null;
}

/**
 * Floating presenter control for stepping through the 5-step demo path.
 * Purely a navigation aid — it holds no product state, just pushes routes.
 * Steps 1 and 2 are deliberately the same screen: the graph, then the analyse
 * action taken on it.
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

  // `null` means "use the default bottom-right corner" (the CSS fallback
  // below) — only a drag ever produces a concrete position, so a presenter
  // who never drags the bar sees the exact old behaviour.
  const [position, setPosition] = useState<Position | null>(() =>
    readStoredPosition(),
  );
  const barRef = useRef<HTMLDivElement>(null);
  const dragState = useRef<{
    pointerId: number;
    offsetX: number;
    offsetY: number;
  } | null>(null);

  // Re-clamp a saved position on resize — a bar dragged near an edge on a
  // wide window must not end up stranded off-screen on a narrower one.
  useEffect(() => {
    function onResize() {
      const el = barRef.current;
      if (!el) return;
      setPosition((prev) => {
        if (!prev) return prev;
        const next = clampToViewport(prev, el.getBoundingClientRect());
        window.localStorage.setItem(POSITION_KEY, JSON.stringify(next));
        return next;
      });
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  function onDragPointerDown(e: React.PointerEvent<HTMLDivElement>) {
    // Only the handle initiates a drag — every other control in the bar
    // (step chips, prev/next, minimize) must keep its own click behaviour.
    if (e.button !== 0) return;
    const el = barRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    dragState.current = {
      pointerId: e.pointerId,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top,
    };
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function onDragPointerMove(e: React.PointerEvent<HTMLDivElement>) {
    const drag = dragState.current;
    const el = barRef.current;
    if (!drag || drag.pointerId !== e.pointerId || !el) return;
    const next = clampToViewport(
      { left: e.clientX - drag.offsetX, top: e.clientY - drag.offsetY },
      el.getBoundingClientRect(),
    );
    setPosition(next);
  }

  function endDrag(e: React.PointerEvent<HTMLDivElement>) {
    if (dragState.current?.pointerId !== e.pointerId) return;
    dragState.current = null;
    setPosition((prev) => {
      if (prev) {
        window.localStorage.setItem(POSITION_KEY, JSON.stringify(prev));
      }
      return prev;
    });
  }

  // The active step matches the longest path prefix, so a sub-route (e.g. a
  // different edge's review screen) still highlights the closest demo step
  // rather than showing no selection at all.
  //
  // A step carrying a `query` only matches when that query is present, and it
  // wins over the bare-path step on the same URL — otherwise steps 1 and 2
  // (same screen) would both resolve to 1 and the presenter could never leave
  // it. The task and draft steps are prefix-compared in declaration order, so
  // `/tasks/x/draft` must be checked against the longer path first; sorting by
  // path length handles that regardless of the order above.
  const activeIndex = useMemo(() => {
    let best = -1;
    let bestScore = -1;
    DEMO_STEPS.forEach((step, i) => {
      const isRoot = step.path === "/";
      const pathMatches = isRoot
        ? location.pathname === "/"
        : location.pathname === step.path ||
          location.pathname.startsWith(`${step.path}/`);
      if (!pathMatches) return;
      if (step.query && !location.search.includes(step.query)) return;
      // A query-qualified match is strictly more specific than a bare path of
      // the same length, so it outranks it.
      const score = step.path.length * 2 + (step.query ? 1 : 0);
      if (score > bestScore) {
        best = i;
        bestScore = score;
      }
    });
    return best;
  }, [location.pathname, location.search]);

  function goTo(index: number) {
    const clamped = Math.max(0, Math.min(DEMO_STEPS.length - 1, index));
    navigate(stepHref(DEMO_STEPS[clamped]));
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
        className="fixed bottom-4 right-4 z-50 grid h-11 w-11 place-items-center rounded-full border border-border bg-card text-primary shadow-md transition hover:bg-accent"
      >
        <Play className="h-4 w-4" />
      </button>
    );
  }

  // Dragged position overrides the default bottom-right corner. `right`/
  // `bottom` are dropped once a `left`/`top` is set so the two positioning
  // schemes never fight each other.
  const positionStyle: React.CSSProperties = position
    ? { left: position.left, top: position.top, right: "auto", bottom: "auto" }
    : {};

  return (
    // `pointer-events-none` on the bar with `pointer-events-auto` on its
    // controls: as a bottom-centred fixed element it otherwise swallows clicks
    // meant for whatever sits beneath it (it was intercepting the new-workstream
    // form's submit button). Only the toolbar's own buttons are clickable now.
    <div
      ref={barRef}
      role="toolbar"
      aria-label="Demo walkthrough"
      style={positionStyle}
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-2xl border border-border bg-card px-3 py-2 text-sm shadow-md [&_button]:pointer-events-auto [&_select]:pointer-events-auto"
    >
      <div
        role="button"
        tabIndex={-1}
        aria-label="Drag to move demo walkthrough panel"
        onPointerDown={onDragPointerDown}
        onPointerMove={onDragPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        className="pointer-events-auto grid h-8 w-4 shrink-0 cursor-grab place-items-center text-muted-foreground/60 touch-none active:cursor-grabbing"
      >
        <GripVertical className="h-4 w-4" />
      </div>

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
            <li key={stepHref(step)}>
              <button
                type="button"
                title={step.label}
                aria-label={`Step ${i + 1}: ${step.label}`}
                aria-current={active ? "step" : undefined}
                onClick={() => goTo(i)}
                className={cn(
                  "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition",
                  active
                    ? "border-primary/50 bg-primary/15 text-primary"
                    : "border-transparent text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "grid h-4 w-4 shrink-0 place-items-center rounded-full text-[10px] font-bold",
                    active
                      ? "bg-primary text-primary-foreground"
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
