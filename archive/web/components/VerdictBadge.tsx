import { VERDICT_BADGE } from "@/lib/labels";
import type { Verdict } from "@/lib/types";

/** The proposed-verdict badge. Five canonical verdicts only. */
export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${VERDICT_BADGE[verdict]}`}
      data-testid={`verdict-${verdict}`}
    >
      {verdict}
    </span>
  );
}
