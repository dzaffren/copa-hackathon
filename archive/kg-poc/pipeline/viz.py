"""Stage 7 — graph → interactive HTML (pyvis).

Documents rendered as boxes; entities as circles coloured by MECE-7 class.
Edge colour encodes edge_type. No unit tests here — this is a thin adapter
over pyvis; smoke coverage comes from tests/test_run.py.
"""

import logging
from pathlib import Path

import networkx as nx
from pyvis.network import Network

from pipeline.config import DATA_DIR

logger = logging.getLogger(__name__)

_CLASS_COLOR: dict[str, str] = {
    "RegulatoryBody": "#B33951",  # deep red
    "Party": "#F29E4C",           # orange
    "Reference": "#916953",       # brown
    "Instrument": "#5C946E",      # green (Documents share family)
    "Requirement": "#4E77BB",     # blue
    "Topic": "#9F5DBF",           # purple
    "Process": "#EACD3F",         # yellow
}
_DOCUMENT_COLOR = "#2F4858"       # dark navy
_EDGE_COLOR = {
    "mentions": "#BBB",
    "about": "#333",
    "co-occurs": "#88C",
    "cites": "#C88",
    "same-as": "#8C8",
}


def render_graph_html(g: nx.MultiDiGraph, output_path: Path) -> Path:
    """Write an interactive HTML rendering of `g` to `output_path`.

    Uses pyvis with a physics-simulated force layout by default. Documents
    are square, Entities are circles coloured by class.
    """
    net = Network(height="750px", width="100%", directed=True, notebook=False)
    net.toggle_physics(True)

    for n, data in g.nodes(data=True):
        if data.get("node_type") == "Document":
            net.add_node(
                n,
                label=data.get("title", n),
                title=f"{data.get('doc_type')} · {data.get('issuer')}",
                color=_DOCUMENT_COLOR,
                shape="box",
            )
        else:
            cls = data.get("class_", "")
            net.add_node(
                n,
                label=data.get("canonical_label", n),
                title=f"{cls} · {data.get('mention_count', 0)} mentions",
                color=_CLASS_COLOR.get(cls, "#888"),
                shape="dot",
            )

    for u, v, d in g.edges(data=True):
        et = d.get("edge_type", "mentions")
        net.add_edge(
            u, v,
            color=_EDGE_COLOR.get(et, "#AAA"),
            title=f"{et} · w={d.get('weight', 0):.2f}",
            value=float(d.get("weight", 0.0)),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(output_path), open_browser=False, notebook=False)
    logger.info("Stage 7: viz written to %s", output_path)
    return output_path


def run_stage_7(
    graph_path: Path = DATA_DIR / "graph.graphml",
    output_path: Path = DATA_DIR / "graph.html",
) -> Path:
    g = nx.read_graphml(graph_path)
    if not isinstance(g, nx.MultiDiGraph):
        g = nx.MultiDiGraph(g)
    return render_graph_html(g, output_path)
