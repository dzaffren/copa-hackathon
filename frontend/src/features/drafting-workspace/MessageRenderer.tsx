import { useState } from "react";
import { Brain, CheckCircle2, Send, Sparkles, X } from "lucide-react";
import {
  CommandTranscript,
  SilentSubStep,
  type CommandStep,
} from "./CommandTranscript";
import {
  ClarificationCard,
} from "./ClarificationCard";
import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";
import {
  ConfidenceMeter,
  ContextCard,
  DraftInstructionCard,
  NodeMetadataList,
  ThinkingOrb,
} from "./copilotViews";
import {
  ANCHOR_DOCS,
  CLARIFICATION_QUESTIONS,
  LEADING_OPTIONS,
  LEADING_QUESTION,
  MISSING_FIELDS,
  THINKING_STEPS,
  type SlashCommandId,
} from "./copilotV2Data";
import type {
  ChatMsg,
  CommandMsg,
  QuestionMsg,
  SuggestionMsg,
} from "./copilotChatTypes";

export interface DeliveredTo {
  name: string;
  email: string;
}

export interface MessageHandlers {
  onAnswerQuestion: (msg: QuestionMsg, answer: string) => void;
  onRunCommand: (id: SlashCommandId) => void;
  onUseSuggestion: (msg: SuggestionMsg, command?: SlashCommandId) => void;
  delivered: DeliveredTo | null;
  onDeliver: (recipient: DeliveredTo) => void;
  expandedCommands: Set<string>;
  onToggleCommand: (id: string) => void;
  resolvedFields: Record<string, string>;
  onSubmitMissingFields: (values: Record<string, string>) => void;
  onDismissBanner: (id: string) => void;
}

function questionParts(msg: QuestionMsg): { prompt: string; options: string[] } {
  if (msg.questionKind === "leading") {
    return { prompt: LEADING_QUESTION, options: LEADING_OPTIONS };
  }
  const q = CLARIFICATION_QUESTIONS.find((c) => c.id === msg.questionId);
  return { prompt: q?.prompt ?? "", options: q?.options ?? [] };
}

/** Confidence for a clarification turn: how far through the questions it sits,
 *  stepping up by one once answered. The final answer lands on 100% → Aligned. */
function clarificationPct(msg: QuestionMsg): number {
  const total = CLARIFICATION_QUESTIONS.length;
  const idx = CLARIFICATION_QUESTIONS.findIndex((c) => c.id === msg.questionId);
  if (idx < 0) return 0;
  const done = msg.answered !== undefined ? idx + 1 : idx;
  return Math.round((done / total) * 100);
}

/** Who the draft goes to is the drafter's own call — every field here is
 *  typed in, never a fabricated default recipient. */
function DeliverPanel({
  delivered,
  onDeliver,
}: {
  delivered: DeliveredTo | null;
  onDeliver: (recipient: DeliveredTo) => void;
}) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [email, setEmail] = useState("");
  const canSend = name.trim().length > 0 && email.trim().length > 0;

  return (
    <div data-testid="deliver-panel" className="space-y-2 text-xs">
      {!delivered ? (
        <>
          <div>
            <label
              htmlFor="deliver-name"
              className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Name
            </label>
            <input
              id="deliver-name"
              aria-label="Recipient name"
              placeholder="e.g. Jarod N."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-0.5 w-full rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
            />
          </div>
          <div>
            <label
              htmlFor="deliver-role"
              className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Role
            </label>
            <input
              id="deliver-role"
              aria-label="Recipient role"
              placeholder="e.g. Policy Owner, Open Finance Division"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="mt-0.5 w-full rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
            />
          </div>
          <div>
            <label
              htmlFor="deliver-email"
              className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Email
            </label>
            <input
              id="deliver-email"
              aria-label="Recipient email"
              placeholder="e.g. name@bnm.gov.my"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-0.5 w-full rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
            />
          </div>
          <button
            type="button"
            disabled={!canSend}
            onClick={() => onDeliver({ name: name.trim(), email: email.trim() })}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
          >
            <Send className="h-3.5 w-3.5" />
            Send for Review
          </button>
        </>
      ) : (
        <p className="flex items-center gap-1.5 font-semibold text-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Draft submitted to {delivered.name} ({delivered.email}) for review.
        </p>
      )}
    </div>
  );
}

