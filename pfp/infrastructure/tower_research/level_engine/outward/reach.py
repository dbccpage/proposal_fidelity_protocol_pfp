# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Level records in the receiving side's ``reach-receipt/1`` shape, and the
pre-flight that runs them through its own checker.  Never ports.

A record has two halves.

* The **carrier half** is the harness's alone: the ladder pins, the framing,
  the provenance, the non-claims, the loss ledger in ``mssn.loss-ledger.v2``
  with every standing entry of the carrier booked, the Lean citations the
  harness built, and the engine's own fixtures by role in its draft schema.
  ``stub`` builds it; ``run_bootstrap`` commits it under
  ``bindings/generated/reach/``.
* The **target half** needs the target: its checker of record (pin, own
  negative, codes) and an adapter that states the engine's fixtures in the
  target's input schema.  ``complete`` joins the halves into a full record
  naming the harness commit that holds the adapter and the positive.

``preflight`` runs a completed record through the receiving side's
``check_record`` with a resolver the caller supplies.  Its output is never
stored or cited; the replay of record is ``tools/reach_replay.py``.

Mode E: the carrier commit of every record is the **harness commit** in this
repository; 19L57G1 is pinned inside it (``PINS.json``).  So the receiving
side must resolve the carrier ``19L57G1`` to this repository for these rows.

AuthorityEffect: None
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, cast

from omega_engine_operations.domain.level_engine_context import (
    ContextRefusal,
    current_context,
)
from omega_engine_operations.use_cases.level_engine.research_engine.canon import dumps
from omega_engine_operations.use_cases.level_engine.research_engine.errors import Refusal
from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult

from . import bundles as B

ROOT = current_context().runtime_root
REPO = B.REPO
ENGINE_REL = "omega_engine_pfp/infrastructure/tower_research/level_engine"
from omega_engine_pfp.infrastructure.tower_research.reach.resources import reach_root
from omega_engine_pfp.infrastructure.tower_research.reach.resources import (
    registry as resource_registry,
)

REACH_DIR = current_context().reach_root or reach_root("v1")
CARRIER = "19L57G1"
STANDING = ("source.admission_reading", "source.claim_class", "source.cost_measure", "source.declared_bounds",
            "source.name_blindness")


def reach(module: str) -> ModuleType:
    """One module of the receiving side's package (``bundles.receiving``)."""
    return B.receiving(module)


def registry() -> dict[str, Any]:
    doc = resource_registry("stage_registry", version="v2")
    assert isinstance(doc, dict)
    return doc


def checkers_of_record() -> dict[str, Any]:
    doc = resource_registry("checkers", version="v2")
    assert isinstance(doc, dict)
    out = doc["checkers"]
    assert isinstance(out, dict)
    return out


def checker_for(level: int, checkers: Mapping[str, Any] | None = None) -> tuple[str, Mapping[str, Any]] | None:
    found = [(cid, e) for cid, e in sorted((checkers or checkers_of_record()).items()) if e.get("level") == level]
    return found[0] if found else None


# ---------------------------------------------------------------------------
# The carrier half
# ---------------------------------------------------------------------------


def apparatus_level(level: int, checkers: Mapping[str, Any] | None = None) -> bool:
    """Ruling D4: the level's checker of record is registered as apparatus."""
    found = checker_for(level, checkers)
    return found is not None and found[1].get("provenance") == "apparatus"


def framing(level: int, result: LevelResult, checkers: Mapping[str, Any] | None = None) -> str:
    """``AP`` for apparatus, which counts in A and never in C: a record whose
    computed answer type is A, or one at a level whose checker of record is
    registered as apparatus (ruling D4).  At such a level the checker decides
    only the carrier's mechanics (encodings, digests, receipts), whatever
    sealed answer rides inside, so the record witnesses apparatus.  ``SC``
    otherwise."""
    return "AP" if B.computed_answer_type(result) == "A" or apparatus_level(level, checkers) else "SC"


