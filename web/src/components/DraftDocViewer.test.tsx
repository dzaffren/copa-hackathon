// Tests for the mock DraftDocViewer (spec-drafter-workspace.md · System Design
// Components: "Word/SharePoint-style render of the living draft + tracked-change
// insertions from workflowState"; Security: never `dangerouslySetInnerHTML`).
//
// #7 only READS the store; the tracked-change markers are seeded here through
// the public `workflowState` writer (owned by Task 3) exactly as #9 would write
// them, then the viewer overlays them on the parsed markdown.

import { render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import type { TrackedChange } from "../types";
import { upsertTrackedChange } from "../lib/workflowState";
import DraftDocViewer from "./DraftDocViewer";

const DOC_ID = "rmit-v2-2026-draft";

function makeChange(overrides: Partial<TrackedChange> = {}): TrackedChange {
  return {
    id: "tc-rmit-17-1",
    findingId: "finding-rmit-17-1-outsourcing",
    clauseNumber: "RMiT 17.1",
    insertedText:
      "having first completed the risk assessment under paragraph 10.50.",
    acceptedAt: "2026-07-12T09:00:00.000Z",
    ...overrides,
  };
}

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  window.localStorage.clear();
});

describe("DraftDocViewer — document surface", () => {
  it("renders markdown headings and paragraphs legibly", () => {
    render(
      <DraftDocViewer
        documentId={DOC_ID}
        markdown={
          "# Risk Management in Technology\n\n" +
          "A financial institution must manage technology risk."
        }
      />,
    );

    expect(
      screen.getByRole("heading", { name: /Risk Management in Technology/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /A financial institution must manage technology risk\./i,
      ),
    ).toBeInTheDocument();
  });
});

describe("DraftDocViewer — tracked-change overlay", () => {
  it("overlays an inserted change from workflowState with a distinct, labelled treatment", () => {
    upsertTrackedChange(
      DOC_ID,
      makeChange({ insertedText: "UNIQUE-INSERTED-CLAUSE-TEXT" }),
    );

    render(
      <DraftDocViewer
        documentId={DOC_ID}
        markdown={
          "## Cloud services\n\n" +
          "17.1 A financial institution shall notify the Bank within 14 days."
        }
      />,
    );

    const insertion = screen.getByTestId("tracked-change");
    // The redraft text is shown …
    expect(insertion).toHaveTextContent("UNIQUE-INSERTED-CLAUSE-TEXT");
    // … carries an accessible label naming the anchor clause …
    expect(insertion).toHaveAttribute(
      "aria-label",
      expect.stringContaining("RMiT 17.1"),
    );
    // … and a visible "tracked change" marker distinguishes it from body text.
    expect(within(insertion).getByText(/tracked change/i)).toBeInTheDocument();
  });

  it("collects insertions whose clause is absent from the draft under a 'Proposed insertions' region", () => {
    upsertTrackedChange(
      DOC_ID,
      makeChange({
        id: "tc-orphan",
        clauseNumber: "RMiT 99.9",
        insertedText: "ORPHAN-INSERTION-TEXT",
      }),
    );

    render(
      <DraftDocViewer
        documentId={DOC_ID}
        markdown={"# Draft\n\nBody text without that anchor clause."}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /proposed insertions/i }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("tracked-change")).toHaveTextContent(
      "ORPHAN-INSERTION-TEXT",
    );
  });
});

describe("DraftDocViewer — safe rendering (no dangerouslySetInnerHTML)", () => {
  it("escapes embedded markup as literal text instead of injecting elements", () => {
    const { container } = render(
      <DraftDocViewer
        documentId={DOC_ID}
        markdown={"A clause with <script>alert('xss')</script> inside."}
      />,
    );

    // The angle-bracket markup survives as literal, escaped text …
    expect(container.textContent).toContain("<script>alert('xss')</script>");
    // … and no live <script> element was ever created from the markdown.
    expect(container.querySelector("script")).toBeNull();
  });
});
