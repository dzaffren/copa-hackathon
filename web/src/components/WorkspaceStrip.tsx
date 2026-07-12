// Workspace strip (spec-drafter-workspace.md · UI/Frontend Requirements
// "Workspace strip"): a slim bar across the top of the workspace that names the
// drafter and her role, states her single working draft, and offers the one-click
// hand-off to the supervisor view.
//
// It carries NO approve / submit / return-to-bank action — approval is a separate
// manager step handled elsewhere (#8/#10) and is never offered on this screen
// (Acceptance: "Approval is never offered in the workspace").

import { Link } from "react-router-dom";

export default function WorkspaceStrip(): JSX.Element {
  return (
    <header
      data-testid="workspace-strip"
      className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3"
    >
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span>
          <span className="text-sm font-semibold text-slate-900">
            Aisyah R.
          </span>
          <span className="ml-2 text-xs uppercase tracking-wide text-slate-500">
            policy drafter
          </span>
        </span>
        <span className="text-slate-300" aria-hidden="true">
          |
        </span>
        <p className="text-sm text-slate-600">
          Drafting: RMiT v2 — your only working draft
        </p>
      </div>

      <Link
        to="/supervisor"
        className="shrink-0 rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Switch to supervisor view
      </Link>
    </header>
  );
}
