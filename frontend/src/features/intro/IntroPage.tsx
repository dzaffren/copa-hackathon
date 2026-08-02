import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  ChevronDown,
  ChevronRight,
  Building2,
  AlertTriangle,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

const SLIDE_COUNT = 3;
const FONT_FAMILY = "'DM Sans', system-ui, sans-serif";
const FONT_LINK_ID = "intro-dm-sans-font";

/** "Enter Workspace" lands on the live demo workstream rather than the home
 *  screen — the graph is what the pitch opens on. See CLAUDE.md: build and demo
 *  against open-finance-pd-2026. */
const DEMO_WORKSTREAM_PATH = "/workstreams/open-finance-pd-2026";

/** True on first mount if the user has asked the OS for reduced motion —
 *  checked once, not reactively. */
function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/** Injects the DM Sans stylesheet link once per mount; removes it on unmount. */
function useIntroFont(): void {
  useEffect(() => {
    if (document.getElementById(FONT_LINK_ID)) return;
    const link = document.createElement("link");
    link.id = FONT_LINK_ID;
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&display=swap";
    document.head.appendChild(link);
    return () => {
      document.getElementById(FONT_LINK_ID)?.remove();
    };
  }, []);
}

function AmbientBackground({ reduceMotion }: { reduceMotion: boolean }) {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      <div
        className="absolute -left-24 -top-24 h-[420px] w-[420px] rounded-full"
        style={{
          backgroundColor: "hsl(var(--primary))",
          opacity: 0.06,
          filter: "blur(80px)",
          animation: reduceMotion
            ? undefined
            : "blobFloat 16s ease-in-out infinite",
        }}
      />
      <div
        className="absolute -bottom-32 -right-24 h-[480px] w-[480px] rounded-full"
        style={{
          backgroundColor: "hsl(var(--primary))",
          opacity: 0.07,
          filter: "blur(80px)",
          animation: reduceMotion
            ? undefined
            : "blobFloat 20s ease-in-out infinite reverse",
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          opacity: 0.4,
        }}
      />
    </div>
  );
}

interface DotsProps {
  active: number;
  onSelect: (index: number) => void;
}

function Dots({ active, onSelect }: DotsProps) {
  return (
    <div className="fixed bottom-8 left-1/2 z-20 flex -translate-x-1/2 gap-2">
      {Array.from({ length: SLIDE_COUNT }, (_, i) => (
        <button
          key={i}
          type="button"
          aria-label={`Go to slide ${i + 1}`}
          aria-current={active === i}
          onClick={() => onSelect(i)}
          className="h-2 rounded-full transition-all duration-300"
          style={{
            width: active === i ? 24 : 8,
            backgroundColor:
              active === i ? "hsl(var(--primary))" : "hsl(var(--border))",
          }}
        />
      ))}
    </div>
  );
}

interface OverlineProps {
  children: ReactNode;
  delayMs: number;
  reduceMotion: boolean;
}

function Overline({ children, delayMs, reduceMotion }: OverlineProps) {
  return (
    <p
      className="text-sm font-semibold uppercase tracking-[0.14em] motion-reduce:opacity-100"
      style={{
        color: "hsl(var(--primary))",
        fontFamily: FONT_FAMILY,
        animation: reduceMotion
          ? undefined
          : `fadeSlideUp 0.5s ${delayMs}ms var(--ease-out-expo) both`,
      }}
    >
      {children}
    </p>
  );
}

interface RoadmapBadgeProps {
  delayMs: number;
  reduceMotion: boolean;
}

/** The MW10 programme badge. Deliberately loud — solid primary fill rather than
 *  a tinted pill, because this is the one label the audience must not miss. */
