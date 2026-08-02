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
          animation: reduceMotion ? undefined : "blobFloat 16s ease-in-out infinite",
        }}
      />
      <div
        className="absolute -bottom-32 -right-24 h-[480px] w-[480px] rounded-full"
        style={{
          backgroundColor: "hsl(var(--primary))",
          opacity: 0.07,
          filter: "blur(80px)",
          animation: reduceMotion ? undefined : "blobFloat 20s ease-in-out infinite reverse",
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
      className="text-[11px] font-semibold uppercase tracking-[0.12em] motion-reduce:opacity-100"
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
function SlidePanel({ index, activeSlide, reduceMotion, children }: SlidePanelProps) {
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
      className="flex h-full w-full max-w-xs flex-col overflow-hidden rounded-xl motion-reduce:opacity-100"
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
      <div className="h-[3px] w-full flex-shrink-0" style={{ backgroundColor: "hsl(var(--primary))" }} />
      <div className="flex flex-1 flex-col p-6">
        <Icon className="h-6 w-6 flex-shrink-0" style={{ color: "hsl(var(--primary))" }} />
        <h3
          className="mt-4 flex-shrink-0 text-lg font-bold"
          style={{ color: "hsl(var(--foreground))", fontFamily: FONT_FAMILY }}
        >
          {title}
        </h3>
        <div
          className="mt-2 flex-1 text-sm leading-relaxed"
          style={{ color: "hsl(var(--muted-foreground))", fontFamily: FONT_FAMILY }}
        >
          {description}
        </div>
      </div>
    </div>
  );
}

const SIP_CARDS: { icon: LucideIcon; title: string; description: ReactNode }[] = [
  {
    icon: Building2,
    title: "Situation",
    description: (
      <p>
        BNM&rsquo;s credibility as a regulator rests on being internally
        consistent with its own body of policy and externally aligned with
        international standards.
      </p>
    ),
  },
  {
    icon: AlertTriangle,
    title: "Problem Statements",
    description: (
      <ul className="list-disc space-y-1.5 pl-4 text-left">
        <li>Manual assessment of overlapping areas of concern with other departments</li>
        <li>Manual benchmarking of BCBS and other jurisdictions&rsquo; policies</li>
        <li>Drafters spend disproportionate time on routine tasks over higher-value work</li>
        <li>Institutional expertise takes years to build and stays with individual drafters</li>
      </ul>
    ),
  },
  {
    icon: TrendingUp,
    title: "Impact",
    description: (
      <ul className="list-disc space-y-1.5 pl-4 text-left">
        <li>Automatic detection of overlaps with other departments</li>
        <li>Optimised opportunity-gap analysis against established practices</li>
        <li>Drafters&rsquo; time reallocated to higher-value review and scoping</li>
        <li>Institutional expertise decoupled from individuals, embedded into the system</li>
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

      <SlidePanel index={0} activeSlide={activeSlide} reduceMotion={reduceMotion}>
        <div className="mx-auto flex max-w-2xl flex-col items-center text-center">
          <Overline delayMs={0} reduceMotion={reduceMotion}>
            COPA Hackathon 2026 &middot; Must-Win 10
          </Overline>
          <h1
            className="mt-6 font-bold tracking-tight text-transparent motion-reduce:opacity-100"
            style={{
              fontSize: "clamp(48px, 6vw, 80px)",
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
          <p
            className="mx-auto mt-6 max-w-xl text-lg leading-relaxed motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--muted-foreground))",
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
            className="mt-4 text-sm font-medium motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--muted-foreground))",
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
            className="absolute bottom-8 right-8 flex items-center gap-1 text-sm font-medium transition-colors hover:text-foreground"
            style={{ color: "hsl(var(--muted-foreground))" }}
          >
            Next <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </SlidePanel>

      <SlidePanel index={1} activeSlide={activeSlide} reduceMotion={reduceMotion}>
        <div className="mx-auto flex max-w-4xl flex-col items-center text-center">
          <Overline delayMs={0} reduceMotion={reduceMotion}>
            WHY THIS MATTERS
          </Overline>
          <h2
            className="mt-6 font-bold tracking-tight text-transparent motion-reduce:opacity-100"
            style={{
              fontSize: "clamp(36px, 4.5vw, 56px)",
              letterSpacing: "-0.025em",
              backgroundImage:
                "linear-gradient(to right, hsl(var(--foreground)), hsl(var(--primary)))",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 100ms var(--ease-out-expo) both",
            }}
          >
            Situation &rarr; Problem &rarr; Impact
          </h2>
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
            className="absolute bottom-8 right-8 flex items-center gap-1 text-sm font-medium transition-colors hover:text-foreground"
            style={{ color: "hsl(var(--muted-foreground))" }}
          >
            Next <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </SlidePanel>

      <SlidePanel index={2} activeSlide={activeSlide} reduceMotion={reduceMotion}>
        {!reduceMotion && (
          <div aria-hidden className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span
              className="absolute h-64 w-64 rounded-full"
              style={{
                border: "1px solid hsl(var(--primary))",
                opacity: 0.05,
                animation: "ringExpand 3s ease-out infinite",
              }}
            />
            <span
              className="absolute h-64 w-64 rounded-full"
              style={{
                border: "1px solid hsl(var(--primary))",
                opacity: 0.04,
                animation: "ringExpand 3s ease-out 1.5s infinite",
              }}
            />
          </div>
        )}

        <div className="relative mx-auto flex max-w-xl flex-col items-center text-center">
          <h2
            className="font-bold tracking-tight text-transparent motion-reduce:opacity-100"
            style={{
              fontSize: "clamp(40px, 5vw, 64px)",
              letterSpacing: "-0.025em",
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
            onClick={() => navigate("/")}
            className="intro-shimmer-btn mt-10 inline-flex items-center gap-2 rounded-full px-10 py-4 font-semibold shadow-sm transition-transform duration-200 hover:scale-[1.02] active:scale-95 motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--primary-foreground))",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 300ms var(--ease-out-expo) both",
            }}
          >
            Enter Workspace
          </button>
          <p
            className="mt-4 text-xs motion-reduce:opacity-100"
            style={{
              color: "hsl(var(--muted-foreground))",
              animation: reduceMotion
                ? undefined
                : "fadeSlideUp 0.5s 400ms var(--ease-out-expo) both",
            }}
          >
            Bank Negara Malaysia · 2026
          </p>
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
      `}</style>
    </div>
  );
}

export default IntroPage;
