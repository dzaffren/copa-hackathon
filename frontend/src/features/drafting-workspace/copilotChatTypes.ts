import type { CommandStepStatus } from "./CommandTranscript";
import type { ClauseCitation, SlashCommandId } from "./copilotV2Data";

// The chat message model for the Copilot chatbox. The panel is a static, scripted
// demo (no live model — see CLAUDE.md "the API is a fixture projection"), so every
// scripted moment — a command running, the silent context pull, a clarification
// question, the drafted-sections summary — is represented as one entry in an
// append-only `messages[]` stream, each keyed by a stable `id`. A command's
// lifecycle mutates its own message in place (statusLine, stepIndex, answered)
// as its timers tick; nothing downstream is appended until invoked, so commands
// reveal one at a time rather than all up front.

export type ChatMsgKind =
  | "user"
  | "text"
  | "command"
  | "thinking"
  | "question"
  | "suggestion"
  | "banner";

/** A document/node the drafter referenced with `@` in a message. */
export interface MentionRef {
  id: string;
  label: string;
}

export interface UserMsg {
  id: string;
  kind: "user";
  text: string;
  mentions?: MentionRef[];
}

/** Assistant prose. `citations` render as compact clause chips beneath the text. */
export interface TextMsg {
  id: string;
  kind: "text";
  text: string;
  citations?: ClauseCitation[];
}

/** Which expandable body a command block renders once it has run. */
export type CommandDetailKind = "metadata" | "outline" | "deliver" | null;

export interface CommandMsg {
  id: string;
  kind: "command";
  command: SlashCommandId;
  status: CommandStepStatus;
  statusLine: string;
  detailKind: CommandDetailKind;
}

/** The silent `/pull-context` sub-step: the thinking orb cycling THINKING_STEPS. */
export interface ThinkingMsg {
  id: string;
  kind: "thinking";
  stepIndex: number;
  done: boolean;
}

export type QuestionKind = "leading" | "clarification";

export interface QuestionMsg {
  id: string;
  kind: "question";
  questionKind: QuestionKind;
  /** Index into CLARIFICATION_QUESTIONS for clarification turns; unused otherwise. */
  questionId?: string;
  /** The answer the drafter picked/typed, once answered — locks the card. */
  answered?: string;
}

/** A clickable next-step chip row — how the "reveal one by one" flow advances. */
export interface SuggestionOption {
  label: string;
  command?: SlashCommandId;
}

export interface SuggestionMsg {
  id: string;
  kind: "suggestion";
  options: SuggestionOption[];
  /** Once a chip is used, the row is spent and stops offering actions. */
  used?: boolean;
}

/** A one-time dismissable notice — used after /write to confirm the full
 *  document landed in the editor. */
export interface BannerMsg {
  id: string;
  kind: "banner";
  text: string;
  dismissed?: boolean;
}

export type ChatMsg =
  | UserMsg
  | TextMsg
  | CommandMsg
  | ThinkingMsg
  | QuestionMsg
  | SuggestionMsg
  | BannerMsg;
