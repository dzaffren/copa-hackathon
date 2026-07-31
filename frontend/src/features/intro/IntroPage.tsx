import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Brain, Quote, Waypoints } from "lucide-react";

// The ambient background motif: a small constellation echoing the app's own
// force-graph (GraphCanvas.tsx) — a glowing primary "task" node connected to
// muted secondary nodes — rather than generic particle-field decoration. Hand-
// placed (not random) for a deliberate, uncluttered composition.
interface MotifNode {
  id: string;
  x: number;
  y: number;
  color: string;
  isTask?: boolean;
}

const NODES: MotifNode[] = [
  { id: "task", x: 56, y: 30, color: "hsl(var(--primary))", isTask: true },
  { id: "a", x: 38, y: 20, color: "#34d399" },
  { id: "b", x: 68, y: 16, color: "#fbbf24" },
  { id: "c", x: 34, y: 40, color: "#fb7185" },
  { id: "d", x: 72, y: 44, color: "#a78bfa" },
  { id: "e", x: 46, y: 58, color: "#2dd4bf" },
  { id: "f", x: 62, y: 62, color: "#94a3b8" },
];

const NODE_BY_ID = Object.fromEntries(NODES.map((n) => [n.id, n]));

// Which edges draw in with an animated stroke (the deliberate motion moment);
// the rest just fade in with the rest of the scene — animating every edge at
// once would read as busy rather than premium.
const EDGES: { from: string; to: string; draw: boolean }[] = [
  { from: "task", to: "a", draw: true },
  { from: "task", to: "c", draw: false },
  { from: "task", to: "d", draw: true },
  { from: "task", to: "f", draw: false },
];

const PROPOSITIONS = [
  { icon: Brain, text: "Institutional memory, made explicit" },
  { icon: Waypoints, text: "Cross-workstream drift detection" },
  { icon: Quote, text: "Verbatim-cited, zero hallucination" },
];

/** True on first mount if the user has asked the OS for reduced motion —
 *  checked once, not reactively, since a live OS-setting change mid-session is
 *  not a case this page needs to handle. */
function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/**
 * The pre-demo splash — a presenter opens this first. A single deliberate
 * motion moment (the ambient node-graph drawing itself in, echoing the
 * product's own graph canvas) rather than scattered particle-field effects,
 * with a staggered entrance for the headline stack. Standalone: mounted as a
 * sibling of the AppShell route in App.tsx, so it renders without the
 * Sidebar/DemoController.
 */
