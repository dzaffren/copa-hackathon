import type { DraftOutlineSection } from "./copilotDraftOutline";
import { ANCHOR_DOCS, NODE_METADATA, WORKSTREAM_CONTEXT } from "./copilotV2Data";

// Shared presentational pieces for the Copilot chatbox — extracted from the
// old CopilotTab so the message renderers can reuse them. All static, all
// light-theme, royal-blue primary; no live data.

/** The thinking orb — the one deliberately theatrical moment in the panel.
 *  Built entirely from the royal-blue primary token and the existing keyframes
 *  (glowPulse / rotateGlow / floatUp / ringExpand): concentric radar ripples,
 *  a breathing halo, a counter-rotating dashed ring, two orbiting satellites,
 *  and a floating gradient core. No new colour, no new animation system. */
export function ThinkingOrb() {
  return (
    <div className="relative mx-auto my-4 h-20 w-20" aria-hidden>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="absolute inset-0 rounded-full border border-primary/40"
          style={{ animation: `ringExpand 2.4s ease-out ${i * 0.8}s infinite` }}
        />
      ))}
      <div
        className="absolute inset-1 rounded-full bg-primary/15"
        style={{ animation: "glowPulse 2s ease-in-out infinite" }}
      />
      <div
        className="absolute inset-2 rounded-full border-2 border-dashed border-primary/40"
        style={{ animation: "rotateGlow 6s linear infinite" }}
      />
      <div
        className="absolute inset-0"
        style={{ animation: "rotateGlow 3s linear infinite" }}
      >
        <span className="absolute left-1/2 top-0 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-primary" />
      </div>
      <div
        className="absolute inset-0"
        style={{ animation: "rotateGlow 4s linear infinite reverse" }}
      >
        <span className="absolute bottom-0 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-primary/70" />
      </div>
      <div
        className="absolute inset-[22px] rounded-full bg-gradient-to-br from-primary to-primary/70 shadow-[0_0_12px_rgba(37,99,235,0.5)]"
        style={{ animation: "floatUp 2.4s ease-in-out infinite" }}
      />
    </div>
  );
}

export function ConfidenceMeter({ pct }: { pct: number }) {
  const aligned = pct >= 100;
  const barColor = pct < 34 ? "bg-red-400" : pct < 67 ? "bg-amber-400" : "bg-emerald-500";
  return (
    <div className="space-y-1 px-1">
      <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
        <span>Understanding</span>
        <span
          className={aligned ? "font-semibold text-emerald-700" : undefined}
          style={
            aligned
              ? { animation: "fadeSlideUp 0.4s var(--ease-spring) both" }
              : undefined
          }
        >
          {aligned ? "Aligned ✓" : `${pct}%`}
        </span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
        style={aligned ? { animation: "countGlow 1s ease-out" } : undefined}
      >
        <div
          className={`relative h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        >
          <span
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.8s linear infinite",
            }}
          />
        </div>
      </div>
    </div>
  );
}

export function ContextCard() {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-3 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground">
          {WORKSTREAM_CONTEXT.name}
        </h3>
        <span className="shrink-0 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
          Target: {WORKSTREAM_CONTEXT.targetPublication}
        </span>
      </div>
      <p className="mt-0.5 text-[11px] text-muted-foreground">
        Owner: {WORKSTREAM_CONTEXT.owner}
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {ANCHOR_DOCS.map((a) => (
          <span
            key={a.title}
            className="rounded-full border border-border/60 bg-muted/40 px-2 py-0.5 text-[10px] text-muted-foreground"
          >
            {a.title}
          </span>
        ))}
      </div>
    </div>
  );
}

/** The task's regulatory profile, revealed by /explore-task. A null value
 *  renders as an honest "Not available" unless the drafter has since
 *  resolved it through the missing-fields form (`overrides`), in which case
 *  it renders as a confirmed row instead. */
export function NodeMetadataList({
  overrides,
}: {
  overrides?: Record<string, string>;
} = {}) {
  return (
    <dl className="space-y-2 text-xs">
      {NODE_METADATA.map((f) => {
        const resolved = f.value === null ? overrides?.[f.key] : undefined;
        const value = resolved ?? f.value;
        return (
          <div key={f.key}>
            <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              {f.label}
            </dt>
            <dd className="mt-0.5 text-foreground">
              {value === null ? (
                <span className="italic text-muted-foreground">Not available</span>
              ) : Array.isArray(value) ? (
                value.join(", ")
              ) : (
                value
              )}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

/** One card in the /draft outline preview — bold title, one-sentence
 *  description, 3-4 "what to write" bullets, and an italic guidance note.
 *  Purely instructional; the editable content this previews is inserted
 *  separately via buildDraftOutline(). */
export function DraftInstructionCard({ section }: { section: DraftOutlineSection }) {
  return (
    <article
      data-testid="draft-instruction-card"
      className="rounded-lg border border-border/60 bg-card p-3 shadow-sm"
    >
      <h4 className="text-sm font-semibold text-foreground">{section.title}</h4>
      <p className="mt-1 text-xs text-muted-foreground">{section.description}</p>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-foreground">
        {section.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] italic text-muted-foreground">{section.guidanceNote}</p>
    </article>
  );
}
