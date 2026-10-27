"""The bootstrap levels, the outward writers, the pre-flight and hygiene."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

import pfp.infrastructure.tower_research.level_engine.outward.bundles as B
from operations.domain.level_engine_context import (
    current_context,
)
from operations.use_cases.level_engine.bind import TREE_REPLAYS
from operations.infrastructure.level_engine_ports import ports
from operations.use_cases.level_engine.bootstrap import build
from operations.use_cases.level_engine.research_engine.canon import dumps, sha256_tag
from operations.use_cases.level_engine.research_engine.components import available
from operations.use_cases.level_engine.research_engine.errors import IntakeRefusal
from operations.use_cases.level_engine.research_engine.hygiene import (
    report,
    scan,
    scan_text,
)
from operations.use_cases.level_engine.research_engine.level import (
    ROOT,
    FixtureVerdict,
    LevelResult,
    apply_mutation,
    check_expectations,
    check_kill_rules,
    load_fixtures,
    load_spec,
    run_level,
)
from operations.use_cases.level_engine.research_engine.preflight import (
    CheckerPin,
    bar,
    load_checker,
    preflight,
    run_checker,
)

# Round P5's harness levels, cheapest first as the band work orders rank them.
P5 = ("mirror_pairs", "unit_rows", "joint_rank", "size_keeping", "signed_totals", "table_roots", "joint_payoffs",
      "stable_profiles", "witnessed_triples", "overlap_choices", "commuting_checks", "step_squares",
      "answer_keeping", "face_products", "named_frames", "two_party_bound", "walk_transport", "side_reduction",
      "split_weights", "square_one", "far_blind", "ordered_splits", "outward_bounds", "rim_cochains",
      "dual_endpoints", "scale_steps", "same_background")
# Answered by derivability alone: nothing is decided over values.
P5_NATIVE = ("step_squares",)
# Round P6's harness levels, in the order they were built.
P6: tuple[str, ...] = ("filtered_pages", "class_operations", "closed_faces", "bound_axioms", "confirmed_runs",
      "hinge_deficits", "isolated_roots", "rated_limits", "refined_sums", "glued_patches",
      "reindexed_fibres", "associator_tables", "use_once_terms", "forced_differences",
      "merge_tables", "exact_grants", "ordered_log", "signed_cells", "budgeted_releases",
      "patched_views", "serial_receipts", "typed_queries", "wired_handshakes", "scoped_release",
      "narrowing_handoffs", "limited_runs", "mutant_challenges", "seeded_shrinks",
      "differential_pairs", "resolution_claims", "lineage_pins", "composed_errors")
P6_NATIVE: tuple[str, ...] = ("glued_patches", "merge_tables", "exact_grants")
P7B: tuple[str, ...] = ("recomputed_labels", "formal_inverses", "coloured_slots", "both_round_trips", "weight_slopes",
                        "paired_frames", "signed_chains", "rerun_calls", "grounded_traces", "covered_clauses",
                        "renamed_formulas", "compiled_branches", "counted_runs", "counted_trials", "killed_mutants")
P7B_NATIVE: tuple[str, ...] = ("formal_inverses",)
BAND = ("cycle_words", "flow_certificate", "scope_fence", "three_way_split", "table_polynomial", "loop_products",
        "step_weights", "weighted_update") + P5 + P6 + P7B
REPLAYS = ("positioned_join", "stage_chain", "conservative_embedding", "carried_reversal", "route_replay",
           "bounded_mask", "host_bound_verdict", "tagged_digest", "boundary_chain", "observed_blocks", "granted_steps")
TREE_CIDS: tuple[str, ...] = tuple(str(m["challenge_id"]) for _, m in sorted(TREE_REPLAYS.items()))
LEVELS = ("bare_inscription", "first_separation", "edge_endpoints", "cell_faces", "cell_orientation",
          "distance_form") + BAND + REPLAYS + TREE_CIDS
CHECKERS = Path(__file__).resolve().parent / "checkers"


@pytest.fixture(scope="module")
def results() -> dict[str, LevelResult]:
    return {cid: run_level(cid) for cid in LEVELS}


# ---------------------------------------------------------------- per level


@pytest.mark.parametrize("cid", LEVELS)
def test_every_level_meets_its_frozen_expectations(cid: str, results: dict[str, LevelResult]) -> None:
    r = results[cid]
    found = B.mismatches(r)
    assert found == (), " ".join(found)


@pytest.mark.parametrize("cid", LEVELS)
def test_every_payload_module_a_spec_imports_is_a_named_source(cid: str) -> None:
    import ast

    tree = ast.parse((ROOT / "payload" / cid / "spec.py").read_text(encoding="utf-8"))
    # Since the relocation a spec imports its payload helpers relatively
    # (``from ..shared import``, one package up from its own folder).
    mods = {("payload." + n.module) if n.level == 2 else n.module for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom) and n.module
            and (n.level == 2 or (n.level == 0 and n.module.startswith("payload.")))}
    paths = {e["path"] for e in B.harness_sources(cid)}
    missing = sorted(m for m in mods if m.replace(".", "/") + ".py" not in paths)
    assert missing == [], "UNNAMED_SOURCE: " + ", ".join(missing)


def test_statuses_and_computed_answer_types(results: dict[str, LevelResult]) -> None:
    got = {cid: (B.computed_answer_type(r), B.status(r)) for cid, r in results.items()}
    assert got == {
        "bare_inscription": ("A", "EXPECTED"),
        "first_separation": ("D", "EXPECTED"),
        "edge_endpoints": ("D", "EXPECTED"),
        "cell_faces": ("D", "EXPECTED"),
        "cell_orientation": ("D", "EXPECTED"),
        "distance_form": ("M", "EXPECTED"),
        "cycle_words": ("M", "EXPECTED"),
        "flow_certificate": ("M", "EXPECTED"),
        "scope_fence": ("M", "EXPECTED"),
        "three_way_split": ("M", "EXPECTED"),
        "table_polynomial": ("M", "EXPECTED"),
        "loop_products": ("M", "EXPECTED"),
        "step_weights": ("M", "EXPECTED"),
        "weighted_update": ("M", "EXPECTED"),
        "positioned_join": ("M", "EXPECTED"),
        "stage_chain": ("M", "EXPECTED"),
        "conservative_embedding": ("M", "EXPECTED"),
        "carried_reversal": ("M", "EXPECTED"),
        "route_replay": ("M", "EXPECTED"),
        "bounded_mask": ("M", "EXPECTED"),
        "host_bound_verdict": ("M", "EXPECTED"),
        "tagged_digest": ("M", "EXPECTED"),
        "boundary_chain": ("M", "EXPECTED"),
        "observed_blocks": ("M", "EXPECTED"),
        "granted_steps": ("M", "EXPECTED"),
        **{cid: ("D" if cid in P5_NATIVE else "M", "EXPECTED") for cid in P5},
        **{cid: ("D" if cid in P6_NATIVE else "M", "EXPECTED") for cid in P6},
        **{cid: ("D" if cid in P7B_NATIVE else "M", "EXPECTED") for cid in P7B},
        **{cid: ("M", "EXPECTED") for cid in TREE_CIDS},
    }


def test_first_separation_reproduces_the_sealed_tie_structure(results: dict[str, LevelResult]) -> None:
    lin: Any = results["first_separation"].extra["lineages"]
    assert {k: v["engine_classes"] for k, v in lin.items()} == {"L.mu1": 3, "L.mu2": 1, "F.mu1": 5, "F.mu2": 1}
    assert all(v["agree"] for v in lin.values())
    st: Any = results["first_separation"].extra["state_level"]
    assert st == {"L_admits_inscription": False, "F_admits_inscription": True}
    tr: Any = results["first_separation"].extra["transport"]
    assert tr["distinct_packets_over_all_classes"] == 1


def test_orientation_witness_grades(results: dict[str, LevelResult]) -> None:
    by: dict[str, Any] = {v.fid: v for v in results["cell_orientation"].verdicts}
    assert by["pos"].witness.grade == "unique_class" and len(by["pos"].witness.minima) == 2
    assert by["named_sign"].witness.grade == "unique_class"
    assert by["named_sign_uneven"].witness.grade == "tie" and len(by["named_sign_uneven"].witness.classes) == 2
    ex = by["near_book"].witness.exhaustion
    assert (ex.status, ex.class_size, ex.class_size_expected, ex.bound) == ("CLOSED", 42, 42, 3)


def test_distance_form_value_clauses_are_decided_in_lean(results: dict[str, LevelResult]) -> None:
    r = results["distance_form"]
    assert r.missing_components == ()
    assert r.extra["clause_evidence"] == {
        "complete": "COMPUTED", "symmetric": "COMPUTED", "one_value": "COMPUTED", "typed": "COMPUTED",
        "diagonal_zero": "LEAN", "form_positive": "LEAN",
    }
    assert len(r.native_claims) == 15 and B.evidence_ceiling(r) == "LEAN_HARNESS_BUILD"
    fixtures = {str(c["fixture"]) for c in r.native_claims}
    assert fixtures == {"pos", "own_neg", "near_degenerate", "near_diagonal", "mut"}
    for c in r.native_claims:
        lean: Any = c["lean"]
        assert set(lean[0]["axioms"]) <= {"propext", "Quot.sound"}
    census = {c: k for c, k, _ in r.census}
    assert census == {"complete": "derivability", "symmetric": "derivability", "one_value": "derivability",
                      "typed": "derivability", "diagonal_zero": "decoded", "form_positive": "decoded"}
    vals: Any = r.extra["decoded_values"]
    assert vals["own_neg"]["first_nonpositive_minor"] == 2
    assert vals["near_degenerate"]["first_nonpositive_minor"] == 3
    assert vals["pos"]["leading_minors"] == ["1/1", "3/4", "1/2"]
    assert B.caps(r) == ["CAP-SUPPLIED:diagonal_zero", "CAP-SUPPLIED:form_positive"]
    no_lean = run_level("distance_form", have=frozenset(c for c in available() if not c.startswith("lean.")))
    assert "lean.exact.qn" in no_lean.missing_components and B.status(no_lean) == "UNRESOLVED"
    assert "lean:DistanceForm.pos_form_positive" in no_lean.missing_components
    withdrawn = run_level("distance_form", have=available() - {"py.exact.q"})
    pos = next(v for v in withdrawn.verdicts if v.fid == "pos")
    assert not pos.satisfied and dict(pos.decoded)["form_positive"] == "MISSING_COMPONENT:py.exact.q"


def test_band_levels_compute_their_values(results: dict[str, LevelResult]) -> None:
    vals: Any = {cid: results[cid].extra.get("decoded_values") for cid in BAND}
    assert vals["scope_fence"]["pos"] == {"determinant": "0/1", "value": "1/1"}
    assert vals["scope_fence"]["near_value"] == {"determinant": "-7/1", "value": "2/1"}
    assert vals["table_polynomial"]["pos"]["polynomial_high_to_low"] == ["1/1", "-1/1", "-1/1"]
    assert vals["table_polynomial"]["pos"]["at_fences"] == [["-1/1", "1/1"]]
    assert vals["table_polynomial"]["own_neg"]["at_roots"] == ["-19/250000"]
    assert vals["three_way_split"]["pos"]["rebuilt"] == vals["three_way_split"]["pos"]["load"]
    assert vals["loop_products"]["pos"]["leading_minors"] == ["1/1", "3/4", "1/2", "5/16"]
    bracket = vals["loop_products"]["own_neg"]["loops"]["bracket:10:11"]
    assert bracket["declared_closed"] and not bracket["ordered_product_is_identity"]
    assert set(bracket["signed_count"].values()) == {0}
    assert {r["least_span"] for r in vals["cycle_words"]["pos"]["rings"].values()} == {1, 2}
    assert vals["weighted_update"]["pos"] == {"evidence": ["1/2", "1/3"],
                                              "weights": [["1/3", "2/3"], ["0/1", "1/1"]]}
    assert vals["step_weights"]["own_neg"] == {"row_sums": ["3/2", "1/1"]}
    assert vals["flow_certificate"]["near_gap"] == {"divergence": ["0/1", "0/1", "0/1"], "dual": "1/1",
                                                    "primal": "3/1"}
    for cid in P5_NATIVE:
        r = results[cid]
        assert r.missing_components == () and {k for _, k, _ in r.census} == {"derivability"}
    for cid in ("cycle_words", "flow_certificate", "scope_fence", "three_way_split", "table_polynomial",
                "loop_products", "step_weights", "weighted_update") + tuple(c for c in P5 if c not in P5_NATIVE):
        r = results[cid]
        assert r.missing_components == () and B.evidence_ceiling(r) == "LEAN_HARNESS_BUILD"
        ev: Any = r.extra["clause_evidence"]
        assert {c for c, k in ev.items() if k == "LEAN"} == {c for c, k, _ in r.census if k == "decoded"}
        assert all(set(c["lean"][0]["axioms"]) <= {"propext", "Quot.sound"} for c in r.native_claims)  # type: ignore[index]
    for cid in BAND:
        assert all(v.witness is not None and v.witness.exhaustion.class_size in (0, 1)
                   for v in results[cid].verdicts)


def test_round_p5_levels_compute_their_values(results: dict[str, LevelResult]) -> None:
    vals: Any = {cid: results[cid].extra["decoded_values"] for cid in P5}
    assert vals["mirror_pairs"]["pos"]["product"] == ["-2/1", "1/1"]
    assert vals["table_roots"]["pos"] == {"polynomial_low_to_high": ["3/1", "-4/1", "1/1"]}
    assert vals["joint_rank"]["pos"] == {"rank": 2, "size": "1/1"}
    assert vals["joint_rank"]["own_neg"]["rank"] == 1
    assert vals["commuting_checks"]["pos"] == {"readings": ["10", "11", "01"]}
    assert vals["two_party_bound"]["pos"] == {"local_bound": "2/1", "total": "14/5"}
    assert vals["face_products"]["pos"] == {"ordered_product": [2, 0, 1]}
    assert vals["face_products"]["near_order"] == {"ordered_product": [1, 2, 0]}
    assert vals["rim_cochains"]["pos"] == {"rim_edges": [0, 1, 2, 3], "rim_vertices": [0, 1, 2, 3]}
    assert vals["same_background"]["pos"] == {"answer": [1], "consistent": [0]}


def test_round_p6_levels_compute_their_values(results: dict[str, LevelResult]) -> None:
    """Prediction L2's values, computed by the engine."""
    vals: Any = {cid: results[cid].extra.get("decoded_values") for cid in P6}
    assert vals["filtered_pages"]["pos"]["pages"] == {"1": [0, 1, 2, 3, 4, 5, 6], "2": [0, 1, 2, 3, 4, 5, 6],
                                                      "3": [0]}
    assert vals["class_operations"]["pos"]["value_class_nonzero"] == [True]
    assert vals["closed_faces"]["own_neg"]["closure"] == [1, 2, 0]
    assert vals["hinge_deficits"]["pos"] == {"deficits": ["1/2", "1/2", "1/2", "1/2"], "total": "2/1"}
    assert vals["isolated_roots"]["pos"] == {"chain_length": 3, "changes": [1, 0], "end_values": ["-1/1", "2/1"]}
    assert vals["rated_limits"]["pos"]["sides_low_to_high"] == [[], ["0/1", "4/1"]]
    assert vals["refined_sums"]["pos"] == {"error_poly_low_to_high": ["-1/2", "1/6"], "integral": "1/3"}
    assert vals["bound_axioms"]["pos"]["axioms"] == ["p0", ["->", "p0", "p1"]]
    assert vals["confirmed_runs"]["pos"] == {"value": 7}
    for cid in P6_NATIVE:
        assert {k for _, k, _ in results[cid].census} == {"derivability"}


