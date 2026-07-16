import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { Person, Task } from "@/lib/types";

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatEdited(iso: string): string {
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
  return (
    <Card data-testid="source-card" className="overflow-hidden">
      <div className="border-b bg-indigo-50 px-4 py-3">
        <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-700">
          Source · task
        </div>
      </div>
      <div className="space-y-3 p-4 text-sm">
        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Document
          </div>
          <div className="font-semibold">{task.source_name}</div>
          <div className="mt-0.5 text-xs text-muted-foreground">
            {task.format} · {task.clause_count} clauses · last edited{" "}
            {formatEdited(task.last_edited_at)}
          </div>
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Owner
          </div>
          <div className="flex items-center gap-2">
            <PersonAvatar person={task.owner} />
            <span>{task.owner.name}</span>
          </div>
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Reviewers
          </div>
          <div className="flex items-center gap-2">
            {task.reviewers.map((r) => (
              <div key={r.id} className="flex items-center gap-1">
                <PersonAvatar person={r} />
                <span className="text-xs">{r.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Status
          </div>
          <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">
            {task.status === "in_progress" ? "in progress" : task.status}
          </Badge>
        </div>
      </div>
    </Card>
  );
}
