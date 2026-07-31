import { useId, useRef, useState } from "react";
import { Info } from "lucide-react";

import { cn } from "@/lib/utils";
import { LABEL_ORDER, LABEL_STYLES } from "@/lib/labels";

/** Hover legend for the five semantic labels, beside the box's heading.
 *
 *  The copy lives in `@/lib/labels` next to the palette, so the legend and the
 *  pills it explains cannot drift apart — and that copy tracks
 *  `_TAXONOMY_PROMPT_BLOCK` in `engine/connections.py`, which is what the finder
 *  and critic are actually told.
 *
 *  Declaration order, not attention order: the point here is "here are the five
 *  labels", not "here is what needs attention" — the card list below already
 *  makes the urgency argument.
 *
 *  Shared: the task screen's Pairwise Findings box and the graph screen's edge
 *  panel both head their finding lists with it.
 */
export function LabelLegend() {
  // Two legends can be mounted at once (the graph screen's edge panel sits
  // beside other panels), so the id a trigger points `aria-describedby` at has
  // to be unique per instance rather than a constant.
  const legendId = useId();
  const [anchor, setAnchor] = useState<{ top: number; left: number } | null>(
    null,
  );
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Measured off the trigger and positioned `fixed`, NOT absolutely inside the
  // header: the card is `overflow-hidden` so its findings can scroll
  // internally, and an absolutely-positioned panel would be clipped by exactly
  // that. Clamped so a trigger near the right edge does not push the panel
  // off-screen.
  function open() {
    const rect = buttonRef.current?.getBoundingClientRect();
    if (!rect) return;
    setAnchor({
      top: rect.bottom + 8,
      left: Math.max(8, Math.min(rect.left, window.innerWidth - 360)),
    });
  }

  const close = () => setAnchor(null);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        data-testid="label-legend-trigger"
        // Hover is the ask, but focus/Escape come along so the legend is not
        // keyboard-only-user-hostile — it costs three handlers.
        onMouseEnter={open}
        onMouseLeave={close}
        onFocus={open}
        onBlur={close}
        onKeyDown={(e) => {
          if (e.key === "Escape") close();
        }}
        aria-label="What the semantic labels mean"
        aria-describedby={anchor ? legendId : undefined}
        className="rounded-full p-0.5 text-muted-foreground transition hover:bg-accent hover:text-foreground focus:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
      >
        <Info className="h-3.5 w-3.5" />
      </button>

      {anchor && (
        <div
          id={legendId}
          role="tooltip"
          data-testid="label-legend"
          style={{ top: anchor.top, left: anchor.left }}
          className="fixed z-50 w-[21rem] rounded-lg border border-border/70 bg-card p-3 shadow-lg"
        >
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Semantic labels
          </p>
          <dl className="space-y-2">
            {LABEL_ORDER.map((label) => {
              const style = LABEL_STYLES[label];
              return (
                <div key={label}>
                  <dt>
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                        style.pill,
                      )}
                    >
                      {style.label}
                    </span>
                  </dt>
                  <dd className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                    {style.description}
                  </dd>
                </div>
              );
            })}
          </dl>
          {/* The direction convention is the one thing a reader cannot infer
              from the labels alone, and silent-on / goes-beyond are meaningless
              without it. */}
          <p className="mt-2 border-t border-border/60 pt-2 text-[11px] leading-relaxed text-muted-foreground">
            &quot;Ours&quot; is this task&apos;s draft; &quot;theirs&quot; is
            the document it is compared against.
          </p>
        </div>
      )}
    </>
  );
}
