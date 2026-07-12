"use client";

import { useCallback, useEffect, useState } from "react";
import { ConnectionRail } from "@/components/ConnectionRail";
import { SourceTypeDot } from "@/components/SourceTypeDot";
import {
  DataUnavailableError,
  analyse as analyseParagraph,
  fetchConnections,
  fetchParagraphs,
  isSnapshot,
} from "@/lib/data";
import { SOURCE_TYPE_LABEL, SOURCE_TYPE_ORDER } from "@/lib/labels";
import { useStore } from "@/lib/store";
import type { ConnectionsResponse, ParagraphSummary } from "@/lib/types";

const DEFAULT_PARAGRAPH = "4.6"; // its PDPA §129 Conflict is the strongest opening hook

export default function WorkspacePage() {
  const [paragraphs, setParagraphs] = useState<ParagraphSummary[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [conn, setConn] = useState<ConnectionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addTitle, setAddTitle] = useState("");

  const connectionsFor = useStore((s) => s.connectionsFor);
  const addSource = useStore((s) => s.addSource);
  const supplyBlocked = useStore((s) => s.supplyBlocked);
  const blocked = useStore((s) => s.blocked);
  const sources = useStore((s) => s.sources);

  // Load the canvas once; default-select 4.6 (or the first analysed paragraph).
  useEffect(() => {
    let live = true;
    fetchParagraphs()
      .then((p) => {
        if (!live) return;
        setParagraphs(p.paragraphs);
        const preferred =
          p.paragraphs.find((x) => x.number === DEFAULT_PARAGRAPH) ??
          p.paragraphs.find((x) => x.state === "analysed");
        if (preferred) setSelected(preferred.number);
      })
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
  }, []);

  // Fetch the selected paragraph's connections, ignoring a stale response if the
  // selection changed mid-flight. Re-runs when the selection OR the drafter's own
  // sources change (add-source / supply-blocked flow through the store and reflect
  // live here). The `cancelled` guard is why the setState calls are safe.
  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    // Fetch-on-selection is a legitimate effect; the `cancelled` guard above
    // makes these state writes safe against a stale async response.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError(null);
    fetchConnections(selected)
      .then((raw) => {
        if (cancelled) return;
        setConn(connectionsFor(selected, raw));
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof DataUnavailableError ? e.message : String(e));
        setConn(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selected, connectionsFor, sources, blocked]);

  const onAnalyse = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const raw = await analyseParagraph(selected);
      setConn(connectionsFor(selected, raw));
      setParagraphs(
        (prev) =>
          prev?.map((p) =>
            p.number === selected
              ? {
                  ...p,
                  state: "analysed",
                  connection_count: raw.connections.length,
                }
              : p,
          ) ?? prev,
      );
    } catch (e) {
      setError(e instanceof DataUnavailableError ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [selected, connectionsFor]);

  const onAddSource = () => {
    if (!selected) return;
    const title = addTitle.trim();
    if (!title) return;
    addSource(selected, { title, source_type: "peer_regulator" });
    setAddTitle("");
  };

  // Running total = engine connections shown + drafter-added sources across the doc.
  const connectedCount = conn?.connections.length ?? 0;
  const analysedCount =
    paragraphs?.filter((p) => p.state === "analysed").length ?? 0;

  return (
    <div className="mx-auto flex min-h-screen max-w-screen-xl flex-col">
      <header className="border-b border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl text-indigo-600">◎</span>
          <div>
            <h1 className="text-lg font-semibold leading-tight">
              Reconciliation Workbench
            </h1>
            <p className="text-xs text-slate-500">
              Due diligence for policy drafters · MVP1 prototype ·{" "}
              {isSnapshot
                ? "prepared analysis (curated source set)"
                : "live engine"}
            </p>
          </div>
        </div>
      </header>

      <div className="grid flex-1 grid-cols-1 gap-4 p-4 md:grid-cols-[1fr_1.1fr]">
        {/* Left: the document canvas */}
        <section aria-label="Document paragraphs" className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>
              {analysedCount} of {paragraphs?.length ?? 0} paragraphs analysed
            </span>
            <span data-testid="connected-count">
              {connectedCount} sources connected
            </span>
          </div>
          <Legend />
          <ol className="space-y-1.5">
            {paragraphs?.map((p) => (
              <li key={p.number}>
                <button
                  onClick={() => setSelected(p.number)}
                  data-testid={`para-${p.number}`}
                  aria-current={selected === p.number}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    selected === p.number
                      ? "border-indigo-400 bg-indigo-50"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-800">
                      {p.number} · {p.title}
                    </span>
                    {p.state === "analysed" ? (
                      <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                        {p.connection_count} sources
                      </span>
                    ) : (
                      <span className="text-xs italic text-slate-400">
                        not yet analysed
                      </span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ol>
        </section>

        {/* Right: the connection rail for the selected paragraph */}
        <section aria-label="Connected sources" className="space-y-3">
          {selected && (
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700">
                {conn?.paragraph.title
                  ? `Paragraph ${selected} — ${conn.paragraph.title}`
                  : `Paragraph ${selected}`}
              </h2>
            </div>
          )}
          <ConnectionRail
            data={selected ? conn : null}
            loading={loading}
            error={error}
            isSupplied={(id) => blocked.includes(id)}
            onSupply={supplyBlocked}
            onAnalyse={onAnalyse}
          />
          {selected && (
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <label
                htmlFor="add-source"
                className="text-xs font-medium text-slate-600"
              >
                Add a source the library missed
              </label>
              <div className="mt-1 flex gap-2">
                <input
                  id="add-source"
                  value={addTitle}
                  onChange={(e) => setAddTitle(e.target.value)}
                  placeholder="e.g. IOSCO — AI in capital markets (2025)"
                  className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
                  data-testid="add-source-input"
                />
                <button
                  onClick={onAddSource}
                  className="rounded-md bg-slate-800 px-3 py-1 text-sm font-medium text-white hover:bg-slate-700"
                  data-testid="add-source-button"
                >
                  Add
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
      {SOURCE_TYPE_ORDER.map((t) => (
        <span key={t} className="flex items-center gap-1">
          <SourceTypeDot type={t} />
          {SOURCE_TYPE_LABEL[t]}
        </span>
      ))}
    </div>
  );
}