function RoadmapBadge({ delayMs, reduceMotion }: RoadmapBadgeProps) {
  return (
    <span
      className="inline-flex items-center rounded-full px-6 py-2.5 text-base font-bold uppercase tracking-[0.1em] motion-reduce:opacity-100"
      style={{
        backgroundColor: "hsl(var(--primary))",
        color: "hsl(var(--primary-foreground))",
        fontFamily: FONT_FAMILY,
        boxShadow: "0 6px 20px -6px hsl(var(--primary) / 0.55)",
        animation: reduceMotion
          ? undefined
          : `fadeSlideUp 0.5s ${delayMs}ms var(--ease-out-expo) both`,
      }}
    >
      MW10 - AI Roadmap
    </span>
  );
}

/** Slide-3 backdrop geometry, in the 1200×800 viewBox the SVG scales from.
 *  Hand-placed rather than generated: the two clusters sit left and right of the
 *  centred headline, bridged across the top and bottom, so the graph reads as a
 *  network without any node landing behind the words. */
const NET_NODES: { x: number; y: number; r: number }[] = [
  { x: 112, y: 178, r: 5 }, // 0  left cluster
  { x: 214, y: 332, r: 7 }, // 1
  { x: 88, y: 468, r: 4 }, // 2
  { x: 246, y: 604, r: 6 }, // 3
  { x: 382, y: 168, r: 4 }, // 4
  { x: 330, y: 470, r: 9 }, // 5  left hub
  { x: 1088, y: 196, r: 5 }, // 6  right cluster
  { x: 982, y: 346, r: 7 }, // 7
  { x: 1112, y: 502, r: 4 }, // 8
  { x: 948, y: 638, r: 6 }, // 9
  { x: 818, y: 158, r: 4 }, // 10
  { x: 872, y: 468, r: 9 }, // 11 right hub
  { x: 600, y: 86, r: 6 }, // 12 top bridge
  { x: 600, y: 726, r: 6 }, // 13 bottom bridge
  { x: 452, y: 662, r: 4 }, // 14
  { x: 742, y: 628, r: 5 }, // 15
];

/** Edges as index pairs into NET_NODES. The four marked `flow` carry a
 *  travelling pulse — enough to read as live traffic, few enough to stay calm. */
const NET_EDGES: { a: number; b: number; flow?: boolean }[] = [
  { a: 0, b: 1 },
  { a: 1, b: 2 },
  { a: 1, b: 5, flow: true },
  { a: 2, b: 3 },
  { a: 3, b: 5 },
  { a: 4, b: 1 },
  { a: 4, b: 12 },
  { a: 5, b: 14 },
  { a: 12, b: 10 },
  { a: 10, b: 6 },
  { a: 6, b: 7 },
  { a: 7, b: 11, flow: true },
  { a: 7, b: 8 },
  { a: 8, b: 9 },
  { a: 9, b: 11 },
  { a: 11, b: 15 },
  { a: 14, b: 13 },
  { a: 13, b: 15 },
  { a: 5, b: 12, flow: true },
  { a: 11, b: 12 },
  { a: 5, b: 13 },
  { a: 13, b: 11, flow: true },
];

/** Slide-3 backdrop: a slowly drifting network graph. Replaces the earlier
 *  concentric rings — a graph is what SELARAS actually builds, so the backdrop
 *  states the product instead of decorating it. Purely presentational, so it is
 *  `aria-hidden` and never interactive. Under reduced motion the same graph
 *  renders without drift, flow pulses, or edge draw-in. */
