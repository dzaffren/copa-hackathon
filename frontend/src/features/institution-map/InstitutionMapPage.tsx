import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQueries, useQuery } from "@tanstack/react-query";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import { AlertTriangle, Building2, Plus, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { fetchCrossLinks, fetchGraph, fetchWorkstreams } from "@/lib/api";
import { CROSS_STORE, type CrossLink, type SemanticLabel } from "@/lib/types";
import { nodeStyle } from "@/features/workstream-graph/legend";
import { labelStyle } from "@/lib/labels";
import { headlineOverlap } from "@/lib/overlaps";

const CROSS_STROKE = "#f43f5e"; // bright rose — the cross-workstream signal
const TASK_R = 12;
const NODE_R = 7;

// Guarantees the cross-workstream overlaps (OpRes↔Open Finance and the
// BCM↔Recovery Planning overlap) are on screen the moment the page loads.
const DEFAULT_SELECTION = ["open-finance-ed", "resolution-recovery", "opres-v2"];

type NearLink = CrossLink & { nearWorkstreamId: string };

interface FGNode {
  id: string;
  nodeType: string;
  title: string;
  isTask: boolean;
  x?: number;
  y?: number;
}
interface FGLink {
  source: string | FGNode;
  target: string | FGNode;
  kind: "intra" | "cross";
  crossId?: string;
}

const posKey = (workstreamId: string, nodeId: string) =>
  `${workstreamId}:${nodeId}`;

function shortLabel(title: string): string {
  return title.split(/[\s—–-]/)[0];
}

export function InstitutionMapPage() {
  const { data: allWorkstreams = [] } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });

  const [selected, setSelected] = useState<string[] | null>(null);
  const [activeCrossId, setActiveCrossId] = useState<string | null>(null);

  const fgRef = useRef<ForceGraphMethods<FGNode, FGLink> | undefined>(undefined);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 900, height: 520 });

  // Default to the overlap-bearing workstreams once the list is known; fall back
  // to the first three when those seeds are absent (e.g. a fresh instance).
  const selectedIds = useMemo(() => {
    if (selected !== null) return selected;
    if (allWorkstreams.length === 0) return [];
    const present = DEFAULT_SELECTION.filter((id) =>
      allWorkstreams.some((w) => w.id === id),
    );
    return present.length > 0
      ? present
      : allWorkstreams.slice(0, 3).map((w) => w.id);
  }, [selected, allWorkstreams]);

  const graphQueries = useQueries({
    queries: selectedIds.map((id) => ({
      queryKey: ["workstream", id, "graph"],
      queryFn: () => fetchGraph(id),
    })),
  });
  const crossQueries = useQueries({
    queries: selectedIds.map((id) => ({
      queryKey: ["cross-links", id],
      queryFn: () => fetchCrossLinks(id),
    })),
  });

  // Cross-links, de-duplicated by id (each link is reported from both ends when
  // both its workstreams are selected).
  const crossLinks = useMemo(() => {
    const byId = new Map<string, NearLink>();
    selectedIds.forEach((id, i) => {
      for (const link of crossQueries[i]?.data ?? []) {
        if (!byId.has(link.id)) byId.set(link.id, { ...link, nearWorkstreamId: id });
      }
    });
    return [...byId.values()];
  }, [selectedIds, crossQueries]);

  // Merge every selected workstream's graph into one force-directed dataset.
  // Node ids are namespaced by workstream, since one document id can appear in
  // more than one workstream's graph.
  const data = useMemo(() => {
    const nodes: FGNode[] = [];
    const links: FGLink[] = [];
    const nodeIds = new Set<string>();

    selectedIds.forEach((wsId, i) => {
      const graph = graphQueries[i]?.data;
      if (!graph) return;
      for (const n of graph.nodes) {
        const key = posKey(wsId, n.id);
        nodeIds.add(key);
        nodes.push({
          id: key,
          nodeType: n.node_type,
          title: n.title,
          isTask: n.id === graph.primary_task_id || n.node_type === "task",
        });
      }
      for (const e of graph.edges) {
        links.push({
          source: posKey(wsId, e.source),
          target: posKey(wsId, e.target),
          kind: "intra",
        });
      }
    });

    for (const link of crossLinks) {
      const s = posKey(link.nearWorkstreamId, link.near.node_id);
      const t = posKey(link.far.workstream_id ?? "", link.far.node_id);
      if (nodeIds.has(s) && nodeIds.has(t)) {
        links.push({ source: s, target: t, kind: "cross", crossId: link.id });
      }
    }
    return { nodes, links };
  }, [selectedIds, graphQueries, crossLinks]);

  const availableToAdd = allWorkstreams.filter(
    (w) => !selectedIds.includes(w.id),
  );
  const remove = (id: string) => setSelected(selectedIds.filter((s) => s !== id));
  const add = (id: string) => setSelected([...selectedIds, id]);

  // The most attention-worthy untriaged overlap on this map — not hardcoded to
  // BCM <-> Recovery Planning, so the banner generalizes to whatever overlap a
  // future workstream pair surfaces (see @/lib/overlaps for the shared rule
  // this shares with the Home dashboard's Overlap Alerts card).
  const headline = headlineOverlap(crossLinks);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const measure = () =>
      setSize({ width: el.clientWidth, height: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force("charge")?.strength(-220);
    const link = fg.d3Force("link");
    if (link && "distance" in link) {
      (link as unknown as { distance: (d: number) => unknown }).distance(90);
    }
  }, [data]);

  const drawNode = useCallback(
    (node: FGNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const style = nodeStyle(node.nodeType as never);
      const r = node.isTask ? TASK_R : NODE_R;
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      ctx.save();
      ctx.shadowColor = style.stroke;
      ctx.shadowBlur = node.isTask ? 10 : 4;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = style.fill;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = style.stroke;
      ctx.stroke();
      ctx.restore();

      const fontSize = Math.max(8 / globalScale, 3);
      ctx.font = `600 ${fontSize}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = "#cbd5e1";
      ctx.fillText(shortLabel(node.title), x, y + r + 1.5);
    },
    [],
  );

  const drawLink = useCallback(
    (link: FGLink, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const s = link.source as FGNode;
      const t = link.target as FGNode;
      if (!s || !t || s.x == null || t.x == null) return;
      const cross = link.kind === "cross";
      const active = cross && link.crossId === activeCrossId;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(s.x, s.y!);
      ctx.lineTo(t.x, t.y!);
      ctx.strokeStyle = cross ? CROSS_STROKE : "#475569";
      ctx.lineWidth = (cross ? (active ? 3 : 2) : 1) / globalScale;
      ctx.globalAlpha = cross ? 1 : 0.5;
      ctx.setLineDash(cross ? [7, 5].map((d) => d / globalScale) : []);
      ctx.stroke();
      ctx.restore();
    },
    [activeCrossId],
  );

  const activeLink = crossLinks.find((l) => l.id === activeCrossId);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-border/60 bg-card/30 px-6 py-4 backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-wider text-violet-300/80">
          Institution map
        </p>
        <h1 className="text-lg font-bold">Cross-workstream drift</h1>
        <p className="mt-0.5 max-w-2xl text-sm text-muted-foreground">
          Documents from every selected workstream on one canvas. The bright
          dashed edges are linkages that cross workstream boundaries — overlaps
          two teams drafting in parallel would otherwise only discover late.
        </p>

        {/* Workstream filter pills */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {selectedIds.map((id) => {
            const ws = allWorkstreams.find((w) => w.id === id);
            return (
              <span
                key={id}
                className="glass inline-flex items-center gap-1.5 rounded-full py-1 pl-3 pr-1.5 text-xs font-medium"
              >
                {ws?.name ?? id}
                <button
                  type="button"
                  aria-label={`Remove ${ws?.name ?? id}`}
                  onClick={() => remove(id)}
                  className="rounded-full p-0.5 text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            );
          })}
          {availableToAdd.length > 0 && (
            <div className="group relative">
              <button
                type="button"
                className="inline-flex items-center gap-1 rounded-full border border-dashed border-border px-3 py-1 text-xs font-medium text-muted-foreground hover:border-cyan-400/60 hover:text-cyan-300"
              >
                <Plus className="h-3 w-3" /> Add workstream
              </button>
              <div className="absolute left-0 top-full z-20 mt-1 hidden min-w-[200px] rounded-md border border-border/60 bg-popover p-1 shadow-lg group-hover:block">
                {availableToAdd.map((w) => (
                  <button
                    key={w.id}
                    type="button"
                    onClick={() => add(w.id)}
                    className="block w-full rounded px-2 py-1.5 text-left text-xs hover:bg-accent"
                  >
                    {w.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {headline && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-400/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-300" />
            <span>
              <strong className="font-semibold">Overlap detected:</strong>{" "}
              {headline.near.title} ↔ {headline.far.title} share{" "}
              {headline.findings_count} linkages across two workstreams, none
              reviewed yet.{" "}
              <button
                type="button"
                onClick={() => setActiveCrossId(headline.id)}
                className="font-semibold underline underline-offset-2"
              >
                Highlight on map
              </button>
            </span>
          </div>
        )}
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
        {/* Force-directed canvas */}
        <div
          ref={wrapRef}
          data-testid="institution-canvas"
          className="relative h-[520px] shrink-0 overflow-hidden border-b border-border/60 bg-[#0b1220]"
        >
          <ForceGraph2D
            ref={fgRef}
            width={size.width}
            height={size.height}
            graphData={data}
            backgroundColor="rgba(0,0,0,0)"
            cooldownTicks={140}
            onEngineStop={() => fgRef.current?.zoomToFit(400, 70)}
            nodeRelSize={NODE_R}
            nodeLabel={(n) => (n as FGNode).title}
            nodeCanvasObject={drawNode}
            linkCanvasObjectMode={() => "replace"}
            linkCanvasObject={drawLink}
            linkPointerAreaPaint={(link, color, ctx) => {
              const l = link as FGLink;
              if (l.kind !== "cross") return;
              const s = l.source as FGNode;
              const t = l.target as FGNode;
              if (!s || !t || s.x == null || t.x == null) return;
              ctx.strokeStyle = color;
              ctx.lineWidth = 10;
              ctx.beginPath();
              ctx.moveTo(s.x, s.y!);
              ctx.lineTo(t.x, t.y!);
              ctx.stroke();
            }}
            onLinkClick={(l) => {
              const link = l as FGLink;
              if (link.kind === "cross" && link.crossId) {
                setActiveCrossId(link.crossId);
              }
            }}
          />

          {/* Active cross-link callout */}
          {activeLink && (
            <div className="glass absolute right-3 top-3 w-72 rounded-lg p-3 text-xs shadow-lg">
              <p className="font-semibold leading-snug">
                {activeLink.near.title}{" "}
                <span className="text-muted-foreground">↔</span>{" "}
                {activeLink.far.title}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {(
                  Object.entries(activeLink.labels) as [SemanticLabel, number][]
                ).map(([label, count]) => (
                  <span
                    key={label}
                    className={cn(
                      "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                      labelStyle(label).pill,
                    )}
                  >
                    {count} {label}
                  </span>
                ))}
              </div>
              <Link
                to={`/workstreams/${CROSS_STORE}/edges/${activeLink.id}/review`}
                className="mt-2 inline-block font-semibold text-cyan-300 hover:underline"
              >
                Review linkages →
              </Link>
            </div>
          )}
        </div>

        {/* Cross-workstream linkage table */}
        <section className="p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Cross-workstream linkages
          </h2>
          {crossLinks.length === 0 ? (
            <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
              <Building2 className="h-4 w-4" />
              No cross-workstream linkages among the selected workstreams.
            </p>
          ) : (
            <div className="glass mt-3 overflow-hidden rounded-xl">
              <table className="w-full text-sm">
                <thead className="bg-muted/30 text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Source</th>
                    <th className="px-4 py-2 font-semibold">Target</th>
                    <th className="px-4 py-2 font-semibold">In workstream</th>
                    <th className="px-4 py-2 font-semibold">Labels</th>
                    <th className="px-4 py-2 font-semibold"></th>
                  </tr>
                </thead>
                <tbody>
                  {crossLinks.map((link) => (
                    <tr
                      key={link.id}
                      className="border-t border-border/60 hover:bg-accent/40"
                      data-testid="cross-link-row"
                    >
                      <td className="px-4 py-2 font-medium">{link.near.title}</td>
                      <td className="px-4 py-2 font-medium">{link.far.title}</td>
                      <td className="px-4 py-2 text-muted-foreground">
                        {link.far.workstream_name ?? link.far.workstream_id}
                      </td>
                      <td className="px-4 py-2">
                        <span className="flex flex-wrap gap-1">
                          {(
                            Object.entries(link.labels) as [
                              SemanticLabel,
                              number,
                            ][]
                          ).map(([label, count]) => (
                            <span
                              key={label}
                              className={cn(
                                "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                                labelStyle(label).pill,
                              )}
                            >
                              {count} {label}
                            </span>
                          ))}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right">
                        <Link
                          to={`/workstreams/${CROSS_STORE}/edges/${link.id}/review`}
                          className="font-semibold text-cyan-300 hover:underline"
                        >
                          Review
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default InstitutionMapPage;
