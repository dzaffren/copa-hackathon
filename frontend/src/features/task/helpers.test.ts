import { describe, it, expect } from "vitest";
import { nodeTypeStyle, shortLabelForNode } from "./nodeType";
import { labelText } from "./semanticLabel";

describe("nodeTypeStyle", () => {
  it("maps each node type to a distinct dot colour", () => {
    const dots = [
      "international-standard",
      "peer-regulator",
      "act-law",
      "industry-input",
    ].map((t) => nodeTypeStyle(t as never).dot);
    expect(new Set(dots).size).toBe(dots.length);
  });
});

describe("shortLabelForNode", () => {
  it("maps known neighbour ids to filter-chip labels", () => {
    expect(shortLabelForNode("hkma-spm-or2", "HKMA SPM OR-2")).toBe("HKMA");
    expect(shortLabelForNode("rmit-pd-2025", "RMiT PD (28 Nov 2025)")).toBe(
      "RMiT",
    );
  });

  it("falls back to the leading token of the title", () => {
    expect(shortLabelForNode("unknown-node", "Basel Committee doc")).toBe(
      "Basel",
    );
  });
});

describe("labelText", () => {
  it("appends the sentiment arrow only for differs-on", () => {
    expect(labelText("differs-on", "tighten")).toBe("differs-on ↑");
    expect(labelText("differs-on", "loosen")).toBe("differs-on ↓");
    expect(labelText("conflicts-with", null)).toBe("conflicts-with");
    expect(labelText("aligns-with", null)).toBe("aligns-with");
  });
});
