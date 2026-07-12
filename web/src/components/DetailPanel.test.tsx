// Tests for DetailPanel (spec-drafter-workspace.md · System Design "Detail panel:
// Routes selection → NodeDetail / EdgeDetail / keeps last on empty click"; the
// panel is a labelled region and is NEVER blank). `engineApi` is mocked so the
// routed children mount without touching the network.

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { GraphEdge, GraphNode } from "../types";
import { getClause, getNode } from "../lib/engineApi";
import DetailPanel from "./DetailPanel";

vi.mock("../lib/engineApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/engineApi")>();
  return { ...actual, getNode: vi.fn(), getClause: vi.fn() };
});

const draftNode: GraphNode = {
  id: "rmit-v2-2026-draft",
  policy_id: "rmit",
  title: "Risk Management in Technology (RMiT)",
  version: "v2 · 2026 draft",
  status: "In progress",
  cluster: "technology-risk",
};

const overlapEdge: GraphEdge = {
  source: "rmit-v2-2026-draft",
  target: "outsourcing-v1-2019",
  type: "overlaps",
  reason: "A public-cloud arrangement is often also a material outsourcing.",
  source_clauses: [],
  target_clauses: ["Outsourcing 12.1"],
};

beforeEach(() => {
  vi.mocked(getNode).mockResolvedValue({
    id: "rmit-v2-2026-draft",
    title: "Risk Management in Technology (RMiT)",
    status: "In progress",
    edges: [],
  });
  vi.mocked(getClause).mockResolvedValue({
    clause_number: "Outsourcing 12.1",
    text:
      "A financial institution must obtain the Bank's written approval before " +
      "entering into a new material outsourcing arrangement.",
    policy_id: "outsourcing",
    document_id: "outsourcing-v1-2019",
    source: "published",
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("DetailPanel", () => {
  it("is a labelled region with the detail-panel test id", async () => {
    render(<DetailPanel selection={{ kind: "node", node: draftNode }} />);
    const panel = screen.getByTestId("detail-panel");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute("role", "region");
    // Let the routed NodeDetail's getNode hydration settle inside act().
    await screen.findByRole("button", { name: /open the draft/i });
  });

  it("routes a node selection to NodeDetail", async () => {
    render(<DetailPanel selection={{ kind: "node", node: draftNode }} />);
    expect(
      await screen.findByRole("button", { name: /open the draft/i }),
    ).toBeInTheDocument();
  });

  it("routes an edge selection to EdgeDetail", async () => {
    render(<DetailPanel selection={{ kind: "edge", edge: overlapEdge }} />);
    expect(
      screen.getByRole("heading", { name: /why these are connected/i }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(
        /written approval before entering into a new material outsourcing/i,
      ),
    ).toBeInTheDocument();
  });

  it("keeps the last selection when selection becomes null (never blank)", async () => {
    const { rerender } = render(
      <DetailPanel selection={{ kind: "node", node: draftNode }} />,
    );
    expect(
      await screen.findByRole("button", { name: /open the draft/i }),
    ).toBeInTheDocument();

    // An empty-pane click clears the selection; the panel must keep the last.
    rerender(<DetailPanel selection={null} />);
    expect(
      screen.getByRole("button", { name: /open the draft/i }),
    ).toBeInTheDocument();
  });
});