export function IntroPage() {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [edgesDrawn, setEdgesDrawn] = useState(prefersReducedMotion());
  const reduceMotion = useRef(prefersReducedMotion()).current;

  useEffect(() => {
    if (reduceMotion) return;
    // Let the entrance stagger start, then draw the edges in — a beat after
    // the scene appears, not simultaneously with it.
    const id = requestAnimationFrame(() =>
      setTimeout(() => setEdgesDrawn(true), 300),
    );
    return () => cancelAnimationFrame(id);
  }, [reduceMotion]);

  function onMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (reduceMotion) return;
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mx", `${e.clientX - rect.left}px`);
    el.style.setProperty("--my", `${e.clientY - rect.top}px`);
  }

  return (
    <div
      ref={containerRef}
      onMouseMove={onMouseMove}
      className="relative min-h-screen w-full overflow-hidden bg-background"
      style={{ "--mx": "50%", "--my": "35%" } as React.CSSProperties}
    >
      {/* Layer 1 — cursor-tracking spotlight, a soft primary tint that follows
          the mouse. Interactive without being garish on a light canvas. */}
      {!reduceMotion && (
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(600px circle at var(--mx) var(--my), hsl(var(--primary) / 0.06), transparent 60%)",
          }}
        />
      )}

      {/* Layer 2 — the ambient node-graph motif. Curved, low-opacity trails
          rather than straight rigid lines, so it reads as a quiet halo behind
          the headline instead of a technical wireframe competing with it. */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <svg
          className="h-full w-full"
          preserveAspectRatio="none"
          viewBox="0 0 100 100"
        >
          {EDGES.map(({ from, to, draw }) => {
            const a = NODE_BY_ID[from];
            const b = NODE_BY_ID[to];
            const mx = (a.x + b.x) / 2;
            const my = (a.y + b.y) / 2;
            // Perpendicular offset on the midpoint gives the path a gentle
            // bow instead of a dead-straight line.
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const curveX = mx - dy * 0.12;
            const curveY = my + dx * 0.12;
            const d = `M ${a.x} ${a.y} Q ${curveX} ${curveY} ${b.x} ${b.y}`;
            const length = Math.hypot(dx, dy) * 1.15;
            return (
              <path
                key={`${from}-${to}`}
                d={d}
                fill="none"
                stroke="hsl(var(--muted-foreground))"
                strokeOpacity={0.18}
                strokeWidth={0.25}
                strokeLinecap="round"
                style={
                  draw
                    ? {
                        strokeDasharray: length,
                        strokeDashoffset: edgesDrawn ? 0 : length,
                        transition:
                          "stroke-dashoffset 1.8s var(--ease-out-expo)",
                      }
                    : undefined
                }
              />
            );
          })}
        </svg>
        {NODES.map((n) => (
          <span
            key={n.id}
            className={[
              "absolute rounded-full",
              n.isTask
                ? "h-3 w-3 animate-[glowPulse_2.6s_ease-in-out_infinite]"
                : "h-1.5 w-1.5 opacity-50",
              "motion-reduce:animate-none",
            ].join(" ")}
            style={{
              left: `${n.x}%`,
              top: `${n.y}%`,
              transform: "translate(-50%, -50%)",
              backgroundColor: n.color,
            }}
          />
        ))}
      </div>

      {/* Layer 3 — foreground content */}
      <div className="absolute left-6 top-6 z-10 sm:left-8 sm:top-8">
        <div
          className="grid h-9 w-9 place-items-center rounded-lg bg-white/80 shadow-sm ring-1 ring-primary/20 motion-reduce:animate-none"
          style={{
            animation: reduceMotion
              ? undefined
              : "fadeSlideDown 0.4s var(--ease-out-expo) both",
          }}
        >
          <img src="/bnm-logo.png" alt="Bank Negara Malaysia" className="h-6 w-6 object-contain" />
        </div>
      </div>

      <div className="relative z-10 flex min-h-screen w-full flex-col items-center justify-center px-6 text-center">
        <p
          className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground motion-reduce:opacity-100"
          style={{
            animation: reduceMotion
              ? undefined
              : "fadeSlideUp 0.5s 0.2s var(--ease-out-expo) both",
          }}
        >
          COPA Hackathon 2026 · Must-Win 10
        </p>

        <h1
          className="mt-4 font-['Fraunces'] text-5xl font-semibold tracking-tight text-transparent motion-reduce:opacity-100 sm:text-6xl"
          style={{
            backgroundImage:
              "linear-gradient(to right, hsl(var(--foreground)), hsl(var(--primary)))",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            animation: reduceMotion
              ? undefined
              : "fadeSlideUp 0.5s 0.4s var(--ease-out-expo) both",
          }}
        >
          Project SELARAS
        </h1>

        <p
          className="mt-3 max-w-lg text-sm font-medium leading-relaxed text-foreground/70 motion-reduce:opacity-100"
          style={{
            animation: reduceMotion
              ? undefined
              : "fadeSlideUp 0.5s 0.5s var(--ease-out-expo) both",
          }}
        >
          <span className="text-primary">S</span>emantic{" "}
          <span className="text-primary">E</span>ngine for{" "}
          <span className="text-primary">L</span>inkage{" "}
          <span className="text-primary">A</span>nalysis across{" "}
          <span className="text-primary">R</span>egulatory{" "}
          <span className="text-primary">A</span>rtefacts &amp;{" "}
          <span className="text-primary">S</span>tandards
        </p>

        <p
          className="mt-4 max-w-xl text-base leading-relaxed text-muted-foreground motion-reduce:opacity-100"
          style={{
            animation: reduceMotion
              ? undefined
              : "fadeSlideUp 0.5s 0.6s var(--ease-out-expo) both",
          }}
        >
          AI-powered policy consistency for Bank Negara Malaysia.
        </p>

        <div
          className="mt-8 flex flex-wrap items-center justify-center gap-2.5 motion-reduce:opacity-100"
          style={{
            animation: reduceMotion
              ? undefined
              : "fadeSlideUp 0.5s 0.8s var(--ease-out-expo) both",
          }}
        >
          {PROPOSITIONS.map(({ icon: Icon, text }) => (
            <span
              key={text}
              className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3.5 py-1.5 text-sm text-foreground/80 shadow-sm"
            >
              <Icon className="h-3.5 w-3.5 text-primary" />
              {text}
            </span>
          ))}
        </div>

        <button
          type="button"
          onClick={() => navigate("/")}
          className="group relative mt-10 flex items-center gap-2 overflow-hidden rounded-full bg-gradient-to-r from-[#050f2c] via-[#0f2a63] to-[#050f2c] px-8 py-3 font-semibold text-white shadow-lg shadow-blue-950/40 transition-transform duration-200 ease-[cubic-bezier(0.34,1.56,0.64,1)] hover:scale-105 hover:shadow-blue-900/50 active:scale-95 motion-reduce:opacity-100"
          style={{
            animation: reduceMotion
              ? undefined
              : "fadeSlideUp 0.5s 1s var(--ease-out-expo) both",
          }}
        >
          {/* The periodic shine — a diagonal streak that sweeps across every
              5s, parked off-screen the rest of the time. */}
          {!reduceMotion && (
            <span
              aria-hidden
              className="pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-white/40 to-transparent"
              style={{ animation: "buttonShine 5s ease-in-out infinite" }}
            />
          )}
          <span className="relative">Enter Demo</span>
          <ArrowRight className="relative h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export default IntroPage;
