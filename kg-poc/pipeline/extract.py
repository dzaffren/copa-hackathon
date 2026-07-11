"""Stage 3 — chunks → typed spans (gazetteer + GLiNER).

Two-pass hybrid. This module implements the gazetteer pass first; the
GLiNER pass is added in the next task. Every emitted Span carries absolute
byte offsets within the parent markdown (chunk-relative offsets added to
chunk.char_start) so downstream `markdown[start:end] == surface` holds.
"""

import logging
from typing import Any, Optional, TypedDict

from pipeline.chunk import Chunk
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
