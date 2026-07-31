import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import DOMPurify from "dompurify";
import { MessageSquare, Send, Trash2, X } from "lucide-react";
import type { LinkageCard } from "@/lib/types";
import { labelStyle } from "@/features/task/semanticLabel";
import { WORKSTREAM_CONTEXT } from "./copilotV2Data";

/** "Aisyah R." → "AR" for the comment popover's avatar. */
function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

interface DraftComment {
  id: string;
  /** The commented passage's own text, kept even if the highlight itself
   *  can't be anchored (a selection spanning multiple block elements can't
   *  always be wrapped in one marker span). */
  quote: string;
  text: string;
  /** Position (px, relative to the paper) of the small marker icon that
   *  sits right after the highlighted passage — on the page itself, not a
   *  side margin. */
  top: number;
  left: number;
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
    "img",
  ],
  ALLOWED_ATTR: ["class", "src", "alt"],
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
  const [activeFormats, setActiveFormats] = useState({
    bold: false,
    italic: false,
    underline: false,
  });
  const [comments, setComments] = useState<DraftComment[]>([]);
  const [commentFormOpen, setCommentFormOpen] = useState(false);
  const [commentDraft, setCommentDraft] = useState("");
  // Position (px, relative to the paper) — scroll-invariant, since the paper
  // and the anchored passage move together when the pane scrolls, only their
  // difference is stored.
  const [commentAnchor, setCommentAnchor] = useState<{ top: number; left: number } | null>(null);
  const [expandedCommentId, setExpandedCommentId] = useState<string | null>(null);
  const pendingRangeRef = useRef<Range | null>(null);
  const commentIdRef = useRef(0);
  const commentPopoverRef = useRef<HTMLDivElement>(null);
  const paperRef = useRef<HTMLDivElement>(null);

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

  /** The toolbar reflects the format at the caret — e.g. Bold stays
   *  highlighted while typing after a click, the same feedback Word gives —
   *  not just whether a selection happens to already be bold. jsdom (the
   *  component test environment) doesn't implement queryCommandState at
   *  all, unlike every real browser, hence the feature check. */
  function updateActiveFormats() {
    if (typeof document.queryCommandState !== "function") return;
    setActiveFormats({
      bold: document.queryCommandState("bold"),
      italic: document.queryCommandState("italic"),
      underline: document.queryCommandState("underline"),
    });
  }

  function handleSelectionChange() {
    saveCursor();
    updateSelectionState();
    updateActiveFormats();
  }

  /** Open the comment compose card on the page itself, just below the
   *  drafter's current selection — not in a side margin. Captured now since
   *  focus is about to move to the card's own textarea, which would
   *  otherwise collapse the browser selection. */
  function openCommentForm() {
    const range = savedRangeRef.current;
    const paper = paperRef.current;
    if (!range || !paper) return;
    pendingRangeRef.current = range.cloneRange();
    const rect = range.getBoundingClientRect();
    const paperRect = paper.getBoundingClientRect();
    setExpandedCommentId(null);
    setCommentAnchor({
      top: rect.bottom - paperRect.top + 6,
      left: Math.min(Math.max(rect.left - paperRect.left, 0), paperRect.width - 272),
    });
    setCommentDraft("");
    setCommentFormOpen(true);
  }

  function cancelCommentForm() {
    setCommentFormOpen(false);
    setCommentDraft("");
    setCommentAnchor(null);
    pendingRangeRef.current = null;
  }

  /** Wrap the anchored selection in a highlighted `.draft-comment-{id}`
   *  marker (a selection confined to one text run) and record the comment,
   *  anchoring its marker icon just after the marker — right on the page,
   *  beside the passage it's about. A selection that crosses element
   *  boundaries can't always be wrapped in a single span — the comment is
   *  still recorded against its quoted text, just without a visual
   *  highlight or precise icon position in that edge case. */
  function submitComment() {
    const range = pendingRangeRef.current;
    const el = editorRef.current;
    const paper = paperRef.current;
    const text = commentDraft.trim();
    if (!range || !el || !paper || !text) return;

    const quote = range.toString().trim();
    const id = `c${++commentIdRef.current}`;
    let top = commentAnchor?.top ?? 0;
    let left = commentAnchor?.left ?? 0;
    try {
      const mark = document.createElement("span");
      mark.className = `draft-comment draft-comment-${id}`;
      range.surroundContents(mark);
      const markRect = mark.getBoundingClientRect();
      const paperRect = paper.getBoundingClientRect();
      top = markRect.top - paperRect.top;
      left = markRect.right - paperRect.left + 4;
    } catch {
      // Selection spans multiple elements — comment recorded without a
      // visual anchor rather than losing it.
    }

    setComments((prev) => [...prev, { id, quote, text, top, left }]);
    setCommentFormOpen(false);
    setCommentDraft("");
    setCommentAnchor(null);
    pendingRangeRef.current = null;
    onChange(el.innerHTML);
  }

  // Click anywhere outside the open card (or Escape) dismisses it — the
  // same behaviour as Word/Google Docs' comment bubble. A click on a marker
  // icon itself is left alone here; its own onClick decides whether that's
  // an open, a close, or a switch to a different comment.
  useEffect(() => {
    if (!commentFormOpen && !expandedCommentId) return;
    function onPointerDown(e: MouseEvent) {
      const target = e.target as HTMLElement;
      if (commentPopoverRef.current?.contains(target)) return;
      if (target.closest("[data-comment-marker]")) return;
      cancelCommentForm();
      setExpandedCommentId(null);
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        cancelCommentForm();
        setExpandedCommentId(null);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [commentFormOpen, expandedCommentId]);

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
    setExpandedCommentId((prev) => (prev === id ? null : prev));
    if (el) onChange(el.innerHTML);
  }

  /** Bold/Italic/Underline via document.execCommand — deprecated but still
   *  universally supported, and the spec explicitly calls for it (H and •
   *  stay disabled, out of scope). No richer rich-text editor is warranted
   *  for three toggle buttons. Works on a collapsed selection too — a real
   *  browser then applies the format to whatever's typed next, the same
   *  sticky-formatting behaviour Word gives when you click Bold with
   *  nothing selected. jsdom doesn't implement execCommand at all, hence
   *  the feature check. */
  function applyFormat(command: "bold" | "italic" | "underline") {
    editorRef.current?.focus();
    if (typeof document.execCommand === "function") {
      document.execCommand(command);
    }
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
            const isActive = activeFormats[command];
            return (
              <button
                key={b}
                type="button"
                title={`Toggle ${command}`}
                aria-pressed={isActive}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => applyFormat(command)}
                className={[
                  "h-6 w-6 rounded text-xs font-semibold transition",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-accent",
                ].join(" ")}
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

      {/* The paper. Comments live on the page itself: a small marker icon
          sits right after the highlighted passage, and clicking it expands
          the full card in place — not a permanent side margin, and not a
          flat list appended after a many-page document. */}
      <div className="flex-1 overflow-auto bg-muted p-4">
        <div
          ref={paperRef}
          className={
            isBnmDoc
              ? "relative mx-auto w-full"
              : "relative mx-auto max-w-2xl rounded-sm bg-white p-8 text-slate-900 shadow-xl shadow-black/30"
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

          {/* Compose card — appears on the page just under the selection. */}
          {commentFormOpen && commentAnchor && (
            <div
              ref={commentPopoverRef}
              data-testid="comment-form"
              style={{ position: "absolute", top: commentAnchor.top, left: commentAnchor.left }}
              className="z-50 w-64 rounded-lg border border-primary/30 bg-card p-3 shadow-xl"
            >
              <div className="mb-2 flex items-center gap-2">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-[11px] font-bold text-primary-foreground">
                  {initials(WORKSTREAM_CONTEXT.owner)}
                </span>
                <span className="text-xs font-semibold text-foreground">
                  {WORKSTREAM_CONTEXT.owner}
                </span>
              </div>
              <textarea
                aria-label="Comment text"
                autoFocus
                rows={3}
                value={commentDraft}
                onChange={(e) => setCommentDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    submitComment();
                  }
                }}
                placeholder="@mention or comment"
                className="w-full resize-none rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-xs outline-none focus:border-primary/60"
              />
              <p className="mt-1 text-[10px] text-muted-foreground">
                Tip: Press Ctrl+Enter to post.
              </p>
              <div className="mt-2 flex justify-end gap-1">
                <button
                  type="button"
                  aria-label="Cancel comment"
                  onClick={cancelCommentForm}
                  className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  aria-label="Post comment"
                  disabled={!commentDraft.trim()}
                  onClick={submitComment}
                  className="rounded-md bg-primary p-1.5 text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* Marker icons — one per posted comment, sitting right after its
              highlighted passage. Click to expand. */}
          {comments.map((c) => (
            <button
              key={c.id}
              type="button"
              data-comment-marker
              aria-label={
                expandedCommentId === c.id ? "Collapse comment" : "Expand comment"
              }
              onClick={() => {
                cancelCommentForm();
                setExpandedCommentId((prev) => (prev === c.id ? null : c.id));
              }}
              style={{ position: "absolute", top: c.top, left: c.left }}
              className={[
                "z-40 flex h-5 w-5 items-center justify-center rounded-full shadow transition",
                expandedCommentId === c.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-amber-400 text-amber-950 hover:bg-amber-300",
              ].join(" ")}
            >
              <MessageSquare className="h-3 w-3" />
            </button>
          ))}

          {comments.map((c) => {
            if (expandedCommentId !== c.id) return null;
            // Flip to the icon's left when there isn't 256px (the card's
            // width) of room to its right — e.g. a passage near the page's
            // right edge — rather than let the card run off the page.
            const paperWidth = paperRef.current?.clientWidth ?? 0;
            const left =
              c.left + 24 + 256 > paperWidth
                ? Math.max(c.left - 256 - 8, 0)
                : c.left + 24;
            return (
                <div
                  key={`${c.id}-card`}
                  ref={commentPopoverRef}
                  data-testid="draft-comment-item"
                  style={{ position: "absolute", top: c.top, left }}
                  className="z-50 w-64 rounded-lg border border-border/60 bg-card p-2.5 shadow-xl"
                >
                  <div className="mb-1 flex items-center gap-1.5">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-primary-foreground">
                      {initials(WORKSTREAM_CONTEXT.owner)}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-[11px] font-semibold text-foreground">
                      {WORKSTREAM_CONTEXT.owner}
                    </span>
                    <button
                      type="button"
                      aria-label="Remove comment"
                      onClick={() => removeComment(c.id)}
                      className="shrink-0 rounded p-0.5 text-muted-foreground hover:bg-accent hover:text-foreground"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                  <p className="line-clamp-1 font-mono text-[10px] text-muted-foreground">
                    &ldquo;{c.quote}&rdquo;
                  </p>
                  <p className="text-[12px] leading-snug text-foreground">{c.text}</p>
                </div>
            );
          })}
        </div>
      </div>
    </section>
  );
  },
);
