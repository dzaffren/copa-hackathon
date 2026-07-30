import { cn } from "@/lib/utils";
import type { PairwiseFilterNode } from "@/lib/types";
import { nodeTypeStyle, shortLabelForNode } from "./nodeType";

interface Props {
  nodes: PairwiseFilterNode[];
  /** Selected node ids. Empty means "no filter" — everything shows. */
  selected: Set<string>;
  onToggle: (nodeId: string) => void;
  onClear: () => void;
}

/** The Pairwise Findings box's document filter.
 *
 *  Multi-select: chips toggle independently, so a drafter can put the two peer
 *  regulators side by side in one pass. `aria-pressed` carries the state — a
 *  toggle-button group is already the correct pattern for multi-select and needs
 *  no extra ARIA. "All" clears rather than being a selectable option, because an
 *  empty selection IS "all" and having both would let them disagree.
 */
export function NodeFilterChips({ nodes, selected, onToggle, onClear }: Props) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-muted-foreground">Filter:</span>
      <div
        role="group"
        aria-label="Filter by node"
        className="flex flex-wrap items-center gap-1"
      >
        <Chip
          label="All"
          selected={selected.size === 0}
          onClick={onClear}
          idleClasses="border-primary/40 text-primary"
        />
        {nodes.map((n) => (
          <Chip
            key={n.id}
            label={shortLabelForNode(n.id, n.title ?? n.id)}
            count={n.findings_count}
            selected={selected.has(n.id)}
            onClick={() => onToggle(n.id)}
            idleClasses={
              n.node_type ? nodeTypeStyle(n.node_type).chip : undefined
            }
          />
        ))}
      </div>
    </div>
  );
}

interface ChipProps {
  label: string;
  count?: number;
  selected: boolean;
  onClick: () => void;
  idleClasses?: string;
}

function Chip({ label, count, selected, onClick, idleClasses }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      data-testid="node-filter-chip"
      className={cn(
        "rounded-md border bg-card/40 px-2 py-1 text-[11px] font-medium transition-colors",
        selected
          ? "border-primary bg-primary text-primary-foreground"
          : (idleClasses ?? "border-border/60 text-muted-foreground"),
      )}
    >
      {label}
      {count !== undefined && (
        <span className="ml-1 opacity-70">· {count}</span>
      )}
    </button>
  );
}
