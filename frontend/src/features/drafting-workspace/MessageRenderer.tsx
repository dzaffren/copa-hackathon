import { CheckCircle2, Send, Sparkles } from "lucide-react";
import {
  CommandTranscript,
  SilentSubStep,
  type CommandStep,
} from "./CommandTranscript";
import {
  ClarificationCard,
} from "./ClarificationCard";
import {
  ConfidenceMeter,
  ContextCard,
  DraftSectionSummary,
  NodeMetadataList,
  ThinkingOrb,
} from "./copilotViews";
import {
  ANCHOR_DOCS,
  CLARIFICATION_QUESTIONS,
  DRAFT_SECTIONS,
  LEADING_OPTIONS,
  LEADING_QUESTION,
  RELEASE_REVIEWERS,
  THINKING_STEPS,
  WORKSTREAM_CONTEXT,
  type SlashCommandId,
} from "./copilotV2Data";
import type {
  ChatMsg,
  CommandMsg,
  QuestionMsg,
  SuggestionMsg,
} from "./copilotChatTypes";

export interface MessageHandlers {
  onAnswerQuestion: (msg: QuestionMsg, answer: string) => void;
  onRunCommand: (id: SlashCommandId) => void;
  onUseSuggestion: (msg: SuggestionMsg, command?: SlashCommandId) => void;
  released: boolean;
  onRelease: () => void;
  expandedCommands: Set<string>;
  onToggleCommand: (id: string) => void;
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

function ReleasePanel({
  released,
  onRelease,
}: {
  released: boolean;
  onRelease: () => void;
}) {
  return (
    <div data-testid="release-panel" className="space-y-2 text-xs">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
          Owner
        </p>
        <p className="mt-0.5 text-foreground">{WORKSTREAM_CONTEXT.owner}</p>
      </div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
          Reviewers
        </p>
        <p className="mt-0.5 text-foreground">
          {RELEASE_REVIEWERS.length === 0 ? (
            <span className="italic text-muted-foreground">
              No reviewers on file for this task yet.
            </span>
          ) : (
            RELEASE_REVIEWERS.join(", ")
          )}
        </p>
      </div>
      {!released ? (
        <button
          type="button"
          onClick={onRelease}
          className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
        >
          <Send className="h-3.5 w-3.5" />
          Send for review
        </button>
      ) : (
        <p className="flex items-center gap-1.5 font-semibold text-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Sent to {WORKSTREAM_CONTEXT.owner}.
        </p>
      )}
    </div>
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
          <NodeMetadataList />
        </div>
      );
    case "outline":
      return (
        <ol className="list-decimal space-y-1 pl-4 text-xs text-foreground">
          {DRAFT_SECTIONS.map((s) => (
            <li key={s.id}>{s.title}</li>
          ))}
        </ol>
      );
    case "deliver":
      return <ReleasePanel released={h.released} onRelease={h.onRelease} />;
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
        <div data-testid="assistant-text" className="space-y-1.5">
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

    case "draft-summary": {
      const sections = msg.sectionIds
        .map((id) => DRAFT_SECTIONS.find((s) => s.id === id))
        .filter((s): s is (typeof DRAFT_SECTIONS)[number] => Boolean(s));
      return (
        <div data-testid="draft-summary" className="space-y-2">
          {sections.map((section, i) => (
            <DraftSectionSummary key={section.id} section={section} index={i} />
          ))}
        </div>
      );
    }

    default:
      return null;
  }
}
