"""Cross-Workstream Intelligence — *why* two workstreams overlap.

Pure functions over the fixture store. Given two documents that live in
different workstreams (a `_cross` edge), each side's concept metadata
(`engine.concepts`), and the edge's findings, this derives the three things the
Cross-Workstream Intelligence panel needs beyond the raw linkage list:

  * ``shared_attributes`` — the concrete facts the two documents have in common
    (legal basis, applicability, keywords/topics, policy owner). Each is the
    *shared value itself*, not a boolean, so a caller renders "Both issued under
    FSA 2013, IFSA 2013" rather than a bare tick.
  * ``reasons`` — those shared facts plus a finding-label rollup, rendered as
    the plain-language "why detected" lines.
  * ``classification`` / ``risk_level`` — a rollup of the five-label taxonomy. A
    ``conflicts-with`` anywhere makes the relationship a conflict (high risk); a
    ``differs-on`` makes it divergent (medium); ``goes-beyond`` / ``silent-on``
    make it an overlap-with-gaps; only ``aligns-with`` makes it aligned (low).

Honesty (the product's hard rule) is preserved: a signal fires only when *both*
sides carry the value, and what is returned is the shared value. ISMP
classification has no offline source, so it never fires today — the field is
honoured, not faked.
"""

from typing import Any, Optional

# Institution / scope phrases we look for inside an `applicability` string.
# Kept explicit so a shared-applicability claim is auditable rather than the
# output of fuzzy matching. Each needle is tested independently (substring), so
# order here is purely the order shared phrases are listed back — broadest
# first, for a natural "licensed banks, licensed Islamic banks, …" reading.
_APPLICABILITY_TOKENS: tuple[tuple[str, str], ...] = (
    ("licensed bank", "licensed banks"),
    ("licensed islamic bank", "licensed Islamic banks"),
    ("licensed investment bank", "licensed investment banks"),
    ("development financial institution", "development financial institutions"),
    ("financial institution", "financial institutions"),
    ("consolidated", "a consolidated basis"),
)

# The label rollup, most-severe first. classification, risk_level, and the
# label that triggered it.
_CLASSIFICATION_ORDER: tuple[tuple[str, str, str], ...] = (
    ("conflicts-with", "conflict", "high"),
    ("differs-on", "divergent", "medium"),
    ("goes-beyond", "overlap", "medium"),
    ("silent-on", "overlap", "medium"),
    ("aligns-with", "aligned", "low"),
)


def _as_list(value: Any) -> list[str]:
    """Normalise a concept value to a list of trimmed strings.

    A list stays a list; a non-empty scalar becomes a one-item list; ``None`` /
    empty becomes ``[]``. Lets `legal_basis` (a list) and `applicability` (a
    scalar) be compared with the same helpers.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _intersect_ci(a: list[str], b: list[str]) -> list[str]:
    """Case-insensitive intersection, preserving the order/casing of ``a``."""
    b_norm = {x.lower() for x in b}
    out: list[str] = []
    seen: set[str] = set()
    for item in a:
        key = item.lower()
        if key in b_norm and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def shared_legal_basis(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Acts both documents are issued under (e.g. ``["FSA 2013", "IFSA 2013"]``)."""
    return _intersect_ci(_as_list(a.get("legal_basis")), _as_list(b.get("legal_basis")))


def shared_keywords(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Topics/keywords both documents carry — the strongest topical-overlap signal."""
    return _intersect_ci(_as_list(a.get("keywords")), _as_list(b.get("keywords")))


def shared_applicability(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Regulated-entity scope both documents apply to, as display phrases.

    Matches a small controlled vocabulary of institution phrases inside each
    side's `applicability` text so the claim "Both apply to licensed banks" is
    auditable, never fuzzy.
    """
    text_a = " ".join(_as_list(a.get("applicability"))).lower()
    text_b = " ".join(_as_list(b.get("applicability"))).lower()
    if not text_a or not text_b:
        return []
    out: list[str] = []
    for needle, display in _APPLICABILITY_TOKENS:
        if needle in text_a and needle in text_b and display not in out:
            out.append(display)
    return out


def shared_scalar(a: dict[str, Any], b: dict[str, Any], field: str) -> Optional[str]:
    """A scalar concept field's value when both sides carry the *same* non-null
    value (used for `policy_owner` and `ismp_classification`)."""
    va, vb = a.get(field), b.get(field)
    if va is not None and vb is not None and str(va).strip().lower() == str(vb).strip().lower():
        return str(va)
    return None


def classify(labels: dict[str, int]) -> tuple[str, str]:
    """Roll the finding-label tally up to ``(classification, risk_level)``.

    Most-severe label present wins. An empty tally (an analysed edge with no
    findings, or none loaded) reads as an unclassified overlap.
    """
    for label, classification, risk in _CLASSIFICATION_ORDER:
        if labels.get(label, 0) > 0:
            return classification, risk
    return "overlap", "low"


_LABEL_REASON = {
    "conflicts-with": "conflict on {n} requirement(s)",
    "differs-on": "differ on {n} requirement(s)",
    "goes-beyond": "one goes beyond the other on {n} requirement(s)",
    "silent-on": "one is silent on {n} area(s) the other covers",
    "aligns-with": "align on {n} requirement(s)",
}


def shared_attributes(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """The structured "what do they share" block for one relationship."""
    return {
        "legal_basis": shared_legal_basis(a, b),
        "applicability": shared_applicability(a, b),
        "keywords": shared_keywords(a, b),
        "policy_owner": shared_scalar(a, b, "policy_owner"),
        "ismp_classification": shared_scalar(a, b, "ismp_classification"),
    }


def reasons(shared: dict[str, Any], labels: dict[str, int]) -> list[str]:
    """Plain-language "why detected" lines from shared attributes + label tally.

    Shared-fact lines come first (they are the *why*), then the label rollup
    (the *what the linkages say*). Only signals that actually fired appear — an
    empty list means the two share nothing derivable, which is itself honest.
    """
    lines: list[str] = []
    if shared.get("applicability"):
        lines.append("Both apply to " + _join(shared["applicability"]))
    if shared.get("legal_basis"):
        lines.append("Both issued under " + _join(shared["legal_basis"]))
    if shared.get("keywords"):
        lines.append("Both address " + _join(shared["keywords"][:4]))
    if shared.get("policy_owner"):
        lines.append("Both owned by " + shared["policy_owner"])
    if shared.get("ismp_classification"):
        lines.append("Both classified as " + shared["ismp_classification"])
    for label, template in _LABEL_REASON.items():
        n = labels.get(label, 0)
        if n > 0:
            lines.append("The linkages " + template.format(n=n))
    return lines


def _join(items: list[str]) -> str:
    """"a", "a and b", "a, b and c" — for readable reason lines."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
