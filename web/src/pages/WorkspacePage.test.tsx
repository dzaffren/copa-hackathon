// Tests for WorkspacePage (spec-drafter-workspace.md · System Design "Workspace
// page"; Functional Requirements "Auto-select the draft on load", "Clicking empty
// canvas is a no-op"; Test 1). The page is a pure READ client: it loads the map
// from `GET /graph`, auto-selects the single editable draft, wires the map to the
// detail panel, and NEVER calls `POST /connections/find` (that is #8) nor renders
// any approval/submit control.
//
// `ClusterGraph` is mocked with a light stand-in (rendering the real React Flow
// canvas in jsdom needs a sized container + ResizeObserver, exercised by
// ClusterGraph.test / E2E instead); `engineApi` is mocked so nothing touches the
// network and `findConnections` can be asserted un-called.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ClusterGraphProps } from "../components/graph/ClusterGraph";
import type { Graph } from "../types";
import {
  EngineConfigError,
  findConnections,
  getGraph,
  getNode,
} from "../lib/engineApi";
import WorkspacePage from "./WorkspacePage";

// Light ClusterGraph stand-in: renders a button per node (so selection wiring is
// observable), reflects `selectedId`, and exposes a pane button for the no-op.
vi.mock("../components/graph/ClusterGraph", () => ({
  default: (props: ClusterGraphProps) => {
    const { graph, selectedId, onNodeSelect, onPaneClick } = props;
    return (
      <div data-testid="cluster-graph-stub">
        <button
          type="button"
          data-testid="rf-pane-stub"
          onClick={() => onPaneClick()}
        >
          empty pane
        </button>
        {graph.nodes.map((node) => (
          <button
            type="button"
            key={node.id}
            data-testid={`node-${node.id}`}
            data-selected={node.id === selectedId ? "true" : undefined}
            onClick={() => onNodeSelect(node.id)}
          >
            {node.title}
          </button>
        ))}
      </div>
    );
  },
}));

vi.mock("../lib/engineApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/engineApi")>();
  return {
    ...actual,
    getGraph: vi.fn(),
    getNode: vi.fn(),
    getClause: vi.fn(),
    findConnections: vi.fn(),
  };
});

// The real 7-node technology-risk corpus (mirrors data/artifacts/graph.json and
// tests/e2e/fixtures/engineStub.ts). `rmit-v2-2026-draft` is the single editable
// draft; `opres-v1-2025-draft` is a published (read-only) in-progress paper.
const CORPUS: Graph = {
  nodes: [
    {
      id: "rmit-v1-2020",
      policy_id: "rmit",
      title: "Risk Management in Technology (RMiT)",
      version: "v1 · 2020",
      status: "Superseded",
      cluster: "technology-risk",
    },
    {
      id: "rmit-v2-2026-draft",
      policy_id: "rmit",
      title: "Risk Management in Technology (RMiT)",
      version: "v2 · 2026 draft",
      status: "In progress",
      cluster: "technology-risk",
    },
    {
      id: "outsourcing-v1-2019",
      policy_id: "outsourcing",
      title: "Outsourcing",
      version: "v1 · 2019",
      status: "In force",
      cluster: "technology-risk",
    },
    {
      id: "bcm-v1-2022",
      policy_id: "bcm",
      title: "Business Continuity Management",
      version: "v1 · 2022",
      status: "In force",
      cluster: "technology-risk",
    },
    {
      id: "opres-v1-2025-draft",
      policy_id: "opres",
      title: "Operational Resilience",
      version: "draft · Discussion Paper 2025",
      status: "In progress",
      cluster: "technology-risk",
    },
    {
      id: "recovery-planning-v1-2021",
      policy_id: "recovery-planning",
      title: "Recovery Planning",
      version: "v1 · 2021",
      status: "In force",
      cluster: "technology-risk",
    },
    {
      id: "customer-info-v1-2025",
      policy_id: "customer-info",
      title: "Management of Customer Information",
      version: "v1 · 2025",
      status: "In force",
      cluster: "technology-risk",
    },
  ],
  edges: [
    {
      source: "rmit-v2-2026-draft",
      target: "outsourcing-v1-2019",
      type: "overlaps",
      reason:
        "A public-cloud arrangement is often also a material outsourcing.",
      source_clauses: ["RMiT 17.1", "RMiT 17.2"],
      target_clauses: ["Outsourcing 12.1"],
      provenance: "curated",
      confidence: 1.0,
    },
  ],
};