function MissingFieldsForm({
  onSubmit,
}: {
  onSubmit: (values: Record<string, string>) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const allFilled = MISSING_FIELDS.every((f) => (values[f.key] ?? "").trim().length > 0);

  return (
    <form
      data-testid="missing-fields-form"
      className="space-y-2 rounded-lg border border-dashed border-border/60 bg-muted/30 p-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (allFilled) onSubmit(values);
      }}
    >
      <p className="text-xs text-foreground">
        Some fields could not be resolved. Please provide the following to improve your draft:
      </p>
      {MISSING_FIELDS.map((f) => (
        <div key={f.key} className="space-y-1">
          <label
            htmlFor={`missing-${f.key}`}
            className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
          >
            {f.label}
          </label>
          <input
            id={`missing-${f.key}`}
            aria-label={f.label}
            placeholder={f.placeholder}
            value={values[f.key] ?? ""}
            onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
            className="w-full rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
          />
        </div>
      ))}
      <button
        type="submit"
        disabled={!allFilled}
        className="rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
      >
        Submit
      </button>
    </form>
  );
}

function commandDetail(msg: CommandMsg, h: MessageHandlers) {
  if (msg.command === "/write" && msg.status === "active") {
    return <ThinkingOrb />;
  }
  switch (msg.detailKind) {
    case "metadata":
      return (
        <div className="space-y-2">
          <ContextCard />
          <NodeMetadataList overrides={h.resolvedFields} />
          {Object.keys(h.resolvedFields).length === 0 && (
            <MissingFieldsForm onSubmit={h.onSubmitMissingFields} />
          )}
        </div>
      );
    case "outline":
      return (
        <div className="space-y-2">
          {DRAFT_OUTLINE_SECTIONS.map((s) => (
            <DraftInstructionCard key={s.id} section={s} />
          ))}
        </div>
      );
    case "deliver":
      return <DeliverPanel delivered={h.delivered} onDeliver={h.onDeliver} />;
    default:
      return undefined;
  }
}

export function MessageRenderer({
  msg,
  handlers,
}: {
  msg: ChatMsg;
  handlers: MessageHandlers;
}) {
  switch (msg.kind) {
    case "user":
      return (
        <div className="flex justify-end" data-testid="user-msg">
          <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3 py-1.5 text-sm text-primary-foreground">
            {msg.text}
          </div>
        </div>
      );

    case "text":
      return (
        <div className="flex items-start gap-2" data-testid="assistant-text">
          <span
            aria-hidden
            className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary"
          >
            <Brain className="h-3 w-3" />
          </span>
          <div className="min-w-0 flex-1 space-y-1.5">
            <p className="whitespace-pre-wrap text-sm leading-snug text-foreground">
              {msg.text}
            </p>
            {msg.citations && msg.citations.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {msg.citations.map((c) => (
                  <span
                    key={c.clauseNumber}
                    className="rounded border border-border/60 bg-muted/40 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                  >
                    {c.clauseNumber}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      );

    case "command": {
      const detail = commandDetail(msg, handlers);
      const step: CommandStep = {
        command: msg.command,
        status: msg.status,
        statusLine: msg.statusLine,
        detail,
        defaultOpen: detail !== undefined,
      };
      return (
        <CommandTranscript
          steps={[step]}
          expanded={handlers.expandedCommands}
          onToggle={handlers.onToggleCommand}
        />
      );
    }

    case "thinking": {
      const line = msg.done
        ? `Context pulled from ${ANCHOR_DOCS.length} anchor documents.`
        : THINKING_STEPS[Math.min(msg.stepIndex, THINKING_STEPS.length - 1)].text;
      return (
        <SilentSubStep command="/pull-context" statusLine={line} active={!msg.done} />
      );
    }

    case "question": {
      const { prompt, options } = questionParts(msg);
      const card = (
        <ClarificationCard
          prompt={prompt}
          options={options}
          answered={msg.answered}
          onAnswer={(a) => handlers.onAnswerQuestion(msg, a)}
          freeTextPlaceholder="Or type your own answer…"
        />
      );
      if (msg.questionKind === "clarification") {
        return (
          <div className="space-y-2">
            <ConfidenceMeter pct={clarificationPct(msg)} />
            {card}
          </div>
        );
      }
      return card;
    }

    case "suggestion":
      return (
        <div className="flex flex-wrap gap-1.5" data-testid="suggestion-row">
          {msg.options.map((o) => (
            <button
              key={o.label}
              type="button"
              data-testid="suggestion-chip"
              disabled={msg.used}
              onClick={() => handlers.onUseSuggestion(msg, o.command)}
              className="flex items-center gap-1.5 rounded-full border border-primary/40 bg-primary/5 px-3 py-1 text-xs font-semibold text-primary transition hover:bg-primary/10 disabled:opacity-40"
            >
              <Sparkles className="h-3 w-3" />
              {o.label}
            </button>
          ))}
        </div>
      );

    case "banner":
      if (msg.dismissed) return null;
      return (
        <div
          data-testid="write-banner"
          className="flex items-center justify-between gap-2 rounded-lg border border-primary/30 bg-primary/5 px-3 py-2 text-xs text-foreground"
        >
          <span>{msg.text}</span>
          <button
            type="button"
            aria-label="Dismiss"
            onClick={() => handlers.onDismissBanner(msg.id)}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      );

    default:
      return null;
  }
}
