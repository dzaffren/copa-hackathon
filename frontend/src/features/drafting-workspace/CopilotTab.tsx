import type { CopilotDraftContext, LinkageCard } from "@/lib/types";
import { CopilotChat } from "./CopilotChat";

interface CopilotTabProps {
  workstreamId: string;
  nodeId: string;
  onInsertSnippet: (html: string) => void;
  /** The drafter's already-accepted findings for this task. Retained on the
   *  props contract; unused by this static demo panel. */
  reviewedCards: LinkageCard[];
  /** Reads the drafter's live editor content + current highlighted selection.
   *  Retained on the contract; unused by this static demo panel. */
  getDraftContext: () => CopilotDraftContext;
}

/** The Copilot tab — a flexible, Claude-Code-style chatbox. All conversation
 *  logic and the scripted demo flow live in CopilotChat; this wrapper keeps the
 *  props contract DraftingWorkspacePage passes (only onInsertSnippet is used —
 *  the others are retained for the eventual live wiring). */
export function CopilotTab({ onInsertSnippet }: CopilotTabProps) {
  return <CopilotChat onInsertSnippet={onInsertSnippet} />;
}
