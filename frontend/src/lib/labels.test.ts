import { describe, it, expect } from "vitest";

import {
  LABEL_SEVERITY_ORDER,
  bySeverity,
  forGroupDisplay,
  labelSeverityRank,
  reviewStateRank,
} from "./labels";
import type { ReviewState, SemanticLabel } from "./types";

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

describe("forGroupDisplay", () => {
  const card = (id: string, review_state: ReviewState) => ({
    id,
    review_state,
  });

  it("floats pending above judged findings", () => {
    expect(reviewStateRank("pending")).toBe(0);
    expect(reviewStateRank("accepted")).toBe(1);
    expect(reviewStateRank("dismissed")).toBe(1);
  });

  it("sinks accepted and dismissed cards to the bottom of the group", () => {
    const cards = [
      card("accepted-1", "accepted"),
      card("pending-1", "pending"),
      card("dismissed-1", "dismissed"),
      card("pending-2", "pending"),
    ];
    expect(forGroupDisplay(cards).map((c) => c.id)).toEqual([
      "pending-1",
      "pending-2",
      "accepted-1",
      "dismissed-1",
    ]);
  });

  it("keeps accepted and dismissed in server order relative to each other", () => {
    // They share a rank, so a stable sort must not interleave or swap them —
    // the drafter's own sequence of decisions is the order she expects.
    const cards = [
      card("dismissed-1", "dismissed"),
      card("accepted-1", "accepted"),
      card("dismissed-2", "dismissed"),
    ];
    expect(forGroupDisplay(cards).map((c) => c.id)).toEqual([
      "dismissed-1",
      "accepted-1",
      "dismissed-2",
    ]);
  });

  it("preserves server order within the pending block", () => {
    const cards = [
      card("a", "pending"),
      card("b", "pending"),
      card("c", "pending"),
    ];
    expect(forGroupDisplay(cards).map((c) => c.id)).toEqual(["a", "b", "c"]);
  });

  it("does not mutate its input", () => {
    const cards = [
      card("accepted-1", "accepted"),
      card("pending-1", "pending"),
    ];
    forGroupDisplay(cards);
    expect(cards.map((c) => c.id)).toEqual(["accepted-1", "pending-1"]);
  });

  it("handles an empty group", () => {
    expect(forGroupDisplay([])).toEqual([]);
  });
});
