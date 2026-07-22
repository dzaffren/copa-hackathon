import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";

export interface ProgressStage {
  /** The % this stage's label holds until reached. */
  pct: number;
  label: string;
}

/** The Analyze button's live call is two sequential Claude turns (finder,
 *  then critic) with no interim signal from the backend — a single blocking
 *  JSON response after ~30-60s. This is a client-simulated staged climb, not
 *  a real progress signal: it advances toward the last stage's % over
 *  `durationMs`, holds there, and lets the caller's mutation resolution
 *  (success or error) replace this component once the real response lands. */
export const ANALYZE_STAGES: ProgressStage[] = [
  { pct: 15, label: "Reading source document…" },
  { pct: 35, label: "Reading target document…" },
  { pct: 60, label: "Finding candidate linkages…" },
  { pct: 90, label: "Reviewing candidates…" },
];

export const COPILOT_STAGES: ProgressStage[] = [
  { pct: 20, label: "Reading the task's document…" },
  { pct: 45, label: "Reading your accepted findings…" },
  { pct: 90, label: "Drafting a reply…" },
];

const STEP_MS = 400;

interface AnalyzeProgressBarProps {
  isPending: boolean;
  stages?: ProgressStage[];
  /** Roughly how long the staged climb to the last stage's % should take. */
  durationMs?: number;
}

export function AnalyzeProgressBar({
  isPending,
  stages = ANALYZE_STAGES,
  durationMs = 40_000,
}: AnalyzeProgressBarProps) {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    if (!isPending) {
      setPct(0);
      return;
    }
    const ceiling = stages[stages.length - 1]?.pct ?? 90;
    const stepPct = ceiling / (durationMs / STEP_MS);
    const id = setInterval(() => {
      setPct((prev) => Math.min(prev + stepPct, ceiling));
    }, STEP_MS);
    return () => clearInterval(id);
  }, [isPending, stages, durationMs]);

  if (!isPending) return null;

  const stageIndex = stages.findIndex((s) => pct < s.pct);
  const stage = stages[stageIndex === -1 ? stages.length - 1 : stageIndex];

  return (
    <div className="space-y-1.5" role="status" aria-live="polite">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        {stage?.label ?? "Working…"}
      </div>
      <Progress value={pct} />
    </div>
  );
}
