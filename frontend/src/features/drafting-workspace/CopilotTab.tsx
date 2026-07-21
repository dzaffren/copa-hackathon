import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendCopilotMessage } from "@/lib/api";
import {
  COPILOT_INTENTS,
  COPILOT_INTENT_LABELS,
  type ChatMessage,
  type CopilotIntent,
} from "@/lib/types";

interface CopilotTabProps {
  workstreamId: string;
  nodeId: string;
  onInsertSnippet: (html: string) => void;
}

/** The Drafting Copilot: a scripted conversation, not a model.
 *
 * Every clause it quotes is verbatim and checkable — see
 * engine/copilot_scripts.py, whose tests re-resolve the RMiT quote against the
 * built clause index. Citations render as their own block precisely so a
 * reviewer can tell an assertion from a quotation at a glance.
 */
export function CopilotTab({
  workstreamId,
  nodeId,
  onInsertSnippet,
}: CopilotTabProps) {
  const [intent, setIntent] = useState<CopilotIntent>("PD");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  // Copilot turns so far — the server holds no conversation state, because the
  // chat is deliberately not persisted across sessions.
  const turn = messages.filter((m) => m.role === "copilot").length;

  const send = useMutation({
    mutationFn: (text: string) =>
      sendCopilotMessage(workstreamId, nodeId, intent, text, turn),
    onSuccess: (res) =>
      setMessages((prev) => [...prev, { ...res.reply, role: "copilot" }]),
  });

  function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || send.isPending) return;
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    send.mutate(trimmed);
  }

  function changeIntent(next: CopilotIntent) {
    setIntent(next);
    // Resetting is the honest behaviour: the reply script is keyed on intent,
    // so keeping the old turns would leave answers on screen that the new
    // preset never gave.
    setMessages([]);
  }

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
        {messages.length === 0 && (
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
              <p className="leading-snug">{m.text}</p>

              {m.citations?.map((c) => (
                <blockquote
                  key={c.clause_number}
                  data-testid="copilot-citation"
                  className="mt-2 border-l-2 border-gray-400 bg-card/70 py-1 pl-2"
                >
                  <p className="font-mono text-[10px] font-semibold text-muted-foreground">
                    {c.clause_number}
                  </p>
                  <p className="text-[12px] italic leading-snug text-foreground">
                    “{c.text}”
                  </p>
                </blockquote>
              ))}

              {m.snippet_html && (
                <div className="mt-2 rounded border border-cyan-400/30 bg-card/60 p-2">
                  <div
                    className="prose-sm max-h-40 overflow-y-auto text-[12px] [&_h2]:mt-0 [&_h2]:text-[11px] [&_h2]:font-bold [&_p]:mt-1"
                    data-testid="copilot-snippet-preview"
                    dangerouslySetInnerHTML={{ __html: m.snippet_html }}
                  />
                  <div className="mt-2 flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => onInsertSnippet(m.snippet_html!)}
                      className="rounded bg-cyan-500 px-2 py-1 text-[11px] font-semibold text-slate-950 hover:bg-cyan-400"
                    >
                      Insert into draft
                    </button>
                    <button
                      type="button"
                      onClick={() => send.mutate("Regenerate")}
                      className="rounded border border-border/70 px-2 py-1 text-[11px] font-semibold hover:bg-accent"
                    >
                      Regenerate
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {send.isPending && (
          <p className="text-xs text-muted-foreground">Copilot is typing…</p>
        )}
      </div>

      <form
        className="mt-2 flex gap-1.5 px-1"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <input
          aria-label="Message the Copilot"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the Copilot…"
          className="flex-1 rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-cyan-400/60"
        />
        <button
          type="submit"
          disabled={send.isPending}
          className="rounded-md bg-cyan-500 px-3 py-1.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
