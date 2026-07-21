import { useEffect, useRef, useState } from "react";
import DOMPurify from "dompurify";
import type { LinkageCard } from "@/lib/types";
import { labelStyle } from "@/features/task/semanticLabel";

interface EditorPaneProps {
  contentHtml: string;
  lastSavedAt: string | null;
  /** Accepted linkages, used to anchor inline callouts beside their clauses. */
  linkages: LinkageCard[];
  onChange: (html: string) => void;
  isSaving: boolean;
}

// Mirrors engine/drafts.py ALLOWED_TAGS/ALLOWED_ATTRS. This is a nicety, not a
// control — anyone can curl the PUT endpoint, so the server sanitizes again on
// receipt regardless of what we send. Keeping the lists aligned just means the
// drafter sees on screen what will actually be stored.
const PURIFY_CONFIG = {
  ALLOWED_TAGS: [
    "h1",
    "h2",
    "h3",
    "p",
    "strong",
    "em",
    "u",
    "ul",
    "ol",
    "li",
    "div",
    "span",
    "br",
  ],
  ALLOWED_ATTR: ["class"],
};

/** Extract the clause number a callout should sit beside, e.g. "5.3" from
 *  "OpRes PD 5.3". The draft marks clauses as `<strong>5.3</strong>`,
 *  so only the trailing numeric part is comparable. */
function clauseTail(clauseNumber: string | null): string | null {
  if (!clauseNumber) return null;
  const match = clauseNumber.match(/(\d+(?:\.\d+)*)\s*$/);
  return match ? match[1] : null;
}

/** The Word-like document surface, plus the auto-save indicator.
 *
 * The editor is uncontrolled on purpose. A `contentEditable` whose innerHTML is
 * driven by React state fights the browser for cursor position on every
 * keystroke — the caret jumps to the start of the node. So the DOM owns the
 * text once mounted, and `contentHtml` seeds it only when the node is empty or
 * when a Copilot insert arrives from outside.
 */
export function EditorPane({
  contentHtml,
  lastSavedAt,
  linkages,
  onChange,
  isSaving,
}: EditorPaneProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [secondsAgo, setSecondsAgo] = useState(0);

  // Seed / re-seed from props only when the DOM genuinely differs, so typing
  // (which does not change `contentHtml` until the debounce fires) never
  // clobbers the caret, while an inserted snippet still lands.
  useEffect(() => {
    const el = ref.current;
    if (el && el.innerHTML !== contentHtml) {
      el.innerHTML = DOMPurify.sanitize(contentHtml, PURIFY_CONFIG);
    }
  }, [contentHtml]);

  // "Auto-saved Ns ago". Cosmetic by spec — the counter is confidence-building
  // chrome, and the real durability signal is the PUT the parent debounces.
  useEffect(() => {
    setSecondsAgo(0);
    const id = setInterval(() => setSecondsAgo((n) => n + 12), 12_000);
    return () => clearInterval(id);
  }, [lastSavedAt]);

  const callouts = linkages
    .map((card) => ({ card, tail: clauseTail(card.source_clause_number) }))
    // silent-on findings anchor to no draft clause, so they get no callout.
    .filter((c) => c.tail && c.card.label !== "silent-on");

  return (
    <section className="flex h-full flex-col" aria-label="Draft editor">
      <div className="flex items-center justify-between border-b border-border/60 bg-card/30 px-3 py-1.5">
        {/* Toolbar is a visual signal only — MVP1 does not require these to
            function, and execCommand is deprecated. Kept non-functional rather
            than wired to something that half-works. */}
        <div className="flex gap-0.5" aria-label="Formatting">
          {["B", "I", "U", "H", "•"].map((b) => (
            <button
              key={b}
              type="button"
              disabled
              title="Formatting is not wired up in this build"
              className="h-6 w-6 rounded text-xs font-semibold text-muted-foreground"
            >
              {b}
            </button>
          ))}
        </div>
        <span
          data-testid="autosave-indicator"
          className="text-[11px] text-muted-foreground"
        >
          {isSaving
            ? "Saving…"
            : lastSavedAt
              ? `Auto-saved ${secondsAgo}s ago`
              : "Not saved yet"}
        </span>
      </div>

      {/* A light "paper" document surface, floated on the dark app backdrop so
          the serif draft reads like a real Word page regardless of theme. */}
      <div className="flex-1 overflow-y-auto bg-[#0b1220] p-4">
        <div className="mx-auto max-w-2xl rounded-sm bg-white p-8 text-slate-900 shadow-xl shadow-black/30">
          <div
            ref={ref}
            contentEditable
            suppressContentEditableWarning
            role="textbox"
            aria-multiline="true"
            aria-label="Working draft"
            data-testid="draft-surface"
            onInput={(e) => onChange((e.target as HTMLDivElement).innerHTML)}
            className={[
              "min-h-[420px] font-serif text-[15px] leading-relaxed text-slate-900 outline-none",
              "[&_h1]:mb-4 [&_h1]:text-2xl [&_h1]:font-bold",
              "[&_h2]:mb-2 [&_h2]:mt-5 [&_h2]:text-xs [&_h2]:font-bold [&_h2]:tracking-wider [&_h2]:text-slate-500",
              "[&_p]:mb-3",
              // The Copilot's provenance mark. Its `copilot-snippet` class
              // survives both sanitizers so the border reliably shows which
              // text the drafter did not write.
              "[&_.copilot-snippet]:border-l-4 [&_.copilot-snippet]:border-cyan-500 [&_.copilot-snippet]:bg-cyan-50 [&_.copilot-snippet]:py-1 [&_.copilot-snippet]:pl-3",
            ].join(" ")}
          />

          {callouts.length > 0 && (
            <div className="mt-6 border-t border-dashed border-slate-200 pt-3">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Accepted context
              </p>
              <div className="space-y-1.5">
                {callouts.map(({ card, tail }) => (
                  <div
                    key={card.id}
                    data-testid="inline-callout"
                    data-label={card.label}
                    data-clause={tail}
                    className={`border-l-4 pl-2 ${labelStyle(card.label).calloutBorder}`}
                  >
                    <p className="font-mono text-[10px] text-muted-foreground">
                      §{tail} · {card.right.title}
                    </p>
                    <p className="text-[12px] leading-snug">{card.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
