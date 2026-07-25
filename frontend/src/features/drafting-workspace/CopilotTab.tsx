import { useEffect, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { FilePlus2, MousePointerClick } from "lucide-react";
import { streamCopilotMessage } from "@/lib/api";
import {
  COPILOT_INTENTS,
  COPILOT_INTENT_LABELS,
  type ChatMessage,
  type CopilotCitation,
  type CopilotDraftContext,
  type CopilotIntent,
  type LinkageCard,
  type StreamingCopilotDone,
} from "@/lib/types";
import { AnalyzeProgressBar, COPILOT_STAGES } from "@/components/AnalyzeProgressBar";
import { CopilotMarkdown } from "./CopilotMarkdown";
import { MentionInput, parseMentions } from "./MentionInput";

interface CopilotTabProps {
  workstreamId: string;
  nodeId: string;
  onInsertSnippet: (html: string) => void;
  /** The drafter's already-accepted findings for this task — the `@` mention
   *  dropdown's source list. */
  reviewedCards: LinkageCard[];
  /** Reads the drafter's live editor content + current highlighted selection
   *  at send time, so the Copilot can see what they are drafting and answer
   *  "suggestions on this part". */
  getDraftContext: () => CopilotDraftContext;
}

// The snippet preview is model-authored HTML. Sanitize before display with the
// same tag set the editor accepts (mirrors EditorPane.PURIFY_CONFIG), so the
// "Suggested addition" card can never render unsafe markup.
const SNIPPET_PURIFY = {
  ALLOWED_TAGS: [
    "h1", "h2", "h3", "p", "strong", "em", "u", "ul", "ol", "li", "div",
    "span", "br",
  ],
  ALLOWED_ATTR: ["class"],
};

type SendState = "idle" | "connecting" | "streaming";

/** The Drafting Copilot: a live Azure AI Foundry Claude chat, streamed token
 *  by token over SSE (`engine/copilot.py`'s `/copilot/stream` route), not a
 *  script.
 *
 * Every clause it quotes is re-grounded server-side — the citation
 * guardrail drops any citation not actually supplied to the model and
 * always re-quotes text from that grounded set, never the model's own echo.
 * Citations render as their own block precisely so a reviewer can tell an
 * assertion from a quotation at a glance. `@` in the message box references
 * an accepted finding (`reviewedCards`), grounding the model with that
 * finding's own verbatim clauses. Citations and any drafted snippet only
 * arrive on the stream's terminal `done` event, so the partial bubble shows
 * prose only — the committed message is what carries them. */
export function CopilotTab({
  workstreamId,
  nodeId,
  onInsertSnippet,
  reviewedCards,
  getDraftContext,
}: CopilotTabProps) {
  const [intent, setIntent] = useState<CopilotIntent>("PD");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sendState, setSendState] = useState<SendState>("idle");
  const [streamingText, setStreamingText] = useState<string>("");
  const [errorText, setErrorText] = useState<string | null>(null);

  // AbortController ref — aborts the in-flight stream when the user
  // changes intent, the component unmounts, or a new send starts.
  const abortRef = useRef<AbortController | null>(null);

  // Cancel any in-flight stream when the component unmounts.
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  function changeIntent(next: CopilotIntent) {
    abortRef.current?.abort();
    abortRef.current = null;
    setSendState("idle");
    setStreamingText("");
    setErrorText(null);
    setIntent(next);
    // A fresh intent framing deserves a fresh thread — keeping old turns
    // would mix system-prompt framings the model never actually saw together.
    setMessages([]);
  }

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sendState !== "idle") return;

    const { referencedFindingIds } = parseMentions(trimmed, reviewedCards);
    // Capture the drafter's live draft + highlighted selection at send time so
    // the Copilot can see what they are working on ("suggestions on this part").
    const draftContext = getDraftContext();

    // Append the user's message immediately.
    const historyForRequest = messages.map((m) => ({ role: m.role, text: m.text }));
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    setErrorText(null);
    setStreamingText("");
    setSendState("connecting");

    const controller = new AbortController();
    abortRef.current = controller;

    let accumulated = "";
    let donePayload: StreamingCopilotDone | null = null;

    try {
      const stream = streamCopilotMessage(
        workstreamId,
        nodeId,
        intent,
        trimmed,
        historyForRequest,
        referencedFindingIds,
        controller.signal,
        draftContext,
      );

      for await (const evt of stream) {
        if (evt.event === "token") {
          accumulated += evt.data.t;
          setSendState("streaming");
          setStreamingText(accumulated);
        } else if (evt.event === "done") {
          donePayload = evt.data;
        } else if (evt.event === "error") {
          setErrorText(evt.data.message || "The Copilot failed to reply.");
          setSendState("idle");
          setStreamingText("");
          return;
        }
      }

      // Stream finished cleanly — commit the full message. Prefer the
      // done event's extracted prose (`text`) over the raw accumulated
      // token buffer: in production the tokens spell out the model's raw
      // JSON envelope, not clean prose, so `accumulated` is only a safe
      // fallback when the server genuinely had no JSON to extract from.
      const fullMessage: ChatMessage = {
        role: "copilot",
        text: donePayload?.text || accumulated || "No matching clause found",
        citations: donePayload?.citations,
        snippet_html: donePayload?.snippet_html,
      };
      setMessages((prev) => [...prev, fullMessage]);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        // Intentional cancel (intent change / unmount) — silent.
      } else {
        const msg = err instanceof Error ? err.message : "The Copilot failed to reply.";
        setErrorText(msg);
      }
    } finally {
      setSendState("idle");
      setStreamingText("");
      abortRef.current = null;
    }
  }

  const isPending = sendState !== "idle";
  const isConnecting = sendState === "connecting";
  const isStreaming = sendState === "streaming";

  return (
    <div className="flex h-full flex-col" data-testid="copilot-tab">
      <label className="block px-1 pb-2">
        <span className="sr-only">Intent preset</span>
        <select
          aria-label="Intent preset"
          value={intent}
          onChange={(e) => changeIntent(e.target.value as CopilotIntent)}
          className="w-full rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-cyan-400/60"
        >
          {COPILOT_INTENTS.map((i) => (
            <option key={i} value={i}>
              {COPILOT_INTENT_LABELS[i]}
            </option>
          ))}
        </select>
      </label>

      <div
        className="flex-1 space-y-3 overflow-y-auto px-1"
        aria-label="Copilot conversation"
      >
        {messages.length === 0 && !isStreaming && (
          <p className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground">
            Ask the Copilot for a preamble, a section skeleton, or an FAQ
            answer. It only quotes clauses it can cite.
          </p>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            data-testid={`chat-${m.role}`}
            className={m.role === "user" ? "flex justify-end" : ""}
          >
            <div
              className={[
                "max-w-[92%] rounded-lg p-2.5 text-sm",
                m.role === "user"
                  ? "bg-cyan-500 text-slate-950"
                  : "bg-muted text-foreground",
              ].join(" ")}
            >
              {/* The user's own message stays plain text; the Copilot's reply
                  is Markdown, so bold/lists/headings render as formatting. */}
              {m.role === "user" ? (
                <p className="leading-snug">{m.text}</p>
              ) : (
                <CopilotMarkdown>{m.text}</CopilotMarkdown>
              )}

              {m.citations?.map((c: CopilotCitation) => (
                <blockquote
                  key={c.clause_number}
                  data-testid="copilot-citation"
                  className="mt-2 border-l-2 border-gray-400 bg-card/70 py-1 pl-2"
                >
                  <p className="font-mono text-[10px] font-semibold text-muted-foreground">
                    {c.clause_number}
                  </p>
                  <p className="text-[12px] italic leading-snug text-foreground">
                    &ldquo;{c.text}&rdquo;
                  </p>
                </blockquote>
              ))}

              {m.snippet_html && (
                <SuggestionCard
                  html={m.snippet_html}
                  onInsert={() => onInsertSnippet(m.snippet_html!)}
                />
              )}
            </div>
          </div>
        ))}

        {/* Partial message bubble while streaming */}
        {isStreaming && streamingText && (
          <div data-testid="chat-copilot-streaming">
            <div className="max-w-[92%] rounded-lg bg-muted p-2.5 text-sm text-foreground">
              <CopilotMarkdown>{streamingText}</CopilotMarkdown>
              <span className="ml-1 inline-block h-3 w-0.5 animate-pulse bg-current" />
            </div>
          </div>
        )}

        {/* Progress bar only while connecting (before first token) */}
        {isConnecting && (
          <AnalyzeProgressBar isPending={true} stages={COPILOT_STAGES} />
        )}

        {errorText && <p className="text-xs text-red-600">{errorText}</p>}
      </div>

      <form
        className="mt-2 flex gap-1.5 px-1"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <MentionInput
          value={input}
          onChange={setInput}
          cards={reviewedCards}
          disabled={isPending}
        />
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-cyan-500 px-3 py-1.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}

