# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""The Q-levels' registrations (binding layer): each band level whose sealed
witness already exists, registered as a replay of sealed evidence.

``bindings/qlevels.json`` names, per level, the sealed theorems and sources
the witness rests on, what a replay still lacks, and any embargo item that
blocks it.  ``registrations`` checks every citation against the pinned
clone: a cited theorem must be in the sealed axiom report within
``{propext, Quot.sound, Classical.choice}`` (``RR-STATEMENT`` or ``RR-AXIOM`` otherwise), a name
listed as not reported must still be absent (``STALE_REGISTRATION``), and a
blocker must be an item of the embargo list or one of the named non-embargo
blockers (``UNKNOWN_BLOCKER`` otherwise).  A level is ``BOUND`` when its
replay record is bound with an adapter, ``BLOCKED`` when a named blocker
stands in the way, and ``AWAITING_REPLAY`` otherwise.  Only a
bound level can reach R1 under the replayed-evidence key, and only the
receiving side grades it.  A level the engine answers by its own computation
(a binding whose kernel is not ``replay``) is recorded under the harness key;
its registration keeps its blocker and names that record
(``harness_record``).

Research-tree witnesses (the author's ruling of 2026-09-25).  A registration
whose ``witness_custody`` is ``research_tree`` names the tree files its
replay reads (``tree_sources``, each checked against the pinned clone), and
is ``BOUND`` through the level's research-tree replay (tag ``T``) only.  The
ruling retires the blocker ``witness_not_sealed``: a registration that still
lists it is refused (``RULED_ADMISSIBLE``).  A research-tree witness that does
not meet its checker is blocked by name (``tree_witness_off_class``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from operations.domain.level_engine_context import (
    current_context,
)
from operations.use_cases.level_engine.research_engine.canon import load_path
from operations.use_cases.level_engine.research_engine.errors import Refusal
from operations.use_cases.level_engine.research_engine.guards import EMBARGO_KINDS
from operations.use_cases.level_engine.research_engine.sealed_evidence import (
    axiom_report,
    lean_citation,
)
from operations.use_cases.level_engine.research_engine.sealed_evidence import (
    source as sealed_source,
)

from . import bundles as B
from . import reach as R

ROOT = current_context().runtime_root
REGISTRY = current_context().historical_path("bindings/qlevels.json")
# Blockers that are not embargo items: the named witness is not sealed (it
# lives in a research tree), or it is sealed but has nothing to replay it.
NON_EMBARGO_BLOCKERS = frozenset({"no_sealed_replay", "tree_witness_off_class"})
RETIRED_BLOCKERS = frozenset({"witness_not_sealed"})
CUSTODIES = frozenset({"sealed", "research_tree"})


def registrations(levels: Mapping[int, Mapping[str, object]], trees: Mapping[int, Mapping[str, object]] | None = None,
                  registry: Path = REGISTRY) -> dict[str, object]:
    doc = load_path(registry)
    assert isinstance(doc, dict) and isinstance(doc["levels"], list)
    report = axiom_report()
    rows: list[dict[str, object]] = []
    for e in doc["levels"]:
        level = int(e["level"])
        stale = [n for n in e["named_not_reported"] if n in report]
        if stale:
            raise Refusal("STALE_REGISTRATION", f"level {level}: {', '.join(stale)} is now reported")
        retired = [k for k in e["blocked_by"] if k in RETIRED_BLOCKERS]
        if retired:
            raise Refusal("RULED_ADMISSIBLE", f"level {level}: {', '.join(retired)} is retired by the author's "
                                              "ruling of 2026-09-25; research-tree witnesses are admissible")
        custody = str(e.get("witness_custody", "sealed"))
        tree_sources = list(e.get("tree_sources", []))
        if custody not in CUSTODIES:
            raise Refusal("UNKNOWN_CUSTODY", f"level {level}: {custody}")
        if (custody == "research_tree") != bool(tree_sources) or (
                custody == "research_tree" and (e["sealed_sources"] or e["sealed_theorems"])):
            raise Refusal("MIXED_CUSTODY", f"level {level}: a research-tree registration names tree sources "
                                           "and nothing sealed; a sealed one names no tree source")
        if any(not str(r).startswith("research/") for r in tree_sources):
            raise Refusal("MIXED_CUSTODY", f"level {level}: a tree source outside research/")
        unknown = [k for k in e["blocked_by"] if k not in EMBARGO_KINDS | NON_EMBARGO_BLOCKERS]
        if unknown:
            raise Refusal("UNKNOWN_BLOCKER", f"level {level}: {', '.join(unknown)} is not a named blocker")
        # A registration speaks for the replayed-sealed-evidence key only.  A
        # level bound through the engine's own computation (any kernel but
        # ``replay``) is the harness key's record, and leaves the registration's
        # blocker standing.
        adapted = level in levels and R.adapter_path(level).exists()
        tree_bound = level in (trees or {}) and R.adapter_path(level, f"T{level:03d}").exists()
        if tree_bound and custody != "research_tree":
            raise Refusal("MIXED_CUSTODY", f"level {level}: a research-tree replay under a sealed registration")
        bound = (adapted and levels[level].get("kernel") == "replay" and custody == "sealed") or tree_bound
        if bound and (e["blocked_by"] or e["missing"]):
            raise Refusal("STALE_REGISTRATION", f"level {level} is bound but still lists a blocker or a gap")
        status = "BOUND" if bound else ("BLOCKED" if e["blocked_by"] else "AWAITING_REPLAY")
        found = R.checker_for(level)
        rows.append({
            "blocked_by": sorted(e["blocked_by"]),
            "challenge_id": (trees or {})[level]["challenge_id"] if tree_bound else (
                levels[level]["challenge_id"] if bound else None),
            "checker": found[0] if found else None,
            "harness_record": levels[level]["challenge_id"] if adapted and levels[level].get("kernel") != "replay"
            else None,
            "level": level,
            "missing": e["missing"],
            "native_name": e["native_name"],
            "findings": list(e.get("findings", [])),
            "named_not_reported": list(e["named_not_reported"]),
            "sealed_sources": [sealed_source(r) for r in e["sealed_sources"]],
            "sealed_theorems": [lean_citation(n, report) for n in e["sealed_theorems"]],
            "status": status,
            "tree_sources": [sealed_source(r) for r in tree_sources],
            "witness_custody": custody,
        })
    return {"authority_effect": "None", "levels": rows, "schema": "level-engine.q-level-registrations.v1",
            "sealed_commit": B.sealed_commit()}
