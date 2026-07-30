import type { CopilotDraftContext, LinkageCard } from "@/lib/types";
import { CopilotChat } from "./CopilotChat";

interface CopilotTabProps {
  workstreamId: string;
  nodeId: string;
  onInsertSnippet: (html: string) => void;
  /** /draft and /write each replace the whole document rather than insert a
   *  snippet — distinct from onInsertSnippet, per Decision 5's pattern of
   *  not conflating different concepts under one callback. */
  onReplaceDraft: (html: string) => void;
  /** The drafter's already-accepted findings for this task. Retained on the
   *  props contract; unused by this static demo panel. */
  reviewedCards: LinkageCard[];
  /** Reads the drafter's live editor content + current highlighted selection.
   *  Retained on the contract; unused by this static demo panel. */
  getDraftContext: () => CopilotDraftContext;
}

/** The Copilot tab — a flexible, Claude-Code-style chatbox. All conversation
 *  logic and the scripted demo flow live in CopilotChat; this wrapper keeps the
 *  props contract DraftingWorkspacePage passes (only onInsertSnippet and
 *  onReplaceDraft are used — the others are retained for the eventual live
 *  wiring). */
export function CopilotTab({ onInsertSnippet, onReplaceDraft }: CopilotTabProps) {
  return <CopilotChat onInsertSnippet={onInsertSnippet} onReplaceDraft={onReplaceDraft} />;
}
