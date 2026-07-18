"""Stage 2 — clean markdown → sentence-level chunks with byte offsets.

Uses spaCy's sentencizer for splitting. Every chunk record carries
`(doc_id, chunk_id, char_start, char_end, text)`; the verbatim invariant is
`markdown[chunk.char_start:chunk.char_end] == chunk.text`, enforced by
tests. Not clause segmentation — GLiNER works best on 1–3 sentence chunks.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional, TypedDict

from pipeline.config import CHUNK_LEN_WARN, DATA_DIR

logger = logging.getLogger(__name__)


class Chunk(TypedDict):
    doc_id: str
    chunk_id: str
    char_start: int
    char_end: int
    text: str


def _load_nlp() -> Any:
    """Lazy spaCy load — a blank English pipeline with just the sentencizer.

    Not imported at module-top so tests can inject `FakeNLP` without paying
    the spaCy import cost.
    """
    import spacy

    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp


def chunk_document(
    doc_id: str,
    markdown: str,
    nlp: Optional[Any] = None,
) -> list[Chunk]:
    """Split `markdown` into sentence-level chunks with byte offsets.

    Verbatim invariant: `markdown[c.char_start:c.char_end] == c.text` for
    every chunk c. `chunk_id` is `{doc_id}:{i:04d}` where `i` is document
    order, zero-padded for stable sort.
    """
    if nlp is None:
        nlp = _load_nlp()

    doc = nlp(markdown)
    chunks: list[Chunk] = []
    for i, sent in enumerate(doc.sents):
        text = sent.text
        # Whitespace-only "sentences" carry no signal; skip.
        if not text.strip():
            continue
        chunks.append(
            {
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}:{i:04d}",
                "char_start": sent.start_char,
                "char_end": sent.end_char,
                "text": text,
            }
        )
    return chunks


def run_stage_2(
    text_dir: Path = DATA_DIR / "text",
    output_path: Path = DATA_DIR / "chunks.jsonl",
    nlp: Optional[Any] = None,
) -> Path:
    """Chunk every `{doc_id}.md` under `text_dir`, write JSONL to `output_path`.

    Warns (does not halt) on any chunk exceeding CHUNK_LEN_WARN chars —
    likely a sentencizer miss on a markdown table or list.
    """
    if nlp is None:
        nlp = _load_nlp()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    n_chunks = 0
    oversize = 0
    with output_path.open("w") as fh:
        for md_path in sorted(text_dir.glob("*.md")):
            doc_id = md_path.stem
            markdown = md_path.read_text()
            for chunk in chunk_document(doc_id, markdown, nlp=nlp):
                if chunk["char_end"] - chunk["char_start"] > CHUNK_LEN_WARN:
                    oversize += 1
                    logger.warning(
                        "oversize chunk %s (%d chars) — probable sentencizer miss",
                        chunk["chunk_id"],
                        chunk["char_end"] - chunk["char_start"],
                    )
                fh.write(json.dumps(chunk) + "\n")
                n_chunks += 1

    logger.info("Stage 2: %d chunks written (%d oversize)", n_chunks, oversize)
    return output_path
