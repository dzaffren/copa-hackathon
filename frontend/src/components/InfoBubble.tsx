import { useId, useRef, useState, type ReactNode } from "react";
import { Info } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Accessible name for the marker. */
  label?: string;
}

/** A small "i" marker beside a title that discloses one line of context —
 *  used for a recommendation's confidence note, the sentence stating what the
 *  tool could not verify from the documents available to it.
 *
 *  Hand-rolled, no tooltip library: `components/ui/` holds eight shadcn
 *  primitives and no tooltip, and `EditorPane.tsx` already hand-rolls its
 *  comment popover rather than pulling one in.
 *
 *  Opens on hover, on keyboard focus and on tap — a pointer-only disclosure
 *  would put the note out of reach on a keyboard or a touchscreen, and the note
 *  is the honesty caveat on the recommendation, not decoration.
 */
export function InfoBubble({ children, label = "More information" }: Props) {
  // Every recommendation on the card carries a marker, so several are mounted
  // at once; the id a marker points `aria-describedby` at has to be unique per
  // instance rather than a constant.
  const bubbleId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [anchor, setAnchor] = useState<{ top: number; left: number } | null>(
    null,
  );
  const open = anchor !== null;

  // Measured off the marker and positioned `fixed`, NOT absolutely beside it:
  // the recommendations card scrolls its list internally behind
  // `overflow-hidden`, which would clip an absolutely-positioned panel.
  // Clamped so a marker near the right edge does not push the bubble
  // off-screen.
  function show() {
    const rect = buttonRef.current?.getBoundingClientRect();
    if (!rect) return;
    setAnchor({
      top: rect.bottom + 6,
      left: Math.max(8, Math.min(rect.left, window.innerWidth - 288)),
    });
  }

  const hide = () => setAnchor(null);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        // Tap: a touchscreen sends no mouseenter and gives no focus ring worth
        // relying on, so the click itself toggles — and toggles, because there
        // is no Escape key to dismiss with either.
        onClick={() => (open ? hide() : show())}
        // Escape hides the bubble but leaves focus on the marker, so the
        // drafter keeps her place in the tab order.
        onKeyDown={(e) => {
          if (e.key === "Escape") hide();
        }}
        // The icon is the whole marker, so the name has to come from an
        // attribute — there is no text to read.
        aria-label={label}
        aria-expanded={open}
        aria-describedby={open ? bubbleId : undefined}
        className="rounded-full p-0.5 text-muted-foreground transition hover:bg-accent hover:text-foreground focus:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
      >
        <Info className="h-3.5 w-3.5" />
      </button>

      {anchor && (
        /* A span, not a div: the marker sits beside a title, so this can be
           mounted inside a heading, where a div would be invalid. */
        <span
          id={bubbleId}
          role="tooltip"
          data-testid="info-bubble"
          style={{ top: anchor.top, left: anchor.left }}
          className="fixed z-50 block w-[17.5rem] rounded-lg border border-border/70 bg-card p-2.5 text-[11px] leading-relaxed text-muted-foreground shadow-lg"
        >
          {children}
        </span>
      )}
    </>
  );
}
