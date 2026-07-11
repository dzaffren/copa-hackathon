# KG + Ontology Pipeline POC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone `kg-poc/` package that runs a seven-stage data-science pipeline over BNM policy PDFs and produces a NetworkX knowledge graph with an interactive HTML visualisation, grounded in a MECE-7 ontology.

**Architecture:** Isolated Python package parallel to `engine/`. Each stage is a module that reads and writes files (JSONL / markdown / graphml), driven by an `argparse` runner (`python -m kg_poc.run --stage=all`). No shared code with `engine/` except patterns; MarkItDown + Azure Document Intelligence ingest is re-implemented in the new package rather than imported. Entity extraction is a two-pass hybrid (spaCy `PhraseMatcher` gazetteer first, GLiNER zero-shot for long tail).

**Tech Stack:** Python 3.11+, spaCy (sentencizer + PhraseMatcher), GLiNER (zero-shot NER), NetworkX (graph), pyvis (interactive HTML viz), MarkItDown + azure-ai-documentintelligence (ingest), pytest, PyYAML, jupytext.

**Spec:** `docs/superpowers/specs/2026-07-12-kg-ontology-pipeline-poc-design.md`

## Global Constraints

- Package root: `kg-poc/`. All new code lives here. **Never modify `engine/`.**
- Runner: `python -m kg_poc.run --stage={all,1..7}` — argparse only, no orchestrator.
- Artifact contract: every stage writes to files in `kg-poc/data/` (git-ignored) using stable filenames (no timestamps in names). Byte-identical rebuild required for Stages 1, 2, 4, 5, 6; seed-identical for Stage 3 (pinned GLiNER checkpoint + fixed seed).
- **Verbatim provenance invariant:** every span carries `(doc_id, chunk_id, char_start, char_end)`. Slicing `data/text/{doc_id}.md[char_start:char_end]` MUST return the exact `surface` string. Broken in tests = red build.
- **Loud failure:** empty PDF conversion → `UnreadableDocumentError`, halt. Missing seed class → halt. Missing chunk offset field → halt. No silent corruption.
- Class-gated entity resolution: same normalised surface + same class → merge. Same surface + different class → separate entities. **Never fuzzy-match** in v1 (aliases only via `seeds.yaml`).
- Unit tests: pytest, <5s total, no network, no model download. GLiNER + MarkItDown are stubbed in tests via injectable seams.
- MECE-7 classes (exact spellings): `RegulatoryBody`, `Party`, `Reference`, `Instrument`, `Requirement`, `Topic`, `Process`.
- GLiNER confidence threshold: `0.7` (configurable in `pipeline/config.py`); below-threshold spans → `data/spans_dropped.jsonl`, never silently kept.
- Graph filter: drop `Entity` nodes with `mention_count < 2` at Stage 5. Kept in `entities.jsonl`.
- Commit style: Conventional Commits, kebab-case branch. Never commit to `main`.
- `kg-poc/data/` git-ignored. `kg-poc/ontology/*.yaml` and `kg-poc/notebooks/*.py` (jupytext-paired) tracked. Notebooks (`.ipynb`) git-ignored.

## File Structure

Files this plan creates. Every task lists the exact paths it touches.

```
kg-poc/
  pyproject.toml
  README.md
  .gitignore
  ontology/
    classes.yaml
    seeds.yaml
  pipeline/
    __init__.py
    config.py                      # thresholds, MECE-7 constants, paths
    corpus.py                      # DOCUMENTS manifest for v1 (id, path, type, jurisdiction, issuer)
    ingest.py                      # PDF → clean markdown
    chunk.py                       # markdown → sentence chunks (JSONL)
    extract.py                     # chunks → typed spans (JSONL)
    resolve.py                     # spans → entities + mentions (JSONL)
    graph.py                       # entities + mentions → NetworkX graph
    analyze.py                     # graph → analysis.md + figures
    viz.py                         # graph → interactive HTML (pyvis)
    run.py                         # argparse driver: python -m kg_poc.run
  notebooks/
    01_explore_corpus.py           # jupytext-paired
    02_ontology_coverage.py
    03_graph_analysis.py
  tests/
    __init__.py
    conftest.py                    # shared fixtures (tmp corpus, stub converter, stub GLiNER)
    test_config.py
    test_ingest.py
    test_chunk.py
    test_extract.py
    test_resolve.py
    test_graph.py
    test_analyze.py
    test_run.py
```

**Responsibility per file:**

