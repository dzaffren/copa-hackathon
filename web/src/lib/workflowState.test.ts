// Tests for the localStorage-backed workflow store
// (spec-drafter-workspace.md · Data Model + Test Scenarios · Test 10, and
// docs/adr/0001-workflow-state-localstorage-demo.md).
//
// jsdom gives us a real `window.localStorage` and `StorageEvent`. jsdom never
// auto-fires `storage` events (there is a single window), so cross-tab sync is
// exercised by mutating `localStorage` to simulate "another tab" and then
// dispatching a synthetic `StorageEvent` — exactly what a second browser tab
// would deliver to this one.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Finding, TrackedChange } from "../types";
import {
  getFindings,
  getTrackedChanges,
  subscribe,
  upsertFinding,
  upsertTrackedChange,
} from "./workflowState";

const DOC_ID = "rmit-v2-2026-draft";
const FINDINGS_KEY = "rr:findings:v1:rmit-v2-2026-draft";
const TRACKED_KEY = "rr:tracked-changes:v1:rmit-v2-2026-draft";

function makeFinding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: "finding-rmit-17-1-outsourcing",
    documentId: DOC_ID,
    tier: "internal-overlap",
    type: "conflict",
    status: "open",
    inDraft: false,
    ...overrides,
  };
}

function makeChange(overrides: Partial<TrackedChange> = {}): TrackedChange {
  return {
    id: "tc-rmit-17-1",
    findingId: "finding-rmit-17-1-outsourcing",
    clauseNumber: "RMiT 17.1",
    insertedText: "The financial institution must obtain the Bank's approval …",
    acceptedAt: "2026-07-12T09:00:00.000Z",
    ...overrides,
  };
}

/** Fire the `storage` event a real second tab would deliver for `key`. */
function dispatchStorage(key: string, newValue: string | null): void {
  window.dispatchEvent(
    new StorageEvent("storage", {
      key,
      newValue,
      storageArea: window.localStorage,
    }),
  );
}

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  window.localStorage.clear();
});

describe("Test 10: workflowState round-trip + cross-tab sync", () => {
  it("writes a Finding under rr:findings:v1:{documentId} and reads it back", () => {
    const finding = makeFinding();

    upsertFinding(finding);

    // Round-trip through the public reader …
    expect(getFindings(DOC_ID)).toEqual([finding]);
    // … and the key is exactly the contracted one.
    expect(window.localStorage.getItem(FINDINGS_KEY)).toBe(
      JSON.stringify([finding]),
    );
  });

  it("delivers a fresh Finding[] to subscribers on a storage event for that key", () => {
    const received: Finding[][] = [];
    const unsubscribe = subscribe(DOC_ID, (findings) => {
      received.push(findings);
    });

    // Simulate a second tab writing an updated finding, then the browser
    // delivering the storage event to this tab.
    const updated = makeFinding({ status: "accepted", inDraft: true });
    const newValue = JSON.stringify([updated]);
    window.localStorage.setItem(FINDINGS_KEY, newValue);
    dispatchStorage(FINDINGS_KEY, newValue);

    expect(received).toHaveLength(1);
    expect(received[0]).toEqual([updated]);

    unsubscribe();
  });

  it("does not notify subscribers for a different document's key", () => {
    const received: Finding[][] = [];
    const unsubscribe = subscribe(DOC_ID, (findings) =>
      received.push(findings),
    );

    const otherKey = "rr:findings:v1:outsourcing-v1-2019";
    const otherValue = JSON.stringify([
      makeFinding({ documentId: "outsourcing-v1-2019" }),
    ]);
    window.localStorage.setItem(otherKey, otherValue);
    dispatchStorage(otherKey, otherValue);

    expect(received).toHaveLength(0);
    unsubscribe();
  });

  it("upserts by id — a repeated write of the same id replaces, never duplicates", () => {
    upsertFinding(makeFinding({ status: "open" }));
    upsertFinding(
      makeFinding({ status: "dismissed", reason: "Not a conflict" }),
    );

    const findings = getFindings(DOC_ID);
    expect(findings).toHaveLength(1);
    expect(findings[0].status).toBe("dismissed");
    expect(findings[0].reason).toBe("Not a conflict");
  });

  it("appends distinct ids rather than replacing", () => {
    upsertFinding(makeFinding({ id: "finding-a" }));
    upsertFinding(makeFinding({ id: "finding-b" }));

    const ids = getFindings(DOC_ID).map((f) => f.id);
    expect(ids).toEqual(["finding-a", "finding-b"]);
  });

  it("notifies same-tab subscribers on an upsert (single-tab demo)", () => {
    const received: Finding[][] = [];
    const unsubscribe = subscribe(DOC_ID, (findings) =>
      received.push(findings),
    );

    upsertFinding(makeFinding());

    expect(received).toHaveLength(1);
    expect(received[0]).toEqual([makeFinding()]);
    unsubscribe();
  });
});

