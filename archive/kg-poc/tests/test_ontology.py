from pathlib import Path

import pytest

from pipeline.ontology import (
    OntologyValidationError,
    load_classes,
    load_seeds,
)


def test_load_seeds_returns_list_of_entries():
    seeds = load_seeds()
    assert len(seeds) > 40  # roughly the seed count we authored
    assert all(isinstance(s, dict) for s in seeds)


def test_every_seed_has_a_valid_class():
    from pipeline.config import MECE_7_CLASSES

    seeds = load_seeds()
    for seed in seeds:
        assert seed["class_"] in MECE_7_CLASSES


def test_every_seed_has_canonical_and_aliases_fields():
    seeds = load_seeds()
    for seed in seeds:
        assert isinstance(seed["canonical"], str)
        assert isinstance(seed["aliases"], list)


def test_load_seeds_raises_on_unknown_class(tmp_path: Path):
    bad = tmp_path / "seeds.yaml"
    bad.write_text(
        "seeds:\n"
        "  - {canonical: foo, class: Nonsense, aliases: []}\n"
    )
    with pytest.raises(OntologyValidationError):
        load_seeds(bad)


def test_load_seeds_raises_on_missing_canonical(tmp_path: Path):
    bad = tmp_path / "seeds.yaml"
    bad.write_text(
        "seeds:\n"
        "  - {class: Party, aliases: []}\n"
    )
    with pytest.raises(OntologyValidationError):
        load_seeds(bad)


def test_load_classes_returns_all_seven():
    from pipeline.config import MECE_7_CLASSES

    classes = load_classes()
    assert set(classes.keys()) == set(MECE_7_CLASSES)


def test_load_classes_has_non_empty_test_per_class():
    classes = load_classes()
    for name, test in classes.items():
        assert isinstance(test, str)
        assert len(test) > 0
