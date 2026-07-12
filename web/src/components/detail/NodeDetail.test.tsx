// Tests for NodeDetail (spec-drafter-workspace.md · "Inspecting my editable
// draft", "Published BNM policies offer no editing action", "The Regulatory
// Handbook reference is a locked, content-withheld placeholder", "An external
// reference node shows that it exists and why it matters"; Validation & Business
// Rules). `engineApi` is mocked so no network is touched; the "Linked to" list
// is hydrated from the mocked `getNode`, and the verbatim-citation guardrail is
// proven by asserting `getClause` is NEVER called from a node detail.

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { GraphNode } from "../../types";
import { getClause, getNode } from "../../lib/engineApi";
import NodeDetail from "./NodeDetail";

// Keep the real error classes; replace only the network functions.
vi.mock("../../lib/engineApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/engineApi")>();
  return { ...actual, getNode: vi.fn(), getClause: vi.fn() };
});

function policyNode(overrides: Partial<GraphNode> = {}): GraphNode {
  return {
    id: "outsourcing-v1-2019",
    policy_id: "outsourcing",
    title: "Outsourcing",
    version: "v1 · 2019",
    status: "In force",
    cluster: "technology-risk",
    ...overrides,
  };
}

const draftNode = policyNode({
  id: "rmit-v2-2026-draft",
  policy_id: "rmit",
  title: "Risk Management in Technology (RMiT)",
  version: "v2 · 2026 draft",
  status: "In progress",
});

function referenceNode(overrides: Partial<GraphNode> = {}): GraphNode {
  return {
    id: "pdpa-2010",
    policy_id: "pdpa",
    title: "Personal Data Protection Act 2010 (Malaysia)",
    version: "2010 · Act 709",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "act",
    access: "public",
    preview: false,
    ...overrides,
  };
}

const handbookNode = referenceNode({
  id: "bnm-handbook",
  policy_id: "bnm-handbook",
  title: "Regulatory Handbook (BNM)",
  version: "internal",
  source_type: "handbook",
  access: "restricted",
});

beforeEach(() => {
  vi.mocked(getNode).mockResolvedValue({
    id: "x",
    title: "x",
    status: "In force",
    edges: [],
  });
  vi.mocked(getClause).mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("NodeDetail — the editable draft", () => {
  it("offers an enabled 'Open the draft' action, its version/status, trail and linked-to list", async () => {
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
        {
          target: "opres-v1-2025-draft",
          type: "overlaps",
          reason: "Both govern continuity of critical services.",
        },
      ],
    });

    render(<NodeDetail node={draftNode} />);

    const open = await screen.findByRole("button", { name: /open the draft/i });
    expect(open).toBeEnabled();
    expect(screen.getByText("v2 · 2026 draft")).toBeInTheDocument();
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
    // "Why this changed" trail is rendered only for the draft.
    expect(screen.getByTestId("why-this-changed")).toBeInTheDocument();
    // "Linked to" list hydrated from getNode's outgoing edges.
    expect(
      await screen.findByTestId("linked-to-outsourcing-v1-2019"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("linked-to-opres-v1-2025-draft"),
    ).toBeInTheDocument();
  });
});

describe("NodeDetail — published, read-only policies", () => {
  it("shows a disabled 'Read-only' action and no edit action", async () => {
    vi.mocked(getNode).mockResolvedValue({
      id: "outsourcing-v1-2019",
      title: "Outsourcing",
      status: "In force",
      edges: [
        {
          target: "customer-info-v1-2025",
          type: "overlaps",
          reason: "Outsourcing engages Management of Customer Information.",
        },
      ],
    });

    render(<NodeDetail node={policyNode()} />);

    const readonly = await screen.findByRole("button", { name: /read-only/i });
    expect(readonly).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: /open the draft/i }),
    ).not.toBeInTheDocument();
    expect(
      await screen.findByTestId("linked-to-customer-info-v1-2025"),
    ).toBeInTheDocument();
  });
});

describe("NodeDetail — restricted reference (Regulatory Handbook)", () => {
  it("renders a locked, content-withheld placeholder and NEVER fetches a clause", () => {
    const { container } = render(<NodeDetail node={handbookNode} />);

    // Locked, access-controlled, content withheld.
    expect(container).toHaveTextContent(/restricted/i);
    expect(container).toHaveTextContent(/withheld/i);
    // The only action is a disabled, restricted action — no hand-off.
    const action = screen.getByRole("button", { name: /restricted/i });
    expect(action).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: /see in the reference radar/i }),
    ).not.toBeInTheDocument();
    // Verbatim-citation guardrail: a withheld reference fetches nothing.
    expect(vi.mocked(getClause)).not.toHaveBeenCalled();
    expect(vi.mocked(getNode)).not.toHaveBeenCalled();
  });
});

describe("NodeDetail — public external reference", () => {
  it("shows a 'why this reference matters' note + Reference Radar hand-off, without verbatim passages", () => {
    const { container } = render(<NodeDetail node={referenceNode()} />);

    expect(
      screen.getByRole("button", { name: /see in the reference radar/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/why this reference matters/i)).toBeInTheDocument();
    // The deep, clause-by-clause content is deferred to the Reference Radar (#26).
    expect(vi.mocked(getClause)).not.toHaveBeenCalled();
    expect(
      container.querySelector('[data-testid="clause-passage"]'),
    ).toBeNull();
  });
});