beforeEach(() => {
  vi.mocked(getGraph).mockResolvedValue(CORPUS);
  vi.mocked(getNode).mockResolvedValue({
    id: "rmit-v2-2026-draft",
    title: "Risk Management in Technology (RMiT)",
    status: "In progress",
    edges: [
      {
        target: "outsourcing-v1-2019",
        type: "overlaps",
        reason:
          "A public-cloud arrangement is often also a material outsourcing.",
      },
    ],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

function renderPage() {
  return render(
    <MemoryRouter>
      <WorkspacePage />
    </MemoryRouter>,
  );
}

describe("WorkspacePage", () => {
  it("loads the map from GET /graph and renders every cluster node", async () => {
    renderPage();
    for (const node of CORPUS.nodes) {
      expect(await screen.findByTestId(`node-${node.id}`)).toBeInTheDocument();
    }
    // Settle the auto-selected draft's getNode hydration inside act().
    await screen.findByTestId("linked-to-outsourcing-v1-2019");
  });

  it("auto-selects the RMiT v2 draft on load — the detail panel is never blank", async () => {
    renderPage();

    // The draft's single enabled action proves NodeDetail(draft) is rendered.
    expect(
      await screen.findByRole("button", { name: /open the draft/i }),
    ).toBeInTheDocument();

    const panel = screen.getByTestId("detail-panel");
    expect(panel).toHaveTextContent("v2 · 2026 draft");
    expect(panel).not.toBeEmptyDOMElement();

    // The map reflects the auto-selection back onto the draft node.
    expect(
      await screen.findByTestId("node-rmit-v2-2026-draft"),
    ).toHaveAttribute("data-selected", "true");
    // Settle the draft's getNode hydration inside act().
    await screen.findByTestId("linked-to-outsourcing-v1-2019");
  });

  it("never calls POST /connections/find (findConnections) — a read-only workspace", async () => {
    renderPage();
    await screen.findByRole("button", { name: /open the draft/i });
    await screen.findByTestId("linked-to-outsourcing-v1-2019");
    expect(findConnections).not.toHaveBeenCalled();
  });

  it("offers no approve / submit / return-to-bank control anywhere", async () => {
    renderPage();
    await screen.findByRole("button", { name: /open the draft/i });
    await screen.findByTestId("linked-to-outsourcing-v1-2019");
    expect(
      screen.queryByRole("button", {
        name: /approve|submit|return to bank/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("keeps the current selection on an empty-pane click (onPaneClick is a no-op)", async () => {
    renderPage();
    // The RMiT v2 draft is auto-selected; settle its getNode hydration.
    await screen.findByRole("button", { name: /open the draft/i });
    await screen.findByTestId("linked-to-outsourcing-v1-2019");

    // Clicking empty canvas is a no-op: the draft detail stays shown (never
    // blanks), and the map keeps the draft selected — no re-selection occurs.
    await userEvent.click(screen.getByTestId("rf-pane-stub"));
    expect(
      screen.getByRole("button", { name: /open the draft/i }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("node-rmit-v2-2026-draft")).toHaveAttribute(
      "data-selected",
      "true",
    );
  });

  it("shows the workspace error state (never a blank screen) when the graph fails to load", async () => {
    vi.mocked(getGraph).mockRejectedValue(
      new EngineConfigError("test: engine base url not set"),
    );
    renderPage();

    expect(await screen.findByTestId("workspace-error")).toBeInTheDocument();
    // The strip stays available even in the error state.
    expect(
      screen.getByRole("link", { name: "Switch to supervisor view" }),
    ).toBeInTheDocument();
  });
});