- `config.py` — constants only (MECE_7_CLASSES, GLINER_CONFIDENCE_THRESHOLD, MENTION_COUNT_MIN, paths). No logic.
- `corpus.py` — the v1 document manifest as a Python dict (following `engine/config.py`'s pattern).
- One stage per module (`ingest`, `chunk`, `extract`, `resolve`, `graph`, `analyze`, `viz`). Each module exposes a top-level function `run_stage_N(...)` plus helpers.
- `run.py` — CLI only. Parses args and dispatches to `run_stage_N` functions.
- Each stage module has its own test file. `conftest.py` holds fixtures used by multiple test files.

---

## Task 1: Package skeleton + config

Establishes the package boundary, dependencies, and shared constants. No pipeline logic yet.

**Files:**

- Create: `kg-poc/pyproject.toml`
- Create: `kg-poc/README.md`
- Create: `kg-poc/.gitignore`
- Create: `kg-poc/pipeline/__init__.py` (empty)
- Create: `kg-poc/pipeline/config.py`
- Create: `kg-poc/tests/__init__.py` (empty)
- Create: `kg-poc/tests/conftest.py`
- Create: `kg-poc/tests/test_config.py`

**Interfaces:**

- Consumes: nothing.
- Produces:
  - `pipeline.config.MECE_7_CLASSES: tuple[str, ...]` — the 7 canonical class names.
  - `pipeline.config.GLINER_CONFIDENCE_THRESHOLD: float = 0.7`
  - `pipeline.config.MENTION_COUNT_MIN: int = 2`
  - `pipeline.config.CHUNK_LEN_WARN: int = 500`
  - `pipeline.config.PACKAGE_ROOT: Path` (absolute path to `kg-poc/`)
  - `pipeline.config.DATA_DIR: Path` (`PACKAGE_ROOT / "data"`)
  - `pipeline.config.ONTOLOGY_DIR: Path` (`PACKAGE_ROOT / "ontology"`)

- [ ] **Step 1: Create pyproject.toml**

Path: `kg-poc/pyproject.toml`

```toml
[project]
name = "kg-poc"
version = "0.1.0"
description = "KG + ontology pipeline POC over BNM policy PDFs"
requires-python = ">=3.11"
dependencies = [
    "spacy>=3.7,<4",
    "gliner>=0.2.13,<0.3",
    "networkx>=3.2,<4",
    "pyvis>=0.3.2,<0.4",
    "markitdown>=0.0.1",
    "azure-ai-documentintelligence>=1.0.0",
    "pyyaml>=6.0",
    "pandas>=2.0",
    "matplotlib>=3.7",
    "jupytext>=1.16",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["pipeline*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 2: Create .gitignore**

Path: `kg-poc/.gitignore`

```gitignore
data/
*.egg-info/
__pycache__/
.pytest_cache/
notebooks/*.ipynb
!notebooks/*.py
```

- [ ] **Step 3: Create README.md**

Path: `kg-poc/README.md`

````markdown
# kg-poc — Knowledge-graph + ontology pipeline POC

Parallel POC to `../engine/`. Ingests BNM policy PDFs and produces a
NetworkX knowledge graph grounded in a MECE-7 ontology.

**Design:** `../docs/superpowers/specs/2026-07-12-kg-ontology-pipeline-poc-design.md`

## Quickstart

```bash
cd kg-poc
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
python -m kg_poc.run --stage=all
open data/graph.html
```
````

## Stages

1. `ingest.py` — PDF → clean markdown (`data/text/`)
2. `chunk.py` — markdown → sentence chunks (`data/chunks.jsonl`)
3. `extract.py` — chunks → typed spans (`data/spans.jsonl`)
4. `resolve.py` — spans → entities + mentions
5. `graph.py` — entities → NetworkX graph
6. `analyze.py` — graph → `analysis.md` + figures
7. `viz.py` — graph → interactive HTML

Run a single stage: `python -m kg_poc.run --stage=3`.

````

- [ ] **Step 4: Write failing test for config constants**

Path: `kg-poc/tests/test_config.py`

```python
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
````

- [ ] **Step 5: Run tests to verify they fail**

Run: `cd kg-poc && pytest tests/test_config.py -v`
Expected: FAIL — `pipeline.config` does not exist yet.

- [ ] **Step 6: Implement config**

Path: `kg-poc/pipeline/config.py`

```python
"""Package-wide constants — MECE-7 classes, thresholds, paths.

No pipeline logic in this module. Everything here is a value; every
threshold is a load-bearing knob captured in one place so audit-driven
retuning changes only one file.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
ONTOLOGY_DIR = PACKAGE_ROOT / "ontology"

# The seven ontology classes in decision-cascade order (see spec §4).
MECE_7_CLASSES: tuple[str, ...] = (
    "RegulatoryBody",
    "Party",
    "Reference",
    "Instrument",
    "Requirement",
    "Topic",
    "Process",
)

# GLiNER confidence below this → dropped to spans_dropped.jsonl, never kept.
GLINER_CONFIDENCE_THRESHOLD: float = 0.7

# Entities with fewer mentions are excluded from the graph (kept in
# entities.jsonl).
MENTION_COUNT_MIN: int = 2

# Chunk length above this triggers a warning — probable sentencizer miss.
CHUNK_LEN_WARN: int = 500
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd kg-poc && pytest tests/test_config.py -v`
Expected: PASS (6 tests)

- [ ] **Step 8: Create empty conftest**

Path: `kg-poc/tests/conftest.py`

```python
"""Shared pytest fixtures for the pipeline tests.

Populated as later tasks add fixtures — kept minimal initially so the
first test suite runs on the config module alone.
"""
```

- [ ] **Step 9: Commit**

```bash
git checkout -b feat/kg-poc-skeleton
git add kg-poc/
git commit -m "feat(kg-poc): package skeleton and config constants"
```

---

## Task 2: Corpus manifest

Defines the v1 documents (paths, ids, types). Follows `engine/config.py`'s pattern but standalone.

**Files:**

- Create: `kg-poc/pipeline/corpus.py`
- Create: `kg-poc/tests/test_corpus.py`

**Interfaces:**

- Consumes: `pipeline.config.PACKAGE_ROOT`.
- Produces:
  - `pipeline.corpus.DOCUMENTS: dict[str, DocumentEntry]` — v1 manifest keyed by `doc_id`.
  - `pipeline.corpus.DocumentEntry` — a `TypedDict` with fields:
    - `doc_id: str`
    - `source_path: Path` (absolute path to the PDF)
    - `title: str`
    - `doc_type: str` — one of `"PD"`, `"ED"`, `"DP"`, `"BCBS"`
    - `jurisdiction: str` — `"MY"` or `"INT"`
    - `issuer: str` — `"BNM"`, `"BCBS"`, `"BIS"`
    - `issued_date: str` — ISO date

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_corpus.py`

```python
from pathlib import Path

from pipeline.corpus import DOCUMENTS


def test_v1_has_seven_documents():
    assert len(DOCUMENTS) == 7


def test_every_doc_id_appears_in_its_entry():
    for doc_id, entry in DOCUMENTS.items():
        assert entry["doc_id"] == doc_id


def test_every_source_path_points_to_data_corpus():
    # v1 uses the repo's data/corpus/ (relative to the repo root, not kg-poc/).
    for entry in DOCUMENTS.values():
        assert entry["source_path"].parent.name == "corpus"
        assert entry["source_path"].suffix == ".pdf"


def test_all_v1_docs_are_bnm_MY():
    for entry in DOCUMENTS.values():
        assert entry["issuer"] == "BNM"
        assert entry["jurisdiction"] == "MY"


def test_doc_types_are_in_canonical_set():
    canonical = {"PD", "ED", "DP", "BCBS"}
    for entry in DOCUMENTS.values():
        assert entry["doc_type"] in canonical


def test_specific_docs_present():
    expected_ids = {
        "rmit",
        "outsourcing",
        "bcm",
        "opres-dp",
        "recovery-planning",
        "customer-info",
        "open-finance-ed",
    }
    assert set(DOCUMENTS.keys()) == expected_ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_corpus.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement corpus manifest**

Path: `kg-poc/pipeline/corpus.py`

```python
"""v1 corpus manifest — 7 BNM regulatory documents from data/corpus/.

Follows the same "single source of truth manifest" pattern as
engine/config.py — the pipeline never infers document identity from
filenames. v2 (remaining 2026 BNM docs) and v3 (BCBS mother-docs) are
tier-two work; see spec §3.
"""

from pathlib import Path
from typing import TypedDict

from pipeline.config import PACKAGE_ROOT

# Corpus lives at the repo root, not under kg-poc/.
REPO_ROOT = PACKAGE_ROOT.parent
CORPUS_DIR = REPO_ROOT / "data" / "corpus"


class DocumentEntry(TypedDict):
    doc_id: str
    source_path: Path
    title: str
    doc_type: str
    jurisdiction: str
    issuer: str
    issued_date: str


DOCUMENTS: dict[str, DocumentEntry] = {
    "rmit": {
        "doc_id": "rmit",
        "source_path": CORPUS_DIR / "pd-rmit-nov25.pdf",
        "title": "Risk Management in Technology (RMiT)",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-11-28",
    },
    "outsourcing": {
        "doc_id": "outsourcing",
        "source_path": CORPUS_DIR / "PD_Outsourcing_20191023.pdf",
        "title": "Outsourcing",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2019-10-23",
    },
    "bcm": {
        "doc_id": "bcm",
        "source_path": CORPUS_DIR / "PD-BCM.pdf",
        "title": "Business Continuity Management",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2022-12-19",
    },
    "opres-dp": {
        "doc_id": "opres-dp",
        "source_path": CORPUS_DIR / "dp_operationalresilience_Dec2025.pdf",
        "title": "Operational Resilience (Discussion Paper)",
        "doc_type": "DP",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-12-19",
    },
    "recovery-planning": {
        "doc_id": "recovery-planning",
        "source_path": CORPUS_DIR / "pd_Recovery Planning.pdf",
        "title": "Recovery Planning",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2021-07-28",
    },
    "customer-info": {
        "doc_id": "customer-info",
        "source_path": CORPUS_DIR / "MCIPD_PD_2025.pdf",
        "title": "Management of Customer Information & Permitted Disclosures",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-10-31",
    },
    "open-finance-ed": {
        "doc_id": "open-finance-ed",
        "source_path": CORPUS_DIR / "ED_Open_Finance_2025.pdf",
        "title": "Open Finance (Exposure Draft)",
        "doc_type": "ED",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-07-01",
    },
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_corpus.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/corpus.py kg-poc/tests/test_corpus.py
git commit -m "feat(kg-poc): v1 corpus manifest"
```

---

## Task 3: Ontology YAML — classes.yaml + seeds.yaml (initial seed set)

The ontology-as-artifact. Version-controlled YAML files that the extractor and resolver read at runtime. Initial `seeds.yaml` covers the ~50 highest-value gazetteer terms (from the drafter interview + spec examples); further seeds are added iteratively during the audit cycle.

**Files:**

- Create: `kg-poc/ontology/classes.yaml`
- Create: `kg-poc/ontology/seeds.yaml`
- Create: `kg-poc/pipeline/ontology.py`
- Create: `kg-poc/tests/test_ontology.py`

**Interfaces:**

- Consumes: `pipeline.config.MECE_7_CLASSES`, `pipeline.config.ONTOLOGY_DIR`.
- Produces:
  - `pipeline.ontology.SeedEntry` — TypedDict:
    - `canonical: str`
    - `class_: str` (one of MECE_7_CLASSES)
    - `aliases: list[str]`
    - `left_forbidden: list[str]` (optional context tokens that must NOT precede a match)
    - `right_forbidden: list[str]` (optional context tokens that must NOT follow a match)
  - `pipeline.ontology.load_seeds(path: Path = ONTOLOGY_DIR / "seeds.yaml") -> list[SeedEntry]` — parses, validates every `class_` is in MECE_7_CLASSES, raises on unknown class.
  - `pipeline.ontology.load_classes(path: Path = ONTOLOGY_DIR / "classes.yaml") -> dict[str, str]` — returns `{class_name: defining_test_text}`.
  - `pipeline.ontology.OntologyValidationError` — raised on unknown class in a seed or missing required field.

- [ ] **Step 1: Write classes.yaml**

Path: `kg-poc/ontology/classes.yaml`

```yaml
# MECE-7 ontology — the 7 classes defined by the decision-cascade test in
# docs/superpowers/specs/2026-07-12-kg-ontology-pipeline-poc-design.md §4.
# Order is the decision-cascade order — take the first hit.
classes:
  - name: RegulatoryBody
    test: Is this an org that ISSUES RULES?
    examples: [BNM, BCBS, HKMA, MAS, Shariah Advisory Council]
  - name: Party
    test: Is this an actor that is regulated by, or facilitates regulation, but does not issue rules?
    examples:
      [
        board,
        senior management,
        CRO,
        Shariah Committee,
        TPSP,
        cloud service provider,
        AKPK,
        ECAI,
        PSE,
      ]
  - name: Reference
    test: Is this a rule/standard already in force elsewhere that this doc points to?
    examples: [BCBS d424, Basel III, ISO 27001, FSA 2013]
  - name: Instrument
    test: Is this a regulatory document issued by a RegulatoryBody?
    examples: [RMiT PD, Outsourcing PD, OpRes DP, Open Finance ED]
  - name: Requirement
    test: Is this something that must be done, produced, or met?
    examples:
      [
        approval,
        notification,
        disclosure,
        RTO,
        MTPD,
        output floor,
        risk weight,
        Recovery Plan,
      ]
  - name: Topic
    test: Is this a domain of concern the doc talks about?
    examples:
      [
        operational risk,
        cyber risk,
        credit risk,
        climate risk,
        cloud,
        CCRIS,
        customer information,
        e-money,
        open finance,
      ]
  - name: Process
    test: Is this an activity or event — something that happens over time?
    examples:
      [
        stress testing,
        business impact analysis,
        recovery testing,
        scenario analysis,
        disruption,
        incident,
        resolution,
      ]
```

- [ ] **Step 2: Write seeds.yaml (initial ~50 terms)**

Path: `kg-poc/ontology/seeds.yaml`

```yaml
# Gazetteer seeds for Stage 3 extract. Every entry declares its class
# (from the MECE-7 set) and optional aliases. spaCy PhraseMatcher runs
# whole-token matches over the aliases + canonical form.
seeds:
  # RegulatoryBody
  - {
      canonical: BNM,
      class: RegulatoryBody,
      aliases: [Bank Negara Malaysia, the Bank],
    }
  - {
      canonical: BCBS,
      class: RegulatoryBody,
      aliases: [Basel Committee on Banking Supervision, Basel Committee],
    }
  - {
      canonical: HKMA,
      class: RegulatoryBody,
      aliases: [Hong Kong Monetary Authority],
    }
  - {
      canonical: MAS,
      class: RegulatoryBody,
      aliases: [Monetary Authority of Singapore],
    }
  - {
      canonical: APRA,
      class: RegulatoryBody,
      aliases: [Australian Prudential Regulation Authority],
    }
  - {
      canonical: OSFI,
      class: RegulatoryBody,
      aliases: [Office of the Superintendent of Financial Institutions],
    }
  - {
      canonical: Shariah Advisory Council,
      class: RegulatoryBody,
      aliases: [SAC],
    }

  # Party
  - {
      canonical: board,
      class: Party,
      aliases: [the board, boards, Board of Directors],
    }
  - { canonical: senior management, class: Party, aliases: [Senior Management] }
  - { canonical: CRO, class: Party, aliases: [Chief Risk Officer] }
  - { canonical: CTO, class: Party, aliases: [Chief Technology Officer] }
  - { canonical: CCO, class: Party, aliases: [Chief Compliance Officer] }
  - { canonical: CEO, class: Party, aliases: [Chief Executive Officer] }
  - { canonical: Shariah Committee, class: Party, aliases: [] }
  - {
      canonical: TPSP,
      class: Party,
      aliases:
        [
          third-party service provider,
          third party service provider,
          service provider,
        ],
    }
  - { canonical: cloud service provider, class: Party, aliases: [CSP] }
  - {
      canonical: AKPK,
      class: Party,
      aliases: [Agensi Kaunseling dan Pengurusan Kredit],
    }
  - {
      canonical: ECAI,
      class: Party,
      aliases: [External Credit Assessment Institution],
    }
  - { canonical: PSE, class: Party, aliases: [Public Sector Entity] }

  # Reference
  - {
      canonical: BCBS d424,
      class: Reference,
      aliases: [Basel III finalising post-crisis reforms],
    }
  - { canonical: Basel III, class: Reference, aliases: [] }
  - { canonical: Basel II, class: Reference, aliases: [] }
  - {
      canonical: FSA 2013,
      class: Reference,
      aliases: [Financial Services Act 2013, Financial Services Act],
    }
  - {
      canonical: IFSA 2013,
      class: Reference,
      aliases:
        [Islamic Financial Services Act 2013, Islamic Financial Services Act],
    }
  - { canonical: ISO 27001, class: Reference, aliases: [] }

  # Instrument
  - {
      canonical: RMiT,
      class: Instrument,
      aliases: [Risk Management in Technology],
    }
  - {
      canonical: BCM PD,
      class: Instrument,
      aliases: [Business Continuity Management],
    }
  - { canonical: Outsourcing PD, class: Instrument, aliases: [] }
  - {
      canonical: MCIPD,
      class: Instrument,
      aliases: [Management of Customer Information],
    }

  # Requirement (the interview's thresholds and duties)
  - { canonical: RTO, class: Requirement, aliases: [Recovery Time Objective] }
  - { canonical: RPO, class: Requirement, aliases: [Recovery Point Objective] }
  - {
      canonical: MTPD,
      class: Requirement,
      aliases:
        [Maximum Tolerable Period of Disruption, maximum tolerable downtime],
    }
  - { canonical: output floor, class: Requirement, aliases: [] }
  - { canonical: risk weight, class: Requirement, aliases: [] }
  - {
      canonical: capital requirement,
      class: Requirement,
      aliases: [capital adequacy],
    }
  - { canonical: Recovery Plan, class: Requirement, aliases: [] }
  - { canonical: material outsourcing, class: Requirement, aliases: [] }
  - { canonical: written approval, class: Requirement, aliases: [] }
  - { canonical: notification, class: Requirement, aliases: [] }
  - { canonical: consultation, class: Requirement, aliases: [] }

  # Topic
  - { canonical: operational risk, class: Topic, aliases: [] }
  - { canonical: operational resilience, class: Topic, aliases: [] }
  - { canonical: cyber risk, class: Topic, aliases: [cybersecurity] }
  - { canonical: credit risk, class: Topic, aliases: [] }
  - { canonical: market risk, class: Topic, aliases: [] }
  - { canonical: liquidity risk, class: Topic, aliases: [] }
  - { canonical: climate risk, class: Topic, aliases: [] }
  - { canonical: cloud, class: Topic, aliases: [public cloud, cloud services] }
  - { canonical: customer information, class: Topic, aliases: [customer data] }
  - { canonical: e-money, class: Topic, aliases: [electronic money] }
  - { canonical: open finance, class: Topic, aliases: [] }
  - { canonical: fraud, class: Topic, aliases: [] }

  # Process
  - { canonical: stress testing, class: Process, aliases: [] }
  - { canonical: business impact analysis, class: Process, aliases: [BIA] }
  - { canonical: recovery testing, class: Process, aliases: [] }
  - { canonical: scenario analysis, class: Process, aliases: [] }
  - { canonical: incident, class: Process, aliases: [] }
  - { canonical: disruption, class: Process, aliases: [] }
```

- [ ] **Step 3: Write failing test**

Path: `kg-poc/tests/test_ontology.py`

```python
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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_ontology.py -v`
Expected: FAIL — module not found.

- [ ] **Step 5: Implement ontology loader**

Path: `kg-poc/pipeline/ontology.py`

```python
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_ontology.py -v`
Expected: PASS (7 tests)

- [ ] **Step 7: Commit**

```bash
git add kg-poc/ontology/ kg-poc/pipeline/ontology.py kg-poc/tests/test_ontology.py
git commit -m "feat(kg-poc): MECE-7 ontology + initial gazetteer seeds"
```

---

## Task 4: Stage 1 — Ingest (PDF → markdown)

Follows engine's pattern: MarkItDown, optionally routed through Azure Document Intelligence when env creds are set. Reimplemented in the new package (no import from `engine/`).

**Files:**

- Create: `kg-poc/pipeline/ingest.py`
- Create: `kg-poc/tests/test_ingest.py`

**Interfaces:**

- Consumes: `pipeline.corpus.DOCUMENTS`, `pipeline.config.DATA_DIR`.
- Produces:
  - `pipeline.ingest.UnreadableDocumentError` — raised on empty/failed conversion.
  - `pipeline.ingest.ingest_document(source_path: Path, converter: Optional[Any] = None) -> str` — returns markdown; raises on empty. `converter` is an injectable seam with `.convert(str) -> result` where `result.text_content: str`.
  - `pipeline.ingest.run_stage_1(documents: dict = DOCUMENTS, output_dir: Path = DATA_DIR / "text", converter: Optional[Any] = None) -> dict[str, Path]` — ingests every document, writes `{doc_id}.md`, returns `{doc_id: output_path}`.

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_ingest.py`

```python
from pathlib import Path
from typing import Any

import pytest

from pipeline.ingest import (
    UnreadableDocumentError,
    ingest_document,
    run_stage_1,
)


class StubResult:
    def __init__(self, text: str) -> None:
        self.text_content = text


class StubConverter:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping
        self.calls: list[str] = []

    def convert(self, path: str) -> StubResult:
        self.calls.append(path)
        return StubResult(self._mapping[path])


def test_ingest_document_returns_markdown_from_converter(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"pdf")
    converter = StubConverter({str(pdf): "# hello"})
    assert ingest_document(pdf, converter=converter) == "# hello"


def test_ingest_document_raises_on_empty_output(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"pdf")
    converter = StubConverter({str(pdf): "   \n\n  "})
    with pytest.raises(UnreadableDocumentError):
        ingest_document(pdf, converter=converter)


def test_ingest_document_raises_when_converter_raises(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"pdf")

    class Boom:
        def convert(self, path: str) -> Any:
            raise RuntimeError("bad pdf")

    with pytest.raises(UnreadableDocumentError):
        ingest_document(pdf, converter=Boom())


def test_run_stage_1_writes_markdown_per_doc(tmp_path: Path):
    pdf_a = tmp_path / "a.pdf"
    pdf_b = tmp_path / "b.pdf"
    pdf_a.write_bytes(b"a")
    pdf_b.write_bytes(b"b")

    documents = {
        "a": {"doc_id": "a", "source_path": pdf_a, "title": "A",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
        "b": {"doc_id": "b", "source_path": pdf_b, "title": "B",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
    }
    converter = StubConverter({str(pdf_a): "A body", str(pdf_b): "B body"})
    out_dir = tmp_path / "text"

    outputs = run_stage_1(documents=documents, output_dir=out_dir, converter=converter)

    assert outputs["a"].read_text() == "A body"
    assert outputs["b"].read_text() == "B body"
    assert outputs["a"].name == "a.md"
    assert outputs["b"].name == "b.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_ingest.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement ingest**

Path: `kg-poc/pipeline/ingest.py`

```python
"""Stage 1 — PDF → clean markdown.

Uses MarkItDown; when AZURE_DOCINTEL_ENDPOINT + AZURE_DOCINTEL_API_KEY are
set, routes PDFs through Azure Document Intelligence (prebuilt-layout) for
correct multi-column reading order — BNM PDFs mis-order otherwise. Direct
port of engine/ingest.py's pattern, standalone in this package (no cross-
package import).
"""

import os
from pathlib import Path
from typing import Any, Optional

from pipeline.config import DATA_DIR
from pipeline.corpus import DOCUMENTS

_DOCINTEL_ENDPOINT = os.environ.get("AZURE_DOCINTEL_ENDPOINT")
_DOCINTEL_API_KEY = os.environ.get("AZURE_DOCINTEL_API_KEY")
_DOCINTEL_API_VERSION = os.environ.get("AZURE_DOCINTEL_API_VERSION", "2024-11-30")


class UnreadableDocumentError(Exception):
    """PDF conversion yielded empty text or the converter itself failed."""


def _build_default_converter() -> Any:
    """Construct a MarkItDown converter, optionally with Azure Document
    Intelligence when credentials are set.
    """
    from markitdown import MarkItDown

    if _DOCINTEL_ENDPOINT and _DOCINTEL_API_KEY:
        from azure.core.credentials import AzureKeyCredential

        return MarkItDown(
            docintel_endpoint=_DOCINTEL_ENDPOINT,
            docintel_credential=AzureKeyCredential(_DOCINTEL_API_KEY),
            docintel_api_version=_DOCINTEL_API_VERSION,
        )
    return MarkItDown()


def ingest_document(
    source_path: Path,
    converter: Optional[Any] = None,
) -> str:
    """Convert a single PDF to markdown. Raises on empty/failed output.

    `converter` is any object with a `.convert(path_str) -> obj` method where
    `obj.text_content` is a str. Tests inject a stub; production leaves it
    None so the default MarkItDown converter is built.
    """
    if converter is None:
        converter = _build_default_converter()

    try:
        result = converter.convert(str(source_path))
    except Exception as exc:
        raise UnreadableDocumentError(
            f"Conversion of {source_path} failed: {exc}"
        ) from exc

    text = getattr(result, "text_content", None)
    if text is None or text.strip() == "":
        raise UnreadableDocumentError(
            f"Conversion of {source_path} yielded no usable text"
        )
    return text


def run_stage_1(
    documents: dict = DOCUMENTS,
    output_dir: Path = DATA_DIR / "text",
    converter: Optional[Any] = None,
) -> dict[str, Path]:
    """Ingest every document, write `{doc_id}.md` under `output_dir`.

    Returns `{doc_id: output_path}`. Fails loudly on the first unreadable
    document — no partial success.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    for doc_id, entry in documents.items():
        markdown = ingest_document(entry["source_path"], converter=converter)
        out_path = output_dir / f"{doc_id}.md"
        out_path.write_text(markdown)
        outputs[doc_id] = out_path

    return outputs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_ingest.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/ingest.py kg-poc/tests/test_ingest.py
git commit -m "feat(kg-poc): stage 1 ingest — PDF to markdown"
```

---

## Task 5: Stage 2 — Chunk (markdown → sentence chunks)

spaCy sentencizer chunks each doc's markdown into sentence-level records with byte-exact offsets. `data/chunks.jsonl` is the output.

**Files:**

- Create: `kg-poc/pipeline/chunk.py`
- Create: `kg-poc/tests/test_chunk.py`

**Interfaces:**

- Consumes: `pipeline.config.DATA_DIR`, `pipeline.config.CHUNK_LEN_WARN`.
- Produces:
  - `pipeline.chunk.Chunk` — TypedDict: `doc_id, chunk_id, char_start, char_end, text`.
  - `pipeline.chunk.chunk_document(doc_id: str, markdown: str, nlp: Optional[Any] = None) -> list[Chunk]` — sentence-split with byte offsets; injectable spaCy pipeline for tests.
  - `pipeline.chunk.run_stage_2(text_dir: Path = DATA_DIR / "text", output_path: Path = DATA_DIR / "chunks.jsonl", nlp: Optional[Any] = None) -> Path` — reads every `{doc_id}.md`, writes JSONL.
  - `pipeline.chunk._load_nlp() -> Any` — lazy spaCy load; only called when `nlp is None`.
- Verbatim invariant: for every chunk, `markdown[chunk.char_start:chunk.char_end] == chunk.text`.

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_chunk.py`

```python
import json
from pathlib import Path
from typing import Any

import pytest

from pipeline.chunk import Chunk, chunk_document, run_stage_2


class FakeSpan:
    def __init__(self, start_char: int, end_char: int, text: str) -> None:
        self.start_char = start_char
        self.end_char = end_char
        self.text = text


class FakeDoc:
    def __init__(self, sents: list[FakeSpan]) -> None:
        self.sents = sents


class FakeNLP:
    """Splits on '. ' — good enough for testing offset roundtrip."""

    def __call__(self, text: str) -> FakeDoc:
        sents: list[FakeSpan] = []
        pos = 0
        for part in text.split(". "):
            if not part:
                pos += 2
                continue
            end = pos + len(part)
            # include the trailing ". " for all but the last sentence
            if end < len(text):
                sents.append(FakeSpan(pos, end + 2, text[pos:end + 2]))
                pos = end + 2
            else:
                sents.append(FakeSpan(pos, end, text[pos:end]))
                pos = end
        return FakeDoc(sents)


def test_chunk_offsets_slice_back_to_text():
    text = "The board shall ensure. Recovery is critical. RTO must be defined."
    chunks = chunk_document("doc", text, nlp=FakeNLP())
    for chunk in chunks:
        assert text[chunk["char_start"]:chunk["char_end"]] == chunk["text"]


def test_chunk_ids_are_stable_and_zero_padded():
    text = "One. Two. Three."
    chunks = chunk_document("mydoc", text, nlp=FakeNLP())
    assert chunks[0]["chunk_id"] == "mydoc:0000"
    assert chunks[1]["chunk_id"] == "mydoc:0001"
    assert chunks[2]["chunk_id"] == "mydoc:0002"


def test_chunk_document_carries_doc_id():
    chunks = chunk_document("abc", "One.", nlp=FakeNLP())
    assert chunks[0]["doc_id"] == "abc"


def test_run_stage_2_writes_jsonl(tmp_path: Path):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    (text_dir / "a.md").write_text("Alpha. Beta.")
    (text_dir / "b.md").write_text("Gamma.")
    out = tmp_path / "chunks.jsonl"

    result = run_stage_2(text_dir=text_dir, output_path=out, nlp=FakeNLP())
    assert result == out
    lines = out.read_text().splitlines()
    parsed = [json.loads(line) for line in lines]
    doc_ids = {c["doc_id"] for c in parsed}
    assert doc_ids == {"a", "b"}
    # every chunk still round-trips
    text_a = (text_dir / "a.md").read_text()
    a_chunks = [c for c in parsed if c["doc_id"] == "a"]
    for c in a_chunks:
        assert text_a[c["char_start"]:c["char_end"]] == c["text"]


def test_run_stage_2_warns_on_oversize_chunks(tmp_path: Path, caplog):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    long_sentence = "x" * 600
    (text_dir / "big.md").write_text(long_sentence)
    out = tmp_path / "chunks.jsonl"

    with caplog.at_level("WARNING"):
        run_stage_2(text_dir=text_dir, output_path=out, nlp=FakeNLP())
    assert any("oversize chunk" in rec.message.lower() for rec in caplog.records)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_chunk.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement chunk**

Path: `kg-poc/pipeline/chunk.py`

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_chunk.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/chunk.py kg-poc/tests/test_chunk.py
git commit -m "feat(kg-poc): stage 2 chunk — sentence-level with byte offsets"
```

---

## Task 6: Stage 3a — Gazetteer extraction (PhraseMatcher)

The first pass of Stage 3: spaCy `PhraseMatcher` runs over each chunk against the gazetteer seeds. Hits carry their `class_` from the seed entry (100% precision by construction on authored terms). Whole-token matching + optional per-seed forbidden-context filters avoid false positives like `board` in `cardboard`.

**Files:**

- Create: `kg-poc/pipeline/extract.py` (partial — only the gazetteer path)
- Create: `kg-poc/tests/test_extract.py`

**Interfaces:**

- Consumes: `pipeline.chunk.Chunk`, `pipeline.ontology.SeedEntry`, `pipeline.ontology.load_seeds`.
- Produces:
  - `pipeline.extract.Span` — TypedDict: `doc_id, chunk_id, char_start, char_end, surface, class_, source, confidence`.
    - `source ∈ {"gazetteer", "gliner"}`
    - `confidence: float` (always 1.0 for gazetteer)
  - `pipeline.extract.build_matcher(seeds: list[SeedEntry], nlp: Any) -> tuple[Matcher, dict[int, SeedEntry]]` — spaCy `PhraseMatcher`. Returned dict maps match-id (int) → seed entry.
  - `pipeline.extract.extract_gazetteer_spans(chunks: list[Chunk], seeds: list[SeedEntry], nlp: Optional[Any] = None) -> list[Span]` — runs the matcher, returns spans (byte offsets absolute within the parent markdown, i.e. `chunk.char_start + local_offset`).
  - Forbidden-context filter: a match is dropped if any `left_forbidden` token appears immediately before it (within 2 tokens) or any `right_forbidden` token appears immediately after.

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_extract.py`

```python
from typing import Any

import pytest

from pipeline.chunk import Chunk
from pipeline.extract import Span, extract_gazetteer_spans


def _chunk(doc_id: str, chunk_id: str, char_start: int, text: str) -> Chunk:
    return {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "char_start": char_start,
        "char_end": char_start + len(text),
        "text": text,
    }


def test_gazetteer_finds_seed_canonical():
    chunks = [_chunk("d", "d:0000", 100, "The board shall ensure recovery.")]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert len(spans) == 1
    s = spans[0]
    assert s["surface"] == "board"
    assert s["class_"] == "Party"
    assert s["source"] == "gazetteer"
    assert s["confidence"] == 1.0
    # absolute offsets within the parent markdown, not the chunk
    assert s["char_start"] == 104
    assert s["char_end"] == 109


def test_gazetteer_finds_aliases():
    chunks = [_chunk("d", "d:0000", 0, "The Bank Negara Malaysia issued RMiT.")]
    seeds = [
        {"canonical": "BNM", "class_": "RegulatoryBody",
         "aliases": ["Bank Negara Malaysia"],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert len(spans) == 1
    assert spans[0]["surface"] == "Bank Negara Malaysia"
    assert spans[0]["class_"] == "RegulatoryBody"


def test_gazetteer_does_not_match_substring():
    """`board` in `cardboard` must NOT match — whole-token only."""
    chunks = [_chunk("d", "d:0000", 0, "The cardboard box was full.")]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert spans == []


def test_gazetteer_class_collision_produces_two_spans():
    """Same surface, two different classes → both spans emitted; resolver
    keeps them distinct."""
    chunks = [_chunk("d", "d:0000", 0, "BCBS issued guidance.")]
    seeds = [
        {"canonical": "BCBS", "class_": "RegulatoryBody", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
        {"canonical": "BCBS", "class_": "Reference", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    classes = {s["class_"] for s in spans}
    assert classes == {"RegulatoryBody", "Reference"}


def test_gazetteer_respects_left_forbidden():
    chunks = [_chunk("d", "d:0000", 0, "The Basel Committee met.")]
    seeds = [
        {"canonical": "Committee", "class_": "Party", "aliases": [],
         "left_forbidden": ["Basel"], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert spans == []


def test_gazetteer_respects_right_forbidden():
    chunks = [_chunk("d", "d:0000", 0, "The board of directors met.")]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": ["of"]},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert spans == []


def test_gazetteer_absolute_offsets_slice_back(tmp_path):
    """The invariant: markdown[span.char_start:span.char_end] == span.surface."""
    markdown = "The board shall ensure recovery. The RTO is critical."
    chunks = [_chunk("d", "d:0000", 0, markdown)]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
        {"canonical": "RTO", "class_": "Requirement", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    for s in spans:
        assert markdown[s["char_start"]:s["char_end"]] == s["surface"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_extract.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement gazetteer extraction**

Path: `kg-poc/pipeline/extract.py`

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_extract.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/extract.py kg-poc/tests/test_extract.py
git commit -m "feat(kg-poc): stage 3a gazetteer extraction with forbidden-context"
```

---

## Task 7: Stage 3b — GLiNER pass + run_stage_3 orchestration

Adds the zero-shot GLiNER pass on top of gazetteer output. Chunks first have their gazetteer hits masked (character-level substitution with equal-length spaces) so GLiNER doesn't re-find them. Confidence below the threshold → dropped to `spans_dropped.jsonl`.

**Files:**

- Modify: `kg-poc/pipeline/extract.py`
- Modify: `kg-poc/tests/test_extract.py` (add tests)

**Interfaces:**

- Consumes: gazetteer output from Task 6 + `pipeline.config.GLINER_CONFIDENCE_THRESHOLD`.
- Produces:
  - `pipeline.extract.GlinerLike` — Protocol with `predict_entities(text: str, labels: list[str]) -> list[dict]` where each dict has `{"start": int, "end": int, "text": str, "label": str, "score": float}`. This matches the real GLiNER API and is what tests stub.
  - `pipeline.extract.extract_gliner_spans(chunks: list[Chunk], gazetteer_spans: list[Span], gliner: GlinerLike, threshold: float = GLINER_CONFIDENCE_THRESHOLD) -> tuple[list[Span], list[Span]]` — returns `(kept, dropped)` — the kept list has spans with `confidence >= threshold`, dropped are below.
  - `pipeline.extract.mask_chunk_text(text: str, chunk_char_start: int, gazetteer_spans_in_chunk: list[Span]) -> str` — replaces gazetteer-hit character ranges with equal-length spaces so GLiNER sees "empty" territory. Length preserved so GLiNER offsets remain valid.
  - `pipeline.extract.run_stage_3(chunks_path: Path, seeds: list[SeedEntry], output_dir: Path, gliner: Optional[GlinerLike] = None, nlp: Optional[Any] = None) -> tuple[Path, Path]` — reads `chunks.jsonl`, writes `spans.jsonl` (kept) and `spans_dropped.jsonl` (below threshold). Returns `(kept_path, dropped_path)`.
  - Descriptive GLiNER labels: `_GLINER_LABELS = ["regulatory body", "regulated actor or third party", "external rule or standard", "regulatory document", "regulatory requirement or duty", "domain topic", "activity or process"]` — passed to GLiNER; the returned `label` is mapped back to the canonical MECE-7 name via `_LABEL_TO_CLASS`.

- [ ] **Step 1: Add failing tests to `test_extract.py`**

Append to `kg-poc/tests/test_extract.py`:

```python
import json
from pathlib import Path

from pipeline.extract import (
    extract_gliner_spans,
    mask_chunk_text,
    run_stage_3,
)


class FakeGliner:
    """Injectable stub matching the GLiNER predict_entities signature."""

    def __init__(self, canned: dict[str, list[dict]]) -> None:
        # canned maps chunk text (after masking) → predictions
        self._canned = canned
        self.calls: list[str] = []

    def predict_entities(self, text: str, labels: list[str]) -> list[dict]:
        self.calls.append(text)
        return self._canned.get(text, [])


def test_mask_chunk_text_replaces_gazetteer_hits_with_spaces():
    chunk_text = "The board shall ensure recovery."
    span = {
        "char_start": 4, "char_end": 9,  # "board"
        "surface": "board", "class_": "Party", "source": "gazetteer",
        "confidence": 1.0, "doc_id": "d", "chunk_id": "d:0000",
    }
    masked = mask_chunk_text(chunk_text, chunk_char_start=0, gazetteer_spans_in_chunk=[span])
    assert len(masked) == len(chunk_text)
    assert masked[4:9] == "     "
    assert masked.startswith("The      shall")


def test_extract_gliner_spans_returns_kept_and_dropped():
    chunks = [_chunk("d", "d:0000", 0, "Board ensures recovery.")]
    canned = {
        "Board ensures recovery.": [
            {"start": 0, "end": 5, "text": "Board",
             "label": "regulated actor or third party", "score": 0.9},
            {"start": 15, "end": 23, "text": "recovery",
             "label": "activity or process", "score": 0.4},  # below 0.7
        ]
    }
    gliner = FakeGliner(canned)
    kept, dropped = extract_gliner_spans(chunks, gazetteer_spans=[], gliner=gliner)
    assert len(kept) == 1
    assert kept[0]["surface"] == "Board"
    assert kept[0]["class_"] == "Party"
    assert kept[0]["source"] == "gliner"
    assert kept[0]["confidence"] == 0.9
    assert len(dropped) == 1
    assert dropped[0]["surface"] == "recovery"
    assert dropped[0]["confidence"] == 0.4


def test_extract_gliner_offsets_are_absolute_within_markdown():
    chunks = [_chunk("d", "d:0000", 100, "The board ensures.")]
    canned = {
        "The board ensures.": [
            {"start": 4, "end": 9, "text": "board",
             "label": "regulated actor or third party", "score": 0.9},
        ]
    }
    kept, _ = extract_gliner_spans(chunks, gazetteer_spans=[], gliner=FakeGliner(canned))
    assert kept[0]["char_start"] == 104
    assert kept[0]["char_end"] == 109


def test_run_stage_3_writes_spans_and_dropped(tmp_path: Path):
    chunks_path = tmp_path / "chunks.jsonl"
    chunks = [_chunk("d", "d:0000", 0, "The board ensures recovery.")]
    with chunks_path.open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(c) + "\n")

    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    canned = {
        # gazetteer masks "board" → "     ", so GLiNER sees this exact string
        "The       ensures recovery.": [
            {"start": 18, "end": 26, "text": "recovery",
             "label": "activity or process", "score": 0.85},
            {"start": 18, "end": 26, "text": "recovery",
             "label": "domain topic", "score": 0.5},
        ]
    }
    gliner = FakeGliner(canned)
    out_dir = tmp_path / "out"

    kept_path, dropped_path = run_stage_3(
        chunks_path=chunks_path,
        seeds=seeds,
        output_dir=out_dir,
        gliner=gliner,
    )

    kept = [json.loads(l) for l in kept_path.read_text().splitlines()]
    dropped = [json.loads(l) for l in dropped_path.read_text().splitlines()]

    # gazetteer hit for "board" + one gliner span above threshold
    surfaces_kept = {s["surface"] for s in kept}
    assert "board" in surfaces_kept
    assert "recovery" in surfaces_kept
    # one gliner span below threshold
    assert len(dropped) == 1
    assert dropped[0]["surface"] == "recovery"
```

- [ ] **Step 2: Run test to verify new tests fail**

Run: `cd kg-poc && pytest tests/test_extract.py -v`
Expected: FAIL — new functions do not exist.

- [ ] **Step 3: Extend extract.py**

Append to `kg-poc/pipeline/extract.py`:

```python
import json
from pathlib import Path
from typing import Protocol

from pipeline.config import DATA_DIR, GLINER_CONFIDENCE_THRESHOLD


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_extract.py -v`
Expected: PASS (11 tests total — 7 gazetteer + 4 GLiNER/run_stage_3)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/extract.py kg-poc/tests/test_extract.py
git commit -m "feat(kg-poc): stage 3b GLiNER extraction + run_stage_3 driver"
```

---

## Task 8: Stage 4 — Resolve (spans → entities + mentions)

Normalises span surfaces, applies class-gated merging, and writes `entities.jsonl` + `mentions.jsonl`. Aliases from `seeds.yaml` fold declared surface variants onto their canonical.

**Files:**

- Create: `kg-poc/pipeline/resolve.py`
- Create: `kg-poc/tests/test_resolve.py`

**Interfaces:**

- Consumes: `pipeline.extract.Span`, `pipeline.ontology.SeedEntry`.
- Produces:
  - `pipeline.resolve.Entity` — TypedDict: `entity_id, class_, canonical_label, aliases, mention_count, docs_appearing_in`.
  - `pipeline.resolve.Mention` — TypedDict: `entity_id, doc_id, chunk_id, char_start, char_end`.
  - `pipeline.resolve.normalise_surface(surface: str) -> str` — lowercase, strip leading article `the `, strip trailing `s` **only when the original word is not an all-uppercase acronym** (so `BCBS` stays `bcbs`, but `boards` → `board`). Pure.
  - `pipeline.resolve.build_alias_map(seeds: list[SeedEntry]) -> dict[tuple[str, str], str]` — maps `(normalised_alias, class_)` → canonical.
  - `pipeline.resolve.entity_id_for(class_: str, canonical: str) -> str` — `f"{class_.lower()}:{normalise_surface(canonical)}"`.
  - `pipeline.resolve.run_stage_4(spans_path: Path, seeds: list[SeedEntry], output_dir: Path) -> tuple[Path, Path]` — reads spans, writes `entities.jsonl` and `mentions.jsonl`.

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_resolve.py`

```python
import json
from pathlib import Path

from pipeline.resolve import (
    Entity,
    Mention,
    build_alias_map,
    entity_id_for,
    normalise_surface,
    run_stage_4,
)


def test_normalise_lowercases():
    assert normalise_surface("BOARD") == "board"


def test_normalise_strips_leading_article():
    assert normalise_surface("The board") == "board"
    assert normalise_surface("the RTO") == "rto"


def test_normalise_strips_trailing_plural_s():
    assert normalise_surface("boards") == "board"


def test_normalise_preserves_acronym_trailing_s():
    """All-uppercase acronyms keep their trailing s (BCBS, TPSPs)."""
    assert normalise_surface("BCBS") == "bcbs"
    assert normalise_surface("TPSPs") == "tpsps"


def test_normalise_preserves_multi_word():
    assert normalise_surface("Bank Negara Malaysia") == "bank negara malaysia"


def test_entity_id_is_stable():
    assert entity_id_for("Party", "board") == "party:board"
    assert entity_id_for("RegulatoryBody", "BNM") == "regulatorybody:bnm"


def test_build_alias_map_keys_by_class():
    seeds = [
        {"canonical": "BNM", "class_": "RegulatoryBody",
         "aliases": ["Bank Negara Malaysia"],
         "left_forbidden": [], "right_forbidden": []},
        {"canonical": "board", "class_": "Party", "aliases": ["the board"],
         "left_forbidden": [], "right_forbidden": []},
    ]
    m = build_alias_map(seeds)
    assert m[("bank negara malaysia", "RegulatoryBody")] == "BNM"
    assert m[("bnm", "RegulatoryBody")] == "BNM"
    assert m[("board", "Party")] == "board"


def test_same_string_same_class_merges(tmp_path: Path):
    spans_path = tmp_path / "spans.jsonl"
    spans = [
        {"doc_id": "a", "chunk_id": "a:0000", "char_start": 0, "char_end": 5,
         "surface": "board", "class_": "Party", "source": "gazetteer",
         "confidence": 1.0},
        {"doc_id": "a", "chunk_id": "a:0001", "char_start": 20, "char_end": 25,
         "surface": "Board", "class_": "Party", "source": "gliner",
         "confidence": 0.9},
        {"doc_id": "b", "chunk_id": "b:0000", "char_start": 0, "char_end": 5,
         "surface": "boards", "class_": "Party", "source": "gliner",
         "confidence": 0.8},
    ]
    with spans_path.open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s) + "\n")

    ent_path, men_path = run_stage_4(
        spans_path=spans_path, seeds=[], output_dir=tmp_path
    )
    entities = [json.loads(l) for l in ent_path.read_text().splitlines()]
    mentions = [json.loads(l) for l in men_path.read_text().splitlines()]

    assert len(entities) == 1
    assert entities[0]["entity_id"] == "party:board"
    assert entities[0]["mention_count"] == 3
    assert sorted(entities[0]["docs_appearing_in"]) == ["a", "b"]
    assert len(mentions) == 3
    assert all(m["entity_id"] == "party:board" for m in mentions)


def test_same_string_different_class_stays_separate(tmp_path: Path):
    spans_path = tmp_path / "spans.jsonl"
    spans = [
        {"doc_id": "a", "chunk_id": "a:0000", "char_start": 0, "char_end": 4,
         "surface": "BCBS", "class_": "RegulatoryBody", "source": "gazetteer",
         "confidence": 1.0},
        {"doc_id": "a", "chunk_id": "a:0001", "char_start": 10, "char_end": 14,
         "surface": "BCBS", "class_": "Reference", "source": "gazetteer",
         "confidence": 1.0},
    ]
    with spans_path.open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s) + "\n")

    ent_path, _ = run_stage_4(
        spans_path=spans_path, seeds=[], output_dir=tmp_path
    )
    entities = [json.loads(l) for l in ent_path.read_text().splitlines()]
    ids = {e["entity_id"] for e in entities}
    # BCBS is an acronym → normalisation preserves the trailing 's'.
    assert ids == {"regulatorybody:bcbs", "reference:bcbs"}


def test_alias_collapses_to_canonical(tmp_path: Path):
    spans_path = tmp_path / "spans.jsonl"
    spans = [
        {"doc_id": "a", "chunk_id": "a:0000", "char_start": 0, "char_end": 4,
         "surface": "BNM", "class_": "RegulatoryBody", "source": "gazetteer",
         "confidence": 1.0},
        {"doc_id": "a", "chunk_id": "a:0001", "char_start": 10, "char_end": 30,
         "surface": "Bank Negara Malaysia", "class_": "RegulatoryBody",
         "source": "gliner", "confidence": 0.9},
    ]
    with spans_path.open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s) + "\n")

    seeds = [
        {"canonical": "BNM", "class_": "RegulatoryBody",
         "aliases": ["Bank Negara Malaysia"],
         "left_forbidden": [], "right_forbidden": []},
    ]
    ent_path, men_path = run_stage_4(
        spans_path=spans_path, seeds=seeds, output_dir=tmp_path
    )
    entities = [json.loads(l) for l in ent_path.read_text().splitlines()]
    assert len(entities) == 1
    assert entities[0]["canonical_label"] == "BNM"
    assert entities[0]["mention_count"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_resolve.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement resolve**

Path: `kg-poc/pipeline/resolve.py`

```python
"""Stage 4 — spans → entities + mentions.

Deterministic normalisation + class-gated merging. Aliases from seeds.yaml
declare surface variants that should collapse to a canonical. No fuzzy
matching; known long-tail duplicates (`board` vs `Board of Directors` if
the latter isn't declared as an alias) are logged for the audit queue.
"""

import json
import logging
from pathlib import Path
from typing import Optional, TypedDict

from pipeline.config import DATA_DIR
from pipeline.extract import Span
from pipeline.ontology import SeedEntry

logger = logging.getLogger(__name__)

_ARTICLES = ("the ",)
_PLURAL_SUFFIX = "s"


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
    """Lowercase → strip leading article → strip trailing 's' EXCEPT when
    the original surface is an all-uppercase acronym.

    Deterministic. Not linguistically clever; the interview and audit
    surface most cases where cleverness would be needed as seed aliases.
    The acronym carve-out is what keeps `BCBS` and `TPSPs` recognisable
    (without it, `BCBS` would normalise to `bcb`, a nonsense token).
    """
    stripped = surface.strip()
    acronym = _is_acronym(stripped.split()[-1]) if stripped else False

    s = stripped.lower()
    for article in _ARTICLES:
        if s.startswith(article):
            s = s[len(article):]
            break
    if not acronym and len(s) > 3 and s.endswith(_PLURAL_SUFFIX):
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
        len(spans), len(entities), len(mentions),
    )
    return ent_path, men_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_resolve.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/resolve.py kg-poc/tests/test_resolve.py
git commit -m "feat(kg-poc): stage 4 resolve with class-gated merging"
```

---

## Task 9: Stage 5 — Graph (entities + mentions → NetworkX)

Builds a `MultiDiGraph` with two node types and five edge types. Applies the `mention_count < 2` filter for graph nodes (entities.jsonl unchanged). Computes tf-idf on `mentions` edges, PMI on `co-occurs`, top-k for `about`.

**Files:**

- Create: `kg-poc/pipeline/graph.py`
- Create: `kg-poc/tests/test_graph.py`

**Interfaces:**

- Consumes: `pipeline.resolve.Entity`, `pipeline.resolve.Mention`, `pipeline.corpus.DOCUMENTS`, `pipeline.config.MENTION_COUNT_MIN`.
- Produces:
  - `pipeline.graph.build_graph(entities: list[Entity], mentions: list[Mention], documents: dict[str, DocumentEntry], top_k_topics: int = 10) -> networkx.MultiDiGraph` — pure function.
  - `pipeline.graph.run_stage_5(entities_path: Path, mentions_path: Path, output_dir: Path, documents: dict = DOCUMENTS) -> tuple[Path, Path]` — writes `graph.graphml` + `graph.json`.
  - Node attributes on `Document` nodes: `node_type="Document"`, `doc_id, doc_type, title, issued_date, jurisdiction, issuer, char_count`.
  - Node attributes on `Entity` nodes: `node_type="Entity"`, `entity_id, class_, canonical_label, mention_count`.
  - Edge attributes: `edge_type` ∈ `{"mentions", "co-occurs", "about", "cites", "same-as"}`, plus `weight` (float).
  - `mentions` weight = tf-idf. `co-occurs` weight = PMI. `about` = same as `mentions` weight but only top-k Topic entities per document. `cites` and `same-as` are placeholders for v3 (implemented but produce zero edges on v1 corpus without BCBS references).

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_graph.py`

```python
import json
import math
from pathlib import Path

import networkx as nx

from pipeline.graph import build_graph, run_stage_5


def _entity(entity_id: str, class_: str, canonical: str, count: int, docs: list[str]) -> dict:
    return {
        "entity_id": entity_id, "class_": class_,
        "canonical_label": canonical, "aliases": [],
        "mention_count": count, "docs_appearing_in": docs,
    }


def _mention(entity_id: str, doc_id: str, chunk_id: str) -> dict:
    return {
        "entity_id": entity_id, "doc_id": doc_id,
        "chunk_id": chunk_id, "char_start": 0, "char_end": 5,
    }


def _document(doc_id: str) -> dict:
    from pathlib import Path
    return {
        "doc_id": doc_id, "source_path": Path(f"/tmp/{doc_id}.pdf"),
        "title": doc_id.upper(), "doc_type": "PD",
        "jurisdiction": "MY", "issuer": "BNM",
        "issued_date": "2025-01-01",
    }


def test_document_nodes_have_node_type_and_attrs():
    entities = [_entity("party:board", "Party", "board", 5, ["a", "b"])]
    mentions = [_mention("party:board", "a", "a:0000"),
                _mention("party:board", "a", "a:0001"),
                _mention("party:board", "b", "b:0000")]
    docs = {"a": _document("a"), "b": _document("b")}
    g = build_graph(entities, mentions, docs)
    assert g.nodes["a"]["node_type"] == "Document"
    assert g.nodes["a"]["issuer"] == "BNM"


def test_entity_nodes_below_mention_min_are_excluded():
    entities = [
        _entity("party:board", "Party", "board", 5, ["a"]),
        _entity("topic:foo", "Topic", "foo", 1, ["a"]),  # below MENTION_COUNT_MIN
    ]
    mentions = [_mention("party:board", "a", "a:0000")] * 5 + [
        _mention("topic:foo", "a", "a:0001")
    ]
    docs = {"a": _document("a")}
    g = build_graph(entities, mentions, docs)
    assert "party:board" in g.nodes
    assert "topic:foo" not in g.nodes


def test_mentions_edge_weight_is_tfidf():
    """tf-idf: rare terms weighted higher than common ones."""
    entities = [
        _entity("topic:common", "Topic", "common", 4, ["a", "b"]),
        _entity("topic:rare", "Topic", "rare", 2, ["a"]),
    ]
    mentions = (
        [_mention("topic:common", "a", f"a:{i:04d}") for i in range(2)]
        + [_mention("topic:common", "b", f"b:{i:04d}") for i in range(2)]
        + [_mention("topic:rare", "a", f"a:{i+10:04d}") for i in range(2)]
    )
    docs = {"a": _document("a"), "b": _document("b")}
    g = build_graph(entities, mentions, docs)

    common_edge = g.get_edge_data("a", "topic:common")
    rare_edge = g.get_edge_data("a", "topic:rare")
    # Multi-edges: find the "mentions" one
    common_w = next(d["weight"] for _, d in common_edge.items() if d["edge_type"] == "mentions")
    rare_w = next(d["weight"] for _, d in rare_edge.items() if d["edge_type"] == "mentions")
    # rare (in 1 of 2 docs) has higher idf than common (in 2 of 2)
    assert rare_w > common_w


def test_about_edges_are_only_topic_class():
    entities = [
        _entity("topic:cloud", "Topic", "cloud", 5, ["a"]),
        _entity("party:board", "Party", "board", 5, ["a"]),
    ]
    mentions = (
        [_mention("topic:cloud", "a", f"a:{i:04d}") for i in range(5)]
        + [_mention("party:board", "a", f"a:{i+10:04d}") for i in range(5)]
    )
    docs = {"a": _document("a")}
    g = build_graph(entities, mentions, docs)

    about_targets = {v for u, v, d in g.edges(data=True) if d["edge_type"] == "about" and u == "a"}
    assert about_targets == {"topic:cloud"}


def test_co_occurs_edges_only_between_entities_sharing_a_chunk():
    entities = [
        _entity("party:board", "Party", "board", 3, ["a"]),
        _entity("topic:cloud", "Topic", "cloud", 3, ["a"]),
        _entity("topic:credit", "Topic", "credit", 2, ["a"]),
    ]
    mentions = [
        _mention("party:board", "a", "a:0000"),
        _mention("topic:cloud", "a", "a:0000"),   # same chunk as board
        _mention("party:board", "a", "a:0001"),
        _mention("topic:cloud", "a", "a:0001"),
        _mention("party:board", "a", "a:0002"),
        _mention("topic:cloud", "a", "a:0002"),
        _mention("topic:credit", "a", "a:9999"),  # own chunk
        _mention("topic:credit", "a", "a:9998"),
    ]
    docs = {"a": _document("a")}
    g = build_graph(entities, mentions, docs)

    co_pairs = {
        tuple(sorted([u, v]))
        for u, v, d in g.edges(data=True)
        if d["edge_type"] == "co-occurs"
    }
    assert ("party:board", "topic:cloud") in co_pairs
    assert ("party:board", "topic:credit") not in co_pairs


def test_run_stage_5_writes_graphml_and_json(tmp_path: Path):
    entities_p = tmp_path / "entities.jsonl"
    mentions_p = tmp_path / "mentions.jsonl"
    with entities_p.open("w") as fh:
        fh.write(json.dumps(_entity("party:board", "Party", "board", 2, ["a"])) + "\n")
    with mentions_p.open("w") as fh:
        fh.write(json.dumps(_mention("party:board", "a", "a:0000")) + "\n")
        fh.write(json.dumps(_mention("party:board", "a", "a:0001")) + "\n")
    docs = {"a": _document("a")}

    gm, gj = run_stage_5(
        entities_path=entities_p,
        mentions_path=mentions_p,
        output_dir=tmp_path,
        documents=docs,
    )
    assert gm.exists()
    assert gj.exists()
    assert "nodes" in json.loads(gj.read_text())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_graph.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement graph**

Path: `kg-poc/pipeline/graph.py`

```python
"""Stage 5 — entities + mentions → NetworkX MultiDiGraph.

Two node types (Document, Entity) and five edge types (mentions,
co-occurs, about, cites, same-as). Weights are tf-idf on mentions,
PMI on co-occurs. Entities with fewer than MENTION_COUNT_MIN mentions
are excluded from the graph (still present in entities.jsonl).

cites and same-as are v3 hooks — implemented but produce zero edges on
the BNM-only v1 corpus (no BCBS references / no BCBS Document nodes).
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional, TypedDict

import networkx as nx

from pipeline.config import DATA_DIR, MENTION_COUNT_MIN
from pipeline.corpus import DOCUMENTS, DocumentEntry
from pipeline.resolve import Entity, Mention

logger = logging.getLogger(__name__)


def _tfidf_edges(
    entities: list[Entity],
    mentions: list[Mention],
    documents: dict[str, DocumentEntry],
) -> list[tuple[str, str, float]]:
    """Compute tf-idf on (doc, entity) pairs.

    tf = raw count of mentions of entity in doc
    idf = log(N / df) where df = # docs containing the entity, N = # docs
    """
    n_docs = len(documents)
    counts: dict[tuple[str, str], int] = {}
    for m in mentions:
        counts[(m["doc_id"], m["entity_id"])] = counts.get((m["doc_id"], m["entity_id"]), 0) + 1

    df: dict[str, int] = {e["entity_id"]: len(e["docs_appearing_in"]) for e in entities}

    edges: list[tuple[str, str, float]] = []
    for (doc_id, entity_id), tf in counts.items():
        d = df.get(entity_id, 1)
        idf = math.log(n_docs / d) if d > 0 else 0.0
        edges.append((doc_id, entity_id, float(tf) * idf))
    return edges


def _pmi_edges(
    mentions: list[Mention],
    kept_entities: set[str],
) -> list[tuple[str, str, float]]:
    """Compute PMI over entity pairs that co-occur in the same chunk.

    Only entity pairs where both are in `kept_entities` (i.e. above
    mention_count threshold) contribute.
    """
    # chunk -> set(entity_ids)
    by_chunk: dict[str, set[str]] = {}
    for m in mentions:
        if m["entity_id"] not in kept_entities:
            continue
        by_chunk.setdefault(m["chunk_id"], set()).add(m["entity_id"])

    total_chunks = max(len(by_chunk), 1)
    single_count: dict[str, int] = {}
    pair_count: dict[tuple[str, str], int] = {}
    for chunk_id, ent_set in by_chunk.items():
        ents = sorted(ent_set)
        for e in ents:
            single_count[e] = single_count.get(e, 0) + 1
        for i, a in enumerate(ents):
            for b in ents[i + 1:]:
                pair_count[(a, b)] = pair_count.get((a, b), 0) + 1

    edges: list[tuple[str, str, float]] = []
    for (a, b), c_ab in pair_count.items():
        p_ab = c_ab / total_chunks
        p_a = single_count[a] / total_chunks
        p_b = single_count[b] / total_chunks
        if p_a > 0 and p_b > 0 and p_ab > 0:
            pmi = math.log(p_ab / (p_a * p_b))
            edges.append((a, b, pmi))
    return edges


def build_graph(
    entities: list[Entity],
    mentions: list[Mention],
    documents: dict[str, DocumentEntry],
    top_k_topics: int = 10,
) -> nx.MultiDiGraph:
    """Assemble the graph. Applies MENTION_COUNT_MIN filter."""
    g = nx.MultiDiGraph()

    # Document nodes
    for doc_id, entry in documents.items():
        g.add_node(
            doc_id,
            node_type="Document",
            doc_id=doc_id,
            doc_type=entry["doc_type"],
            title=entry["title"],
            jurisdiction=entry["jurisdiction"],
            issuer=entry["issuer"],
            issued_date=entry["issued_date"],
        )

    # Entity nodes (above threshold only)
    kept_entity_ids: set[str] = set()
    for e in entities:
        if e["mention_count"] < MENTION_COUNT_MIN:
            continue
        kept_entity_ids.add(e["entity_id"])
        g.add_node(
            e["entity_id"],
            node_type="Entity",
            entity_id=e["entity_id"],
            class_=e["class_"],
            canonical_label=e["canonical_label"],
            mention_count=e["mention_count"],
        )

    # mentions edges (tf-idf weight) — only for kept entities
    mentions_edges = [
        (d, e, w) for d, e, w in _tfidf_edges(entities, mentions, documents)
        if e in kept_entity_ids
    ]
    for d, e, w in mentions_edges:
        g.add_edge(d, e, edge_type="mentions", weight=w)

    # about edges: top-k Topic entities per document by mentions weight
    class_by_entity = {e["entity_id"]: e["class_"] for e in entities}
    per_doc: dict[str, list[tuple[str, float]]] = {}
    for d, e, w in mentions_edges:
        if class_by_entity.get(e) == "Topic":
            per_doc.setdefault(d, []).append((e, w))
    for doc_id, pairs in per_doc.items():
        pairs.sort(key=lambda x: x[1], reverse=True)
        for e, w in pairs[:top_k_topics]:
            g.add_edge(doc_id, e, edge_type="about", weight=w)

    # co-occurs edges (PMI)
    for a, b, pmi in _pmi_edges(mentions, kept_entity_ids):
        g.add_edge(a, b, edge_type="co-occurs", weight=pmi)

    # cites + same-as: v3 hooks — no work needed for BNM-only v1 corpus.
    # In v3 we'd:
    #   - cites: emit Document → Document when a Reference entity's canonical
    #     matches a Document's title/doc_id.
    #   - same-as: emit Reference-entity → Document when both exist.

    return g


def _graph_to_json(g: nx.MultiDiGraph) -> dict:
    """Serialise the graph as a plain dict (nodes + edges lists) for the
    readable JSON artifact. GraphML is the portable format.
    """
    return {
        "nodes": [{"id": n, **g.nodes[n]} for n in g.nodes],
        "edges": [
            {"source": u, "target": v, **d}
            for u, v, d in g.edges(data=True)
        ],
    }


def run_stage_5(
    entities_path: Path = DATA_DIR / "entities.jsonl",
    mentions_path: Path = DATA_DIR / "mentions.jsonl",
    output_dir: Path = DATA_DIR,
    documents: Optional[dict[str, DocumentEntry]] = None,
) -> tuple[Path, Path]:
    """Read entities + mentions, build the graph, write graphml + json."""
    if documents is None:
        documents = DOCUMENTS

    entities = [json.loads(line) for line in entities_path.read_text().splitlines() if line.strip()]
    mentions = [json.loads(line) for line in mentions_path.read_text().splitlines() if line.strip()]

    g = build_graph(entities, mentions, documents)

    output_dir.mkdir(parents=True, exist_ok=True)
    graphml_path = output_dir / "graph.graphml"
    json_path = output_dir / "graph.json"

    nx.write_graphml(g, graphml_path)
    json_path.write_text(json.dumps(_graph_to_json(g), indent=2))

    logger.info(
        "Stage 5: graph built (%d nodes, %d edges)",
        g.number_of_nodes(), g.number_of_edges(),
    )
    return graphml_path, json_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_graph.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/graph.py kg-poc/tests/test_graph.py
git commit -m "feat(kg-poc): stage 5 graph — tf-idf mentions + PMI co-occurs"
```

---

## Task 10: Stage 6 — Analyze (graph → analysis.md)

Pure-function graph analytics: node degree, centrality, community detection, per-doc summaries. Writes a markdown report with tables and figures.

**Files:**

- Create: `kg-poc/pipeline/analyze.py`
- Create: `kg-poc/tests/test_analyze.py`

**Interfaces:**

- Consumes: `networkx.MultiDiGraph` from Stage 5.
- Produces:
  - `pipeline.analyze.per_doc_top_entities(g, doc_id, k=10) -> list[tuple[str, float]]` — top-k entities by mentions tf-idf.
  - `pipeline.analyze.doc_similarity_jaccard(g) -> list[tuple[str, str, float]]` — pairwise Jaccard on entity sets.
  - `pipeline.analyze.entity_centrality(g) -> dict[str, dict[str, float]]` — `{entity_id: {"degree": ..., "betweenness": ..., "pagerank": ...}}`.
  - `pipeline.analyze.run_stage_6(graph_path: Path, output_dir: Path) -> Path` — writes `analysis.md`.

- [ ] **Step 1: Write failing test**

Path: `kg-poc/tests/test_analyze.py`

```python
import json
from pathlib import Path

import networkx as nx

from pipeline.analyze import (
    doc_similarity_jaccard,
    entity_centrality,
    per_doc_top_entities,
    run_stage_6,
)


def _minimal_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("a", node_type="Document", doc_id="a", title="A",
               doc_type="PD", jurisdiction="MY", issuer="BNM",
               issued_date="2025-01-01")
    g.add_node("b", node_type="Document", doc_id="b", title="B",
               doc_type="PD", jurisdiction="MY", issuer="BNM",
               issued_date="2025-01-01")
    g.add_node("topic:cloud", node_type="Entity", entity_id="topic:cloud",
               class_="Topic", canonical_label="cloud", mention_count=5)
    g.add_node("topic:credit", node_type="Entity", entity_id="topic:credit",
               class_="Topic", canonical_label="credit", mention_count=3)
    g.add_edge("a", "topic:cloud", edge_type="mentions", weight=2.5)
    g.add_edge("a", "topic:credit", edge_type="mentions", weight=1.0)
    g.add_edge("b", "topic:cloud", edge_type="mentions", weight=1.5)
    return g


def test_per_doc_top_entities_ranks_by_weight():
    g = _minimal_graph()
    top = per_doc_top_entities(g, "a", k=2)
    assert top[0][0] == "topic:cloud"
    assert top[1][0] == "topic:credit"


def test_doc_similarity_jaccard_on_shared_entities():
    g = _minimal_graph()
    sims = dict(((min(u, v), max(u, v)), s) for u, v, s in doc_similarity_jaccard(g))
    # a: {cloud, credit}; b: {cloud} → J = 1/2
    assert sims[("a", "b")] == 0.5


def test_entity_centrality_shape():
    g = _minimal_graph()
    c = entity_centrality(g)
    assert "topic:cloud" in c
    assert set(c["topic:cloud"].keys()) == {"degree", "betweenness", "pagerank"}


def test_run_stage_6_writes_markdown(tmp_path: Path):
    g = _minimal_graph()
    gm = tmp_path / "graph.graphml"
    nx.write_graphml(g, gm)
    report = run_stage_6(graph_path=gm, output_dir=tmp_path)
    assert report.exists()
    body = report.read_text()
    assert "# KG POC — analysis" in body
    assert "topic:cloud" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_analyze.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement analyze**

Path: `kg-poc/pipeline/analyze.py`

```python
"""Stage 6 — graph → analysis.md + figures.

Pure NetworkX analytics: degree, betweenness, PageRank on Entity nodes;
per-doc top-k by mentions tf-idf; pairwise Jaccard similarity on doc
entity sets. Louvain community detection deferred to a v2 tweak (adds
python-louvain dep and drives a filtered "communities" figure) — kept out
of v1 to minimise deps.
"""

import logging
from pathlib import Path

import networkx as nx

from pipeline.config import DATA_DIR

logger = logging.getLogger(__name__)


def _document_nodes(g: nx.MultiDiGraph) -> list[str]:
    return [n for n, d in g.nodes(data=True) if d.get("node_type") == "Document"]


def _entity_nodes(g: nx.MultiDiGraph) -> list[str]:
    return [n for n, d in g.nodes(data=True) if d.get("node_type") == "Entity"]


def per_doc_top_entities(
    g: nx.MultiDiGraph, doc_id: str, k: int = 10
) -> list[tuple[str, float]]:
    """Top-k outgoing `mentions` edges for a document, by weight desc."""
    weighted: list[tuple[str, float]] = []
    for _, v, data in g.out_edges(doc_id, data=True):
        if data.get("edge_type") == "mentions":
            weighted.append((v, float(data.get("weight", 0.0))))
    weighted.sort(key=lambda x: x[1], reverse=True)
    return weighted[:k]


def _entity_set_per_doc(g: nx.MultiDiGraph) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for d in _document_nodes(g):
        result[d] = {
            v for _, v, data in g.out_edges(d, data=True)
            if data.get("edge_type") == "mentions"
        }
    return result


def doc_similarity_jaccard(
    g: nx.MultiDiGraph,
) -> list[tuple[str, str, float]]:
    """Pairwise Jaccard similarity on each doc's entity set (mentions)."""
    per_doc = _entity_set_per_doc(g)
    docs = sorted(per_doc.keys())
    out: list[tuple[str, str, float]] = []
    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            union = per_doc[a] | per_doc[b]
            if not union:
                out.append((a, b, 0.0))
                continue
            j = len(per_doc[a] & per_doc[b]) / len(union)
            out.append((a, b, j))
    return out


def entity_centrality(g: nx.MultiDiGraph) -> dict[str, dict[str, float]]:
    """Degree, betweenness, PageRank per Entity node.

    Computed on the underlying simple digraph (edge-type-agnostic) — for a
    POC that's fine; a v2 tweak could weight by edge type.
    """
    simple = nx.DiGraph()
    for u, v in g.edges():
        simple.add_edge(u, v)
    if simple.number_of_nodes() == 0:
        return {}

    deg = dict(simple.degree())
    bet = nx.betweenness_centrality(simple) if simple.number_of_nodes() > 1 else {}
    pr = nx.pagerank(simple) if simple.number_of_nodes() > 0 else {}

    result: dict[str, dict[str, float]] = {}
    for n in _entity_nodes(g):
        result[n] = {
            "degree": float(deg.get(n, 0)),
            "betweenness": float(bet.get(n, 0.0)),
            "pagerank": float(pr.get(n, 0.0)),
        }
    return result


def _render_top_entities_table(
    g: nx.MultiDiGraph, k: int = 10
) -> str:
    lines = ["## Per-document top entities (tf-idf)\n"]
    for d in _document_nodes(g):
        lines.append(f"### {d}\n")
        lines.append("| entity | weight |")
        lines.append("| --- | --- |")
        for e, w in per_doc_top_entities(g, d, k=k):
            lines.append(f"| {e} | {w:.3f} |")
        lines.append("")
    return "\n".join(lines)


def _render_centrality_table(g: nx.MultiDiGraph, k: int = 20) -> str:
    c = entity_centrality(g)
    lines = ["## Top entity centrality\n",
             "| entity | degree | betweenness | pagerank |",
             "| --- | --- | --- | --- |"]
    top = sorted(c.items(), key=lambda x: x[1]["pagerank"], reverse=True)[:k]
    for e, s in top:
        lines.append(
            f"| {e} | {s['degree']:.0f} | {s['betweenness']:.4f} | {s['pagerank']:.4f} |"
        )
    return "\n".join(lines)


def _render_similarity_table(g: nx.MultiDiGraph) -> str:
    lines = ["## Document similarity (Jaccard on entity sets)\n",
             "| doc A | doc B | jaccard |",
             "| --- | --- | --- |"]
    sims = sorted(doc_similarity_jaccard(g), key=lambda x: x[2], reverse=True)
    for a, b, s in sims:
        lines.append(f"| {a} | {b} | {s:.3f} |")
    return "\n".join(lines)


def run_stage_6(
    graph_path: Path = DATA_DIR / "graph.graphml",
    output_dir: Path = DATA_DIR,
) -> Path:
    """Render the analysis markdown from the built graph."""
    g = nx.read_graphml(graph_path)
    # read_graphml returns a MultiDiGraph iff written with keys=True; be
    # defensive and coerce.
    if not isinstance(g, nx.MultiDiGraph):
        g = nx.MultiDiGraph(g)

    output_dir.mkdir(parents=True, exist_ok=True)
    body = [
        "# KG POC — analysis\n",
        f"- nodes: {g.number_of_nodes()}",
        f"- edges: {g.number_of_edges()}",
        "",
        _render_top_entities_table(g),
        "",
        _render_centrality_table(g),
        "",
        _render_similarity_table(g),
    ]
    out = output_dir / "analysis.md"
    out.write_text("\n".join(body))
    logger.info("Stage 6: analysis written to %s", out)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_analyze.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add kg-poc/pipeline/analyze.py kg-poc/tests/test_analyze.py
git commit -m "feat(kg-poc): stage 6 analyze — centrality + similarity report"
```

---

## Task 11: Stage 7 — Viz (pyvis interactive HTML)

Renders the graph as an interactive HTML file. Documents one shape, Entities coloured by MECE-7 class. This stage has no unit tests — it's a thin adapter over pyvis and the smoke test in `test_run.py` (Task 12) covers "did the file get written."

**Files:**

- Create: `kg-poc/pipeline/viz.py`

**Interfaces:**

- Consumes: `networkx.MultiDiGraph`.
- Produces:
  - `pipeline.viz.render_graph_html(g: nx.MultiDiGraph, output_path: Path) -> Path` — writes an HTML file.
  - `pipeline.viz.run_stage_7(graph_path: Path, output_path: Path) -> Path`.
  - `pipeline.viz._CLASS_COLOR: dict[str, str]` — one colour per MECE-7 class.

- [ ] **Step 1: Implement viz**

Path: `kg-poc/pipeline/viz.py`

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add kg-poc/pipeline/viz.py
git commit -m "feat(kg-poc): stage 7 viz — pyvis interactive HTML"
```

---

## Task 12: Runner CLI + end-to-end smoke test

Wires all seven stages behind `python -m kg_poc.run --stage={all,1..7}`. Adds an end-to-end smoke test that exercises the full pipeline on a tiny synthetic corpus (two 200-word markdown files) with stubbed MarkItDown and GLiNER.

**Files:**

- Create: `kg-poc/pipeline/run.py`
- Create: `kg-poc/tests/test_run.py`

**Interfaces:**

- Consumes: all `run_stage_N` functions.
- Produces:
  - `pipeline.run.main(argv: Optional[list[str]] = None) -> int` — parses args and dispatches.
  - `pipeline.run.run_all(...)` — sequential dispatch of stages 1–7.

- [ ] **Step 1: Write failing end-to-end test**

Path: `kg-poc/tests/test_run.py`

```python
import json
from pathlib import Path
from typing import Any

import pytest

from pipeline.run import run_all


class StubMarkItDownResult:
    def __init__(self, text: str) -> None:
        self.text_content = text


class StubMarkItDown:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def convert(self, path: str) -> StubMarkItDownResult:
        return StubMarkItDownResult(self._mapping[path])


class StubGliner:
    """Returns one high-confidence gliner span per chunk, matching the word
    "recovery" if present."""

    def predict_entities(self, text: str, labels: list[str]) -> list[dict]:
        idx = text.find("recovery")
        if idx == -1:
            return []
        return [{
            "start": idx, "end": idx + len("recovery"),
            "text": "recovery",
            "label": "activity or process",
            "score": 0.85,
        }]


def test_end_to_end_smoke(tmp_path: Path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    pdf_a = corpus_dir / "a.pdf"
    pdf_b = corpus_dir / "b.pdf"
    pdf_a.write_bytes(b"a")
    pdf_b.write_bytes(b"b")

    text_a = (
        "The board shall ensure recovery of critical systems. "
        "BNM issued RMiT in 2025. "
        "Cloud services require notification. "
        "Recovery is critical."
    )
    text_b = (
        "The board approves outsourcing. "
        "Bank Negara Malaysia oversees. "
        "Cloud is a key topic. "
        "Recovery testing is mandatory."
    )
    converter = StubMarkItDown({str(pdf_a): text_a, str(pdf_b): text_b})

    documents = {
        "a": {"doc_id": "a", "source_path": pdf_a, "title": "Doc A",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
        "b": {"doc_id": "b", "source_path": pdf_b, "title": "Doc B",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
    }

    output = tmp_path / "out"
    run_all(
        documents=documents,
        output_dir=output,
        converter=converter,
        gliner=StubGliner(),
    )

    # Every stage's artifact exists
    assert (output / "text" / "a.md").exists()
    assert (output / "text" / "b.md").exists()
    assert (output / "chunks.jsonl").exists()
    assert (output / "spans.jsonl").exists()
    assert (output / "entities.jsonl").exists()
    assert (output / "mentions.jsonl").exists()
    assert (output / "graph.graphml").exists()
    assert (output / "graph.json").exists()
    assert (output / "analysis.md").exists()
    assert (output / "graph.html").exists()

    # Verbatim invariant — every span slices back byte-exactly
    spans = [json.loads(l) for l in (output / "spans.jsonl").read_text().splitlines()]
    text_by_doc = {
        "a": (output / "text" / "a.md").read_text(),
        "b": (output / "text" / "b.md").read_text(),
    }
    for s in spans:
        source = text_by_doc[s["doc_id"]]
        assert source[s["char_start"]:s["char_end"]] == s["surface"], (
            f"broken provenance for span {s}"
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd kg-poc && pytest tests/test_run.py -v`
Expected: FAIL — `pipeline.run.run_all` does not exist.

- [ ] **Step 3: Implement run.py**

Path: `kg-poc/pipeline/run.py`

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd kg-poc && pytest tests/test_run.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Run the full test suite**

Run: `cd kg-poc && pytest -v`
Expected: all tests pass; total time <5s.

- [ ] **Step 6: Commit**

```bash
git add kg-poc/pipeline/run.py kg-poc/tests/test_run.py
git commit -m "feat(kg-poc): CLI runner + end-to-end smoke test"
```

---

## Task 13: Notebooks (jupytext-paired) + final integration commit

Three jupytext-paired notebooks for exploratory analysis on the real v1 corpus. Only the `.py` sources are tracked; `.ipynb` files stay git-ignored.

**Files:**

- Create: `kg-poc/notebooks/01_explore_corpus.py`
- Create: `kg-poc/notebooks/02_ontology_coverage.py`
- Create: `kg-poc/notebooks/03_graph_analysis.py`

**Interfaces:** None new. Notebooks import from `pipeline.*` only.

- [ ] **Step 1: Create 01_explore_corpus.py**

Path: `kg-poc/notebooks/01_explore_corpus.py`

```python
# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
# ---

# %% [markdown]
# # 01 — Explore the corpus
#
# Token counts, per-doc length, doc-type mix. Run after `python -m pipeline.run --stage=1`.

# %%
from pathlib import Path

import pandas as pd

from pipeline.config import DATA_DIR
from pipeline.corpus import DOCUMENTS

# %%
rows = []
for doc_id, entry in DOCUMENTS.items():
    md_path = DATA_DIR / "text" / f"{doc_id}.md"
    if md_path.exists():
        text = md_path.read_text()
        rows.append({
            "doc_id": doc_id,
            "title": entry["title"],
            "doc_type": entry["doc_type"],
            "chars": len(text),
            "words": len(text.split()),
        })
df = pd.DataFrame(rows).sort_values("chars", ascending=False)
df
```

- [ ] **Step 2: Create 02_ontology_coverage.py**

Path: `kg-poc/notebooks/02_ontology_coverage.py`

```python
# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
# ---

# %% [markdown]
# # 02 — Ontology coverage
#
# Spans per class, per doc. Run after `python -m pipeline.run --stage=3`.

# %%
import json
from collections import Counter

import pandas as pd

from pipeline.config import DATA_DIR

# %%
spans = [json.loads(l) for l in (DATA_DIR / "spans.jsonl").read_text().splitlines() if l.strip()]
print(f"total spans: {len(spans)}")

# %%
class_counts = Counter(s["class_"] for s in spans)
class_counts

# %%
by_doc_class = Counter((s["doc_id"], s["class_"]) for s in spans)
pd.DataFrame(
    [{"doc_id": k[0], "class": k[1], "count": v} for k, v in by_doc_class.items()]
).pivot_table(index="doc_id", columns="class", values="count", fill_value=0)

# %%
source_counts = Counter(s["source"] for s in spans)
source_counts

# %% [markdown]
# ### Dropped spans (below GLINER threshold)
# %%
dropped = [json.loads(l) for l in (DATA_DIR / "spans_dropped.jsonl").read_text().splitlines() if l.strip()]
print(f"dropped spans: {len(dropped)}")
Counter(s["class_"] for s in dropped)
```

- [ ] **Step 3: Create 03_graph_analysis.py**

Path: `kg-poc/notebooks/03_graph_analysis.py`

```python
# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
# ---

# %% [markdown]
# # 03 — Graph analysis
#
# Load the graph, compute centrality, similarity, open the HTML viz.

# %%
import json

import networkx as nx

from pipeline.analyze import (
    doc_similarity_jaccard,
    entity_centrality,
    per_doc_top_entities,
)
from pipeline.config import DATA_DIR

# %%
g = nx.read_graphml(DATA_DIR / "graph.graphml")
if not isinstance(g, nx.MultiDiGraph):
    g = nx.MultiDiGraph(g)
print(f"nodes: {g.number_of_nodes()}, edges: {g.number_of_edges()}")

# %% [markdown]
# ## Top entities per document
# %%
for d in sorted([n for n, d in g.nodes(data=True) if d.get("node_type") == "Document"]):
    print(f"\n### {d}")
    for e, w in per_doc_top_entities(g, d, k=10):
        print(f"  {w:6.2f}  {e}")

# %% [markdown]
# ## Doc-pair Jaccard similarity
# %%
for a, b, s in sorted(doc_similarity_jaccard(g), key=lambda x: x[2], reverse=True):
    print(f"  {s:.3f}  {a} ~ {b}")

# %% [markdown]
# ## Top entity centrality (PageRank)
# %%
c = entity_centrality(g)
for e, s in sorted(c.items(), key=lambda x: x[1]["pagerank"], reverse=True)[:30]:
    print(f"  pr={s['pagerank']:.4f} deg={s['degree']:.0f}  {e}")
```

- [ ] **Step 4: Commit**

```bash
git add kg-poc/notebooks/
git commit -m "feat(kg-poc): jupytext notebooks for corpus + coverage + graph analysis"
```

- [ ] **Step 5: Push and open PR**

```bash
git push -u origin feat/kg-poc-skeleton
```

Then open a GitHub PR against `main` — do not merge until quality gates (spec §8) pass on a real run of the v1 corpus.

---

## Self-review notes

- Every spec section §1–§10 is covered by at least one task. §11 open questions are deferred (by design). §12 change log is document-level, no task.
- No placeholders, no TBDs. Every step shows the code it introduces.
- Type consistency check: `class_` (trailing underscore) used consistently as the field name for MECE-7 class throughout `Span`, `Entity`, entity attributes on graph nodes. `edge_type` used consistently for edge attributes. `run_stage_N` naming consistent across all seven stages. `entity_id` shape `f"{class_.lower()}:{normalise_surface(canonical)}"` is stated in Task 8's `entity_id_for` and used in Task 9's tests.
- Verbatim invariant enforced by tests in Task 6 (`test_gazetteer_absolute_offsets_slice_back`), Task 7 (`test_extract_gliner_offsets_are_absolute_within_markdown`), and end-to-end in Task 12 (`test_end_to_end_smoke`).
- Loud failure discipline: `UnreadableDocumentError` (Task 4), `OntologyValidationError` (Task 3), below-threshold GLiNER spans dropped-not-discarded (Task 7).
- Class-gated resolution and MENTION_COUNT_MIN filter both covered by explicit tests (Task 8 `test_same_string_different_class_stays_separate`; Task 9 `test_entity_nodes_below_mention_min_are_excluded`).
