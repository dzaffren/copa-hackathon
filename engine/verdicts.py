"""Verdict stage (stage 4b) — propose a verdict + confidence for a connection.

Design (see docs/specs/reconciliation-workbench/spec-source-connection-engine.md,
"Functional Requirements" / Task 4): the connection engine
(`engine.connections`) emits *raw, validated* clause-anchored connections and
deliberately does NOT classify them. This module layers on top of that guardrail:
given a connection whose citation already resolves verbatim in the `ClauseIndex`,
it proposes exactly one verdict —

    Consensus | Conflict | Gap | Duplicate | Partial

— with a plain-language `rationale` and a **confidence band** (High/Medium/Low)
computed *deterministically in code* from signals already present (the finder
edge score + a critic `scope_note` + a Gap-vs-Deviates ambiguity flag). No second
model round-trip decides the band.

Key invariants (mirrors `engine.connections`):

- **Verdict is a proposal, never final.** Every record carries
  `verdict_status: "proposed"`; the engine never emits `"confirmed"`.
- **Guardrail precedence.** The verdict stage runs AFTER the citation validator.
  A connection whose `clause_number` does not resolve in the index is
  `unsupported` and gets **no verdict record at all** — a verdict presupposes a
  resolved, verbatim citation. (Restricted/preview reference targets have no
  ingested passage, so their clause never resolves and they are skipped by the
  same rule — defence in depth.)
- **Verbatim by construction.** The record references the source clause by
  *number* only (`clause_number`); the verbatim quote text is fetched from the
  `ClauseIndex` at read time (the API / snapshot exporter), never authored here.
- **Blocked sources** (e.g. MAS FEAT, un-retrievable) get an honest
  `status: "could_not_retrieve"` record with `verdict: null` — never a fabricated
  verdict or quote.
- **Pending extraction** (a real source whose passage is not yet extracted) is
  the one case a non-resolving clause still yields a record: it carries
  `verification: "pending_extraction"`, and the read layer renders its quote text
  as `null` — never an approximated string.

The verdict itself is an **injectable seam** (`verdict_fn`) with an Azure default,
exactly like `finder_fn`/`critic_fn`. In the frozen demo the connections already
carry a hand-set `verdict` (the output of a one-off pass, frozen-as-fixture — see
`engine.config.AI_DP_CONNECTIONS`), so the offline build is deterministic and
needs no credentials; `verdict_fn` is only reached for a *live* analysis of a
not-yet-analysed paragraph (`POST …/analyse`), and tests stub it.
"""

from typing import Any, Callable, Optional, TypedDict

from engine.clauses import ClauseIndex

# Confidence-band thresholds — named constants so they can be tuned without
# touching callers (spec Functional Requirements § Confidence derivation).
HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.70

HIGH = "High"
MEDIUM = "Medium"
LOW = "Low"

# The five verdicts the stage may propose. ("Deviates" is a nuance on a Gap — a
# Gap-vs-Deviates-ambiguous connection is surfaced by capping confidence, not by
# a sixth verdict.)
VERDICTS = ("Consensus", "Conflict", "Gap", "Duplicate", "Partial")

_DEFAULT_BLOCKED_REASON = "This source could not be retrieved automatically."


class VerdictRecord(TypedDict, total=False):
    """One verdicts.json record, keyed by the connection `id`. Shape matches the
    read-API / snapshot-exporter join (`scripts.export_poc_snapshot`)."""

    id: str
    paragraph: str
    branch: str
    source_document_id: str
    verdict: Optional[str]
    verdict_status: str
    confidence: Optional[str]
    rationale: str
    clause_number: Optional[str]
    verification: str
    stance: str
    status: str
    reason: str


# A verdict turn reads a single validated connection (+ its verbatim clause text
# via the index) and returns {"verdict": <one of VERDICTS>, "rationale": str}.
VerdictFn = Callable[[dict[str, Any], ClauseIndex], dict[str, Any]]


class VerdictError(Exception):
    """Raised when a proposed verdict is not one of the five allowed values."""


def compute_confidence_band(
    score: float,
    scope_note: Optional[str] = None,
    gap_deviates_ambiguous: bool = False,
) -> str:
    """Deterministically map a finder score (+ signals) to High/Medium/Low.

    - ``High``   when ``score >= 0.85`` AND the critic attached no ``scope_note``.
    - ``Medium`` when ``0.70 <= score < 0.85`` OR a ``scope_note`` is present.
    - ``Low``    when ``score < 0.70``.
    - A **Gap-vs-Deviates-ambiguous** connection is capped at ``Medium`` (a score
      that would otherwise band High is surfaced as Medium so the nuance shows,
      rather than a blind High call). It never *raises* a band.
    """
    if score < MEDIUM_CONFIDENCE_THRESHOLD:
        band = LOW
    elif score < HIGH_CONFIDENCE_THRESHOLD or scope_note:
        band = MEDIUM
    else:
        band = HIGH

    if gap_deviates_ambiguous and band == HIGH:
        band = MEDIUM  # cap at Medium — surface the alternative reading
    return band


