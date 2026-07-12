// Contract test: the committed snapshot in public/data parses into the engine
// read-API types, and lib/data.ts's fetch seam returns it. Guards the boundary
// between the hand-authored demo JSON and the TypeScript types the UI relies on.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchConnections, fetchParagraphs } from "./data";
import { isBlocked } from "./types";

const DATA = resolve(__dirname, "..", "public", "data");
const readSnapshot = (rel: string) => readFileSync(resolve(DATA, rel), "utf8");

// Stub global fetch to serve the committed snapshot files (snapshot mode uses
// relative /data/* URLs, which have no origin under jsdom).
beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const rel = url.replace(/^\/data\//, "");
      try {
        return new Response(readSnapshot(rel), { status: 200 });
      } catch {
        return new Response("not found", { status: 404 });
      }
    }),
  );
});

afterEach(() => vi.unstubAllGlobals());

describe("committed snapshot ↔ types contract", () => {
  it("parses paragraphs.json with 54 paragraphs and the showcase trio analysed", async () => {
    const p = await fetchParagraphs();
    expect(p.document_id).toBe("ai-dp-2025");
    expect(p.total_paragraphs).toBe(54);
    const byNumber = Object.fromEntries(p.paragraphs.map((x) => [x.number, x]));
    for (const n of ["3.5", "3.11", "4.6"]) {
      expect(byNumber[n].state).toBe("analysed");
      expect(byNumber[n].connection_count).toBeGreaterThan(0);
    }
  });

  it("4.6 carries the PDPA §129 Conflict with a verified verbatim quote", async () => {
    const c = await fetchConnections("4.6");
    expect(c.connections).toHaveLength(3);
    const pdpa = c.connections.find((x) => x.id.includes("pdpa-2010"));
    expect(pdpa?.verdict).toBe("Conflict");
    expect(pdpa && !isBlocked(pdpa) && pdpa.quote.verification).toBe(
      "verified",
    );
    expect(pdpa && !isBlocked(pdpa) && pdpa.quote.text).toContain(
      "transfer any personal data",
    );
  });

  it("3.5 includes a blocked MAS connection with no verdict or quote", async () => {
    const c = await fetchConnections("3.5");
    const mas = c.connections.find((x) => x.id.includes("mas-feat"));
    expect(mas && isBlocked(mas)).toBe(true);
    expect(mas?.verdict).toBeNull();
    expect(mas?.quote).toBeNull();
  });

  it("a paragraph with no snapshot file resolves to not_analysed, not a crash", async () => {
    const c = await fetchConnections("9.9");
    expect(c.state).toBe("not_analysed");
    expect(c.connections).toEqual([]);
  });
});
