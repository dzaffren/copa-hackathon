import { forwardRef, useImperativeHandle } from "react";

// react-force-graph-2d drives a real <canvas> + rAF loop that jsdom cannot back
// (canvas.getContext returns null), so the real component throws on mount and
// its animation loop leaks async errors across test files. This stub renders an
// accessible, deterministic DOM instead: one button per node and per cross/edge
// link, wired to the same onNodeClick / onLinkClick callbacks the real library
// fires. Interaction tests exercise selection through these; the canvas drawing
// itself is a visual concern covered by manual/E2E checks.

interface StubNode {
  id: string;
  title?: string;
  [key: string]: unknown;
}
interface StubLink {
  id?: string;
  crossId?: string;
  edge_type?: string;
  source: string | StubNode;
  target: string | StubNode;
  [key: string]: unknown;
}

interface Props {
  graphData?: { nodes: StubNode[]; links: StubLink[] };
  onNodeClick?: (node: StubNode) => void;
  onLinkClick?: (link: StubLink) => void;
  [key: string]: unknown;
}

const chainableForce = {
  strength: () => chainableForce,
  distance: () => chainableForce,
};

const MockForceGraph2D = forwardRef<unknown, Props>(function MockForceGraph2D(
  { graphData, onNodeClick, onLinkClick },
  ref,
) {
  useImperativeHandle(ref, () => ({
    zoom: () => 1,
    zoomToFit: () => {},
    centerAt: () => {},
    d3Force: () => chainableForce,
  }));

  const nodes = graphData?.nodes ?? [];
  const links = graphData?.links ?? [];

  return (
    <div data-testid="force-graph-mock">
      {nodes.map((n) => (
        <button
          key={n.id}
          type="button"
          aria-label={n.title ?? n.id}
          onClick={() => onNodeClick?.(n)}
        >
          {n.title ?? n.id}
        </button>
      ))}
      {links.map((l, i) => {
        const key = l.id ?? l.crossId ?? `link-${i}`;
        const srcId = typeof l.source === "string" ? l.source : l.source?.id;
        const tgtId = typeof l.target === "string" ? l.target : l.target?.id;
        return (
          <button
            key={key}
            type="button"
            data-link-id={key}
            aria-label={`edge ${l.edge_type ?? l.kind ?? "link"} ${srcId} to ${tgtId}`}
            onClick={() => onLinkClick?.(l)}
          />
        );
      })}
    </div>
  );
});

export default MockForceGraph2D;
