import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConnectionRail } from "./ConnectionRail";
import type { ConnectionsResponse } from "@/lib/types";

const noop = () => {};
const notSupplied = () => false;

const analysed: ConnectionsResponse = {
  paragraph: { number: "3.5", title: "Fair usage & bias" },
  state: "analysed",
  no_matching_source: false,
  connections: [
    {
      id: "ai-dp-2025:3.5::oecd:OECD 1.2",
      branch: "cited",
      source: {
        document_id: "oecd-ai",
        title: "OECD AI Principles",
        source_type: "international_standard",
      },
      verdict: "Consensus",
      verdict_status: "proposed",
      confidence: "High",
      rationale: "OECD backs the fairness stance.",
      quote: {
        clause_number: "OECD 1.2",
        text: "AI actors...",
        verification: "verified",
      },
    },
    {
      id: "ai-dp-2025:3.5::ftfc:FTFC 8.1",
      branch: "uncited",
      source: {
        document_id: "bnm-ftfc",
        title: "BNM Fair Treatment",
        source_type: "internal_bnm",
      },
      verdict: "Duplicate",
      verdict_status: "proposed",
      confidence: "Medium",
      rationale: "Already covered.",
      quote: {
        clause_number: "FTFC 8.1",
        text: "A financial service provider...",
        verification: "illustrative",
      },
    },
    {
      id: "ai-dp-2025:3.5::mas-feat",
      branch: "uncited",
      source: {
        document_id: "mas-feat",
        title: "MAS — FEAT Principles",
        source_type: "peer_regulator",
      },
      status: "could_not_retrieve",
      reason: "The MAS site blocks automated access.",
      verdict: null,
      quote: null,
    },
  ],
};

describe("ConnectionRail — the four distinct states", () => {
  it("state 1+4: analysed shows verified vs illustrative distinctly, plus a blocked card with no verdict/quote", () => {
    render(
      <ConnectionRail
        data={analysed}
        isSupplied={notSupplied}
        onSupply={noop}
        onAnalyse={noop}
      />,
    );
    // verified vs illustrative markers both present and distinct
    expect(
      screen.getByText(/verified against source document/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/illustrative quote — not yet verified/),
    ).toBeInTheDocument();
    // blocked card: reason shown, no verdict badge, no quote
    const blocked = screen.getByTestId("blocked-card");
    expect(blocked).toHaveTextContent(/couldn’t retrieve/);
    expect(
      screen.getByTestId("conn-ai-dp-2025:3.5::mas-feat"),
    ).not.toHaveTextContent("Consensus");
    // two real verdict badges (OECD Consensus, BNM Duplicate) — blocked has none
    expect(screen.getByTestId("verdict-Consensus")).toBeInTheDocument();
    expect(screen.getByTestId("verdict-Duplicate")).toBeInTheDocument();
  });

  it("state 2: analysed with no bearing source shows 'No matching source found'", () => {
    const empty: ConnectionsResponse = {
      paragraph: { number: "5.4", title: "x" },
      state: "analysed",
      no_matching_source: true,
      connections: [],
    };
    render(
      <ConnectionRail
        data={empty}
        isSupplied={notSupplied}
        onSupply={noop}
        onAnalyse={noop}
      />,
    );
    expect(screen.getByTestId("rail-no-source")).toHaveTextContent(
      /No matching source found/,
    );
  });

  it("state 3: not_analysed shows the analyse prompt and calls onAnalyse", async () => {
    const onAnalyse = vi.fn();
    const na: ConnectionsResponse = {
      paragraph: { number: "3.2", title: "x" },
      state: "not_analysed",
      no_matching_source: false,
      connections: [],
    };
    render(
      <ConnectionRail
        data={na}
        isSupplied={notSupplied}
        onSupply={noop}
        onAnalyse={onAnalyse}
      />,
    );
    const btn = screen.getByTestId("analyse-paragraph");
    expect(btn).toBeInTheDocument();
    btn.click();
    expect(onAnalyse).toHaveBeenCalledOnce();
  });

  it("nothing selected shows the empty prompt", () => {
    render(
      <ConnectionRail
        data={null}
        isSupplied={notSupplied}
        onSupply={noop}
        onAnalyse={noop}
      />,
    );
    expect(screen.getByTestId("rail-empty")).toHaveTextContent(
      /Select a paragraph/,
    );
  });

  it("supplied blocked source flips to 'you supplied it' with no fabricated quote", () => {
    render(
      <ConnectionRail
        data={analysed}
        isSupplied={(id) => id === "ai-dp-2025:3.5::mas-feat"}
        onSupply={noop}
        onAnalyse={noop}
      />,
    );
    expect(screen.getByTestId("blocked-supplied")).toHaveTextContent(
      /You supplied it/,
    );
    expect(screen.queryByTestId("blocked-card")).not.toBeInTheDocument();
  });
});
