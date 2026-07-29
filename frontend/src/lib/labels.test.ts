import { describe, it, expect } from "vitest";

import { LABEL_SEVERITY_ORDER, bySeverity, labelSeverityRank } from "./labels";
import type { SemanticLabel } from "./types";

describe("bySeverity", () => {
  it("ranks the five labels conflicts → differs → silent → goes-beyond → aligns", () => {
    expect(LABEL_SEVERITY_ORDER).toEqual([
      "conflicts-with",
      "differs-on",
      "silent-on",
      "goes-beyond",
      "aligns-with",
    ]);
  });

  it("orders a shuffled list of findings by attention", () => {
    const findings = (
      [
        "aligns-with",
        "goes-beyond",
        "conflicts-with",
        "silent-on",
        "differs-on",
      ] as SemanticLabel[]
    ).map((label) => ({ label }));

    expect(bySeverity(findings).map((f) => f.label)).toEqual(
      LABEL_SEVERITY_ORDER,
    );
  });

  it("keeps same-label findings in their original file order", () => {
    const findings = [
      { label: "aligns-with" as SemanticLabel, id: "a" },
      { label: "conflicts-with" as SemanticLabel, id: "b" },
      { label: "aligns-with" as SemanticLabel, id: "c" },
    ];
    expect(bySeverity(findings).map((f) => f.id)).toEqual(["b", "a", "c"]);
  });

  it("does not mutate its input", () => {
    const findings = [
      { label: "aligns-with" as SemanticLabel },
      { label: "conflicts-with" as SemanticLabel },
    ];
    bySeverity(findings);
    expect(findings.map((f) => f.label)).toEqual([
      "aligns-with",
      "conflicts-with",
    ]);
  });

  it("sorts an unknown label last rather than dropping it", () => {
    const rogue = "not-a-label" as SemanticLabel;
    expect(labelSeverityRank(rogue)).toBe(LABEL_SEVERITY_ORDER.length);
    expect(
      bySeverity([{ label: rogue }, { label: "aligns-with" }]).map(
        (f) => f.label,
      ),
    ).toEqual(["aligns-with", rogue]);
  });
});