def test_round_p7b_levels_host_texts_and_decide_them(results: dict[str, LevelResult]) -> None:
    """Round P7B: the apparatus levels that need text host it, and every new
    level meets its frozen expectations with every clause claimed natively
    or decoded; 025 is answered by derivability alone."""
    from operations.use_cases.level_engine.research_engine.level import load_fixtures

    with_texts = {cid for cid in P7B if any(fx.structure.texts for fx in load_fixtures(ROOT / "payload" / cid))}
    assert {"signed_chains", "rerun_calls", "grounded_traces", "covered_clauses", "counted_runs",
            "counted_trials"} <= with_texts
    assert {k for _, k, _ in results["formal_inverses"].census} == {"derivability"}
    for cid in P7B:
        assert B.status(results[cid]) == "EXPECTED" and results[cid].missing_components == ()


def test_replays_of_sealed_evidence(results: dict[str, LevelResult]) -> None:
    join: Any = results["positioned_join"].extra["peak"]
    assert (join["source"], join["join"], join["left_step"], join["right_step"]) == ("hha", "h", [0, 3], [1, 4])
    chain: Any = results["stage_chain"].extra["chain"]
    assert [s["generators"] for s in chain["stages"]] == [["<>"], ["<>", "<a>"], ["<>", "<a>", "<ab>"]]
    for cid in REPLAYS:
        r = results[cid]
        assert r.carrier_part == "repo_content" and B.evidence_ceiling(r) == "LEAN_CITED_FROM_SEALED_REPORT"
        assert r.sources and all(set(c["lean"][0]["axioms"]) <= {"propext", "Quot.sound"}  # type: ignore[index]
                                 for c in r.native_claims)
    spec: Any = load_spec("positioned_join")
    assert spec.apply("hha", (0, 99)) is None and spec.apply("hab", (0, 4)) is None
    assert spec.decide({**join, "rules": []}) == spec.CLAUSES
    assert spec.decide({**join, "left_arm": "x"}) == ("steps_replayed",)
    assert spec.decide({**join, "left_arm": [[5, 0]]}) == ("steps_replayed",)


