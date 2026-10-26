"""Replay of research-tree evidence: a cancellation certificate splits a
signed list into exact-opposite pairs and a rest of one sign, and its total
is exact; a zero total alone is never a certificate.

The witnesses are ``research/natural_sections`` and
``research/fresh_characters`` (read only, through the vendored clone at its
pin; admitted by the author's ruling of 2026-09-25):

* the positive is natural_sections' pinned witness weight family
  (1, 2, -1, -2, 1, 1) from its sign-repair module: two exact-opposite pairs
  (magnitudes 1 and 2) and the rest (1, 1), total 2, which its test matches
  to its Lean decomposition;
* the refused case is fresh_characters' smallest refusing row, the totals of
  its hit carrier at part count 3, (2, -1, -1): total 0, and no certificate
  by the per-magnitude criterion nor by brute-force search, in either tree;
* the near-miss wedge (-2, -2, -1, 2, 2, 2) is natural_sections' least
  uncertified family with a positive total, from its committed receipt: a
  positive total buys no certificate either.

Clauses, decided on the packet in exact arithmetic:

* ``partition``: the pairs and the rest use every index exactly once;
* ``opposite_pairs``: each pair's two terms are nonzero and sum to 0;
* ``single_signed_rest``: the rest holds no positive term beside a negative
  one;
* ``total``: the claimed total is the exact sum of the terms.

Beside the record, both trees' criteria (per-magnitude domination, and the
brute-force search each tree cross-checks it against) decide the positive,
the refused row, the wedge and a certified zero row.

AuthorityEffect: None
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from types import ModuleType
from typing import Any, Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result, tree_json, tree_module

CHALLENGE_ID = "pairing_certificates"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
REPAIR = "natural_sections"
FRESH = "fresh_characters"
TREES = (REPAIR, FRESH)
REPAIR_RECEIPT = "receipts/sign_repair.json"
FRESH_RECEIPT = "receipts/fresh_characters.json"
SOURCES = (f"research/{REPAIR}/sign_repair.py", f"research/{REPAIR}/{REPAIR_RECEIPT}",
           f"research/{FRESH}/magnitude_census.py", f"research/{FRESH}/characters.py",
           f"research/{FRESH}/{FRESH_RECEIPT}")
CLAUSES = ("partition", "opposite_pairs", "single_signed_rest", "total")
# fresh_characters' hit carrier, and the part counts of its refusing row and
# of a certified row that also totals zero.
CARRIER = "V6"
REFUSING_PARTS = 3
CERTIFIED_ZERO_PARTS = 6


def repair() -> ModuleType:
    return tree_module(REPAIR, "sign_repair")


def fresh() -> ModuleType:
    return tree_module(FRESH, "magnitude_census")


def exact(v: int) -> str:
    return f"{v}/1"


def first_come(weights: tuple[int, ...]) -> tuple[list[list[int]], list[int]]:
    """Each term paired with the first later unpaired exact opposite, in
    index order; the rest is what stays unpaired."""
    used: set[int] = set()
    pairs: list[list[int]] = []
    for i, v in enumerate(weights):
        if i in used or v == 0:
            continue
        j = next((j for j in range(i + 1, len(weights)) if j not in used and weights[j] == -v), None)
        if j is not None:
            used |= {i, j}
            pairs.append([i, j])
    return pairs, [i for i in range(len(weights)) if i not in used]


def certificate_packet(weights: tuple[int, ...]) -> Packet:
    pairs, rest = first_come(weights)
    return {"pairs": pairs, "rest": rest, "terms": [exact(v) for v in weights],
            "total": exact(sum(weights[i] for i in rest))}


def positive() -> Packet:
    return certificate_packet(tuple(repair().PINNED_WITNESS))


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    terms = [Fraction(str(t)) for t in pk["terms"]]  # type: ignore[attr-defined]
    pairs = [(int(i), int(j)) for i, j in pk["pairs"]]  # type: ignore[attr-defined]
    rest = [int(i) for i in pk["rest"]]  # type: ignore[attr-defined]
    inside = range(len(terms))
    if sorted([i for pair in pairs for i in pair] + rest) != list(inside):
        failed.append("partition")
    if any(i not in inside or j not in inside or terms[i] == 0 or terms[i] + terms[j] != 0 for i, j in pairs):
        failed.append("opposite_pairs")
    if len({terms[i] > 0 for i in rest if i in inside and terms[i] != 0}) > 1:
        failed.append("single_signed_rest")
    if Fraction(str(pk["total"])) != sum(terms, Fraction(0)):
        failed.append("total")
    return tuple(failed)


def decisions(weights: list[int]) -> dict[str, bool]:
    """Both trees' criteria and their brute-force searches on one list."""
    return {"counting": repair().has_certificate_by_counting(tuple(weights)),
            "search": repair().has_certificate_by_search(tuple(weights)),
            "domination": bool(fresh().certificate_decision(weights)["certificate_exists"]),
            "brute_force": fresh().has_certificate_by_search(weights)}


@lru_cache(maxsize=1)
def recorded() -> dict[str, list[int]]:
    """The trees' rows: the refusing row and a certified zero row recomputed
    by fresh_characters' code, the refusing row from its receipt, and the
    wedge from natural_sections' receipt."""
    doc = tree_json(FRESH, FRESH_RECEIPT)
    rep = tree_json(REPAIR, REPAIR_RECEIPT)
    assert isinstance(doc, dict) and isinstance(rep, dict)
    witness = doc["stage_4_magnitude_census"]["row_family_kind"]["smallest_refusal_witness"]
    return {"refusing_row": list(fresh().row_family(CARRIER, REFUSING_PARTS)),
            "refusing_row_recorded": list(witness["terms"]),
            "certified_zero_row": list(fresh().row_family(CARRIER, CERTIFIED_ZERO_PARTS)),
            "wedge": list(rep["minimal_positive_total_uncertified"])}


def _terms(pk: Packet) -> list[int]:
    out = []
    for t in pk["terms"]:  # type: ignore[attr-defined]
        f = Fraction(str(t))
        assert f.denominator == 1
        out.append(int(f))
    return out


def evaluate(have: frozenset[str]) -> LevelResult:
    rows = recorded()
    by = {fid: pk for fid, _, pk, _ in packets()}
    extra: dict[str, Any] = {
        "positive": decisions(_terms(by["pos"])),
        "refusing_row": decisions(rows["refusing_row"]),
        "wedge": decisions(rows["wedge"]),
        "certified_zero_row": decisions(rows["certified_zero_row"]),
        "fixtures_are_the_trees_rows": _terms(by["own_neg"]) == rows["refusing_row"] == rows["refusing_row_recorded"]
        and _terms(by["near_wedge"]) == rows["wedge"] and _terms(by["zero_certified"]) == rows["certified_zero_row"],
    }
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=TREES)
