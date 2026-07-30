import { useEffect, useReducer, useRef } from "react";
import { RotateCcw } from "lucide-react";
import { ChatInput } from "./ChatInput";
import { MessageRenderer, type DeliveredTo, type MessageHandlers } from "./MessageRenderer";
import { WelcomeScreen } from "./WelcomeScreen";
import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";
import {
  CLARIFICATION_QUESTIONS,
  DRAFT_SECTIONS,
  NODE_METADATA,
  THINKING_STEPS,
  buildDraftOutline,
  buildFullDraft,
  isCommandUnlocked,
  type SlashCommandId,
} from "./copilotV2Data";
import type {
  ChatMsg,
  MentionRef,
  QuestionMsg,
  SuggestionMsg,
} from "./copilotChatTypes";

// The Copilot chatbox. A static, scripted demo (no live model) rendered as a
// Claude-Code-style conversation: an append-only message stream plus a bottom
// input with slash/mention autocomplete. Commands are invoked by the drafter
// (typed, /-picked, or via a suggestion chip) and reveal one at a time; each
// runs a scripted lifecycle that mutates its own message as timers tick.

const THINKING_STEP_MS = 450;
const METADATA_REVEAL_MS = 500;
const BUILD_REVEAL_MS = 600;

const METADATA_AVAILABLE = NODE_METADATA.filter((f) => f.value !== null).length;

// --- Reducer ---------------------------------------------------------------

interface ChatState {
  messages: ChatMsg[];
  delivered: DeliveredTo | null;
  expandedCommands: Set<string>;
  resolvedFields: Record<string, string>;
  /** Commands whose lifecycle has reached its terminal step — gates which
   *  command runs next (see isCommandUnlocked). */
  completedSteps: Set<SlashCommandId>;
}

/** A partial patch merged into an existing message by id. Typed loosely because
 *  ChatMsg is a discriminated union (Partial<ChatMsg> would only expose the
 *  common keys); the reducer re-casts the merged result back to ChatMsg. */
type MsgPatch = Record<string, unknown>;

type Action =
  | { type: "append"; msg: ChatMsg }
  | { type: "update"; id: string; patch: MsgPatch }
  | { type: "deliver"; recipient: DeliveredTo }
  | { type: "resolve-fields"; values: Record<string, string> }
  | { type: "toggle-command"; id: string }
  | { type: "complete-step"; id: SlashCommandId }
  | { type: "reset"; state: ChatState };

function reducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case "append":
      return { ...state, messages: [...state.messages, action.msg] };
    case "update":
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.id ? ({ ...m, ...action.patch } as ChatMsg) : m,
        ),
      };
    case "deliver":
      return { ...state, delivered: action.recipient };
    case "resolve-fields":
      return { ...state, resolvedFields: { ...state.resolvedFields, ...action.values } };
    case "toggle-command": {
      const next = new Set(state.expandedCommands);
      if (next.has(action.id)) next.delete(action.id);
      else next.add(action.id);
      return { ...state, expandedCommands: next };
    }
    case "complete-step":
      return { ...state, completedSteps: new Set(state.completedSteps).add(action.id) };
    case "reset":
      return action.state;
    default:
      return state;
  }
}

function initialState(): ChatState {
  return {
    messages: [],
    delivered: null,
    expandedCommands: new Set(),
    resolvedFields: {},
    completedSteps: new Set(),
  };
}