def test_the_q_level_replays_state_their_sealed_facts(results: dict[str, LevelResult]) -> None:
    emb: Any = results["conservative_embedding"].extra
    assert emb["old_stage"] == [["<x>", "<y>"], []]
    valid = [c for c in emb["candidates"] if c["sealed_valid"]]
    assert len(valid) == 1 and valid[0]["new_stage"] == [["<x>", "<y>", "<z>"], [["<x>", "<z>"]]]
    rev: Any = results["carried_reversal"].extra
    assert rev == {"closure_of_directed": ["a01"], "dagger_on_directed": []}
    route: Any = results["route_replay"].extra
    assert set(route["balanced"]) == {"0/1"}
    mask: Any = results["bounded_mask"].extra
    assert mask == {"exhaustive_reports_obstruction": False, "menu_length": 3, "repairing_positions": [1, 2],
                    "truncated_at_one_reports_obstruction": True}
    assert results["host_bound_verdict"].extra == {"class_counts": {"F": 5, "L": 3}}
    assert results["tagged_digest"].extra == {"counts": [2, 2], "words": ["11", "00", "00"]}
    join: Any = results["positioned_join"].extra["peaks_with_an_empty_arm"]
    assert join == {"searched_up_to_length": 4, "sources": []}
    spec: Any = load_spec("route_replay")
    pos = spec.positive()
    assert spec.decide({**pos, "cycle": [0, 9]}) == ("repeat_replayed",)
    assert spec.decide({**pos, "trace": [[7, "exact"]], "cycle": [0, 0]}) == ("repeat_replayed",)
    tag: Any = load_spec("tagged_digest")
    assert not tag.decodes("t0", "n") and not tag.decodes("t0", {"n": True})
    mask_spec: Any = load_spec("bounded_mask")
    assert mask_spec.decide({**mask_spec.positive(), "budget": "six"}) == ("within_budget",)
    assert mask_spec.decide({**mask_spec.positive(), "formula": ["not", ["eq", 0, 0]]})[0] == "menu_replayed"
    emb_spec: Any = load_spec("conservative_embedding")
    assert emb_spec.decide({**emb_spec.positive(), "old_relations": [["<x>", "<q>"]]}) == ("old_replayed",)


