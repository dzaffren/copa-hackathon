// Tests for the cluster-map legend (spec-drafter-workspace.md · UI/Frontend
// Requirements "The cluster map with a legend"). One row per treatment kind, each
// with a swatch and the exact marking string `deriveMarking` produces — driven
// from the same `LEGEND_ROWS` source so the legend can never drift from the map.

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Legend, { LEGEND_ROWS } from "./Legend";

describe("Legend", () => {
  it("shows one row per treatment kind (all eight)", () => {
    render(<Legend />);
    expect(LEGEND_ROWS).toHaveLength(8);
    for (const { kind } of LEGEND_ROWS) {
      expect(screen.getByTestId(`legend-${kind}`)).toBeInTheDocument();
    }
  });

  it("labels every row with its derived marking and a swatch", () => {
    render(<Legend />);
    for (const { kind, marking } of LEGEND_ROWS) {
      const row = screen.getByTestId(`legend-${kind}`);
      expect(row).toHaveTextContent(marking);
      // The swatch is an aria-hidden decorative span.
      expect(row.querySelector('span[aria-hidden="true"]')).not.toBeNull();
    }
  });

  it("shows the contractual marking strings verbatim", () => {
    render(<Legend />);
    expect(
      within(screen.getByTestId("legend-editable-draft")).getByText(
        "your draft — you edit",
      ),
    ).toBeInTheDocument();
    expect(
      within(screen.getByTestId("legend-cross-cluster")).getByText(
        "other cluster (preview only)",
      ),
    ).toBeInTheDocument();
    expect(
      within(screen.getByTestId("legend-reference-restricted")).getByText(
        "external reference · restricted (locked)",
      ),
    ).toBeInTheDocument();
  });

  it("is an accessible, labelled region", () => {
    render(<Legend />);
    expect(screen.getByTestId("legend")).toHaveAttribute(
      "aria-label",
      "Map legend",
    );
  });
});
