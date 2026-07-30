import type { SlashCommandId } from "./copilotV2Data";

interface QuickAction {
  label: string;
  command: SlashCommandId;
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: "Explore Task", command: "/explore-task" },
  { label: "Brainstorm", command: "/brainstorm" },
  { label: "Draft Outline", command: "/draft" },
  { label: "Write Document", command: "/write" },
];

/** The Copilot's entry point — shown whenever the conversation has no
 *  messages yet. Replaces the old greeting + intent-picker question: the
 *  four quick actions here are the sole way in, alongside typing the
 *  matching slash command directly. */
export function WelcomeScreen({
  onRunCommand,
}: {
  onRunCommand: (id: SlashCommandId) => void;
}) {
  return (
    <div
      data-testid="copilot-welcome"
      className="flex h-full flex-col items-center justify-center gap-6 px-4 text-center"
    >
      <div>
        <h2 className="text-lg font-semibold text-foreground">Welcome, Aisyah.</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          I am your drafting assistant for the Open Finance PD · 2026 workstream.
        </p>
      </div>
      <div className="grid w-full max-w-sm grid-cols-2 gap-2.5">
        {QUICK_ACTIONS.map((a) => (
          <button
            key={a.command}
            type="button"
            data-testid="welcome-quick-action"
            onClick={() => onRunCommand(a.command)}
            className="rounded-lg border-l-2 border-primary/60 bg-card px-3 py-2.5 text-left text-xs font-semibold text-foreground shadow-sm transition hover:bg-accent"
          >
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}
