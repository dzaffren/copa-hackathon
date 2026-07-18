from pathlib import Path

from pipeline import config


def test_mece_7_classes_are_exactly_seven():
    assert len(config.MECE_7_CLASSES) == 7


def test_mece_7_classes_are_the_canonical_names():
    assert config.MECE_7_CLASSES == (
        "RegulatoryBody",
        "Party",
        "Reference",
        "Instrument",
        "Requirement",
        "Topic",
        "Process",
    )


def test_gliner_confidence_threshold_is_zero_point_seven():
    assert config.GLINER_CONFIDENCE_THRESHOLD == 0.7


def test_mention_count_min_is_two():
    assert config.MENTION_COUNT_MIN == 2


def test_data_dir_is_under_package_root():
    assert config.DATA_DIR == config.PACKAGE_ROOT / "data"


def test_ontology_dir_is_under_package_root():
    assert config.ONTOLOGY_DIR == config.PACKAGE_ROOT / "ontology"
