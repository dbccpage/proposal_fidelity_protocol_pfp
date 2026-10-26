"""The lift certificate in the receiving side's shape.  Never ports.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from engine.canon import dumps, sha256_tag
from engine.kinds import req_json
from engine.ladder_cert import LadderResult, StepResult, load_pinned
from engine.regimek import RegimeK
from engine.search import delta_json
from engine.stage import ConditionResult, StageProposal, licensed


def to_lift_certificate(sc: StageProposal, s: RegimeK, results: Sequence[ConditionResult]) -> dict[str, object]:
    """C05's ``mssn.lift-certificate.v1`` field set, filled from the proposal."""
    return {
        "authority_effect": "None",
        "conditions": [{"number": r.number, "passed": r.passed, "reason": r.reason} for r in results],
        "context_witness": list(sc.context_witness) if sc.context_witness else None,
        "down_rule": {
            "defaulted": sc.down.defaulted,
            "non_descent_refusals": sc.down.non_descent_cases,
            "old_image_identity_cases": sc.down.old_image_cases,
        },
        "exhibit_at_target": sha256_tag(dumps(delta_json(sc.answer))),
        "extension_class": {"digest": sc.family_sha256, "members": [t.name for t in sc.family]},
        "licensed": licensed(results),
        "minimality": {
            "cost": f"{sc.cost}/1",
            "tied_minima": list(sc.chosen),
        },
        "new_pair": None,
        "nontrivial_action": sc.nontrivial,
        "protected_distinctions": {"count": len(sc.protected), "digest": sha256_tag(dumps(list(sc.protected)))},
        "residual": {"requirements": [req_json(q) for q in s.reqs if q.rid in sc.residual]},
        "same_level_search": sc.attempts.to_json(),
        "schema": "mssn.lift-certificate.v1",
        "source_stage": sc.source.name,
        "stop": sc.stop,
        "target_stage": sc.target.name,
    }


# ---------------------------------------------------------------------------
# A reading ladder's stage changes (the carrier's own rungs, not levels)
# ---------------------------------------------------------------------------


def _ladder_step(r: StepResult, step: Mapping[str, object], class_sha: str, members: list[str]) -> dict[str, object]:
    f = r.facts
    down = f["down_rule"]
    assert isinstance(down, dict)
    mx = f["minimal_extension"]
    assert isinstance(mx, dict)
    prot = f["protected"]
    assert isinstance(prot, dict)
    cw = f["context_witness"]
    return {
        "authority_effect": "None",
        "conditions": [c.to_json() for c in r.conditions],
        "context_witness": cw,
        "down_rule": {
            "defaulted": down["defaulted"],
            "map": down["map"],
            "non_descent_refusals": down["non_descent_refusals"],
            "old_image_identity_cases": down["old_image_identity_cases"],
            "old_image_programs": down["old_image_programs"],
        },
        "exhibit_at_target": sha256_tag(dumps(step["answer"])),
        "extension_class": {"digest": class_sha, "members": members},
        "lean": f["lean"],
        "licensed": r.licensed,
        "minimality": {"cost": f"{mx['cost']}/1", "nonminimal_probe": mx["nonminimal_probe"],
                       "tied_minima": mx["tied_minima"], "tied_minima_sha256": mx["tied_minima_sha256"]},
        "new_pair": None if not isinstance(cw, dict) else [cw["x"], cw["y"]],
        "nontrivial_action": {"price": f["price"]},
        "protected_distinctions": {"count": prot["distinct_old_tapes"], "digest": prot["tapes_sha256"],
                                   "programs_by_start": prot["programs_by_start"]},
        "residual": {"requirements": [{"kind": "write_the_tape", "tape": f["demand"],
                                       "pointer": step["demand_pointer"]}],
                     "dual_witnesses": f["dual_witnesses"]},
        "same_level_search": f["same_level_search"],
        "schema": "mssn.lift-certificate.v1",
        "source_stage": r.facts["source"],
        "step": r.step,
        "stop": step["stop"],
        "survival": f["survival"],
        "target_stage": r.facts["target"],
    }


def ladder_document(result: LadderResult, props: Mapping[str, object], sealed_commit: str) -> dict[str, object]:
    """The carrier's own-ladder lift records, with the certified depth the
    certifier computes.  Recorded, not counted: counting is the author's act
    (ruling D4)."""
    pinned = load_pinned(props)
    raw = pinned.class_doc["members"]
    assert isinstance(raw, list)
    members = [str(m["name"]) for m in raw]
    steps = props["steps"]
    assert isinstance(steps, list)
    carrier = props["carrier"]
    assert isinstance(carrier, dict)
    return {
        "authority_effect": "None",
        "carrier": {"commit": sealed_commit, "part": "harness_computation", "repo": "19L57G1",
                    "tree": carrier["tree"], "evidence": carrier["evidence"]},
        "certificates": [_ladder_step(r, s, pinned.class_sha256, members) for r, s in zip(result.steps, steps)],
        "chain": result.chain.to_json(),
        "computed_depth": result.depth,
        "counting": "recorded, not counted: a lift counts toward depth only when every condition holds and the "
                    "author accepts it (ruling D4); the computed depth is the longest licensed prefix of the chain",
        "diagnostic_harness_restriction": {
            "note": "the same steps with the harness's partial restriction in place of the carrier's down map; "
                    "not the carrier's map, so it never enters a verdict or the depth",
            "steps": [{"conditions": [c.to_json() for c in r.conditions], "licensed": r.licensed,
                       "step": r.step, "down_rule": r.facts["down_rule"]} for r in result.diagnostics],
        },
        "lean_status": "cited from the carrier's committed reliance record at the pin; the tree's Lean is a manual "
                       "receipt, not a gated one",
        "schema": "level-engine.ladder-lifts.v1",
    }
