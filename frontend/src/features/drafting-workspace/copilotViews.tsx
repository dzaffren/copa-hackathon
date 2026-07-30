import { labelStyle, labelText } from "@/features/task/semanticLabel";
import type { SemanticLabel } from "@/lib/types";
import {
  ANCHOR_DOCS,
  NODE_METADATA,
  WORKSTREAM_CONTEXT,
  type ClauseCitation,
  type DraftSection,
  type SectionStatus,
} from "./copilotV2Data";

// Shared presentational pieces for the Copilot chatbox — extracted from the
// old CopilotTab so the message renderers can reuse them. All static, all
// light-theme, royal-blue primary; no live data.

const STATUS_META: Record<SectionStatus, { text: string; className: string }> = {
  ready: {
    text: "Ready",
    className: "bg-emerald-500/15 text-emerald-800 border-emerald-400/30",
  },
  drafted: {
    text: "Drafted",
    className: "bg-amber-400/15 text-amber-800 border-amber-300/30",
  },
  gap: {
    text: "Gap detected",
    className: "bg-red-500/15 text-red-800 border-red-400/30",
  },
};

/** Left-edge accent bar colour per semantic label — mirrors the taxonomy hues
 *  used elsewhere. Semantic colour only, never the royal-blue brand accent. */
const LABEL_ACCENT: Record<SemanticLabel, string> = {
  "aligns-with": "bg-emerald-400",
  "differs-on": "bg-amber-400",
  "conflicts-with": "bg-red-400",
  "silent-on": "bg-sky-400",
  "goes-beyond": "bg-violet-400",
};

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

/** The task's regulatory profile, revealed by /pull-node-metadata. A null value
 *  renders as an honest "Not available" — never invented. */
export function NodeMetadataList() {
  return (
    <dl className="space-y-2 text-xs">
      {NODE_METADATA.map((f) => (
        <div key={f.key}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {f.label}
          </dt>
          <dd className="mt-0.5 text-foreground">
            {f.value === null ? (
              <span className="italic text-muted-foreground">Not available</span>
            ) : Array.isArray(f.value) ? (
              f.value.join(", ")
            ) : (
              f.value
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** A read-only summary row for one drafted section — used in the post-/build
 *  draft-summary message. No "Insert into Editor" button: /build has already
 *  auto-populated the editor, so this is a receipt, not an action. */
export function DraftSectionSummary({
  section,
  index,
}: {
  section: DraftSection;
  index: number;
}) {
  const status = STATUS_META[section.status];
  const style = labelStyle(section.label);
  const accent = LABEL_ACCENT[section.label] ?? "bg-slate-400";
  const citation: ClauseCitation | undefined =
    section.status === "gap"
      ? undefined
      : section.targetCitations[0] ?? section.sourceCitations[0];

  return (
    <article
      data-testid="draft-section-summary"
      className={`group relative overflow-hidden rounded-xl border bg-card p-3 pl-4 shadow-sm ${
        section.status === "gap" ? "border-dashed border-border" : "border-border/60"
      }`}
      style={{
        animation: "fadeSlideUp 0.5s var(--ease-spring) both",
        animationDelay: `${index * 90}ms`,
      }}
    >
      <span className={`absolute inset-y-0 left-0 w-1 ${accent}`} aria-hidden />
      <div className="mb-1 flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground">{section.title}</h4>
        <span
          className={`shrink-0 rounded-full border px-1.5 py-0.5 text-[9px] font-semibold ${status.className}`}
        >
          {status.text}
        </span>
      </div>
      <span
        className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold ${style.pill}`}
      >
        {labelText(section.label, section.sentiment)}
      </span>
      <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">
        {section.summary}
      </p>
      {citation ? (
        <p className="mt-1.5 line-clamp-2 font-mono text-[10px] text-muted-foreground">
          {citation.clauseNumber} — &ldquo;{citation.text}&rdquo;
        </p>
      ) : (
        <p className="mt-1.5 text-[10px] italic text-muted-foreground">
          No matching clause found.
        </p>
      )}
    </article>
  );
}
