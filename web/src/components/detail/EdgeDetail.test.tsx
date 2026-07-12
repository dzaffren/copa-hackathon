// Tests for EdgeDetail (spec-drafter-workspace.md · Tests 3–5 + "The deep
// reference content is deferred to the Reference Radar"). `getClause` is mocked
// (the real `EngineNotFound` class is preserved so `instanceof` holds), proving:
//   • a connection quotes the cited clause VERBATIM by number (Tests 3–4);
//   • a missing clause shows the "No matching clause found" guardrail (Test 5),
//     never invented text and never a crash;
//   • a reference connection hands off to the Reference Radar and fetches nothing.

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Clause, GraphEdge } from "../../types";
import { EngineNotFound, getClause } from "../../lib/engineApi";
import EdgeDetail from "./EdgeDetail";

vi.mock("../../lib/engineApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/engineApi")>();
  return { ...actual, getClause: vi.fn() };
});

const OUTSOURCING_12_1 =
  "A financial institution must obtain the Bank's written approval before " +
  "entering into a new material outsourcing arrangement.";
const OPRES_1_1 =
  "This Discussion Paper sets out the emerging direction for strengthening " +
  "the continuity of critical financial services amid deeper third-party " +
  "dependencies.";

function clause(clauseNumber: string, text: string): Clause {
  return {
    clause_number: clauseNumber,
    text,
    policy_id: "x",
    document_id: "x",
    source: "published",
  };
}

beforeEach(() => {
  vi.mocked(getClause).mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("EdgeDetail — verbatim connection citations", () => {
  it("Test 3: quotes Outsourcing 12.1 verbatim for the core RMiT↔Outsourcing connection", async () => {
    vi.mocked(getClause).mockImplementation(async (clauseNumber: string) => {
      if (clauseNumber === "Outsourcing 12.1")
        return clause("Outsourcing 12.1", OUTSOURCING_12_1);
      if (clauseNumber === "RMiT 17.1")
        return clause("RMiT 17.1", "RMiT 17.1 notification text");
      if (clauseNumber === "RMiT 17.2")
        return clause("RMiT 17.2", "RMiT 17.2 subsequent-adoption text");
      throw new EngineNotFound("CLAUSE_NOT_FOUND", "nope");
    });

    const edge: GraphEdge = {
      source: "rmit-v2-2026-draft",
      target: "outsourcing-v1-2019",
      type: "overlaps",
      reason:
        "A public-cloud arrangement is often also a material outsourcing. " +
        "RMiT clause 17 interacts with Outsourcing 12.1 (written approval) — " +
        "the core conflict in this cluster.",
      source_clauses: ["RMiT 17.1", "RMiT 17.2"],
      target_clauses: ["Outsourcing 12.1"],
    };

    render(<EdgeDetail edge={edge} />);

    expect(
      screen.getByRole("heading", { name: /why these are connected/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/core conflict in this cluster/i),
    ).toBeInTheDocument();
    expect(await screen.findByText(OUTSOURCING_12_1)).toBeInTheDocument();
    // The clause number labels the quote.
    expect(screen.getAllByText(/Outsourcing 12\.1/).length).toBeGreaterThan(0);
  });

  it("Test 4: cites RMiT 10.50 ↔ Operational Resilience 1.1 and never the phantom 6.11", async () => {
    vi.mocked(getClause).mockImplementation(async (clauseNumber: string) => {
      if (clauseNumber === "Operational Resilience 1.1")
        return clause("Operational Resilience 1.1", OPRES_1_1);
      if (clauseNumber === "RMiT 10.50")
        return clause("RMiT 10.50", "RMiT 10.50 cloud risk-assessment text");
      throw new EngineNotFound("CLAUSE_NOT_FOUND", "nope");
    });

    const edge: GraphEdge = {
      source: "rmit-v2-2026-draft",
      target: "opres-v1-2025-draft",
      type: "overlaps",
      reason:
        "Both govern the continuity of critical services that depend on " +
        "cloud/third parties. RMiT 10.50 overlaps Operational Resilience 1.1.",
      source_clauses: ["RMiT 10.50"],
      target_clauses: ["Operational Resilience 1.1"],
    };

    render(<EdgeDetail edge={edge} />);

    expect(await screen.findByText(OPRES_1_1)).toBeInTheDocument();
    expect(
      screen.getAllByText(/Operational Resilience 1\.1/).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/RMiT 10\.50/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/6\.11/)).not.toBeInTheDocument();
  });
});

describe("EdgeDetail — verbatim-citation guardrail", () => {
  it("Test 5: shows 'No matching clause found' for a clause that does not resolve", async () => {
    vi.mocked(getClause).mockRejectedValue(
      new EngineNotFound(
        "CLAUSE_NOT_FOUND",
        "No matching clause found for 'RMiT 99.9'",
      ),
    );

    const edge: GraphEdge = {
      source: "rmit-v2-2026-draft",
      target: "phantom",
      type: "overlaps",
      reason: "An edge citing a clause absent from the index.",
      source_clauses: [],
      target_clauses: ["RMiT 99.9"],
    };

    render(<EdgeDetail edge={edge} />);

    expect(
      await screen.findByText(/no matching clause found/i),
    ).toBeInTheDocument();
    // No invented text: the unresolved clause number is still shown honestly.
    expect(screen.getAllByText(/RMiT 99\.9/).length).toBeGreaterThan(0);
  });
});

describe("EdgeDetail — reference connections defer deep content to #26", () => {
  it("hands off to the Reference Radar and never fetches a verbatim passage", () => {
    const edge: GraphEdge = {
      source: "rmit-v2-2026-draft",
      target: "pdpa-2010",
      type: "references",
      reason:
        "A cloud region outside Malaysia engages the PDPA's limits on " +
        "transferring personal data abroad.",
      source_clauses: ["RMiT 17.1"],
      target_clauses: ["PDPA 129"],
    };

    const { container } = render(<EdgeDetail edge={edge} />);

    expect(
      screen.getByRole("heading", { name: /why this reference matters/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/limits on transferring personal data abroad/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /see in the reference radar/i }),
    ).toBeInTheDocument();
    expect(vi.mocked(getClause)).not.toHaveBeenCalled();
    expect(
      container.querySelector('[data-testid="clause-passage"]'),
    ).toBeNull();
  });
});
