"""Stage 4 — spans → entities + mentions.

Deterministic normalisation + class-gated merging. Aliases from seeds.yaml
declare surface variants that should collapse to a canonical. No fuzzy
matching; known long-tail duplicates (`board` vs `Board of Directors` if
the latter isn't declared as an alias) are logged for the audit queue.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, TypedDict

from pipeline.config import DATA_DIR
from pipeline.extract import Span
from pipeline.ontology import SeedEntry

logger = logging.getLogger(__name__)

_ARTICLES = ("the ",)
_PLURAL_SUFFIX = "s"
_VOWELS = "aeiou"
_WHITESPACE_RUN = re.compile(r"\s+")


class Entity(TypedDict):
    entity_id: str
    class_: str
    canonical_label: str
    aliases: list[str]
    mention_count: int
    docs_appearing_in: list[str]


class Mention(TypedDict):
    entity_id: str
    doc_id: str
    chunk_id: str
    char_start: int
    char_end: int


def _is_acronym(word: str) -> bool:
    """Heuristic: an all-uppercase word of at least two letters, ignoring a
    trailing lowercase 's' (so `BCBS` and `TPSPs` both count).

    Used by `normalise_surface` to avoid stripping the plural-`s` off an
    acronym like `BCBS` (turning it into `bcb`) or `TPSPs` (into `tpsp`).
    """
    if not word:
        return False
    body = word[:-1] if word.endswith("s") and len(word) > 1 else word
    return len(body) >= 2 and body.isupper() and body.isalpha()


def normalise_surface(surface: str) -> str:
    """Lowercase → collapse whitespace → strip leading article → strip
    trailing 's' EXCEPT for acronyms and vowel-before-s singulars.

    Deterministic. Not linguistically clever; the interview and audit
    surface most cases where cleverness would be needed as seed aliases.

    Carve-outs on the plural-s strip:
    - all-uppercase acronyms (`BCBS` → `bcbs`, not `bcb`)
    - vowel-before-s singulars (`analysis` → `analysis`, not `analysi`;
      also `focus`, `bias`, `chaos`)

    Whitespace collapse: `"financial  institution"` and
    `"financial institution"` normalise identically. PDF extraction routinely
    injects double spaces around clause boundaries.
    """
    s = _WHITESPACE_RUN.sub(" ", surface).strip()
    acronym = _is_acronym(s.split()[-1]) if s else False

    s = s.lower()
    for article in _ARTICLES:
        if s.startswith(article):
            s = s[len(article) :]
            break
    if (
        not acronym
        and len(s) > 3
        and s.endswith(_PLURAL_SUFFIX)
        and s[-2] not in _VOWELS
    ):
        s = s[:-1]
    return s


def entity_id_for(class_: str, canonical: str) -> str:
    """`{class_.lower()}:{normalise_surface(canonical)}` — stable id."""
    return f"{class_.lower()}:{normalise_surface(canonical)}"


def build_alias_map(seeds: list[SeedEntry]) -> dict[tuple[str, str], str]:
    """Map `(normalised_surface, class_)` → canonical form.

    Includes the canonical itself + every declared alias. Enables the
    resolver to collapse a span's normalised form onto the canonical
    without knowing which seed generated it.
    """
    m: dict[tuple[str, str], str] = {}
    for seed in seeds:
        canonical = seed["canonical"]
        for form in [canonical, *seed["aliases"]]:
            m[(normalise_surface(form), seed["class_"])] = canonical
    return m


def resolve_spans(
    spans: list[Span],
    seeds: list[SeedEntry],
) -> tuple[list[Entity], list[Mention]]:
    """In-memory resolution: spans → (entities, mentions)."""
    alias_map = build_alias_map(seeds)
    by_id: dict[str, Entity] = {}
    mentions: list[Mention] = []

    for span in spans:
        normalised = normalise_surface(span["surface"])
        # Prefer a seed-declared canonical for this (normalised, class) pair;
        # otherwise the span's own surface stands in as its canonical.
        canonical = alias_map.get((normalised, span["class_"]), span["surface"])

        eid = entity_id_for(span["class_"], canonical)

        if eid not in by_id:
            by_id[eid] = {
                "entity_id": eid,
                "class_": span["class_"],
                "canonical_label": canonical,
                "aliases": [],
                "mention_count": 0,
                "docs_appearing_in": [],
            }
        entity = by_id[eid]
        entity["mention_count"] += 1
        if span["doc_id"] not in entity["docs_appearing_in"]:
            entity["docs_appearing_in"].append(span["doc_id"])
        # Track distinct surface forms as observed aliases (not seed-declared).
        if span["surface"] != canonical and span["surface"] not in entity["aliases"]:
            entity["aliases"].append(span["surface"])

        mentions.append(
            {
                "entity_id": eid,
                "doc_id": span["doc_id"],
                "chunk_id": span["chunk_id"],
                "char_start": span["char_start"],
                "char_end": span["char_end"],
            }
        )

    entities = sorted(by_id.values(), key=lambda e: e["entity_id"])
    return entities, mentions


def run_stage_4(
    spans_path: Path = DATA_DIR / "spans.jsonl",
    seeds: Optional[list[SeedEntry]] = None,
    output_dir: Path = DATA_DIR,
) -> tuple[Path, Path]:
    """Read spans.jsonl, write entities.jsonl + mentions.jsonl."""
    if seeds is None:
        from pipeline.ontology import load_seeds

        seeds = load_seeds()

    spans: list[Span] = [
        json.loads(line) for line in spans_path.read_text().splitlines() if line.strip()
    ]
    entities, mentions = resolve_spans(spans, seeds)

    output_dir.mkdir(parents=True, exist_ok=True)
    ent_path = output_dir / "entities.jsonl"
    men_path = output_dir / "mentions.jsonl"
    with ent_path.open("w") as fh:
        for e in entities:
            fh.write(json.dumps(e) + "\n")
    with men_path.open("w") as fh:
        for m in mentions:
            fh.write(json.dumps(m) + "\n")

    logger.info(
        "Stage 4: %d spans → %d entities, %d mentions",
        len(spans),
        len(entities),
        len(mentions),
    )
    return ent_path, men_path
