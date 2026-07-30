import { useMemo, useRef, useState } from "react";
import { Send } from "lucide-react";
import { AutocompleteMenu, type AutocompleteItem } from "./AutocompleteMenu";
import {
  MENTIONABLE,
  SLASH_COMMANDS,
  type SlashCommandId,
} from "./copilotV2Data";
import type { MentionRef } from "./copilotChatTypes";

type MenuKind = "slash" | "mention" | null;

/** The `@token` immediately before the caret, if the current word is a mention
 *  in progress. Returns its start index and the text after the `@`. */
function activeMention(
  value: string,
  caret: number,
): { start: number; query: string } | null {
  const before = value.slice(0, caret);
  const at = before.lastIndexOf("@");
  if (at === -1) return null;
  // A mention token runs from "@" to the caret with no whitespace inside, and
  // "@" must start a word (preceded by start-of-string or a space).
  const token = before.slice(at);
  if (/\s/.test(token)) return null;
  const prev = at === 0 ? " " : before[at - 1];
  if (!/\s/.test(prev)) return null;
  return { start: at, query: token.slice(1) };
}

export function ChatInput({
  onRunCommand,
  onSend,
  disabled,
}: {
  onRunCommand: (id: SlashCommandId) => void;
  onSend: (text: string, mentions: MentionRef[]) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const [caret, setCaret] = useState(0);
  const [highlight, setHighlight] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // A slash command is offered while the whole value is a single "/token" with
  // no space yet; a mention while the word at the caret is an "@token".
  const isSlash = value.startsWith("/") && !/\s/.test(value);
  const mention = isSlash ? null : activeMention(value, caret);
  const menuKind: MenuKind = isSlash ? "slash" : mention ? "mention" : null;

  const items: AutocompleteItem[] = useMemo(() => {
    if (menuKind === "slash") {
      const q = value.slice(1).toLowerCase();
      return SLASH_COMMANDS.filter((c) => c.id.toLowerCase().includes(q)).map(
        (c) => ({ id: c.id, label: c.label, description: c.description }),
      );
    }
    if (menuKind === "mention" && mention) {
      const q = mention.query.toLowerCase();
      return MENTIONABLE.filter((m) =>
        m.label.toLowerCase().includes(q),
      ).map((m) => ({ id: m.id, label: m.label, description: m.kind }));
    }
    return [];
  }, [menuKind, value, mention]);

  const menuOpen = menuKind !== null && value.length > 0 && !dismissed;
  const clampedHighlight = Math.min(highlight, Math.max(0, items.length - 1));

  function resetCaret(el: HTMLTextAreaElement) {
    setCaret(el.selectionStart ?? el.value.length);
  }

  function pick(item: AutocompleteItem) {
    if (menuKind === "slash") {
      onRunCommand(item.id as SlashCommandId);
      setValue("");
      setHighlight(0);
      return;
    }
    if (menuKind === "mention" && mention) {
      const next =
        value.slice(0, mention.start) +
        `@${item.label} ` +
        value.slice(caret);
      setValue(next);
      setHighlight(0);
      // Restore focus so the drafter keeps typing after inserting a mention.
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  function submit() {
    const text = value.trim();
    if (!text) return;
    if (text.startsWith("/")) {
      const match = SLASH_COMMANDS.find((c) => c.id === text);
      setValue("");
      if (match) {
        onRunCommand(match.id);
      } else {
        onSend(text, []);
      }
      return;
    }
    const mentions: MentionRef[] = MENTIONABLE.filter((m) =>
      value.includes(`@${m.label}`),
    ).map((m) => ({ id: m.id, label: m.label }));
    setValue("");
    onSend(text, mentions);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (menuOpen && items.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setHighlight((h) => (h + 1) % items.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setHighlight((h) => (h - 1 + items.length) % items.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        pick(items[clampedHighlight]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setDismissed(true);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <form
      className="relative shrink-0 px-1 pt-2"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      {menuOpen && (
        <AutocompleteMenu
          items={items}
          highlight={clampedHighlight}
          onPick={pick}
          onHover={setHighlight}
          testId={menuKind === "slash" ? "slash-menu" : "mention-menu"}
          emptyLabel={menuKind === "slash" ? "No commands" : "No documents"}
        />
      )}
      <div className="flex items-end gap-1.5 rounded-xl border border-border/60 bg-background/60 px-2.5 py-1.5 focus-within:border-primary/60">
        <textarea
          ref={inputRef}
          aria-label="Message the Copilot"
          data-testid="chat-input"
          rows={1}
          value={value}
          disabled={disabled}
          placeholder="Message the Copilot — type / for commands, @ to reference a document"
          onChange={(e) => {
            setValue(e.target.value);
            resetCaret(e.target);
            setHighlight(0);
            setDismissed(false);
          }}
          onKeyUp={(e) => resetCaret(e.currentTarget)}
          onClick={(e) => resetCaret(e.currentTarget)}
          onKeyDown={onKeyDown}
          className="max-h-32 min-h-[1.5rem] min-w-0 flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
        <button
          type="submit"
          aria-label="Send"
          disabled={disabled || !value.trim()}
          className="flex shrink-0 items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:opacity-40"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
    </form>
  );
}