def loss_ledger_v2(result: LevelResult, unmapped_sorts: Sequence[str] = (),
                   domain: Mapping[str, str] | None = None,
                   extra: Sequence[tuple[str, str, str, str]] = ()) -> dict[str, Any]:
    """The engine's loss rows in ``mssn.loss-ledger.v2``, each standing entry
    of the carrier booked, each unmapped sort booked as dropped.  Unsealed:
    the receiving side's ``seal_ledger`` adds the commitment."""
    rows: dict[str, dict[str, Any]] = {}
    for f, s, t, c in B.loss_fields(result):
        rows[f] = {"classification": c, "field_or_law": f, "not_applicable_reason": None,
                   "source_value": s, "target_value": t}
    if "source.cost_measure" not in rows:
        tied = [k for k in rows if k.startswith("source.cost_measure.")]
        rows["source.cost_measure"] = (
            {"classification": "WEAKENED", "field_or_law": "source.cost_measure", "not_applicable_reason": None,
             "source_value": f"ties kept as forks in {len(tied)} lineages", "target_value": "one packet"}
            if tied else
            {"classification": "PRESERVED", "field_or_law": "source.cost_measure",
             "not_applicable_reason": "the answer is decided per fixture; no minimum is chosen among ties",
             "source_value": "witness grade with its tie structure", "target_value": "verdict per fixture"})
    rows.setdefault("source.name_blindness", {
        "classification": "DROPPED", "field_or_law": "source.name_blindness", "not_applicable_reason": None,
        "source_value": "not blind: the challenge is supplied and named", "target_value": "named level"})
    if domain is not None and domain["source"] != domain["target"]:
        rows.setdefault("source.coefficient_domain", {
            "classification": "WEAKENED", "field_or_law": "source.coefficient_domain", "not_applicable_reason": None,
            "source_value": domain["source"], "target_value": domain["target"]})
    for f, s, tv, c in extra:
        rows[f] = {"classification": c, "field_or_law": f, "not_applicable_reason": None,
                   "source_value": s, "target_value": tv}
    for sort in unmapped_sorts:
        rows[f"sort:{sort}"] = {"classification": "DROPPED", "field_or_law": f"sort:{sort}",
                                "not_applicable_reason": None, "source_value": sort, "target_value": "not presented"}
    count: dict[str, int] = {}
    for r in rows.values():
        count[r["classification"]] = count.get(r["classification"], 0) + 1
    return {
        "authority_effect": "None",
        "changed_assumptions": ["the challenge is supplied; no demand for it is derived"]
        + (["values are decided outside the grammar"] if B.caps(result) else []),
        "count": count,
        "fields": [rows[k] for k in sorted(rows)],
        "measure": None,
        "open_obligations": sorted(["target replay by the receiving side's checker"]
                                   + [f"component {m}" for m in result.missing_components]),
        "reframe_decision": "NONE",
        "schema": "mssn.loss-ledger.v2",
        "status_ceiling": "PROPOSED",
    }


def lean_theorems(result: LevelResult) -> list[str]:
    """The harness-built Lean certificates of the positive fixture that this
    level cites (a record cites only what the harness commit holds and
    builds; the sealed citations stay at the pinned 19L57G1 commit)."""
    out: set[str] = set()
    for claim in result.native_claims:
        lean = claim.get("lean", [])
        if claim.get("fixture") != "pos" or not isinstance(lean, list):
            continue
        out |= {str(entry["name"]) for entry in lean if isinstance(entry, dict)}
    return sorted(out)


def axioms_report_bytes() -> bytes:
    """``lean/axioms.txt`` restated line by line in the receiving side's
    ``#print axioms`` form.  The content is the harness gate's audit."""
    out = []
    for line in (current_context().lean_path("axioms.txt")).read_text(encoding="utf-8").splitlines():
        name, _, ax = line.partition(":")
        axioms = [a.strip() for a in ax.split(",") if a.strip() and a.strip() != "(none)"]
        out.append(f"'{name.strip()}' depends on axioms: [{', '.join(axioms)}]" if axioms
                   else f"'{name.strip()}' does not depend on any axioms")
    return ("\n".join(out) + "\n").encode("ascii")


