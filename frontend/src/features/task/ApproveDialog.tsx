import { useState } from "react";
import { ShieldCheck } from "lucide-react";

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

/**
 * Confirms the sign-off before a task moves Pending Review -> Approved. The
 * assigned checker is pre-selected: this MVP has no separate reviewer/approver
 * persona (CLAUDE.md), so whoever was assigned as checker is who approves.
 */
export function ApproveDialog({
  checker,
  onApproved,
}: {
  checker: Person;
  onApproved?: (approver: Person) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-emerald-500 text-slate-950 hover:bg-emerald-400">
          <ShieldCheck /> Approve
        </Button>
      </DialogTrigger>
      <DialogContent className="glass">
        <DialogHeader>
          <DialogTitle>Approve task</DialogTitle>
          <DialogDescription>
            Confirm sign-off as the assigned checker. The task moves to
            Approved and the sign-off is recorded.
          </DialogDescription>
        </DialogHeader>
        <button
          type="button"
          onClick={() => {
            onApproved?.(checker);
            setOpen(false);
          }}
          className="flex w-full items-center gap-3 rounded-md border border-border/60 p-2 text-left text-sm hover:bg-accent"
        >
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-muted text-xs font-bold text-muted-foreground">
              {initials(checker.name)}
            </AvatarFallback>
          </Avatar>
          <span className="font-medium">Approve as {checker.name}</span>
        </button>
      </DialogContent>
    </Dialog>
  );
}

export default ApproveDialog;
