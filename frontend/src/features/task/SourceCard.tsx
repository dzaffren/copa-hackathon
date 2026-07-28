import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Person, Task } from "@/lib/types";

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatEdited(iso: string | null): string | null {
  // `new Date(null)` is the epoch, not NaN — so an absent stamp has to be
  // caught here or the card confidently reports "last edited Jan 1, 1970".
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function PersonAvatar({ person }: { person: Person }) {
  return (
    <Avatar className="h-6 w-6" title={person.name}>
      <AvatarFallback className="bg-muted text-[10px] font-bold text-muted-foreground">
        {initials(person.name)}
      </AvatarFallback>
    </Avatar>
  );
}

export function SourceCard({ task }: { task: Task }) {
  // A new workstream's focal node has no document yet. Say so plainly rather
  // than rendering the gaps — an empty draft is the expected starting state.
  const edited = formatEdited(task.last_edited_at);
  const documentMeta = [
    task.format,
    `${task.clause_count} clauses`,
    edited && `last edited ${edited}`,
  ].filter(Boolean);

  return (
    <Card data-testid="source-card" className="glass overflow-hidden">
      <div className="border-b border-border/60 bg-primary/10 px-4 py-3">
        <div className="text-[10px] font-bold uppercase tracking-wider text-primary">
          Source · task
        </div>
      </div>
      <div className="space-y-3 p-4 text-sm">
        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Document
          </div>
          <div
            className={cn(
              "font-semibold",
              !task.source_name && "font-normal italic text-muted-foreground",
            )}
          >
            {task.source_name ?? "No document attached"}
          </div>
          <div className="mt-0.5 text-xs text-muted-foreground">
            {documentMeta.join(" · ")}
          </div>
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Owner
          </div>
          {task.owner ? (
            <div className="flex items-center gap-2">
              <PersonAvatar person={task.owner} />
              <span>{task.owner.name}</span>
            </div>
          ) : (
            <span className="text-xs italic text-muted-foreground">
              Unassigned
            </span>
          )}
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Reviewers
          </div>
          {task.reviewers.length > 0 ? (
            <div className="flex items-center gap-2">
              {task.reviewers.map((r) => (
                <div key={r.id} className="flex items-center gap-1">
                  <PersonAvatar person={r} />
                  <span className="text-xs">{r.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <span className="text-xs italic text-muted-foreground">
              None yet
            </span>
          )}
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Status
          </div>
          {/* An untouched focal node has no node-level status of its own. The
              header's Maker-Checker badge still reports the workflow state, so
              the honest thing here is "not started", not an empty badge. */}
          <Badge className="border border-amber-300/30 bg-amber-400/15 text-amber-800 hover:bg-amber-400/15">
            {task.status === "in_progress"
              ? "in progress"
              : (task.status ?? "not started")}
          </Badge>
        </div>
      </div>
    </Card>
  );
}