def test_the_band_two_replays_state_their_sealed_facts(results: dict[str, LevelResult]) -> None:
    chain: Any = results["boundary_chain"].extra
    assert chain == {"cells_by_degree": [5, 7, 4, 1], "signless_composites_vanish": False}
    blocks: Any = results["observed_blocks"].extra["readings"]
    assert sum(1 for r in blocks if not set(map(tuple, r["protected"])) & set(map(tuple, r["ledger"]))) == 1
    steps: Any = results["granted_steps"].extra
    assert steps == {"effect_rows": {"add_view": ["augment", "spend"], "mark": ["spend"], "note": []},
                     "grants": {"licensed": ["augment", "spend"], "unlicensed": ["spend"]}}
    spec: Any = load_spec("granted_steps")
    assert spec.decide({**spec.positive(), "edges": [["e1", "nowhere", ["note"]]]}) == ("edges_progress",)


def test_bare_inscription_is_apparatus_with_native_inertia(results: dict[str, LevelResult]) -> None:
    r = results["bare_inscription"]
    assert r.census == (("bytes_exact", "apparatus", ()),)
    assert r.extra["native"] == {"contexts_after_supply": 0, "supply_is_inert": True}
    assert r.carrier_part == "repo_content" and B.evidence_ceiling(r) == "LEAN_CITED_FROM_SEALED_REPORT"


