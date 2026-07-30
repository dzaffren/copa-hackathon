import type { ReactNode } from "react";
import { CheckCircle2, ChevronDown, ChevronRight } from "lucide-react";

export type CommandStepStatus = "pending" | "active" | "done" | "error";

export interface CommandStep {
  /** The slash command this step represents, e.g. "/pull-node-metadata". */
  command: string;
  status: CommandStepStatus;
  /** One-line summary — present tense while active, past tense once done. */
  statusLine: string;
  /** Expandable body: field list, clarification card, skeleton preview, draft
   *  grid, or the release panel — whatever this phase renders. Omitted while
   *  a step is still pending. */
  detail?: ReactNode;
  /** Keep this step open even though it's no longer active — used for the
   *  step immediately behind the active one, so its result (a confirmation,
   *  a completed field list) stays visible for one more step instead of
   *  collapsing the instant it finishes. */
  defaultOpen?: boolean;
}

const STATUS_ICON_CLASS: Record<CommandStepStatus, string> = {
  pending: "text-muted-foreground",
  active: "text-primary",
  done: "text-primary",
  error: "text-red-600",
};

/** One row in the transcript: a `/command` name, a one-line status, and an
 *  expandable body. Generalizes this panel's existing "thinking step" visual
 *  language (active shimmer, done checkmark — see the shared `shimmer`/
 *  `fadeSlideUp` keyframes) so every phase of the Copilot's flow reads as one
 *  consistent tool-call log, Claude-Code style, instead of five differently
 *  shaped panels. */
function CommandTranscriptStep({
  step,
  expanded,
  onToggle,
}: {
  step: CommandStep;
  expanded: boolean;
  onToggle: () => void;
}) {
  const isActive = step.status === "active";
  const isError = step.status === "error";
  const isOpen = isActive || Boolean(step.defaultOpen) || expanded;
  const canToggle = Boolean(step.detail) && !isActive;

  return (
    <div
      data-testid="command-step"
      data-command={step.command}
      data-status={step.status}
      className={`relative overflow-hidden rounded-lg border transition-colors ${
        isActive
          ? "border-primary/40 bg-primary/[0.06]"
          : isError
            ? "border-red-400/30 bg-red-500/[0.04]"
            : "border-border/60 bg-muted/30"
      }`}
      style={{ animation: "fadeSlideUp 0.4s var(--ease-out-expo) both" }}
    >
      {isActive && (
        <span
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "linear-gradient(90deg, transparent, rgba(37,99,235,0.10), transparent)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.6s linear infinite",
          }}
        />
      )}
      <button
        type="button"
        onClick={onToggle}
        disabled={!canToggle}
        className="relative flex w-full items-center gap-2 px-2.5 py-1.5 text-left text-xs disabled:cursor-default"
      >
        {step.status === "done" || isError ? (
          <CheckCircle2
            className={`h-3.5 w-3.5 shrink-0 ${STATUS_ICON_CLASS[step.status]}`}
          />
        ) : (
          <span
            className={`h-3.5 w-3.5 shrink-0 rounded-full border ${
              isActive
                ? "animate-pulse border-primary"
                : "border-muted-foreground/40"
            }`}
          />
        )}
        <span className="shrink-0 font-mono text-[11px] font-semibold text-primary">
          {step.command}
        </span>
        <span className="min-w-0 flex-1 truncate text-muted-foreground">
          {step.statusLine}
        </span>
        {canToggle &&
          (isOpen ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          ))}
      </button>
      {step.detail && isOpen && (
        <div className="relative space-y-2 border-t border-border/60 px-2.5 py-2">
          {step.detail}
        </div>
      )}
    </div>
  );
}

export function CommandTranscript({
  steps,
  expanded,
  onToggle,
}: {
  steps: CommandStep[];
  expanded: Set<string>;
  onToggle: (command: string) => void;
}) {
  return (
    <div className="space-y-2">
      {steps.map((step) => (
        <CommandTranscriptStep
          key={step.command}
          step={step}
          expanded={expanded.has(step.command)}
          onToggle={() => onToggle(step.command)}
        />
      ))}
    </div>
  );
}

/** A compact, indented row for a silent sub-step (e.g. `/pull-context`)
 *  nested inside its parent phase's detail — never its own top-level
 *  transcript row, per the Claude-like framing where background tool calls
 *  don't compete with the visible steps of the flow. */
export function SilentSubStep({
  command,
  statusLine,
  active,
}: {
  command: string;
  statusLine: string;
  active: boolean;
}) {
  return (
    <div
      data-testid="silent-sub-step"
      className="flex items-center gap-1.5 border-l-2 border-border/60 pl-2 text-[11px] text-muted-foreground"
    >
      {active ? (
        <span className="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-primary" />
      ) : (
        <CheckCircle2 className="h-3 w-3 shrink-0 text-primary" />
      )}
      <span className="font-mono font-medium text-primary/80">{command}</span>
      <span className="min-w-0 flex-1 truncate">{statusLine}</span>
    </div>
  );
}
