"""CLI driver: `python -m pipeline.run --stage={all,1..7}`.

Sequential dispatch to `run_stage_N` functions in each stage module. Each
stage takes a stage-specific set of paths, all rooted at `output_dir`. The
`run_all` function is the primary integration surface — tests invoke it
directly with stubs for the network seams (MarkItDown, GLiNER).
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from pipeline.analyze import run_stage_6
from pipeline.chunk import run_stage_2
from pipeline.config import DATA_DIR
from pipeline.corpus import DOCUMENTS, DocumentEntry
from pipeline.extract import run_stage_3
from pipeline.graph import run_stage_5
from pipeline.ingest import run_stage_1
from pipeline.resolve import run_stage_4
from pipeline.viz import run_stage_7

logger = logging.getLogger(__name__)


def run_all(
    documents: Optional[dict[str, DocumentEntry]] = None,
    output_dir: Path = DATA_DIR,
    converter: Optional[Any] = None,
    gliner: Optional[Any] = None,
) -> None:
    """Run stages 1..7 in sequence, sharing output_dir as the root."""
    if documents is None:
        documents = DOCUMENTS
    output_dir.mkdir(parents=True, exist_ok=True)

    text_dir = output_dir / "text"
    run_stage_1(documents=documents, output_dir=text_dir, converter=converter)

    chunks_path = output_dir / "chunks.jsonl"
    run_stage_2(text_dir=text_dir, output_path=chunks_path)

    run_stage_3(
        chunks_path=chunks_path,
        seeds=None,
        output_dir=output_dir,
        gliner=gliner,
    )

    spans_path = output_dir / "spans.jsonl"
    run_stage_4(spans_path=spans_path, seeds=None, output_dir=output_dir)

    entities_path = output_dir / "entities.jsonl"
    mentions_path = output_dir / "mentions.jsonl"
    run_stage_5(
        entities_path=entities_path,
        mentions_path=mentions_path,
        output_dir=output_dir,
        documents=documents,
    )

    graph_path = output_dir / "graph.graphml"
    run_stage_6(graph_path=graph_path, output_dir=output_dir)
    run_stage_7(graph_path=graph_path, output_path=output_dir / "graph.html")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the KG POC pipeline (stages 1–7)."
    )
    parser.add_argument(
        "--stage",
        default="all",
        choices=["all", "1", "2", "3", "4", "5", "6", "7"],
        help="Which stage to run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR,
        help="Output directory (default: kg-poc/data).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    out = args.output_dir

    if args.stage == "all":
        run_all(output_dir=out)
    elif args.stage == "1":
        run_stage_1(output_dir=out / "text")
    elif args.stage == "2":
        run_stage_2(text_dir=out / "text", output_path=out / "chunks.jsonl")
    elif args.stage == "3":
        run_stage_3(chunks_path=out / "chunks.jsonl", output_dir=out)
    elif args.stage == "4":
        run_stage_4(spans_path=out / "spans.jsonl", output_dir=out)
    elif args.stage == "5":
        run_stage_5(
            entities_path=out / "entities.jsonl",
            mentions_path=out / "mentions.jsonl",
            output_dir=out,
        )
    elif args.stage == "6":
        run_stage_6(graph_path=out / "graph.graphml", output_dir=out)
    elif args.stage == "7":
        run_stage_7(
            graph_path=out / "graph.graphml", output_path=out / "graph.html"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