# ---------------------------------------------------------------- fixture intake


def _payload(tmp: Path, fixtures: list[dict[str, object]], mutation: dict[str, object] | None = None) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "instance.json").write_bytes(dumps({"fixtures": fixtures}))
    if mutation is not None:
        (tmp / "mutation.json").write_bytes(dumps(mutation))
    return tmp


S = {"sorts": [["node", 2]], "symbols": [{"name": "arc", "sorts": ["node", "node"]}], "tuples": [["arc", [0, 1]]]}


def test_fixture_intake_refusals(tmp_path: Path) -> None:
    pos = {"id": "pos", "role": "positive", "structure": S}
    neg = {"id": "neg", "role": "own_negative", "structure": S}
    cases = [
        ([pos], None, "MISSING_NEGATIVE"),
        ([neg], None, "MISSING_POSITIVE"),
        ([], None, "EMPTY_FIXTURE"),
        ([pos, neg, {**neg, "id": "pos"}], None, "MALFORMED_FIXTURE"),
        ([pos, {**neg, "role": "other"}], None, "MALFORMED_FIXTURE"),
        ([pos, {**neg, "structure": {}}], None, "EMPTY_FIXTURE"),
        ([pos, neg], {"id": "m", "of": "pos", "violates": "x"}, "MUTATION_IS_IDENTITY"),
        ([pos, neg], {"id": "m", "of": "pos", "violates": "x", "remove_tuples": [["arc", [1, 0]]]}, "MALFORMED_FIXTURE"),
    ]
    for k, (fx, mut, code) in enumerate(cases):
        with pytest.raises(IntakeRefusal) as e:
            load_fixtures(_payload(tmp_path / str(k), fx, mut))  # type: ignore[arg-type]
        assert e.value.code == code, k


