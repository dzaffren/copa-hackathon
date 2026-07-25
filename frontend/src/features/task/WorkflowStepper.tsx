import { Check, Pencil, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";

// A horizontal stepper modelled on the GEMA design-system stepper: a row of
// circular step markers joined by a connecting line, each in one of four
// states — completed (blue fill + check), current (blue fill + active icon),
// error (red fill + warning), or upcoming (grey outline). One source of truth
// for a step's visual state so the task workflow reads at a glance.

export type StepState = "completed" | "current" | "upcoming" | "error";

export interface Step {
  key: string;
  label: string;
}

interface WorkflowStepperProps {
  steps: Step[];
  /** State resolver for each step, keyed by its position in `steps`. */
  stateFor: (index: number) => StepState;
}

function Marker({ state, index }: { state: StepState; index: number }) {
  const base =
    "grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-semibold transition-colors";
  if (state === "completed") {
    return (
      <span className={cn(base, "bg-primary text-primary-foreground")}>
        <Check className="h-4 w-4" />
      </span>
    );
  }
  if (state === "current") {
    return (
      <span
        className={cn(
          base,
          "bg-primary text-primary-foreground ring-4 ring-primary/20",
        )}
      >
        <Pencil className="h-3.5 w-3.5" />
      </span>
    );
  }
  if (state === "error") {
    return (
      <span className={cn(base, "bg-destructive text-destructive-foreground")}>
        <TriangleAlert className="h-4 w-4" />
      </span>
    );
  }
  return (
    <span
      className={cn(
        base,
        "border-2 border-border bg-card text-muted-foreground",
      )}
    >
      {index + 1}
    </span>
  );
}

export function WorkflowStepper({ steps, stateFor }: WorkflowStepperProps) {
  return (
    <ol className="flex items-center gap-1" aria-label="Task workflow progress">
      {steps.map((step, i) => {
        const state = stateFor(i);
        const active = state === "current";
        return (
          <li key={step.key} className="flex items-center gap-1">
            <div className="flex items-center gap-2">
              <Marker state={state} index={i} />
              <span
                className={cn(
                  "text-sm",
                  active
                    ? "font-semibold text-foreground"
                    : state === "completed"
                      ? "font-medium text-foreground"
                      : "text-muted-foreground",
                )}
              >
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <span
                aria-hidden
                className={cn(
                  "mx-2 h-px w-8 shrink-0",
                  state === "completed" ? "bg-primary" : "bg-border",
                )}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default WorkflowStepper;
