import { SLASH_COMMANDS, type SlashCommandId } from "./copilotV2Data";

interface FlowStep {
  id: SlashCommandId;
  label: string;
}

const FLOW_STEPS: FlowStep[] = [
  { id: "/explore-task", label: "Explore Task" },
  { id: "/brainstorm", label: "Brainstorm" },
  { id: "/draft", label: "Draft Outline" },
  { id: "/write", label: "Write Document" },
  { id: "/deliver", label: "Deliver" },
];

function descriptionFor(id: SlashCommandId): string {
  return SLASH_COMMANDS.find((c) => c.id === id)?.description ?? "";
}

/** The Copilot's entry point — shown whenever the conversation has no
 *  messages yet. A numbered flow through the five commands, in order,
 *  rather than an unordered grid of buttons — each step is directly
 *  runnable (typing the matching slash command works identically), the
 *  numbering is just the suggested path through the demo. */
export function WelcomeScreen({
  onRunCommand,
}: {
  onRunCommand: (id: SlashCommandId) => void;
}) {
  return (
    <div
      data-testid="copilot-welcome"
      className="flex h-full flex-col items-center justify-center gap-8 px-6 text-center"
    >
      <div>
        <h2 className="text-lg font-semibold text-foreground">Welcome, Aisyah.</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Drafting assistant for the Open Finance PD · 2026 workstream.
        </p>
      </div>
      <ol className="w-full max-w-sm text-left">
        {FLOW_STEPS.map((step, i) => (
          <li key={step.id} className="relative flex pb-5 last:pb-0">
            {i < FLOW_STEPS.length - 1 && (
              <span
                aria-hidden
                className="absolute left-[15px] top-8 h-[calc(100%-8px)] w-px bg-border"
              />
            )}
            <button
              type="button"
              data-testid="welcome-quick-action"
              aria-label={step.label}
              onClick={() => onRunCommand(step.id)}
              className="flex w-full items-start gap-3 rounded-lg px-2 py-1.5 text-left transition hover:bg-accent"
            >
              <span aria-hidden className="relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-primary/50 bg-card text-xs font-bold text-primary">
                {i + 1}
              </span>
              <span aria-hidden className="min-w-0 pt-1">
                <span className="block text-sm font-semibold text-foreground">
                  {step.label}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {descriptionFor(step.id)}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}
