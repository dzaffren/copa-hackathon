import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import DOMPurify from "dompurify";
import { MessageSquare, Trash2 } from "lucide-react";
import type { LinkageCard } from "@/lib/types";
import { labelStyle } from "@/features/task/semanticLabel";

interface DraftComment {
  id: string;
  /** The commented passage's own text, kept even if the highlight itself
   *  can't be anchored (a selection spanning multiple block elements can't
   *  always be wrapped in one marker span). */
  quote: string;
  text: string;
}

interface EditorPaneProps {
  contentHtml: string;
  lastSavedAt: string | null;
  /** Accepted linkages, used to anchor inline callouts beside their clauses. */
  linkages: LinkageCard[];
  onChange: (html: string) => void;
  isSaving: boolean;
}

export interface EditorPaneHandle {
  /** Insert `html` at the last place the drafter had their cursor in the
   *  editor (falling back to the end of the document if they've never
   *  clicked into it yet), and return the editor's full resulting HTML so
   *  the caller can persist it. Used by the Copilot's "Insert into draft" —
   *  the drafter picks where a suggested clause lands, not just append. */
  insertAtCursor: (html: string) => string | null;
  /** Replace the entire editor contents with `html` — used by /draft and
   *  /write, which each generate a complete document rather than a snippet
   *  to insert alongside existing text. Running one after the other
   *  replaces the page wholesale, it doesn't stack on top of it. */
  replaceContent: (html: string) => string | null;
  /** The plain text the drafter currently has highlighted in the editor
   *  (empty string when the selection is collapsed or outside the editor).
   *  Sent to the Copilot as focused context so "suggestions on this part"
   *  resolves to the highlighted passage. */
  getSelectionText: () => string;
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
export const EditorPane = forwardRef<EditorPaneHandle, EditorPaneProps>(
  function EditorPane(
    { contentHtml, lastSavedAt, linkages, onChange, isSaving },
    ref,
  ) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [hasSelection, setHasSelection] = useState(false);
  const [comments, setComments] = useState<DraftComment[]>([]);
  const [commentFormOpen, setCommentFormOpen] = useState(false);
  const [commentDraft, setCommentDraft] = useState("");
  const pendingRangeRef = useRef<Range | null>(null);
  const commentIdRef = useRef(0);

  // The last cursor/selection position the drafter left inside the editor —
  // captured on blur (before focus moves to, say, the Copilot panel's "Insert
  // into draft" button) so a snippet insert lands where they were looking,
  // not always at the end of the document.
  const savedRangeRef = useRef<Range | null>(null);
  function saveCursor() {
    const el = editorRef.current;
    const selection = window.getSelection();
    if (!el || !selection || selection.rangeCount === 0) return;
    const range = selection.getRangeAt(0);
    if (el.contains(range.commonAncestorContainer)) {
      savedRangeRef.current = range.cloneRange();
    }
  }

  function updateSelectionState() {
    const el = editorRef.current;
    const selection = window.getSelection();
    if (!el || !selection || selection.rangeCount === 0 || selection.isCollapsed) {
      setHasSelection(false);
      return;
    }
    const range = selection.getRangeAt(0);
    setHasSelection(el.contains(range.commonAncestorContainer));
  }

  function handleSelectionChange() {
    saveCursor();
    updateSelectionState();
  }

  /** Open the comment form for the drafter's current selection — captured
   *  now since focus is about to move to the form's own textarea, which
   *  would otherwise collapse the browser selection. */
  function openCommentForm() {
    const range = savedRangeRef.current;
    if (!range) return;
    pendingRangeRef.current = range.cloneRange();
    setCommentDraft("");
    setCommentFormOpen(true);
  }

  function cancelCommentForm() {
    setCommentFormOpen(false);
    setCommentDraft("");
    pendingRangeRef.current = null;
  }

  /** Wrap the anchored selection in a highlighted `.draft-comment-{id}`
   *  marker (a selection confined to one text run) and record the comment.
   *  A selection that crosses element boundaries can't always be wrapped in
   *  a single span — the comment is still recorded against its quoted text,
   *  just without a visual highlight in that edge case. */
  function submitComment() {
    const range = pendingRangeRef.current;
    const el = editorRef.current;
    const text = commentDraft.trim();
    if (!range || !el || !text) return;

    const quote = range.toString().trim();
    const id = `c${++commentIdRef.current}`;
    try {
      const mark = document.createElement("span");
      mark.className = `draft-comment draft-comment-${id}`;
      range.surroundContents(mark);
    } catch {
      // Selection spans multiple elements — comment recorded without a
      // visual anchor rather than losing it.
    }

    setComments((prev) => [...prev, { id, quote, text }]);
    setCommentFormOpen(false);
    setCommentDraft("");
    pendingRangeRef.current = null;
    onChange(el.innerHTML);
  }

  function removeComment(id: string) {
    const el = editorRef.current;
    if (el) {
      const mark = el.querySelector(`.draft-comment-${id}`);
      if (mark?.parentNode) {
        const parent = mark.parentNode;
        while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
        parent.removeChild(mark);
      }
    }
    setComments((prev) => prev.filter((c) => c.id !== id));
    if (el) onChange(el.innerHTML);
  }

  /** Bold/Italic/Underline via document.execCommand — deprecated but still
   *  universally supported, and the spec explicitly calls for it (H and •
   *  stay disabled, out of scope). No richer rich-text editor is warranted
   *  for three toggle buttons. */
  function applyFormat(command: "bold" | "italic" | "underline") {
    editorRef.current?.focus();
    document.execCommand(command);
    handleSelectionChange();
    const el = editorRef.current;
    if (el) onChange(el.innerHTML);
  }

  useImperativeHandle(ref, () => ({
    insertAtCursor(html: string) {
      const el = editorRef.current;
      if (!el) return null;

      let range = savedRangeRef.current;
      // A stale range (from a previous mount, or one the DOM has since
      // moved past) is worse than no range — fall back to end-of-document.
      if (!range || !el.contains(range.commonAncestorContainer)) {
        range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
      }

      const sanitized = DOMPurify.sanitize(html, PURIFY_CONFIG);
      const wrapper = document.createElement("div");
      wrapper.innerHTML = sanitized;
      const fragment = document.createDocumentFragment();
      let lastInserted: ChildNode | null = null;
      while (wrapper.firstChild) {
        lastInserted = fragment.appendChild(wrapper.firstChild);
      }

      range.deleteContents();
      range.insertNode(fragment);

      // Move the caret to just after what was inserted, so typing right
      // after an insert continues from there, not from the old position.
      if (lastInserted) {
        const after = document.createRange();
        after.setStartAfter(lastInserted);
        after.collapse(true);
        savedRangeRef.current = after.cloneRange();
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(after);
      }

      const next = el.innerHTML;
      onChange(next);
      return next;
    },
    replaceContent(html: string) {
      const el = editorRef.current;
      if (!el) return null;

      el.innerHTML = DOMPurify.sanitize(html, PURIFY_CONFIG);

      const after = document.createRange();
      after.selectNodeContents(el);
      after.collapse(false);
      savedRangeRef.current = after.cloneRange();

      const next = el.innerHTML;
      onChange(next);
      return next;
    },
    getSelectionText() {
      // Read the last range saved inside the editor, not the live
      // `window.getSelection()`: by the time the drafter has clicked into the
      // Copilot input to ask their question, the browser selection points at
      // that input, so only `savedRangeRef` (captured on the editor's
      // mouseup/keyup/blur) still holds what they highlighted in the document.
      const el = editorRef.current;
      const range = savedRangeRef.current;
      if (!el || !range || range.collapsed) return "";
      if (!el.contains(range.commonAncestorContainer)) return "";
      return range.toString().trim();
    },
  }));

  // Seed / re-seed from props only when the DOM genuinely differs, so typing
  // (which does not change `contentHtml` until the debounce fires) never
  // clobbers the caret, while an inserted snippet still lands.
  useEffect(() => {
    const el = editorRef.current;
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

  // /draft and /write insert a `.bnm-doc` of full-width, individually
  // paginated `.bnm-page`s, each already carrying its own white background,
  // shadow, and padding. Wrapping that in this pane's own padded/shadowed
  // "paper" card would nest one page look inside another and clip the
  // wider BNM pages against the narrower default reading column — so that
  // wrapper only applies to plain (non-BNM) draft content.
  const isBnmDoc = contentHtml.includes('class="bnm-doc"');

  return (
    <section className="flex h-full flex-col" aria-label="Draft editor">
      <div className="flex items-center justify-between border-b border-border/60 bg-card/30 px-3 py-1.5">
        <div className="flex gap-0.5" aria-label="Formatting">
          {(["B", "I", "U"] as const).map((b) => {
            const command = b === "B" ? "bold" : b === "I" ? "italic" : "underline";
            return (
              <button
                key={b}
                type="button"
                disabled={!hasSelection}
                title={hasSelection ? `Toggle ${command}` : "Select text in the editor to format it"}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => applyFormat(command)}
                className="h-6 w-6 rounded text-xs font-semibold text-muted-foreground enabled:text-foreground enabled:hover:bg-accent"
              >
                {b}
              </button>
            );
          })}
          {["H", "•"].map((b) => (
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
          <div className="mx-1 h-4 w-px bg-border/60" aria-hidden />
          <button
            type="button"
            data-testid="add-comment-button"
            disabled={!hasSelection}
            title={hasSelection ? "Comment on the selected text" : "Select text in the editor to comment on it"}
            onMouseDown={(e) => e.preventDefault()}
            onClick={openCommentForm}
            className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground enabled:hover:bg-accent enabled:hover:text-foreground"
          >
            <MessageSquare className="h-3.5 w-3.5" />
          </button>
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

      {commentFormOpen && (
        <div
          data-testid="comment-form"
          className="border-b border-border/60 bg-card px-3 py-2"
        >
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Comment on: <span className="italic normal-case text-foreground">&ldquo;{pendingRangeRef.current?.toString().trim().slice(0, 80)}&rdquo;</span>
          </p>
          <div className="flex items-start gap-1.5">
            <textarea
              aria-label="Comment text"
              autoFocus
              rows={2}
              value={commentDraft}
              onChange={(e) => setCommentDraft(e.target.value)}
              placeholder="Add a comment…"
              className="min-w-0 flex-1 resize-none rounded-md border border-border/60 bg-background/60 px-2 py-1 text-xs outline-none focus:border-primary/60"
            />
            <div className="flex shrink-0 flex-col gap-1">
              <button
                type="button"
                disabled={!commentDraft.trim()}
                onClick={submitComment}
                className="rounded-md bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
              >
                Comment
              </button>
              <button
                type="button"
                onClick={cancelCommentForm}
                className="rounded-md px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-accent"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* A white "paper" document surface, floated on a soft neutral canvas so
          the serif draft reads like a real page rather than blending into the
          surrounding chrome. */}
      <div className="flex-1 overflow-auto bg-muted p-4">
        <div
          className={
            isBnmDoc
              ? "w-full"
              : "mx-auto max-w-2xl rounded-sm bg-white p-8 text-slate-900 shadow-xl shadow-black/30"
          }
        >
          <div
            ref={editorRef}
            contentEditable
            suppressContentEditableWarning
            role="textbox"
            aria-multiline="true"
            aria-label="Working draft"
            data-testid="draft-surface"
            onInput={(e) => onChange((e.target as HTMLDivElement).innerHTML)}
            onMouseUp={handleSelectionChange}
            onKeyUp={handleSelectionChange}
            onBlur={handleSelectionChange}
            className={[
              isBnmDoc ? "outline-none" : "min-h-[420px] text-slate-900 outline-none",
              "[&_h1]:mb-4 [&_h1]:text-2xl [&_h1]:font-bold",
              "[&_h2]:mb-2 [&_h2]:mt-5 [&_h2]:text-xs [&_h2]:font-bold [&_h2]:tracking-wider [&_h2]:text-slate-500",
              "[&_p]:mb-3",
              // The Copilot's provenance mark. Its `copilot-snippet` class
              // survives both sanitizers so the border reliably shows which
              // text the drafter did not write.
              "[&_.copilot-snippet]:border-l-4 [&_.copilot-snippet]:border-primary [&_.copilot-snippet]:bg-primary/5 [&_.copilot-snippet]:py-1 [&_.copilot-snippet]:pl-3",
            ].join(" ")}
          />

          {!isBnmDoc && callouts.length > 0 && (
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

          {comments.length > 0 && (
            <div className="mt-6 border-t border-dashed border-slate-200 pt-3">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Comments
              </p>
              <div className="space-y-1.5">
                {comments.map((c) => (
                  <div
                    key={c.id}
                    data-testid="draft-comment-item"
                    className="flex items-start justify-between gap-2 border-l-4 border-amber-400 bg-amber-50/60 pl-2 pr-1.5 py-1"
                  >
                    <div className="min-w-0">
                      <p className="line-clamp-1 font-mono text-[10px] text-muted-foreground">
                        &ldquo;{c.quote}&rdquo;
                      </p>
                      <p className="text-[12px] leading-snug text-slate-900">{c.text}</p>
                    </div>
                    <button
                      type="button"
                      aria-label="Remove comment"
                      onClick={() => removeComment(c.id)}
                      className="shrink-0 rounded p-0.5 text-muted-foreground hover:bg-accent hover:text-foreground"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
  },
);