/** A Copilot-proposed clause the drafter can drop into their document. Shows a
 *  sanitized preview and inserts at the drafter's cursor on click (the drafter
 *  first clicks where they want it in the draft, then presses Insert). */
function SuggestionCard({
  html,
  onInsert,
}: {
  html: string;
  onInsert: () => void;
}) {
  const clean = DOMPurify.sanitize(html, SNIPPET_PURIFY);
  return (
    <div
      data-testid="copilot-suggestion"
      className="mt-2 rounded-lg border border-cyan-400/40 bg-card/60 p-2"
    >
      <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-cyan-300">
        <FilePlus2 className="h-3.5 w-3.5" />
        Suggested addition to your draft
      </p>
      <div
        className="max-h-40 overflow-y-auto rounded bg-background/40 p-2 text-[12px] leading-snug [&_h2]:mt-0 [&_h2]:text-[11px] [&_h2]:font-bold [&_h3]:text-[11px] [&_h3]:font-semibold [&_p]:mt-1"
        data-testid="copilot-snippet-preview"
        dangerouslySetInnerHTML={{ __html: clean }}
      />
      <button
        type="button"
        onClick={onInsert}
        className="mt-2 flex items-center gap-1.5 rounded bg-cyan-500 px-2 py-1 text-[11px] font-semibold text-slate-950 hover:bg-cyan-400"
      >
        <MousePointerClick className="h-3.5 w-3.5" />
        Insert at cursor
      </button>
      <p className="mt-1 text-[10px] leading-snug text-muted-foreground">
        Click where you want it in your draft to place the cursor, then press
        Insert at cursor.
      </p>
    </div>
  );
}
