import { Link } from "react-router-dom";
import { Lock } from "lucide-react";

import { PlaybookDraftUpload } from "./PlaybookDraftUpload";
import type { PlaybookStage } from "./playbookStages";

interface Props {
  stage: PlaybookStage;
  value: string;
  onChange: (next: string) => void;
  /** Where `/explore-task` sends the drafter to change what it reports. */
  profileHref: string;
}

/** One stage's section of the Playbook.
 *
 *  Editable stages render a labelled textarea. The locked stage renders no form
 *  control at all — not a disabled one. A disabled textarea still looks like a
 *  field that might one day be filled in, and it would sit in the tab order as a
 *  dead stop; an explanation plus a link to the thing that actually governs the
 *  stage is the honest rendering.
 */
export function PlaybookSection({
  stage,
  value,
  onChange,
  profileHref,
}: Props) {
  const locked = stage.section === null;
  const id = `playbook-${stage.stage.replace(/^\//, "")}`;

  return (
    <section
      data-testid="playbook-section"
      data-stage={stage.stage}
      data-locked={locked}
      aria-disabled={locked || undefined}
      className="rounded-lg border border-border/60 bg-card p-3"
    >
      <div className="mb-1 flex items-center gap-1.5">
        <h3 className="font-mono text-xs font-bold text-primary">
          {stage.label}
        </h3>
        {locked && (
          <Lock aria-hidden="true" className="h-3 w-3 text-muted-foreground" />
        )}
      </div>

      <p className="mb-2 text-[11px] leading-relaxed text-muted-foreground">
        {stage.helper}
      </p>

      {locked ? (
        <div data-testid="explore-task-locked">
          <Link
            to={profileHref}
            className="text-[11px] font-semibold text-primary hover:text-primary/80"
          >
            Open the document's regulatory profile →
          </Link>
        </div>
      ) : (
        <>
          <label htmlFor={id} className="sr-only">
            {stage.label} instructions
          </label>
          <textarea
            id={id}
            data-testid="playbook-input"
            data-section={stage.section}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            rows={4}
            className="w-full rounded-md border border-border/60 bg-background p-2 text-xs leading-relaxed outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
          />
          {stage.section === "draft" && <PlaybookDraftUpload />}
        </>
      )}
    </section>
  );
}
