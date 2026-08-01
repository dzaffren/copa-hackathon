import { SLASH_COMMANDS, type SlashCommandId } from "./copilotV2Data";
import type { PlaybookSectionKey } from "@/lib/types";

export interface PlaybookStage {
  stage: SlashCommandId;
  label: string;
  /** What the drafter records here, in her terms — not a restatement of the
   *  stage's name. */
  helper: string;
  /** The stored section, or `null` for the locked stage, which has none. */
  section: PlaybookSectionKey | null;
}

const HELPERS: Record<SlashCommandId, string> = {
  "/explore-task":
    "Reads this document's recorded regulatory profile. Nothing to configure — change the profile itself to change what this stage reports.",
  "/brainstorm":
    "The drafting decisions you have already taken, and what you want done with each — evidence for, or peer practice against. Written here, they are waiting when the stage runs.",
  "/draft":
    "The template or style guide a draft should follow — the house skeleton, the numbering convention.",
  "/write":
    "Writing preferences and house rules. How obligations and guidance are phrased, where defined terms may appear.",
  "/deliver":
    "Approval and review conventions, and the layers to route to. Recorded so the Copilot can prepare the routing — nothing is ever sent.",
};

const SECTIONS: Record<SlashCommandId, PlaybookSectionKey | null> = {
  // No section, deliberately. `/explore-task` reports what the document's profile
  // records; an editable override would let the tool state a regulatory identity
  // the document does not have. Locked in the data, not merely in the markup.
  "/explore-task": null,
  "/brainstorm": "brainstorm",
  "/draft": "draft",
  "/write": "write",
  "/deliver": "deliver",
};

/** The five stages in the order the Copilot runs them.
 *
 *  Derived from `SLASH_COMMANDS` rather than hand-listed, so a stage added or
 *  reordered there flows through here. That is what stops the Playbook drifting
 *  from the flow it configures — a form claiming to configure five stages in
 *  order is only true while the two lists agree.
 */
export const PLAYBOOK_STAGES: PlaybookStage[] = SLASH_COMMANDS.map(
  (command) => ({
    stage: command.id,
    label: command.label,
    helper: HELPERS[command.id],
    section: SECTIONS[command.id],
  }),
);
