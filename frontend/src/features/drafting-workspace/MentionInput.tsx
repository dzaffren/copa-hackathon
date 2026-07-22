import { useMemo, useRef, useState } from "react";
import * as Popover from "@radix-ui/react-popover";

import type { LinkageCard } from "@/lib/types";
import { labelStyle, labelText } from "@/features/task/semanticLabel";

const TRIGGER = /@(\w*)$/;

/** Extracts every `@{card.id}` token in `text` that matches a known accepted
 *  finding, deduplicated — sent alongside the message as
 *  `referenced_finding_ids` so the backend can ground its reply with those
 *  findings' verbatim clauses (see `engine/copilot.py`'s grounding context).
 *  A `@word` that doesn't match a real card id is left as plain text — no
 *  false-positive references. */
export function parseMentions(
  text: string,
  cards: LinkageCard[],
): { referencedFindingIds: string[] } {
  const knownIds = new Set(cards.map((c) => c.id));
  const found = new Set<string>();
  for (const match of text.matchAll(/@(\S+)/g)) {
    if (knownIds.has(match[1])) found.add(match[1]);
  }
  return { referencedFindingIds: [...found] };
}

interface MentionInputProps {
  value: string;
  onChange: (value: string) => void;
  cards: LinkageCard[];
  disabled?: boolean;
}

/** The Copilot's message input, with an `@`-triggered dropdown over the
 *  drafter's already-accepted findings (`cards`). Selecting an entry inserts
 *  the card's own `id` as a plain `@{id}` token — supporting multiple
 *  references in one message is then just "however many tokens appear in the
 *  text," parsed by `parseMentions` on submit. The token is the raw id
 *  (not a pretty label): a plain `<input>` can't style part of its own text,
 *  so a human-friendly rendering is deferred to the read-only message list. */
export function MentionInput({
  value,
  onChange,
  cards,
  disabled,
}: MentionInputProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const matches = useMemo(() => {
    if (!open || cards.length === 0) return [];
    const q = query.toLowerCase();
    return cards
      .filter((c) =>
        `${c.summary} ${c.right.title ?? ""} ${c.left.title ?? ""}`
          .toLowerCase()
          .includes(q),
      )
      .slice(0, 6);
  }, [open, query, cards]);

  function handleChange(next: string) {
    onChange(next);
    const caret = inputRef.current?.selectionStart ?? next.length;
    const trigger = next.slice(0, caret).match(TRIGGER);
    if (trigger) {
      setQuery(trigger[1]);
      setOpen(true);
    } else {
      setOpen(false);
    }
  }

  function select(card: LinkageCard) {
    const caret = inputRef.current?.selectionStart ?? value.length;
    const upToCaret = value.slice(0, caret);
    const next = upToCaret.replace(TRIGGER, `@${card.id} `) + value.slice(caret);
    onChange(next);
    setOpen(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  return (
    <Popover.Root open={open && matches.length > 0}>
      <Popover.Anchor asChild>
        <input
          ref={inputRef}
          aria-label="Message the Copilot"
          value={value}
          disabled={disabled}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setOpen(false);
            if (e.key === "Enter" && open && matches.length > 0) {
              e.preventDefault();
              select(matches[0]);
            }
          }}
          placeholder="Ask the Copilot… (@ to reference an accepted finding)"
          className="flex-1 rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-cyan-400/60"
        />
      </Popover.Anchor>
      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={4}
          onOpenAutoFocus={(e) => e.preventDefault()}
          className="z-50 w-72 space-y-0.5 rounded-md border border-border/60 bg-popover p-1 shadow-lg"
        >
          {matches.map((card) => (
            <button
              key={card.id}
              type="button"
              onClick={() => select(card)}
              className="block w-full rounded px-2 py-1.5 text-left text-xs hover:bg-accent"
            >
              <span
                className={`mr-1.5 rounded px-1 py-0.5 text-[10px] font-semibold ${labelStyle(card.label).pill}`}
              >
                {labelText(card.label, card.sentiment)}
              </span>
              <span className="text-muted-foreground">
                {card.right.title ?? card.left.title}
              </span>
              <p className="mt-0.5 truncate text-foreground">{card.summary}</p>
            </button>
          ))}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
