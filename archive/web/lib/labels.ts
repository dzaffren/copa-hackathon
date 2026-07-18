// Human-facing labels for the engine's enum values, in one place so every
// component renders the same wording (spec-upload-and-workspace.md → "Right rail
// renders connections verbatim from the engine payload"). The UI never invents a
// verdict/verification value — it only maps the engine's value to display text.

import type { Branch, SourceType, Verdict, Verification } from "./types";

export const BRANCH_LABEL: Record<Branch, string> = {
  cited: "cited in your doc",
  uncited: "surfaced — not cited",
  feedback: "industry feedback",
};

export const SOURCE_TYPE_LABEL: Record<SourceType, string> = {
  international_standard: "international standard / principle",
  peer_regulator: "peer regulator",
  act: "act / law",
  internal_bnm: "internal BNM policy",
  industry_feedback: "industry feedback",
};

// A dot colour per source type (Tailwind classes; the legend + rail share them).
export const SOURCE_TYPE_DOT: Record<SourceType, string> = {
  international_standard: "bg-indigo-500",
  peer_regulator: "bg-sky-500",
  act: "bg-amber-500",
  internal_bnm: "bg-emerald-500",
  industry_feedback: "bg-rose-500",
};

// Verdict badge styling. The five canonical verdicts only — "Deviates" is a
// documented nuance on Gap, not a badge (per the shared business rules).
export const VERDICT_BADGE: Record<Verdict, string> = {
  Consensus: "bg-emerald-100 text-emerald-800 ring-emerald-600/20",
  Conflict: "bg-red-100 text-red-800 ring-red-600/20",
  Gap: "bg-amber-100 text-amber-800 ring-amber-600/20",
  Duplicate: "bg-slate-100 text-slate-700 ring-slate-500/20",
  Partial: "bg-violet-100 text-violet-800 ring-violet-600/20",
};

export interface VerificationDisplay {
  mark: string;
  label: string;
  className: string;
}

// Verified vs illustrative vs pending must be visibly distinct and never conflated.
export const VERIFICATION: Record<Verification, VerificationDisplay> = {
  verified: {
    mark: "✓",
    label: "verbatim — verified against source document",
    className: "text-emerald-700",
  },
  illustrative: {
    mark: "◦",
    label: "illustrative quote — not yet verified against source",
    className: "text-amber-700",
  },
  pending_extraction: {
    mark: "…",
    label: "pending extraction — exact source passage not yet confirmed",
    className: "text-slate-500",
  },
};

export const SOURCE_TYPE_ORDER: SourceType[] = [
  "international_standard",
  "peer_regulator",
  "act",
  "internal_bnm",
  "industry_feedback",
];
