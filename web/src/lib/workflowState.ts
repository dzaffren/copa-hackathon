// Drafter workflow-state store — the single seam #8 (alignment) and #9 (copilot)
// share (spec-drafter-workspace.md · Data Model; ADR
// docs/adr/0001-workflow-state-localstorage-demo.md).
//
// For MVP1 this is backed by the browser's `localStorage`, with cross-tab live
// sync via the `window` `storage` event — the pattern the clickable POC proved.
// The whole store lives behind THIS module: no other file touches `localStorage`
// or builds a storage key, so the production swap (a server-side, per-document
// workflow store) is an implementation change here, not a rewrite of #8/#9.
//
// Two record kinds, one key each per document:
//   • `rr:findings:v1:{documentId}`         → Finding[]        (written by #8/#9)
//   • `rr:tracked-changes:v1:{documentId}`  → TrackedChange[]  (written by #9)
//
// #7 (this story) DEFINES and READS these; #8/#9 write them. Reads tolerate a
// missing / blank / corrupt value by returning `[]` — a workflow store must never
// throw on load. Writes are upsert-by-`id`: a repeated write of the same id
// REPLACES it, so re-running a classifier never duplicates a finding.

import type { Finding, TrackedChange } from "../types";

// ---------------------------------------------------------------------------
// Storage keys (the localStorage contract consumed by #8/#9)
// ---------------------------------------------------------------------------

const FINDINGS_PREFIX = "rr:findings:v1:";
const TRACKED_CHANGES_PREFIX = "rr:tracked-changes:v1:";

function findingsKey(documentId: string): string {
  return `${FINDINGS_PREFIX}${documentId}`;
}

function trackedChangesKey(documentId: string): string {
  return `${TRACKED_CHANGES_PREFIX}${documentId}`;
}

// ---------------------------------------------------------------------------
// Swappable storage backend
// ---------------------------------------------------------------------------

/**
 * Resolve the `localStorage` backend, or `null` when it is unavailable (SSR, a
 * privacy mode that throws on access). Every read/write funnels through here so
 * the store degrades to a safe no-op instead of crashing the workspace.
 */
function getStorage(): Storage | null {
  try {
    if (typeof window === "undefined" || !window.localStorage) return null;
    return window.localStorage;
  } catch {
    return null;
  }
}

/** Read + parse a JSON array at `key`, tolerating missing/blank/corrupt data. */
function readArray<T>(key: string): T[] {
  const storage = getStorage();
  if (!storage) return [];

  let raw: string | null;
  try {
    raw = storage.getItem(key);
  } catch {
    return [];
  }
  if (raw === null || raw.trim() === "") return [];

  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as T[]) : [];
  } catch {
    return [];
  }
}

/** Serialise + persist an array at `key`; a failing backend is swallowed. */
function writeArray<T>(key: string, items: T[]): void {
  const storage = getStorage();
  if (!storage) return;
  try {
    storage.setItem(key, JSON.stringify(items));
  } catch {
    // Quota / privacy-mode errors are non-fatal for the demo store.
  }
}

/** Insert `item` by `id`, replacing an existing entry with the same id. */
function upsertById<T extends { id: string }>(key: string, item: T): T[] {
  const items = readArray<T>(key);
  const index = items.findIndex((existing) => existing.id === item.id);
  if (index >= 0) {
    items[index] = item;
  } else {
    items.push(item);
  }
  writeArray(key, items);
  return items;
}

// ---------------------------------------------------------------------------
// Subscriptions (cross-tab + same-tab live sync of findings)
// ---------------------------------------------------------------------------

/** A findings subscriber, called with a fresh array whenever findings change. */
export type FindingsListener = (findings: Finding[]) => void;

/** documentId → its live findings listeners. */
const findingsListeners = new Map<string, Set<FindingsListener>>();

let storageListenerAttached = false;

/**
 * Handle a `window` `storage` event delivered by ANOTHER tab. Browsers fire
 * this only in tabs that did not make the write, so this path covers cross-tab
 * sync; same-tab writes notify directly from the upsert helpers below.
 */
function handleStorageEvent(event: StorageEvent): void {
  // `key === null` means the whole store was cleared — refresh every document.
  if (event.key === null) {
    for (const [documentId, listeners] of findingsListeners) {
      notify(listeners, getFindings(documentId));
    }
    return;
  }
  if (!event.key.startsWith(FINDINGS_PREFIX)) return;

  const documentId = event.key.slice(FINDINGS_PREFIX.length);
  const listeners = findingsListeners.get(documentId);
  if (!listeners) return;
  notify(listeners, getFindings(documentId));
}

function notify(listeners: Set<FindingsListener>, findings: Finding[]): void {
  // Copy so a listener that (un)subscribes during dispatch can't corrupt the set.
  for (const listener of [...listeners]) listener(findings);
}

function ensureStorageListener(): void {
  if (storageListenerAttached || typeof window === "undefined") return;
  window.addEventListener("storage", handleStorageEvent);
  storageListenerAttached = true;
}

/**
 * Subscribe to a document's findings. The listener fires with a fresh
 * `Finding[]` when another tab writes (via the `storage` event) AND when this
 * tab writes (so a single-tab demo updates live). Returns an unsubscribe fn.
 */
export function subscribe(
  documentId: string,
  listener: FindingsListener,
): () => void {
  let listeners = findingsListeners.get(documentId);
  if (!listeners) {
    listeners = new Set();
    findingsListeners.set(documentId, listeners);
  }
  listeners.add(listener);
  ensureStorageListener();

  return () => {
    const set = findingsListeners.get(documentId);
    if (!set) return;
    set.delete(listener);
    if (set.size === 0) findingsListeners.delete(documentId);
  };
}

// ---------------------------------------------------------------------------
// Findings
// ---------------------------------------------------------------------------

/** All findings for a document (`[]` when none / unreadable). */
export function getFindings(documentId: string): Finding[] {
  return readArray<Finding>(findingsKey(documentId));
}

/**
 * Write a finding, keyed by its own `documentId`. Upserts by `id` (replace, no
 * duplicate) and notifies same-tab subscribers with the fresh array.
 */
export function upsertFinding(finding: Finding): void {
  const items = upsertById<Finding>(findingsKey(finding.documentId), finding);
  const listeners = findingsListeners.get(finding.documentId);
  if (listeners) notify(listeners, items);
}

// ---------------------------------------------------------------------------
// Tracked changes
// ---------------------------------------------------------------------------

/** All tracked-change markers for a document (`[]` when none / unreadable). */
export function getTrackedChanges(documentId: string): TrackedChange[] {
  return readArray<TrackedChange>(trackedChangesKey(documentId));
}

/**
 * Write a tracked-change marker, keyed by `documentId`. `documentId` is an
 * explicit argument because — unlike `Finding` — `TrackedChange` carries no
 * `documentId` field (see `web/src/types.ts`, which #7 must not modify).
 * Upserts by `id` (replace, no duplicate).
 */
export function upsertTrackedChange(
  documentId: string,
  change: TrackedChange,
): void {
  upsertById<TrackedChange>(trackedChangesKey(documentId), change);
}
