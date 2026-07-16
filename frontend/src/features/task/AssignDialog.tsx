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

// Static workflow picker — MVP1 does not persist the assignment.
const MEMBERS: Person[] = [
  { id: "fm", name: "Farid M." },
  { id: "ps", name: "Priya S." },
];

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function AssignDialog() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <UserPlus /> Assign
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Assign task</DialogTitle>
          <DialogDescription>
            Pick a workstream member to review this task. Assignment is not
            persisted in this preview.
          </DialogDescription>
        </DialogHeader>
        <ul className="space-y-1">
          {MEMBERS.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="flex w-full items-center gap-3 rounded-md border p-2 text-left text-sm hover:bg-accent"
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
