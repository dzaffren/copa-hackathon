import { beforeEach, describe, expect, it } from "vitest";
import { useStore } from "./store";
import type { ConnectionsResponse } from "./types";

const engineEmpty: ConnectionsResponse = {
  paragraph: { number: "3.11", title: "GenAI hallucinations" },
  state: "analysed",
  no_matching_source: true,
  connections: [],
};

beforeEach(() => {
  localStorage.clear();
  useStore.getState().reset();
});

describe("addSource", () => {
  it("adds a drafter source and surfaces it as a connection (idempotent)", () => {
    const { addSource } = useStore.getState();
    addSource("3.11", {
      title: "IOSCO — AI in capital markets (2025)",
      source_type: "peer_regulator",
    });
    addSource("3.11", {
      title: "IOSCO — AI in capital markets (2025)",
      source_type: "peer_regulator",
    });

    const merged = useStore.getState().connectionsFor("3.11", engineEmpty);
    expect(merged.connections).toHaveLength(1); // second identical add is a no-op
    expect(merged.connections[0].source.title).toBe(
      "IOSCO — AI in capital markets (2025)",
    );
    expect(merged.no_matching_source).toBe(false); // an added source is a real result
  });

  it("rejects an empty title (no slice entry written)", () => {
    useStore
      .getState()
      .addSource("3.11", { title: "   ", source_type: "peer_regulator" });
    expect(useStore.getState().sources["3.11"]).toBeUndefined();
  });
});

describe("supplyBlocked", () => {
  it("records a supplied blocked connection idempotently", () => {
    const { supplyBlocked } = useStore.getState();
    supplyBlocked("ai-dp-2025:3.5::mas-feat");
    supplyBlocked("ai-dp-2025:3.5::mas-feat");
    expect(useStore.getState().blocked).toEqual(["ai-dp-2025:3.5::mas-feat"]);
  });
});

describe("reset", () => {
  it("clears every slice — a fresh upload is a fresh session", () => {
    const s = useStore.getState();
    s.addSource("3.11", { title: "IOSCO", source_type: "peer_regulator" });
    s.supplyBlocked("ai-dp-2025:3.5::mas-feat");

    useStore.getState().reset();

    const after = useStore.getState();
    expect(after.sources).toEqual({});
    expect(after.blocked).toEqual([]);
    expect(after.trail).toEqual([]);
    expect(after.submitted).toBeNull();
  });
});

describe("connectionsFor", () => {
  it("returns the engine payload unchanged when the drafter added nothing", () => {
    expect(useStore.getState().connectionsFor("4.6", engineEmpty)).toBe(
      engineEmpty,
    );
  });
});