export function CopilotChat({
  onInsertSnippet,
  onReplaceDraft,
}: {
  onInsertSnippet: (html: string) => void;
  onReplaceDraft: (html: string) => void;
}) {
  const [state, dispatch] = useReducer(reducer, undefined, initialState);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Stable id generator (no Date.now/Math.random needed) and timer registry so
  // an unmount or "Start over" cancels any in-flight scripted sequence.
  const idRef = useRef(0);
  const nextId = () => `m${++idRef.current}`;
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const intervals = useRef<ReturnType<typeof setInterval>[]>([]);
  const brainstormCmdId = useRef<string | null>(null);
  const deliverCmdId = useRef<string | null>(null);
  const insertRef = useRef(onInsertSnippet);
  insertRef.current = onInsertSnippet;
  const replaceRef = useRef(onReplaceDraft);
  replaceRef.current = onReplaceDraft;

  function later(fn: () => void, ms: number) {
    const t = setTimeout(fn, ms);
    timers.current.push(t);
    return t;
  }
  function clearAll() {
    timers.current.forEach(clearTimeout);
    intervals.current.forEach(clearInterval);
    timers.current = [];
    intervals.current = [];
  }
  useEffect(() => clearAll, []);

  const append = (msg: ChatMsg) => dispatch({ type: "append", msg });
  const update = (id: string, patch: MsgPatch) =>
    dispatch({ type: "update", id, patch });

  function suggest(options: SuggestionMsg["options"]) {
    append({ id: nextId(), kind: "suggestion", options });
  }

  // --- Command lifecycles --------------------------------------------------

  function runExploreTask() {
    const cmdId = nextId();
    append({
      id: cmdId,
      kind: "command",
      command: "/explore-task",
      status: "active",
      statusLine: "Pulling node metadata…",
      detailKind: null,
    });
    later(() => {
      update(cmdId, {
        status: "done",
        statusLine: `${METADATA_AVAILABLE} of ${NODE_METADATA.length} fields found on the connected anchor document.`,
        detailKind: "metadata",
      });
      append({
        id: nextId(),
        kind: "text",
        text: "Here's the task's regulatory profile — task type through legal basis. Fields with no honest source read \"Not available\" rather than a guess.",
      });
    }, METADATA_REVEAL_MS);
  }

  function onSubmitMissingFields(values: Record<string, string>) {
    dispatch({ type: "resolve-fields", values });
    dispatch({ type: "complete-step", id: "/explore-task" });
    append({
      id: nextId(),
      kind: "text",
      text: "Thanks — I've folded those into the task's profile.",
    });
    suggest([{ label: "Run /brainstorm", command: "/brainstorm" }]);
  }

  function runBrainstorm() {
    const cmdId = nextId();
    brainstormCmdId.current = cmdId;
    append({
      id: cmdId,
      kind: "command",
      command: "/brainstorm",
      status: "active",
      statusLine: "Pulling context…",
      detailKind: null,
    });
    const thinkId = nextId();
    append({ id: thinkId, kind: "thinking", stepIndex: 0, done: false });

    let step = 0;
    const interval = setInterval(() => {
      step = Math.min(step + 1, THINKING_STEPS.length - 1);
      update(thinkId, { stepIndex: step });
      if (step >= THINKING_STEPS.length - 1) {
        clearInterval(interval);
        later(() => {
          update(thinkId, { done: true });
          update(cmdId, {
            statusLine: "Context pulled — let's align on the focus.",
          });
          append({ id: nextId(), kind: "question", questionKind: "leading" });
        }, 500);
      }
    }, THINKING_STEP_MS);
    intervals.current.push(interval);
  }

  function finalizeBrainstorming() {
    if (brainstormCmdId.current) {
      update(brainstormCmdId.current, {
        status: "done",
        statusLine: "Understanding aligned ✓",
      });
    }
    dispatch({ type: "complete-step", id: "/brainstorm" });
    append({
      id: nextId(),
      kind: "text",
      text: "Understanding aligned ✓ — I have enough to outline the draft.",
    });
    suggest([{ label: "Run /draft", command: "/draft" }]);
  }

  function runDraftOutline() {
    replaceRef.current(buildDraftOutline());
    dispatch({ type: "complete-step", id: "/draft" });
    append({
      id: nextId(),
      kind: "command",
      command: "/draft",
      status: "done",
      statusLine: `Outline ready — ${DRAFT_OUTLINE_SECTIONS.length} sections.`,
      detailKind: "outline",
    });
    append({
      id: nextId(),
      kind: "text",
      text: "I've outlined the draft in your editor — replace each guidance block with your own drafting.",
    });
    suggest([{ label: "Run /write", command: "/write" }]);
  }

  function runWrite() {
    const cmdId = nextId();
    append({
      id: cmdId,
      kind: "command",
      command: "/write",
      status: "active",
      statusLine: `Writing ${DRAFT_SECTIONS.length} sections…`,
      detailKind: null,
    });
    later(() => {
      replaceRef.current(buildFullDraft());
      dispatch({ type: "complete-step", id: "/write" });
      update(cmdId, {
        status: "done",
        statusLine: `${DRAFT_SECTIONS.length} sections written into your editor.`,
      });
      append({
        id: nextId(),
        kind: "banner",
        text: "This draft has been inserted into the editor. You may edit it directly.",
      });
      append({
        id: nextId(),
        kind: "text",
        text: "Done — I've written the full document straight into your editor, every clause quoted verbatim. Review and edit it inline.",
      });
      suggest([{ label: "Run /deliver", command: "/deliver" }]);
    }, BUILD_REVEAL_MS);
  }

  function onDismissBanner(id: string) {
    update(id, { dismissed: true });
  }

  function runDeliver() {
    const cmdId = nextId();
    deliverCmdId.current = cmdId;
    append({
      id: cmdId,
      kind: "command",
      command: "/deliver",
      status: "active",
      statusLine: "Ready to send for review.",
      detailKind: "deliver",
    });
  }

  function runCommand(id: SlashCommandId) {
    // Enforced regardless of how the command was invoked — a welcome-screen
    // step, a suggestion chip, the slash menu, or typing the exact command
    // — so there's no route around doing the flow in order.
    if (!isCommandUnlocked(id, state.completedSteps)) return;
    switch (id) {
      case "/explore-task":
        return runExploreTask();
      case "/brainstorm":
        return runBrainstorm();
      case "/draft":
        return runDraftOutline();
      case "/write":
        return runWrite();
      case "/deliver":
        return runDeliver();
    }
  }

  // --- Handlers ------------------------------------------------------------

  function onAnswerQuestion(msg: QuestionMsg, answer: string) {
    update(msg.id, { answered: answer });
    if (msg.questionKind === "leading") {
      append({
        id: nextId(),
        kind: "question",
        questionKind: "clarification",
        questionId: CLARIFICATION_QUESTIONS[0].id,
      });
      return;
    }
    // clarification
    const idx = CLARIFICATION_QUESTIONS.findIndex((q) => q.id === msg.questionId);
    const next = CLARIFICATION_QUESTIONS[idx + 1];
    if (next) {
      append({
        id: nextId(),
        kind: "question",
        questionKind: "clarification",
        questionId: next.id,
      });
    } else {
      finalizeBrainstorming();
    }
  }

  function onUseSuggestion(msg: SuggestionMsg, command?: SlashCommandId) {
    update(msg.id, { used: true });
    if (command) runCommand(command);
  }

  function onDeliver(recipient: DeliveredTo) {
    dispatch({ type: "deliver", recipient });
    dispatch({ type: "complete-step", id: "/deliver" });
    if (deliverCmdId.current) {
      update(deliverCmdId.current, {
        status: "done",
        statusLine: `Sent to ${recipient.name} (${recipient.email}).`,
      });
    }
  }

  function onSend(text: string, mentions: MentionRef[]) {
    void mentions; // parsed for future use; the scripted demo only echoes text
    append({ id: nextId(), kind: "user", text });
    append({
      id: nextId(),
      kind: "text",
      text: "I can help through a command — try /brainstorm to align on the draft, or /write to populate it. Type / to see every option.",
    });
  }

  function reset() {
    clearAll();
    brainstormCmdId.current = null;
    deliverCmdId.current = null;
    dispatch({ type: "reset", state: initialState() });
  }

  const handlers: MessageHandlers = {
    onAnswerQuestion,
    onRunCommand: runCommand,
    onUseSuggestion,
    delivered: state.delivered,
    onDeliver,
    expandedCommands: state.expandedCommands,
    onToggleCommand: (id) => dispatch({ type: "toggle-command", id }),
    resolvedFields: state.resolvedFields,
    onSubmitMissingFields,
    onDismissBanner,
  };

  // Keep the newest message in view as the conversation grows. Guarded because
  // jsdom (test env) doesn't implement Element.scrollTo.
  useEffect(() => {
    const el = scrollRef.current;
    if (el && typeof el.scrollTo === "function") {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [state.messages]);

  return (
    <div className="flex h-full flex-col" data-testid="copilot-chat">
      <div
        ref={scrollRef}
        className="flex-1 space-y-3 overflow-y-auto px-1 pb-2"
        aria-label="Copilot conversation"
      >
        {state.messages.length === 0 ? (
          <WelcomeScreen onRunCommand={runCommand} />
        ) : (
          <>
            <button
              type="button"
              onClick={reset}
              className="flex items-center gap-1.5 px-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
            >
              <RotateCcw className="h-3 w-3" />
              Start over
            </button>
            {state.messages.map((msg) => (
              <div
                key={msg.id}
                style={{ animation: "fadeSlideUp 0.4s var(--ease-out-expo) both" }}
              >
                <MessageRenderer msg={msg} handlers={handlers} />
              </div>
            ))}
          </>
        )}
      </div>

      <ChatInput onRunCommand={runCommand} onSend={onSend} />
    </div>
  );
}