function NetworkBackdrop({ reduceMotion }: { reduceMotion: boolean }) {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      <svg
        viewBox="0 0 1200 800"
        preserveAspectRatio="xMidYMid slice"
        className="h-full w-full"
      >
        <defs>
          {/* Dims the middle of the canvas so the headline never competes with
              an edge crossing behind it, while the periphery stays legible. */}
          <radialGradient id="net-fade" cx="50%" cy="50%" r="68%">
            <stop offset="0%" stopColor="#1a1a1a" />
            <stop offset="30%" stopColor="#8f8f8f" />
            <stop offset="70%" stopColor="#fff" />
            <stop offset="100%" stopColor="#fff" />
          </radialGradient>
          <mask id="net-mask">
            <rect width="1200" height="800" fill="url(#net-fade)" />
          </mask>
          <radialGradient id="net-node" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="1" />
            <stop
              offset="100%"
              stopColor="hsl(var(--primary))"
              stopOpacity="0.7"
            />
          </radialGradient>
        </defs>

        <g mask="url(#net-mask)">
          {NET_EDGES.map((e, i) => {
            const a = NET_NODES[e.a];
            const b = NET_NODES[e.b];
            const id = `net-edge-${i}`;
            return (
              <g key={id}>
                <line
                  id={id}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke="hsl(var(--primary))"
                  strokeWidth={1.4}
                  strokeOpacity={0.55}
                  style={
                    reduceMotion
                      ? undefined
                      : {
                          // Draw each edge in, staggered around the graph.
                          strokeDasharray: 620,
                          animation: `netDraw 1.5s ${300 + i * 55}ms ease-out both`,
                        }
                  }
                />
                {!reduceMotion && e.flow && (
                  <circle r={2.6} fill="hsl(var(--primary))" opacity={0.75}>
                    <animateMotion
                      dur={`${4.5 + (i % 3) * 1.4}s`}
                      begin={`${i * 0.7}s`}
                      repeatCount="indefinite"
                      rotate="auto"
                      keyPoints="0;1"
                      keyTimes="0;1"
                      calcMode="linear"
                    >
                      <mpath href={`#${id}`} />
                    </animateMotion>
                  </circle>
                )}
              </g>
            );
          })}

          {NET_NODES.map((n, i) => (
            <g
              key={`net-node-${i}`}
              style={
                reduceMotion
                  ? undefined
                  : {
                      transformBox: "fill-box",
                      transformOrigin: "center",
                      animation: `netDrift ${11 + (i % 5) * 2.5}s ${i * 0.45}s ease-in-out infinite`,
                    }
              }
            >
              {/* A soft halo on the two hubs only — the graph has one focal
                  weight per side rather than sixteen competing glows. */}
              {n.r >= 9 && (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={n.r * 3.4}
                  fill="hsl(var(--primary))"
                  opacity={0.07}
                  style={
                    reduceMotion
                      ? undefined
                      : {
                          transformBox: "fill-box",
                          transformOrigin: "center",
                          animation: `netHalo 5.5s ${i * 0.9}s ease-in-out infinite`,
                        }
                  }
                />
              )}
              <circle cx={n.x} cy={n.y} r={n.r} fill="url(#net-node)" />
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

interface SlidePanelProps {
  index: number;
  activeSlide: number;
  reduceMotion: boolean;
  children: ReactNode;
}

/** One full-viewport slide. In motion mode all three are always mounted and
 *  stacked absolutely; only the active one is opaque/interactive, and a
 *  hidden panel rests above (translateY -20px) or below (translateY 24px)
 *  the viewport depending on whether it is behind or ahead of the active
 *  index, so switching always reads as a directional enter/exit rather than
 *  a generic cross-fade. In reduced-motion mode every slide renders in
 *  normal flow instead, so the page is a static, scrollable stack. */
function SlidePanel({
  index,
  activeSlide,
  reduceMotion,
  children,
}: SlidePanelProps) {
  if (reduceMotion) {
    return (
      <section className="relative z-10 flex min-h-screen w-full flex-col items-center justify-center px-6 py-24">
        {children}
      </section>
    );
  }

  const isActive = index === activeSlide;
  const isPast = index < activeSlide;

  return (
    <section
      aria-hidden={!isActive}
      className="absolute inset-0 z-10 flex flex-col items-center justify-center px-6 transition-all duration-500"
      style={{
        opacity: isActive ? 1 : 0,
        transform: isActive
          ? "translateY(0)"
          : isPast
            ? "translateY(-20px)"
            : "translateY(24px)",
        pointerEvents: isActive ? "auto" : "none",
      }}
    >
      {children}
    </section>
  );
}

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: ReactNode;
  delayMs: number;
  active: boolean;
  reduceMotion: boolean;
}

/** A slide-2 capability card. `active` gates the animation prop between
 *  `undefined` and a fadeSlideUp string, so the entrance stagger replays
 *  every time slide 2 becomes the active slide, not just on first mount. */
function FeatureCard({
  icon: Icon,
  title,
  description,
  delayMs,
  active,
  reduceMotion,
}: FeatureCardProps) {
  return (
    <div
      className="flex h-full w-full max-w-sm flex-col overflow-hidden rounded-xl motion-reduce:opacity-100"
      style={{
        backgroundColor: "hsl(var(--card))",
        border: "1px solid hsl(var(--border))",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
        animation:
          reduceMotion || !active
            ? undefined
            : `fadeSlideUp 0.5s ${delayMs}ms var(--ease-out-expo) both`,
      }}
    >
      <div
        className="h-[3px] w-full flex-shrink-0"
        style={{ backgroundColor: "hsl(var(--primary))" }}
      />
      <div className="flex flex-1 flex-col p-6">
        <Icon
          className="h-8 w-8 flex-shrink-0"
          style={{ color: "hsl(var(--primary))" }}
        />
        <h3
          className="mt-4 flex-shrink-0 text-2xl font-bold"
          style={{ color: "hsl(var(--foreground))", fontFamily: FONT_FAMILY }}
        >
          {title}
        </h3>
        {/* Body copy uses --foreground, not --muted-foreground: these cards get
            read from across a room during the pitch, so grey-on-white loses. */}
        <div
          className="mt-3 flex-1 text-base leading-relaxed"
          style={{
            color: "hsl(var(--foreground))",
            fontFamily: FONT_FAMILY,
          }}
        >
          {description}
        </div>
      </div>
    </div>
  );
}

/** The pain half of a problem/impact pair. Red carries the meaning here, so it
 *  is also bolded: colour alone would not survive a projector or a colour-blind
 *  viewer. Deliberately darker than `--destructive` (#ef4444), which only
 *  reaches ~3.7:1 on white and greys out under projection. */
function Pain({ children }: { children: ReactNode }) {
  return (
    <strong className="font-bold" style={{ color: "#b91c1c" }}>
      {children}
    </strong>
  );
}

/** The resolved half of a problem/impact pair. Emerald rather than the theme's
 *  royal-blue primary, so "fixed" never reads as "just another accent". */
function Gain({ children }: { children: ReactNode }) {
  return (
    <strong className="font-bold" style={{ color: "#15803d" }}>
      {children}
    </strong>
  );
}

const SIP_CARDS: { icon: LucideIcon; title: string; description: ReactNode }[] =
  [
    {
      icon: Building2,
      title: "Situation",
      description: (
        <p>
          BNM&rsquo;s credibility as a regulator rests on being{" "}
          <strong
            className="font-bold"
            style={{ color: "hsl(var(--primary))" }}
          >
            internally consistent
          </strong>{" "}
          with its own body of policy and{" "}
          <strong
            className="font-bold"
            style={{ color: "hsl(var(--primary))" }}
          >
            externally aligned
          </strong>{" "}
          with international standards.
        </p>
      ),
    },
    {
      icon: AlertTriangle,
      title: "Problem Statements",
      description: (
        <ul className="list-disc space-y-1.5 pl-4 text-left">
          <li>
            <Pain>Manual assessment</Pain> of overlapping areas of concern with
            other departments
          </li>
          <li>
            <Pain>Manual benchmarking</Pain> of BCBS and other
            jurisdictions&rsquo; policies
          </li>
          <li>
            Drafters spend <Pain>disproportionate time on routine tasks</Pain>{" "}
            over higher-value work
          </li>
          <li>
            <Pain>Institutional expertise takes years to build</Pain> and stays
            with individual drafters
          </li>
        </ul>
      ),
    },
    {
      icon: TrendingUp,
      title: "Impact",
      description: (
        <ul className="list-disc space-y-1.5 pl-4 text-left">
          <li>
            <Gain>Automatic detection</Gain> of overlaps with other departments
          </li>
          <li>
            <Gain>Optimised opportunity-gap analysis</Gain> against established
            practices
          </li>
          <li>
            Drafters&rsquo; time reallocated to{" "}
            <Gain>higher-value review and scoping</Gain>
          </li>
          <li>
            <Gain>Institutional expertise</Gain> decoupled from individuals,{" "}
            <Gain>embedded into the system</Gain>
          </li>
        </ul>
      ),
    },
  ];

/**
 * The pre-demo splash for Project Selaras: a 3-slide, dot-navigated
 * presentation. Standalone — mounted as a sibling of the AppShell route, so
 * it renders without the Sidebar/DemoController.
 */
export function IntroPage() {
  const navigate = useNavigate();
  const [reduceMotion] = useState(prefersReducedMotion);
  const [activeSlide, setActiveSlide] = useState(0);
  useIntroFont();

  function goToSlide(index: number) {
    setActiveSlide(Math.max(0, Math.min(SLIDE_COUNT - 1, index)));
  }

  useEffect(() => {
    if (reduceMotion) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "ArrowRight") {
        setActiveSlide((s) => Math.min(SLIDE_COUNT - 1, s + 1));
      }
      if (e.key === "ArrowLeft") {
        setActiveSlide((s) => Math.max(0, s - 1));
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [reduceMotion]);

  const wrapperClassName = reduceMotion
    ? "relative w-full bg-background"
    : "relative h-screen w-full overflow-hidden bg-background";

  return (
    <div className={wrapperClassName} style={{ fontFamily: FONT_FAMILY }}>
      <AmbientBackground reduceMotion={reduceMotion} />

      <SlidePanel
        index={0}
        activeSlide={activeSlide}
        reduceMotion={reduceMotion}
      >
        <div className="mx-auto flex max-w-5xl flex-col items-center text-center">
          <Overline delayMs={0} reduceMotion={reduceMotion}>
            COPA Hackathon 2026
          </Overline>
          <h1
            className="mt-6 font-bold tracking-tight text-transparent motion-reduce:opacity-100"
            style={{
              /* Must never wrap: "Project SELARAS" is the brand lockup, so the
                 size is viewport-relative and the line is pinned with nowrap
                 rather than left to the container width. */
              fontSize: "clamp(30px, 7.2vw, 96px)",
              whiteSpace: "nowrap",
              letterSpacing: "-0.025em",
              lineHeight: 1.05,
              backgroundImage:
                "linear-gradient(to right, hsl(var(--foreground)), hsl(var(--primary)))",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 100ms var(--ease-out-expo) both",
            }}
          >
            Project SELARAS
          </h1>
          <div className="mt-7">
            <RoadmapBadge delayMs={150} reduceMotion={reduceMotion} />
          </div>
          <p
            className="mx-auto mt-7 max-w-2xl text-xl leading-relaxed motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--foreground))",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 200ms var(--ease-out-expo) both",
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
            className="mt-5 text-lg font-semibold motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--foreground))",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 250ms var(--ease-out-expo) both",
            }}
          >
            by Team Copang
          </p>
        </div>

        {!reduceMotion && (
          <ChevronDown
            aria-hidden
            className="absolute bottom-24 h-5 w-5"
            style={{
              color: "hsl(var(--muted-foreground))",
              animation: "floatUp 2.4s ease-in-out infinite",
            }}
          />
        )}

        {!reduceMotion && (
          <button
            type="button"
            onClick={() => goToSlide(1)}
            className="absolute bottom-8 right-8 flex items-center gap-1.5 text-base font-semibold transition-colors hover:text-primary"
            style={{ color: "hsl(var(--foreground))" }}
          >
            Next <ChevronRight className="h-5 w-5" />
          </button>
        )}
      </SlidePanel>

      <SlidePanel
        index={1}
        activeSlide={activeSlide}
        reduceMotion={reduceMotion}
      >
        <div className="mx-auto flex max-w-5xl flex-col items-center text-center">
          <h2
            className="font-bold tracking-tight text-transparent motion-reduce:opacity-100"
            style={{
              fontSize: "clamp(44px, 5.5vw, 68px)",
              letterSpacing: "-0.025em",
              lineHeight: 1.05,
              backgroundImage:
                "linear-gradient(to right, hsl(var(--foreground)), hsl(var(--primary)))",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 100ms var(--ease-out-expo) both",
            }}
          >
            About Project SELARAS
          </h2>
          <div className="mt-6">
            <RoadmapBadge delayMs={150} reduceMotion={reduceMotion} />
          </div>
          <div className="mt-12 flex w-full flex-col items-center gap-6 sm:flex-row sm:items-stretch sm:justify-center">
            {SIP_CARDS.map((card, i) => (
              <div key={card.title} className="flex items-stretch gap-4">
                <FeatureCard
                  icon={card.icon}
                  title={card.title}
                  description={card.description}
                  delayMs={i * 100}
                  active={activeSlide === 1}
                  reduceMotion={reduceMotion}
                />
                {i < SIP_CARDS.length - 1 && (
                  <ChevronRight
                    aria-hidden
                    className="hidden h-6 w-6 flex-shrink-0 self-center sm:block"
                    style={{ color: "hsl(var(--muted-foreground))" }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {!reduceMotion && (
          <button
            type="button"
            onClick={() => goToSlide(2)}
            className="absolute bottom-8 right-8 flex items-center gap-1.5 text-base font-semibold transition-colors hover:text-primary"
            style={{ color: "hsl(var(--foreground))" }}
          >
            Next <ChevronRight className="h-5 w-5" />
          </button>
        )}
      </SlidePanel>

      <SlidePanel
        index={2}
        activeSlide={activeSlide}
        reduceMotion={reduceMotion}
      >
        <NetworkBackdrop reduceMotion={reduceMotion} />

        <div className="relative mx-auto flex max-w-2xl flex-col items-center text-center">
          <h2
            className="font-bold tracking-tight text-transparent motion-reduce:opacity-100"
            style={{
              fontSize: "clamp(48px, 6vw, 76px)",
              letterSpacing: "-0.025em",
              lineHeight: 1.05,
              backgroundImage:
                "linear-gradient(to right, hsl(var(--foreground)), hsl(var(--primary)))",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 0ms var(--ease-out-expo) both",
            }}
          >
            Start where policy meets intelligence.
          </h2>
          <button
            type="button"
            onClick={() => navigate(DEMO_WORKSTREAM_PATH)}
            className="intro-shimmer-btn mt-10 inline-flex items-center gap-2 rounded-full px-12 py-5 text-lg font-semibold shadow-sm transition-transform duration-200 hover:scale-[1.02] active:scale-95 motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--primary-foreground))",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 300ms var(--ease-out-expo) both",
            }}
          >
            Enter Workspace
          </button>
        </div>
      </SlidePanel>

      {!reduceMotion && <Dots active={activeSlide} onSelect={goToSlide} />}

      <style>{`
        .intro-shimmer-btn {
          background-color: hsl(var(--primary));
          background-image: linear-gradient(
            110deg,
            transparent 40%,
            rgba(255, 255, 255, 0.35) 50%,
            transparent 60%
          );
          background-size: 200% 100%;
          background-position: -200% 0;
          background-repeat: no-repeat;
        }
        .intro-shimmer-btn:hover {
          animation: shimmer 1.4s linear infinite !important;
        }

        /* Slide-3 network backdrop. Scoped here rather than added to
           index.css because nothing else in the app draws this graph. */
        @keyframes netDraw {
          from { stroke-dashoffset: 620; }
          to   { stroke-dashoffset: 0; }
        }
        @keyframes netDrift {
          0%, 100% { transform: translate(0, 0); }
          33%      { transform: translate(7px, -9px); }
          66%      { transform: translate(-6px, 6px); }
        }
        @keyframes netHalo {
          0%, 100% { opacity: 0.05; transform: scale(0.92); }
          50%      { opacity: 0.11; transform: scale(1.08); }
        }

        @media (prefers-reduced-motion: reduce) {
          .intro-shimmer-btn:hover { animation: none !important; }
        }
      `}</style>
    </div>
  );
}

export default IntroPage;