def _blocked_record(connection: dict[str, Any]) -> VerdictRecord:
    """An honest could_not_retrieve record: no verdict, no quote."""
    record: VerdictRecord = {
        "id": connection["id"],
        "paragraph": connection["paragraph"],
        "branch": connection.get("branch", "uncited"),
        "source_document_id": connection["source_document_id"],
        "status": "could_not_retrieve",
        "reason": connection.get("reason", _DEFAULT_BLOCKED_REASON),
        "verdict": None,
        "verdict_status": "proposed",
        "clause_number": None,
    }
    if "stance" in connection:
        record["stance"] = connection["stance"]
    return record


def propose_verdicts(
    connections: list[dict[str, Any]],
    clause_index: ClauseIndex,
    verdict_fn: Optional[VerdictFn] = None,
) -> dict[str, VerdictRecord]:
    """Propose a verdict record per connection, keyed by connection ``id``.

    Args:
        connections: validated connection specs. Each is a dict with ``id``,
            ``paragraph``, ``branch``, ``source_document_id`` and either
            (a) ``status == "could_not_retrieve"`` (+ ``reason``) for a blocked
            source, or (b) a ``clause_number`` plus a frozen ``verdict`` +
            ``rationale`` + ``confidence_score`` (+ optional ``scope_note``,
            ``gap_deviates_ambiguous``, ``verification``, ``stance``). When a
            connection has no frozen ``verdict``, ``verdict_fn`` supplies it (the
            live ``POST …/analyse`` path).
        clause_index: the built index; used ONLY to gate the guardrail (does the
            cited clause resolve?) — the quote text is fetched downstream.
        verdict_fn: injectable seam for the live verdict turn; defaults to the
            Azure call. Unused when every connection already carries a verdict.

    Returns:
        ``{connection_id: VerdictRecord}``. Unsupported / restricted / preview
        connections are **omitted entirely** (no verdict). Blocked sources get a
        ``could_not_retrieve`` record. Pending-extraction connections get a
        record whose quote the read layer nulls.
    """
    records: dict[str, VerdictRecord] = {}

    for connection in connections:
        connection_id = connection["id"]

        # Blocked (un-retrievable) source → honest record, no verdict/quote.
        if connection.get("status") == "could_not_retrieve":
            records[connection_id] = _blocked_record(connection)
            continue

        clause_number = connection.get("clause_number")
        verification = connection.get("verification", "illustrative")
        resolves = (
            clause_number is not None and clause_index.get(clause_number) is not None
        )

        # Guardrail: no verbatim citation → no verdict. The ONLY exception is a
        # pending-extraction source (a real, known source whose passage is not
        # yet extracted): its record is kept and the read layer renders a null
        # quote — never an approximated string.
        if not resolves and verification != "pending_extraction":
            continue

        verdict = connection.get("verdict")
        rationale = connection.get("rationale", "")
        if verdict is None:
            if verdict_fn is None:
                # No frozen verdict and no live seam → cannot classify; skip
                # rather than emit a verdictless (but supported) record.
                continue
            proposal = verdict_fn(connection, clause_index)
            verdict = proposal.get("verdict")
            rationale = proposal.get("rationale", rationale)

        if verdict not in VERDICTS:
            raise VerdictError(
                f"Proposed verdict {verdict!r} for {connection_id!r} is not one "
                f"of {VERDICTS}"
            )

        confidence = compute_confidence_band(
            score=connection.get("confidence_score", 0.0),
            scope_note=connection.get("scope_note"),
            gap_deviates_ambiguous=connection.get("gap_deviates_ambiguous", False),
        )

        record: VerdictRecord = {
            "id": connection_id,
            "paragraph": connection["paragraph"],
            "branch": connection.get("branch", "uncited"),
            "source_document_id": connection["source_document_id"],
            "verdict": verdict,
            "verdict_status": "proposed",
            "confidence": confidence,
            "rationale": rationale,
            "clause_number": clause_number,
            "verification": verification,
        }
        if "stance" in connection:
            record["stance"] = connection["stance"]
        records[connection_id] = record

    return records