def test_expectation_and_kill_rule_checks() -> None:
    fx = load_fixtures(ROOT / "payload" / "edge_endpoints")
    good = run_level("edge_endpoints").verdicts
    assert check_expectations("edge_endpoints", good) == () and check_kill_rules(fx, good) == ()
    passed = tuple(FixtureVerdict(v.fid, v.role, True, True, "ACCEPT", ()) for v in good)
    out = check_expectations("edge_endpoints", passed)
    assert "RR-FIXTURE-PASSED:own_neg" in out and "EXPECTATION_MISMATCH:near_source" in out
    assert "EXPECTATION_MISMATCH:pos:grade" in out
    assert check_expectations("edge_endpoints", good[:1] + (FixtureVerdict("zz", "extra", True, True, "ACCEPT", ()),))[-1] == "EXPECTATION_UNUSED:own_neg"
    assert "EXPECTATION_MISSING:zz" in check_expectations("edge_endpoints", (FixtureVerdict("zz", "extra", True, True, "ACCEPT", ()),))
    wrong = tuple(FixtureVerdict(v.fid, v.role, v.admitted, False, "FAILS:other", ("other",)) for v in good)
    kills = check_kill_rules(fx, wrong)
    assert "RR-WRONG-REASON:near_source" in kills and "RR-NO-FLIP:mut" in kills


def test_mutation_applies_to_the_positive() -> None:
    fx = load_fixtures(ROOT / "payload" / "edge_endpoints")
    pos = fx[0]
    m = apply_mutation(pos, {"id": "m2", "of": "pos", "violates": "protect", "add_tuples": [["arc", [2, 1]]]})
    assert m.role == "mutation" and ("arc", (2, 1)) in m.structure.tuples


# ---------------------------------------------------------------- outward records


def test_records_are_byte_identical_and_level_free(tmp_path: Path) -> None:
    a = build(tmp_path / "a", ports())
    b = build(tmp_path / "b", ports())
    assert a == b
    for rel in a:
        assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes()
        if rel.startswith("bundles/"):
            doc = json.loads((tmp_path / "a" / rel).read_text(encoding="utf-8"))
            assert "level" not in _keys(doc), rel


