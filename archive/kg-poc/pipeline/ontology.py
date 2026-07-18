"""Load and validate the ontology YAML files (classes + gazetteer seeds).

The loader turns YAML rows into typed dicts and enforces two invariants at
parse time: every seed's `class` field is one of the MECE-7 canonical names,
and every seed carries a non-empty `canonical` label. Both violations raise
`OntologyValidationError` at load — never silently kept, per spec §6
'loud failure'.
"""

from pathlib import Path
from typing import Optional, TypedDict

import yaml

from pipeline.config import MECE_7_CLASSES, ONTOLOGY_DIR


class SeedEntry(TypedDict):
    canonical: str
    class_: str
    aliases: list[str]
    left_forbidden: list[str]
    right_forbidden: list[str]


class OntologyValidationError(Exception):
    """A seeds.yaml or classes.yaml entry violates the ontology contract."""


def load_seeds(path: Optional[Path] = None) -> list[SeedEntry]:
    """Parse seeds.yaml into SeedEntry dicts.

    Renames YAML key `class` (Python keyword) to `class_` internally.
    Every seed must have `canonical` (non-empty str) and `class` in MECE_7_CLASSES.
    """
    if path is None:
        path = ONTOLOGY_DIR / "seeds.yaml"

    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict) or "seeds" not in raw:
        raise OntologyValidationError(
            f"{path}: expected top-level key 'seeds' with a list of entries"
        )

    entries: list[SeedEntry] = []
    for i, item in enumerate(raw["seeds"]):
        if not isinstance(item, dict):
            raise OntologyValidationError(
                f"{path}: entry {i} is not a mapping: {item!r}"
            )
        if "canonical" not in item or not item["canonical"]:
            raise OntologyValidationError(
                f"{path}: entry {i} missing non-empty 'canonical' field"
            )
        if "class" not in item:
            raise OntologyValidationError(
                f"{path}: entry {i} ({item['canonical']!r}) missing 'class'"
            )
        if item["class"] not in MECE_7_CLASSES:
            raise OntologyValidationError(
                f"{path}: entry {i} ({item['canonical']!r}) has unknown "
                f"class {item['class']!r} — must be one of {MECE_7_CLASSES}"
            )

        entries.append(
            {
                "canonical": item["canonical"],
                "class_": item["class"],
                "aliases": list(item.get("aliases", []) or []),
                "left_forbidden": list(item.get("left_forbidden", []) or []),
                "right_forbidden": list(item.get("right_forbidden", []) or []),
            }
        )
    return entries


def load_classes(path: Optional[Path] = None) -> dict[str, str]:
    """Parse classes.yaml into {class_name: defining_test_text}.

    Validates that every one of the MECE-7 canonical class names appears.
    """
    if path is None:
        path = ONTOLOGY_DIR / "classes.yaml"

    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict) or "classes" not in raw:
        raise OntologyValidationError(
            f"{path}: expected top-level key 'classes' with a list of entries"
        )

    result: dict[str, str] = {}
    for item in raw["classes"]:
        if "name" not in item or "test" not in item:
            raise OntologyValidationError(
                f"{path}: class entry missing 'name' or 'test': {item!r}"
            )
        result[item["name"]] = item["test"]

    missing = set(MECE_7_CLASSES) - set(result.keys())
    if missing:
        raise OntologyValidationError(
            f"{path}: missing class definitions for {sorted(missing)}"
        )
    return result
