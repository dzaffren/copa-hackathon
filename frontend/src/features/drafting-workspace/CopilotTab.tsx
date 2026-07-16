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
          className="w-full rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm"
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
          <p className="rounded-lg bg-gray-50 p-3 text-sm text-muted-foreground">
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
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-900",
              ].join(" ")}
            >
              <p className="leading-snug">{m.text}</p>

              {m.citations?.map((c) => (
                <blockquote
                  key={c.clause_number}
                  data-testid="copilot-citation"
                  className="mt-2 border-l-2 border-gray-400 bg-white/70 py-1 pl-2"
                >
                  <p className="font-mono text-[10px] font-semibold text-gray-600">
                    {c.clause_number}
                  </p>
                  <p className="text-[12px] italic leading-snug text-gray-700">
                    “{c.text}”
                  </p>
                </blockquote>
              ))}

              {m.snippet_html && (
                <div className="mt-2 rounded border border-indigo-200 bg-white p-2">
                  <div
                    className="prose-sm max-h-40 overflow-y-auto text-[12px] [&_h2]:mt-0 [&_h2]:text-[11px] [&_h2]:font-bold [&_p]:mt-1"
                    data-testid="copilot-snippet-preview"
                    dangerouslySetInnerHTML={{ __html: m.snippet_html }}
                  />
                  <div className="mt-2 flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => onInsertSnippet(m.snippet_html!)}
                      className="rounded bg-indigo-600 px-2 py-1 text-[11px] font-semibold text-white hover:bg-indigo-700"
                    >
                      Insert into draft
                    </button>
                    <button
                      type="button"
                      onClick={() => send.mutate("Regenerate")}
                      className="rounded border border-gray-300 px-2 py-1 text-[11px] font-semibold hover:bg-gray-50"
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
          className="flex-1 rounded-md border border-gray-200 px-2 py-1.5 text-sm"
        />
        <button
          type="submit"
          disabled={send.isPending}
          className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
