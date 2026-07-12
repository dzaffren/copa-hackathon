// Tests for ProvenanceTrail (spec-drafter-workspace.md · Test 9 + "The 'Why this
// changed' trail lists public supporting documents" / "An internal supporting
// document appears locked and content-withheld"). Reads the client-side
// `provenance.ts` fixture directly — no engine, no graph node.

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ProvenanceTrail from "./ProvenanceTrail";

const DRAFT_ID = "rmit-v2-2026-draft";

describe("ProvenanceTrail — Why this changed", () => {
  it("Test 9: shows public docs with titles + dates and locks the internal doc's content", () => {
    render(<ProvenanceTrail documentId={DRAFT_ID} />);

    const trail = screen.getByTestId("why-this-changed");
    expect(trail).toBeInTheDocument();

    // Public supporting documents — title + date shown.
    expect(
      within(trail).getByText("Operational Resilience — Discussion Paper"),
    ).toBeInTheDocument();
    expect(within(trail).getByText("19 Dec 2025")).toBeInTheDocument();
    expect(within(trail).getByText("RMiT FAQs (updated)")).toBeInTheDocument();
    expect(within(trail).getByText("1 Jul 2026")).toBeInTheDocument();

    // Internal document — listed so the trail stays complete, content withheld.
    const internal = within(trail).getByTestId(
      "provenance-prov-jpp-minutes-cloud-review",
    );
    expect(internal).toHaveTextContent(
      "JPP Committee minutes — cloud policy review",
    );
    expect(internal).toHaveTextContent(/restricted/i);
    expect(internal).toHaveTextContent(/content withheld/i);
  });

  it("renders nothing for a document with no trail (never a graph node)", () => {
    const { container } = render(
      <ProvenanceTrail documentId="outsourcing-v1-2019" />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
