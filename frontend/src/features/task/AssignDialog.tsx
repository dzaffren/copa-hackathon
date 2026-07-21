import { useState } from "react";
import { UserPlus } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { Person } from "@/lib/types";

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function AssignDialog({
  members,
  onAssigned,
}: {
  /** Who can be picked as checker — the task's own reviewers, so the picker
   *  never drifts from who is actually on the task. */
  members: Person[];
  /** Called when a member is picked. The caller is responsible for
   *  persisting the assignment (`setTaskWorkflow`) — this dialog is UI only. */
  onAssigned?: (member: Person) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <UserPlus /> Assign to Checker
        </Button>
      </DialogTrigger>
      <DialogContent className="glass">
        <DialogHeader>
          <DialogTitle>Assign to Checker</DialogTitle>
          <DialogDescription>
            Pick a workstream member to check this task. The task moves to
            Pending Review.
          </DialogDescription>
        </DialogHeader>
        <ul className="space-y-1">
          {members.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                onClick={() => {
                  onAssigned?.(m);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-md border border-border/60 p-2 text-left text-sm hover:bg-accent"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-muted text-xs font-bold text-muted-foreground">
                    {initials(m.name)}
                  </AvatarFallback>
                </Avatar>
                <span className="font-medium">{m.name}</span>
              </button>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