describe("corrupt / missing JSON is tolerated (returns [])", () => {
  it("returns [] when the key is missing", () => {
    expect(getFindings("never-written")).toEqual([]);
    expect(getTrackedChanges("never-written")).toEqual([]);
  });

  it("returns [] when the stored value is blank", () => {
    window.localStorage.setItem(FINDINGS_KEY, "");
    expect(getFindings(DOC_ID)).toEqual([]);
  });

  it("returns [] and does not throw on corrupt JSON", () => {
    window.localStorage.setItem(FINDINGS_KEY, "{ not valid json");
    expect(() => getFindings(DOC_ID)).not.toThrow();
    expect(getFindings(DOC_ID)).toEqual([]);
  });

  it("returns [] when the JSON parses but is not an array", () => {
    window.localStorage.setItem(FINDINGS_KEY, JSON.stringify({ id: "x" }));
    expect(getFindings(DOC_ID)).toEqual([]);
  });
});

describe("unsubscribe stops notifications", () => {
  it("stops both same-tab and storage-event notifications after unsubscribe", () => {
    const received: Finding[][] = [];
    const unsubscribe = subscribe(DOC_ID, (findings) =>
      received.push(findings),
    );

    upsertFinding(makeFinding());
    expect(received).toHaveLength(1);

    unsubscribe();

    // Same-tab write: no notification.
    upsertFinding(makeFinding({ status: "accepted" }));
    // Cross-tab event: no notification.
    const value = JSON.stringify([makeFinding({ status: "accepted" })]);
    window.localStorage.setItem(FINDINGS_KEY, value);
    dispatchStorage(FINDINGS_KEY, value);

    expect(received).toHaveLength(1);
  });
});

describe("tracked changes", () => {
  it("writes under rr:tracked-changes:v1:{documentId} and reads back", () => {
    const change = makeChange();
    upsertTrackedChange(DOC_ID, change);

    expect(getTrackedChanges(DOC_ID)).toEqual([change]);
    expect(window.localStorage.getItem(TRACKED_KEY)).toBe(
      JSON.stringify([change]),
    );
  });

  it("upserts a tracked change by id (replace, no duplicate)", () => {
    upsertTrackedChange(DOC_ID, makeChange({ insertedText: "first" }));
    upsertTrackedChange(DOC_ID, makeChange({ insertedText: "second" }));

    const changes = getTrackedChanges(DOC_ID);
    expect(changes).toHaveLength(1);
    expect(changes[0].insertedText).toBe("second");
  });

  it("keeps findings and tracked changes in separate keys", () => {
    upsertFinding(makeFinding());
    upsertTrackedChange(DOC_ID, makeChange());

    expect(getFindings(DOC_ID)).toHaveLength(1);
    expect(getTrackedChanges(DOC_ID)).toHaveLength(1);
  });
});

describe("storage swappability", () => {
  it("tolerates a missing storage backend without throwing", () => {
    const spy = vi
      .spyOn(window.localStorage, "getItem")
      .mockImplementation(() => {
        throw new Error("storage disabled");
      });

    expect(() => getFindings(DOC_ID)).not.toThrow();
    expect(getFindings(DOC_ID)).toEqual([]);

    spy.mockRestore();
  });
});