def custody_checked(result: LevelResult, tag: str | None, ledger: Mapping[str, Any]) -> None:
    """A research-tree replay (tag ``T``) must carry its custody, and a record
    that carries it must book it in the loss ledger: the witness is
    research-tree evidence, not sealed (``UNBOOKED_CUSTODY`` otherwise)."""
    custody = result.extra.get("witness_custody")
    booked = any(f["field_or_law"] == "source.witness_custody" for f in ledger["fields"])
    if (tag or "").startswith("T") and not custody:
        raise Refusal("UNBOOKED_CUSTODY", f"{result.challenge_id}: a research-tree record with no custody")
    if custody and not booked:
        raise Refusal("UNBOOKED_CUSTODY", f"{result.challenge_id}: the custody is not booked in the loss ledger")


def stub(level: int, result: LevelResult, inputs: Sequence[tuple[str, str, object]],
         tag: str | None = None) -> dict[str, Any]:
    reg = registry()
    row = next(e for e in reg["levels"] if e["level"] == level)
    by = {v.fid: v for v in result.verdicts}
    ledger = loss_ledger_v2(result)
    custody_checked(result, tag, ledger)
    return {
        "authority_effect": "None",
        "awaiting": ["a checker of record for this level", "an adapter to the checker's input schema",
                     "the harness commit holding the adapter and the positive"],
        "carrier_part": result.carrier_part,
        "challenge_id": result.challenge_id,
        "draft_fixtures": [{"id": fid, "input": obj, "native_code": by[fid].code, "role": role}
                           for fid, role, obj in inputs],
        "framing": framing(level, result),
        "inputs": {"receipts_consumed": []},
        "ladder": {"level": level, "registry_version": reg["registry_version"], "row_sha256": row["row_sha256"],
                   "table_sha256": reg["table"]["sha256"]},
        "lean_theorems": lean_theorems(result),
        "loss_ledger": ledger,
        "non_claims": non_claims(result),
        "placement": "the_symbol_game",
        "provenance": {"isolation": "NOT_APPLICABLE", "purity": "NOT_APPLICABLE", "source_blindness": "NOT_BLIND"},
        "receipt_schema": "reach-receipt/1",
        "schema": "level-engine.reach-stub.v1",
    }


def non_claims(result: LevelResult) -> list[str]:
    out = [
        "answers a supplied challenge; not a derivation from the seed",
        "Mode E: the carrier commit is the harness commit in the_symbol_game; 19L57G1 is pinned inside it",
        "no independent convergence with any outside list is claimed",
    ]
    custody = result.extra.get("witness_custody")
    if isinstance(custody, Mapping):
        trees = ", ".join(f"research/{t}" for t in custody["trees"])
        out.append(f"the witness is research-tree evidence ({trees} at the pinned 19L57G1 commit), not sealed; "
                   "it is admitted for a replay under the 19L57G1 key by the author's ruling of 2026-09-25")
    elif result.carrier_part == "repo_content":
        out.append("the sealed Lean the harness cites for this level is at the pinned 19L57G1 commit, "
                   "outside this record's sources")
    if B.caps(result):
        out.append("value clauses are decided outside the grammar (supplied capability)")
    return out


# ---------------------------------------------------------------------------
# The target half
# ---------------------------------------------------------------------------


class Adapter(Protocol):
    """States the engine's fixtures in one target checker's input schema."""

    CHECKER_ID: str
    CLAUSES: tuple[tuple[str, str], ...]
    COEFFICIENT_DOMAIN: Mapping[str, str]
    SORTS: tuple[tuple[str, str], ...]
    UNMAPPED_SORTS: tuple[str, ...]
    STRUCTURE_MAP_REASON: str

    def fixtures(self, result: LevelResult, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]: ...

    def pairs(self, positive: object) -> list[list[str]]: ...