def _keys(obj: object) -> set[str]:
    if isinstance(obj, dict):
        return set(obj) | {k for v in obj.values() for k in _keys(v)}
    if isinstance(obj, list):
        return {k for v in obj for k in _keys(v)}
    return set()


def test_transport_collapse_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(B, "to_target", lambda structure, protected: {"sorts": structure["sorts"]})
    with pytest.raises(IntakeRefusal) as e:
        B.check_injective(B.fixture_inputs("cell_faces"))
    assert e.value.code == "RR-TRANSPORT-COLLAPSE"


def test_certificate_envelope_and_loss_commitment(results: dict[str, LevelResult]) -> None:
    r = results["cell_faces"]
    binding = json.loads((current_context().historical_path("bindings") / "L003.json").read_text(encoding="utf-8"))
    inputs = B.fixture_inputs("cell_faces")
    cert = B.transport_certificate(3, binding, r, "sha256:" + "0" * 64, "sha256:" + "1" * 64, inputs)
    env = cert.pop("envelope")
    assert isinstance(env, dict)
    assert env["payload_digest"] == sha256_tag(b"mssn.transport-certificate\0" + dumps(cert))
    c3: Any = cert["c3_compatibility"]
    assert c3["not_applicable_reason"] is None
    loss = B.loss_ledger(r)
    commitment = loss.pop("commitment")
    body = {k: v for k, v in loss.items() if k not in ("authority_effect", "schema")}
    assert commitment == sha256_tag(dumps(body))


@pytest.mark.parametrize("cid", LEVELS)
def test_the_probe_battery_is_refused_at_intake(cid: str) -> None:
    positive = next(obj for _, role, obj in B.fixture_inputs(cid) if role == "positive")
    probes = B.intake_probes(positive)
    assert B.intake_ok(probes, positive), probes
    assert set(probes) >= {"empty_object", "empty_list", "null", "lists_emptied", "flags_for_data",
                           "verdict_only", "data_plus_verdict"}
    assert not B.intake_ok({**probes, "null": "ACCEPTED"}, positive)
    assert not B.intake_ok({k: v for k, v in probes.items() if k != "null"}, positive)
    left = B.left_to_target(positive)
    if cid == "bare_inscription":
        assert left == {} and probes["lists_emptied"] == B.inapplicable_mark()
        assert not B.intake_ok({**probes, "lists_emptied": "ACCEPTED"}, positive)
    elif cid in ("first_separation", "positioned_join", "bounded_mask", "host_bound_verdict", "row_margin",
                 "site_checks", "walk_relabels", "face_walk_products", "register_squares", "pairing_certificates"):
        assert left == {"lists_emptied": "needs_target_schema"}  # its strings still carry data
    else:
        assert left == {}
    if left:
        assert not B.intake_ok({**probes, "lists_emptied": "EMPTY_FIXTURE"}, positive)


def test_mismatched_answer_type_is_flagged(results: dict[str, LevelResult]) -> None:
    import dataclasses

    r = dataclasses.replace(results["cell_faces"], answer_type="M")
    assert "ANSWER_TYPE_DISAGREES" in B.mismatches(r) and B.status(r) == "MISMATCH"


# ---------------------------------------------------------------- pre-flight


def _pin(name: str) -> CheckerPin:
    p = CHECKERS / name
    return CheckerPin(p, sha256_tag(p.read_bytes()))


