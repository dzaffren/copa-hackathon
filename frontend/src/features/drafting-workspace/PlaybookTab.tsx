import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { fetchPlaybook, savePlaybook } from "@/lib/api";
import type { Playbook, PlaybookSectionKey } from "@/lib/types";
import { PLAYBOOK_STAGES } from "./playbookStages";
import { PlaybookSection } from "./PlaybookSection";

interface Props {
  workstreamId: string;
  nodeId: string;
}

type Sections = Pick<Playbook, PlaybookSectionKey>;

const EMPTY: Sections = {
  brainstorm: "",
  draft: "",
  write: "",
  deliver: "",
};

function sectionsOf(playbook: Playbook): Sections {
  return {
    brainstorm: playbook.brainstorm,
    draft: playbook.draft,
    write: playbook.write,
    deliver: playbook.deliver,
  };
}

/** The Playbook tab: what the drafter tells each Copilot stage to do for her.
 *
 *  Replaced the Reviewed tab, which duplicated the task screen. One section per
 *  stage, in the order the stages run, derived from the Copilot's own command
 *  list so the two cannot drift.
 *
 *  One Save for the whole form, and a FULL REPLACEMENT on the wire: all four
 *  sections always travel, so clearing one is a real edit rather than an omission
 *  the server has to guess about.
 */
export function PlaybookTab({ workstreamId, nodeId }: Props) {
  const queryClient = useQueryClient();
  const queryKey = ["playbook", workstreamId];
  const [draft, setDraft] = useState<Sections | null>(null);
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey,
    queryFn: () => fetchPlaybook(workstreamId),
  });

  // Seed once from the server, then leave alone: re-seeding on every render would
  // discard what the drafter is typing.
  useEffect(() => {
    if (query.data && draft === null) setDraft(sectionsOf(query.data));
  }, [query.data, draft]);

  const mutation = useMutation({
    mutationFn: (sections: Sections) => savePlaybook(workstreamId, sections),
    onMutate: () => setError(null),
    onSuccess: (saved) => {
      queryClient.setQueryData<Playbook>(queryKey, saved);
      setDraft(sectionsOf(saved));
    },
    // The drafter's edits stay on screen: she may have typed several paragraphs,
    // and losing them to a failed request would be worse than the failure.
    onError: () => setError("We could not save your playbook. Try again."),
  });

  const values = draft ?? EMPTY;
  const stored = query.data ? sectionsOf(query.data) : null;
  const dirty =
    stored !== null &&
    PLAYBOOK_STAGES.some(
      (stage) =>
        stage.section !== null &&
        values[stage.section] !== stored[stage.section],
    );

  if (query.isPending) {
    return (
      <div
        role="status"
        className="flex items-center gap-2 p-4 text-sm text-muted-foreground"
      >
        <Loader2 className="h-4 w-4 animate-spin" /> Loading playbook…
      </div>
    );
  }

  if (query.isError) {
    return (
      <p className="p-4 text-sm text-muted-foreground">
        We could not load the playbook for this workstream.
      </p>
    );
  }

  return (
    <div data-testid="playbook-tab" className="space-y-2">
      <p className="text-[11px] leading-relaxed text-muted-foreground">
        What each Copilot stage should do for you. Saved here, it applies to
        every draft in this workstream — you do not restate it in the
        conversation.
      </p>

      {PLAYBOOK_STAGES.map((stage) => (
        <PlaybookSection
          key={stage.stage}
          stage={stage}
          value={stage.section ? values[stage.section] : ""}
          onChange={(next) =>
            stage.section && setDraft({ ...values, [stage.section]: next })
          }
          profileHref={`/workstreams/${workstreamId}?node=${encodeURIComponent(nodeId)}`}
        />
      ))}

      {error && <p className="text-[11px] text-destructive">{error}</p>}

      <div className="flex items-center gap-2 pb-2">
        <Button
          size="sm"
          data-testid="playbook-save"
          disabled={!dirty || mutation.isPending}
          onClick={() => mutation.mutate(values)}
        >
          {mutation.isPending && (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          )}
          Save
        </Button>
        {query.data?.updated_at && !dirty && (
          <span className="text-[11px] text-muted-foreground">Saved</span>
        )}
      </div>
    </div>
  );
}
