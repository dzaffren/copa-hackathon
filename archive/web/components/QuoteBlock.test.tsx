import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QuoteBlock } from "./QuoteBlock";

describe("QuoteBlock", () => {
  it("renders a verified quote with the verified marker (never upgraded)", () => {
    render(
      <QuoteBlock
        quote={{
          clause_number: "OECD 1.2",
          text: "AI actors should implement...",
          verification: "verified",
        }}
      />,
    );
    const fig = screen.getByTestId("quote-block");
    expect(fig).toHaveAttribute("data-verification", "verified");
    expect(screen.getByText(/verified against source/)).toBeInTheDocument();
    expect(
      screen.getByText(/“AI actors should implement...”/),
    ).toBeInTheDocument();
  });

  it("marks an illustrative quote distinctly and never as verified", () => {
    render(
      <QuoteBlock
        quote={{
          clause_number: "FTFC 8.1",
          text: "A financial service provider...",
          verification: "illustrative",
        }}
      />,
    );
    expect(screen.getByTestId("quote-block")).toHaveAttribute(
      "data-verification",
      "illustrative",
    );
    expect(
      screen.getByText(/illustrative quote — not yet verified/),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/verified against source document/),
    ).not.toBeInTheDocument();
  });

  it("shows a pending_extraction placeholder, never an approximated string", () => {
    render(
      <QuoteBlock
        quote={{
          clause_number: "Basel RBC20",
          text: null,
          verification: "pending_extraction",
        }}
      />,
    );
    expect(screen.getByTestId("quote-block")).toHaveAttribute(
      "data-verification",
      "pending_extraction",
    );
    expect(screen.getAllByText(/pending extraction/i).length).toBeGreaterThan(
      0,
    );
    // No fabricated quote text (no smart-quotes wrapper).
    expect(screen.queryByText(/“/)).not.toBeInTheDocument();
  });
});