def _checker_input() -> dict[str, object]:
    doc = json.loads((current_context().historical_path("bindings") / "generated" / "checker_input" / "L002.json").read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def test_no_checker_means_the_row_waits() -> None:
    assert preflight(_checker_input(), None) == {"rows": [], "target": "NEEDS_TARGET_CHECKER"}


def test_a_faithful_draft_checker_agrees() -> None:
    assert preflight(_checker_input(), _pin("arcs.py")) == {"rows": [], "target": "AGREES"}


def test_a_lossy_checker_disagrees_by_name() -> None:
    out = preflight(_checker_input(), _pin("arcs_endpoints_only.py"))
    assert out["target"] == "DISAGREES"
    assert out["rows"] == ["DISAGREEMENT:near_protect", "DISAGREEMENT:mut"]


def test_checker_below_the_bar_and_pin_and_errors(tmp_path: Path) -> None:
    with pytest.raises(IntakeRefusal) as e:
        bar(load_checker(_pin("accepts_all.py")))
    assert e.value.code == "CHECKER_BELOW_BAR"
    with pytest.raises(IntakeRefusal) as e:
        load_checker(CheckerPin(CHECKERS / "arcs.py", "sha256:" + "0" * 64))
    assert e.value.code == "RR-PIN"
    out = preflight(_checker_input(), _pin("crashes.py"))
    rows = out["rows"]
    assert isinstance(rows, list)
    assert out["target"] == "DISAGREES" and all(str(r).startswith("ERROR:") for r in rows)
    bad = tmp_path / "bad.py"
    bad.write_text("print('not json')\n", encoding="utf-8")
    assert run_checker(bad, {}) == ("ERROR", None)


# ---------------------------------------------------------------- hygiene


def test_native_layers_are_clean() -> None:
    total, lines = report(scan())
    assert total == 0 and lines == []


def test_the_scan_counts_each_kind_of_hit() -> None:
    from operations.use_cases.level_engine.research_engine.hygiene import _firewall

    assert scan_text("curva" + "ture")[0] == 1
    assert scan_text("the " + "m" + "ss rows")[2] == 1
    name = _firewall()[0].pattern.split("(?![")[0].replace("(?<![\\w])", "").replace("\\", "")
    assert scan_text(f"x {name} y")[1] >= 1


def test_the_scan_finds_an_injected_word(tmp_path: Path) -> None:
    (tmp_path / "payload").mkdir()
    (tmp_path / "payload" / "note.md").write_text("an injected " + "curva" + "ture here\n", encoding="utf-8")
    total, lines = report(scan(tmp_path, ("payload",)))
    assert total == 1 and lines == ["payload/note.md: watch=1 firewall=0 outside=0"]


def test_specs_load() -> None:
    for cid in LEVELS:
        assert load_spec(cid).CHALLENGE_ID == cid


def test_active_bundle_separates_vendor_and_package_source_custody() -> None:
    result = run_level("edge_endpoints")
    bundle = cast(dict[str, Any], B.witness_bundle(result, "sha256:" + "1" * 64, "sha256:" + "2" * 64, B.fixture_inputs(result.challenge_id)))
    assert bundle["schema"] == "mssn.witness-bundle.v2"
    assert bundle["carrier"]["repo"] == "the_symbol_game"
    assert bundle["carrier"]["commit"] is None
    assert bundle["sealed_dependency"] == {"repo": "19L57G1", "commit": B.sealed_commit(), "access": "read_only"}
    provenance = bundle["implementation"]
    assert provenance["source_manifest_sha256"] == sha256_tag(dumps(provenance["sources"]))
    for source in provenance["sources"]:
        assert source["sha256"] == sha256_tag((ROOT / source["path"]).read_bytes())
    replay = run_level("bare_inscription")
    replay_bundle = cast(dict[str, Any], B.witness_bundle(replay, "sha256:" + "1" * 64, "sha256:" + "2" * 64, B.fixture_inputs(replay.challenge_id)))
    assert replay_bundle["carrier"]["repo"] == "19L57G1"
    assert replay_bundle["carrier"]["commit"] == B.sealed_commit()
    assert all(not source["path"].startswith("challenge-evidence:") for source in replay_bundle["carrier"]["sources"])


def test_active_transport_uses_the_same_carrier_custody_as_its_bundle() -> None:
    for cid in ("edge_endpoints", "bare_inscription"):
        result = run_level(cid)
        inputs = B.fixture_inputs(cid)
        bundle = cast(dict[str, Any], B.witness_bundle(result, "sha256:" + "1" * 64, "sha256:" + "2" * 64, inputs))
        certificate = cast(dict[str, Any], B.transport_certificate(2, {"row": {"row_sha256": "sha256:" + "3" * 64}},
                                              result, "sha256:" + "4" * 64, "sha256:" + "2" * 64, inputs))
        assert certificate["carrier"] == {key: value for key, value in bundle["carrier"].items() if key != "sources"}
        assert certificate["implementation"]["source_manifest_sha256"] == bundle["implementation"]["source_manifest_sha256"]
        assert certificate["sealed_dependency"] == bundle["sealed_dependency"]