def load_adapter(path: Path) -> Adapter | None:
    if not path.exists():
        return None
    if path.parent == ROOT / "adapters":
        return cast(Adapter, __import__("importlib").import_module(__package__.rsplit(".", 1)[0] + ".adapters." + path.stem))
    # Explicit test-only checker adapters are loaded from the supplied file, never by path search.
    import sys
    spec = importlib.util.spec_from_file_location("level_engine_fixture_adapter_" + path.stem, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(Adapter, module)


def adapter_path(level: int, tag: str | None = None) -> Path:
    return ROOT / "adapters" / f"{tag or f'L{level:03d}'}.py"


def positive_rel(level: int, tag: str | None = None) -> str:
    return "omega_engine_pfp/infrastructure/tower_evidence/level_engine/v2/bindings/generated/reach/" + f"{tag or f'L{level:03d}'}.positive.json"


def complete(st: Mapping[str, Any], result: LevelResult, inputs: Sequence[tuple[str, str, object]],
             adapter: Adapter, checker_id: str, entry: Mapping[str, Any], checker_source: bytes,
             commit: str, sources: Sequence[Mapping[str, str]], lean: Mapping[str, Any] | None,
             tag: str | None = None) -> dict[str, Any]:
    """The full record.  The own negative and its code come from the pinned
    checker itself; everything the target decides is left to it."""
    targets = reach("targets")
    transport = reach("transport")
    canonical = reach("canonical")
    module = targets.load_checker(checker_source, checker_id)
    level = int(st["ladder"]["level"])
    fixtures = [dict(f) for f in adapter.fixtures(result, inputs)]
    for f in fixtures:
        if f["kind"] == "positive":
            f["source_path"] = positive_rel(level, tag)
    fixtures.append({"expected_code": module.OWN_NEGATIVE_CODE, "id": "own-neg", "kind": "own_negative",
                     "payload": module.OWN_NEGATIVE, "row_sha256": st["ladder"]["row_sha256"]})
    positive = next(f["payload"] for f in fixtures if f["kind"] == "positive")
    squares = compatibility_squares(adapter, inputs, positive)
    carrier = {"commit": commit, "part": st["carrier_part"], "repo": CARRIER, "sources": list(sources)}
    ledger = transport.seal_ledger(loss_ledger_v2(result, adapter.UNMAPPED_SORTS, adapter.COEFFICIENT_DOMAIN,
                                                  getattr(adapter, "LOSS_ROWS", ())))
    adapter_rel = adapter_path(level, tag).relative_to(current_context().require_repository()).as_posix()
    adapter_sha = next((s["sha256"] for s in sources if s["path"] == adapter_rel), "")
    cost = next((v.witness.cost[0] for v in result.verdicts if v.role == "positive" and v.witness is not None
                 and v.witness.cost is not None), 0)
    certificate = transport.seal_certificate({
        "authority_effect": "None",
        "c1_identity_custody": {"adapter": {"path": adapter_rel, "sha256": adapter_sha},
                                "coefficient_domain": dict(adapter.COEFFICIENT_DOMAIN), "same_carrier": False,
                                "source_manifest_sha256": transport.manifest_digest(list(sources))},
        "c2_typed_map": {"kind": "SORT_MAP", "pairs": adapter.pairs(positive),
                         "sorts": [{"source": a, "target": b} for a, b in adapter.SORTS],
                         "unmapped_sorts": list(adapter.UNMAPPED_SORTS)},
        "c3_compatibility": {"not_applicable_reason": None if squares else (adapter.STRUCTURE_MAP_REASON or None),
                             "squares": squares},
        "c4_goal_and_moves": {"cost": {"source_measure": "mu1", "target_convention": "declared-cost/v1",
                                       "value": f"{cost}/1"},
                              "source_goal_sha256": B.restatement_digest(result.challenge_id),
                              "target_goal_sha256": st["ladder"]["row_sha256"]},
        "c5_target_verification": {"source_admission_is_provenance_only": True,
                                   "witness_sha256": canonical.digest_obj(positive)},
        "c6_loss_and_authority": {"loss_ledger": ledger, "reframe": {"child": None, "decision": "NONE"}},
        "carrier": {"commit": commit, "part": st["carrier_part"], "repo": CARRIER},
        "disposition": "TARGET_REPLAY_REQUIRED",
        "schema": transport.SCHEMA_ID,
        "status": "PROPOSED",
        "target": {"checker_id": checker_id, "level": level, "registry_version": st["ladder"]["registry_version"],
                   "repo": "the_symbol_game", "row_sha256": st["ladder"]["row_sha256"]},
    })
    return {
        "authority_effect": "None",
        "carrier": carrier,
        "checker": {"commit": entry["commit"], "id": checker_id, "path": entry["path"], "sha256": entry["sha256"]},
        "clauses": [{"code": code, "id": cid} for cid, code in adapter.CLAUSES],
        "declared_fixture_count": len(fixtures),
        "fiber": None,
        "fixtures": fixtures,
        "framing": st["framing"],
        "gates": None,
        "inputs": st["inputs"],
        "ladder": st["ladder"],
        "lean": lean,
        "non_claims": st["non_claims"],
        "placement": st["placement"],
        "provenance": st["provenance"],
        "receipt_schema": st["receipt_schema"],
        "stage_change": None,
        "transport": certificate,
    }


def compatibility_squares(adapter: Adapter, inputs: Sequence[tuple[str, str, object]],
                          positive: object) -> list[dict[str, str]]:
    """Criterion 3 for a level that names structure maps: for each map, the
    digest of the engine's map carried through the typed map (left) and of
    the target's map read from the positive (right).  An adapter that states
    no ``squares`` gives none, and its N/A reason stands."""
    squares = getattr(adapter, "squares", None)
    if squares is None:
        return []
    canonical = reach("canonical")
    source = next(obj for _, role, obj in inputs if role == "positive")
    return [{"lhs_sha256": canonical.digest_obj(lhs), "rhs_sha256": canonical.digest_obj(rhs), "structure_map": name}
            for name, lhs, rhs in squares(source, positive)]


def preflight(record: Mapping[str, Any], resolver: object, checkers: Mapping[str, Any] | None = None) -> Any:
    """The receiving side's own ``check_record`` on a completed record.  The
    result is a local receipt, never stored or cited."""
    receipt = reach("receipt")
    gates = reach("gates")
    canonical = reach("canonical")
    carriers = resource_registry("carriers", version="v2")
    assert isinstance(carriers, dict)
    ctx = receipt.Context(resolver=resolver, stage_registry=registry(),
                          checkers=checkers_of_record() if checkers is None else checkers,
                          carriers=carriers["carriers"], gated_steps=gates.GATED_STEPS, level_texts={})
    return receipt.check_record(canonical.canonical_bytes(dict(record)), ctx)


def lean_block(read: Callable[[str], bytes | None], names: Sequence[str]) -> dict[str, Any] | None:
    """The record's Lean block: the harness-built certificates, the restated
    axiom report, and each statement's digest as the receiving side cuts it."""
    if not names:
        return None
    receipt = reach("receipt")
    canonical = reach("canonical")
    report_rel = "omega_engine_pfp/infrastructure/tower_evidence/level_engine/v2/bindings/generated/reach/axioms.reach.txt"
    report = read(report_rel)
    if report is None:
        return None
    rels = {n: lean_source_rel(n) for n in names}
    texts: dict[str, bytes] = {}
    for rel in sorted(set(rels.values())):
        src = read(rel)
        if src is None:
            return None
        texts[rel] = src
    return {
        "report": {"path": report_rel, "sha256": canonical.digest(report)},
        "sources": [{"path": rel, "sha256": canonical.digest(src)} for rel, src in sorted(texts.items())],
        "theorems": [{"name": n, "source_path": rels[n],
                      "statement_sha256": canonical.digest(
                          str(receipt.statement_text(texts[rels[n]].decode("utf-8"), n)).encode("utf-8"))}
                     for n in names],
    }


def lean_source_rel(name: str) -> str:
    """The certificate module a harness-built theorem is declared in: the
    payload file named after the theorem's first component."""
    module = name.split(".", 1)[0]
    try:
        source = current_context().lean_path(f"{module}.lean")
    except ContextRefusal as exc:
        # A module outside the packaged Lean closure is no certificate module.
        raise KeyError(f"no certificate module for {name}") from exc
    if not source.is_file():
        raise KeyError(f"no certificate module for {name}")
    return source.relative_to(current_context().require_repository()).as_posix()



def stub_bytes(level: int, result: LevelResult, inputs: Sequence[tuple[str, str, object]],
               tag: str | None = None) -> bytes:
    return dumps(stub(level, result, inputs, tag))
