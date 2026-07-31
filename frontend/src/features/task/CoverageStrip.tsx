import { Loader2, Search } from "lucide-react";

import { AnalyzeProgressBar } from "@/components/AnalyzeProgressBar";
import { Button } from "@/components/ui/button";
import { useAnalyzeEdge } from "@/lib/hooks/useAnalyzeEdge";
import type { UnanalysedPair } from "@/lib/types";

interface Props {
  workstreamId: string;
  pairs: UnanalysedPair[];
  onAnalysed: () => void;
  /** Fold to the count line alone. Driven by the findings list's scroll
   *  position — the gaps matter when you arrive, not while you are reading. */
  collapsed?: boolean;
}

/** Coverage gaps, above the label groups.
 *
 *  Grouping findings by label means a pair with no findings contributes no card
 *  and would vanish silently — so the pairs that have never been analysed get
 *  their own row, each with its own Analyze action. Renders nothing once every
 *  pair is analysed, so a fully-seeded demo workstream pays no visual cost.
 *
 *  Collapsing HIDES the rows rather than unmounting them: a row owns the state
 *  of its own in-flight analyze, and dropping it mid-request would take the
 *  progress bar with it and leave the drafter unsure whether the run survived.
 */
export function CoverageStrip({
  workstreamId,
  pairs,
  onAnalysed,
  collapsed = false,
}: Props) {
  if (pairs.length === 0) return null;

  return (
    <div
      data-testid="coverage-strip"
      data-collapsed={collapsed}
      className="shrink-0 border-b border-border/60 bg-muted/20 px-4 py-3"
    >
      <p className="text-[11px] font-semibold text-muted-foreground">
        Not yet analysed · {pairs.length}{" "}
        {pairs.length === 1 ? "pair" : "pairs"}
        {collapsed && (
          <span className="ml-1 font-normal opacity-70">
            · scroll up to expand
          </span>
        )}
      </p>
      {/* The `hidden` ATTRIBUTE, not a utility class: it hides the rows from
          assistive tech and the accessibility tree too, which a display class
          alone would not. */}
      <div hidden={collapsed} className="mt-2 space-y-2">
        {pairs.map((pair) => (
          <CoveragePairRow
            key={pair.edge_id}
            workstreamId={workstreamId}
            pair={pair}
            onAnalysed={onAnalysed}
          />
        ))}
      </div>
    </div>
  );
}

function CoveragePairRow({
  workstreamId,
  pair,
  onAnalysed,
}: {
  workstreamId: string;
  pair: UnanalysedPair;
  onAnalysed: () => void;
}) {
  // Per-pair mutation state, so one failing pair never blocks another.
  const analyze = useAnalyzeEdge(workstreamId, pair.edge_id, {
    onSuccess: (result) => {
      // `no_linkages_found` writes no findings file, so the pair stays here and
      // stays re-analysable — refetching would be a no-op that hides that.
      if (result.status === "analysed") onAnalysed();
    },
  });
  const noLinkages = analyze.data?.status === "no_linkages_found";

  const label = `${pair.left.title ?? pair.left.id} ↔ ${
    pair.right.title ?? pair.right.id
  }`;

  return (
    <div
      data-testid="coverage-pair"
      data-edge-id={pair.edge_id}
      className="rounded-lg border border-dashed border-border/70 bg-card/40 p-2.5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-medium text-foreground">{label}</span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => analyze.mutate()}
          disabled={analyze.isPending}
        >
          {analyze.isPending ? (
            <>
              <Loader2 className="animate-spin" /> Analyzing…
            </>
          ) : (
            <>
              <Search /> Analyze
            </>
          )}
        </Button>
      </div>
      {analyze.isPending && (
        <AnalyzeProgressBar isPending={analyze.isPending} />
      )}
      {noLinkages && (
        <p className="mt-1 text-[11px] italic text-muted-foreground">
          No matching clause found — no linkages surfaced for this pair.
        </p>
      )}
      {analyze.isError && (
        <p className="mt-1 text-[11px] text-red-600">
          Analysis failed. Check the engine has model credentials, then retry.
        </p>
      )}
    </div>
  );
}
