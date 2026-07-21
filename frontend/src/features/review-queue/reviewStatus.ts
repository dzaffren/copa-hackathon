import type { LinkageAction, LinkageStatus } from "@/lib/types";

// Presentation + state-machine metadata for the per-linkage maker-checker
// workflow, in one place so the queue list, the status filter, and the review
// panel stay consistent. Mirrors engine/linkage_review.py TRANSITIONS.

export interface StatusStyle {
  label: string;
  pill: string;
  dot: string;
}

export const STATUS_STYLES: Record<LinkageStatus, StatusStyle> = {
  ai_detected: {
    label: "AI detected",
    pill: "bg-slate-500/15 text-slate-300 border border-slate-400/40",
    dot: "bg-slate-400",
  },
  maker_review: {
    label: "Maker review",
    pill: "bg-cyan-500/15 text-cyan-300 border border-cyan-400/30",
    dot: "bg-cyan-400",
  },
  submitted_for_check: {
    label: "Submitted for check",
    pill: "bg-sky-500/15 text-sky-300 border border-sky-400/30",
    dot: "bg-sky-400",
  },
  checker_review: {
    label: "Checker review",
    pill: "bg-violet-500/15 text-violet-300 border border-violet-400/30",
    dot: "bg-violet-400",
  },
  approved: {
    label: "Approved",
    pill: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/30",
    dot: "bg-emerald-400",
  },
  rejected: {
    label: "Rejected",
    pill: "bg-red-500/15 text-red-300 border border-red-400/30",
    dot: "bg-red-400",
  },
  changes_requested: {
    label: "Changes requested",
    pill: "bg-amber-400/15 text-amber-300 border border-amber-300/30",
    dot: "bg-amber-400",
  },
};

export function statusStyle(status: LinkageStatus): StatusStyle {
  return STATUS_STYLES[status] ?? STATUS_STYLES.ai_detected;
}

/** Display order for the status filter + the counts header. */
export const STATUS_ORDER: LinkageStatus[] = [
  "ai_detected",
  "maker_review",
  "submitted_for_check",
  "checker_review",
  "changes_requested",
  "approved",
  "rejected",
];

export type ActorRole = "maker" | "checker";

export interface NextAction {
  action: LinkageAction;
  label: string;
  role: ActorRole;
  /** Visual weight — the constructive action reads primary. */
  tone: "primary" | "neutral" | "danger";
}

/** The actions available from a given status (mirrors the engine's TRANSITIONS).
 *  Approved and rejected are terminal — no further action. */
export const NEXT_ACTIONS: Record<LinkageStatus, NextAction[]> = {
  ai_detected: [{ action: "claim", label: "Claim as maker", role: "maker", tone: "primary" }],
  maker_review: [
    { action: "submit", label: "Submit for check", role: "maker", tone: "primary" },
  ],
  submitted_for_check: [
    { action: "pick_up", label: "Pick up as checker", role: "checker", tone: "primary" },
  ],
  checker_review: [
    { action: "approve", label: "Approve", role: "checker", tone: "primary" },
    { action: "request_changes", label: "Request changes", role: "checker", tone: "neutral" },
    { action: "reject", label: "Reject", role: "checker", tone: "danger" },
  ],
  changes_requested: [
    { action: "submit", label: "Resubmit for check", role: "maker", tone: "primary" },
  ],
  approved: [],
  rejected: [],
};

/** Human label for an action verb, for the audit trail. */
export const ACTION_LABELS: Record<LinkageAction, string> = {
  claim: "claimed",
  submit: "submitted for check",
  pick_up: "picked up for checking",
  approve: "approved",
  reject: "rejected",
  request_changes: "requested changes",
};
