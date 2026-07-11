"""Stage 3 — chunks → typed spans (gazetteer + GLiNER).

Two-pass hybrid. This module implements the gazetteer pass first; the
GLiNER pass is added in the next task. Every emitted Span carries absolute
byte offsets within the parent markdown (chunk-relative offsets added to
chunk.char_start) so downstream `markdown[start:end] == surface` holds.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional, Protocol, TypedDict

from pipeline.chunk import Chunk
from pipeline.config import DATA_DIR, GLINER_CONFIDENCE_THRESHOLD
from pipeline.ontology import SeedEntry

logger = logging.getLogger(__name__)


class Span(TypedDict):
    doc_id: str
    chunk_id: str
    char_start: int
    char_end: int
    surface: str
    class_: str
    source: str
    confidence: float


def _load_nlp() -> Any:
    """Lazy spaCy load — same shape as chunk._load_nlp so a single blank
    English pipeline is enough for tokenisation + PhraseMatcher.
    """
    import spacy

    return spacy.blank("en")


def _passes_forbidden(
    tokens: list[str],
    match_start: int,
    match_end: int,
    left_forbidden: list[str],
    right_forbidden: list[str],
    window: int = 2,
) -> bool:
    """A match is kept only if none of the forbidden tokens sit within
    `window` tokens on the specified side. Case-insensitive.
    """
    if left_forbidden:
        left = [t.lower() for t in tokens[max(0, match_start - window):match_start]]
        for bad in left_forbidden:
            if bad.lower() in left:
                return False
    if right_forbidden:
        right = [t.lower() for t in tokens[match_end:match_end + window]]
        for bad in right_forbidden:
            if bad.lower() in right:
                return False
    return True


def extract_gazetteer_spans(
    chunks: list[Chunk],
    seeds: list[SeedEntry],
    nlp: Optional[Any] = None,
) -> list[Span]:
    """Run spaCy PhraseMatcher over `chunks` against every seed's canonical
    + aliases. Whole-token matches only.

    Absolute byte offsets are computed as
    `chunk.char_start + local_span.start_char`.
    """
    from spacy.matcher import PhraseMatcher

    if nlp is None:
        nlp = _load_nlp()

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    # spaCy expects one match-id per rule; we key by index and look up the
    # seed after matching.
    seed_by_id: dict[int, SeedEntry] = {}
    for i, seed in enumerate(seeds):
        phrases = [seed["canonical"], *seed["aliases"]]
        patterns = [nlp.make_doc(p) for p in phrases if p.strip()]
        if not patterns:
            continue
        key = f"seed_{i}"
        matcher.add(key, patterns)
        seed_by_id[nlp.vocab.strings[key]] = seed

    spans: list[Span] = []
    for chunk in chunks:
        doc = nlp(chunk["text"])
        tokens = [t.text for t in doc]
        for match_id, tok_start, tok_end in matcher(doc):
            seed = seed_by_id[match_id]
            if not _passes_forbidden(
                tokens, tok_start, tok_end,
                seed["left_forbidden"], seed["right_forbidden"],
            ):
                continue
            span_obj = doc[tok_start:tok_end]
            surface = span_obj.text
            spans.append(
                {
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "char_start": chunk["char_start"] + span_obj.start_char,
                    "char_end": chunk["char_start"] + span_obj.end_char,
                    "surface": surface,
                    "class_": seed["class_"],
                    "source": "gazetteer",
                    "confidence": 1.0,
                }
            )
    return spans


# Descriptive labels boost zero-shot precision — GLiNER hasn't seen the
# terse MECE-7 names as training data, but understands the phrases.
_GLINER_LABELS: list[str] = [
    "regulatory body",
    "regulated actor or third party",
    "external rule or standard",
    "regulatory document",
    "regulatory requirement or duty",
    "domain topic",
    "activity or process",
]
_LABEL_TO_CLASS: dict[str, str] = {
    "regulatory body": "RegulatoryBody",
    "regulated actor or third party": "Party",
    "external rule or standard": "Reference",
    "regulatory document": "Instrument",
    "regulatory requirement or duty": "Requirement",
    "domain topic": "Topic",
    "activity or process": "Process",
}


class GlinerLike(Protocol):
    """Duck-typed GLiNER interface — matches the real
    `gliner.GLiNER.predict_entities` signature so tests can inject a stub.
    """

    def predict_entities(
        self, text: str, labels: list[str]
    ) -> list[dict]: ...


def mask_chunk_text(
    text: str,
    chunk_char_start: int,
    gazetteer_spans_in_chunk: list[Span],
) -> str:
    """Replace character ranges covered by gazetteer spans with equal-length
    spaces so GLiNER doesn't re-find them.

    Length is preserved so any offsets GLiNER returns still map back to the
    original markdown via chunk_char_start.
    """
    if not gazetteer_spans_in_chunk:
        return text
    buf = list(text)
    for span in gazetteer_spans_in_chunk:
        local_start = span["char_start"] - chunk_char_start
        local_end = span["char_end"] - chunk_char_start
        for i in range(local_start, local_end):
            if 0 <= i < len(buf):
                buf[i] = " "
    return "".join(buf)


def extract_gliner_spans(
    chunks: list[Chunk],
    gazetteer_spans: list[Span],
    gliner: GlinerLike,
    threshold: float = GLINER_CONFIDENCE_THRESHOLD,
) -> tuple[list[Span], list[Span]]:
    """Run GLiNER zero-shot over each chunk (with gazetteer hits masked).

    Returns `(kept, dropped)`. `kept` are spans with score >= threshold,
    class mapped from the descriptive label back to the canonical MECE-7
    name. Absolute offsets computed as `chunk.char_start + local`.
    """
    by_chunk: dict[str, list[Span]] = {}
    for span in gazetteer_spans:
        by_chunk.setdefault(span["chunk_id"], []).append(span)

    kept: list[Span] = []
    dropped: list[Span] = []

    for chunk in chunks:
        masked = mask_chunk_text(
            chunk["text"], chunk["char_start"], by_chunk.get(chunk["chunk_id"], [])
        )
        predictions = gliner.predict_entities(masked, _GLINER_LABELS)
        for pred in predictions:
            label = pred["label"]
            if label not in _LABEL_TO_CLASS:
                # GLiNER shouldn't invent labels, but be defensive.
                continue
            span: Span = {
                "doc_id": chunk["doc_id"],
                "chunk_id": chunk["chunk_id"],
                "char_start": chunk["char_start"] + pred["start"],
                "char_end": chunk["char_start"] + pred["end"],
                "surface": pred["text"],
                "class_": _LABEL_TO_CLASS[label],
                "source": "gliner",
                "confidence": float(pred["score"]),
            }
            if span["confidence"] >= threshold:
                kept.append(span)
            else:
                dropped.append(span)

    return kept, dropped


def _load_gliner() -> GlinerLike:
    """Lazy GLiNER load — pinned checkpoint. Only called when caller passes
    `gliner=None` in production; tests always inject a stub.
    """
    from gliner import GLiNER

    return GLiNER.from_pretrained("urchade/gliner_medium-v2.1")


def run_stage_3(
    chunks_path: Path = DATA_DIR / "chunks.jsonl",
    seeds: Optional[list[SeedEntry]] = None,
    output_dir: Path = DATA_DIR,
    gliner: Optional[GlinerLike] = None,
    nlp: Optional[Any] = None,
) -> tuple[Path, Path]:
    """End-to-end Stage 3 driver: read chunks, run gazetteer + GLiNER,
    write `spans.jsonl` (kept) + `spans_dropped.jsonl` (below threshold).
    """
    if seeds is None:
        from pipeline.ontology import load_seeds

        seeds = load_seeds()
    if gliner is None:
        gliner = _load_gliner()

    chunks: list[Chunk] = [json.loads(line) for line in chunks_path.read_text().splitlines() if line.strip()]

    gazetteer_spans = extract_gazetteer_spans(chunks, seeds, nlp=nlp)
    kept_gliner, dropped_gliner = extract_gliner_spans(
        chunks, gazetteer_spans, gliner
    )

    all_kept = gazetteer_spans + kept_gliner

    output_dir.mkdir(parents=True, exist_ok=True)
    kept_path = output_dir / "spans.jsonl"
    dropped_path = output_dir / "spans_dropped.jsonl"
    with kept_path.open("w") as fh:
        for s in all_kept:
            fh.write(json.dumps(s) + "\n")
    with dropped_path.open("w") as fh:
        for s in dropped_gliner:
            fh.write(json.dumps(s) + "\n")

    logger.info(
        "Stage 3: %d spans kept (%d gazetteer, %d gliner), %d dropped",
        len(all_kept), len(gazetteer_spans), len(kept_gliner), len(dropped_gliner),
    )
    return kept_path, dropped_path
