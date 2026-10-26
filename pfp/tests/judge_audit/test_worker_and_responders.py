"""Return normalization, responder instantiation, type confusion and strategies."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from omega_engine_woland.tests.pilots.judge_packet_audit import responders, worker


@dataclass(frozen=True)
class _Result:
    verdict: str


def test_normalize_covers_the_return_conventions_in_the_packages() -> None:
    assert worker.normalize(True)[0] == "ACCEPT"
    assert worker.normalize((False, "bad"))[:3] == ("REJECT", "tuple[2]", "bad")
    assert worker.normalize((True, "ok", {}))[0] == "ACCEPT"
    assert worker.normalize({"verdict": "PASS"})[0] == "ACCEPT"
    assert worker.normalize({"verdict": "CHECKER_DISAGREEMENT"})[0] == "REJECT"
    assert worker.normalize({"valid": False, "reason": "x"})[:3] == ("REJECT", "dict.valid", "x")
    assert worker.normalize(_Result("FAIL"))[0] == "REJECT"
    # a truthy non-bool is not a verdict
    assert worker.normalize((1, "ok"))[0] == "UNINTERPRETABLE"
    assert worker.normalize({"verdict": "MAYBE"})[0] == "UNINTERPRETABLE"


def test_instantiate_rewrites_only_identifier_keys() -> None:
    template = {"case_id": "<case id>", "status": "UNKNOWN", "witness": {"case_id": "other"}}
    answer = worker.instantiate(template, {"case_id": "c1", "a": 1})
    assert answer == {"case_id": "c1", "status": "UNKNOWN", "witness": {"case_id": "other"}}
    assert worker.instantiate({}, {"case_id": "c1"}) == {}


def test_type_confusion_variants_never_touch_identifiers() -> None:
    answer = {
        "id": "c1",
        "n": 1,
        "k": 7,
        "xs": ["3/4", "2", "v0"],
        "flag": True,
        "q": Fraction(1, 3),
    }
    as_float, count = worker.variant(answer, "float_for_int")
    assert as_float == {
        "id": "c1",
        "n": 1.0,
        "k": 7.0,
        "xs": ["3/4", "2", "v0"],
        "flag": True,
        "q": Fraction(1, 3),
    }
    assert count == 2
    as_bool, count = worker.variant(answer, "bool_for_01")
    assert as_bool["n"] is True and as_bool["k"] == 7 and count == 1
    as_str, count = worker.variant(answer, "float_for_numeric_string")
    assert as_str["xs"] == [0.75, 2.0, "v0"] and count == 2
    _, count = worker.variant({"id": "7"}, "float_for_numeric_string")
    assert count == 0


def test_jsonable_reports_inexact_conversions() -> None:
    assert worker.jsonable({"a": [1, "x"]}) == ({"a": [1, "x"]}, True)
    value, exact = worker.jsonable({"a": (Fraction(1, 2),)})
    assert value == {"a": ["1/2"]} and exact is False


def test_strategies_include_every_enum_code_and_an_unlisted_control() -> None:
    vocab = {
        "refusal_statuses": ["UNKNOWN"],
        "code_keys": ["refusal_code"],
        "codes": ["BUDGET", "MALFORMED"],
    }
    references = [
        {"status": "SOLVED", "json": {"id": "c1", "status": "SOLVED", "x": "1"}},
        {"status": "UNKNOWN", "json": {"id": "c2", "status": "UNKNOWN", "refusal_code": "BOUND"}},
    ]
    examples = [("ex01.json", {"id": "e1", "status": "SOLVED", "x": "2"})]
    strategies = responders.build_strategies(
        answer_id_key="id", vocab=vocab, references=references, example_outputs=examples
    )
    ids = [s["id"] for s in strategies]
    assert ids[:4] == ["empty", "non_object:list", "non_object:string", "abstain:UNKNOWN"]
    for code in ("BOUND", "BUDGET", "MALFORMED", responders.BOGUS_CODE):
        assert f"refuse:UNKNOWN:refusal_code={code}" in ids
    assert "refuse_template:01" in ids
    assert "template_example:ex01.json" in ids
    assert "constant_reference:SOLVED" in ids
    refuse = next(s for s in strategies if s["id"] == "refuse:UNKNOWN:refusal_code=BUDGET")
    assert refuse["template"] == {"id": "<case id>", "status": "UNKNOWN", "refusal_code": "BUDGET"}
    assert len(ids) == len(set(ids))


def test_truncating_float_variant_round_trips_through_int() -> None:
    # counterexample: int(2.3) == 2, so a checker that casts with int() accepts 2.3 for 2
    answer = {"id": "c1", "l": 2, "lower": 0, "delta": -3}
    variant, count = worker.variant(answer, "float_truncating_to_int")
    assert count == 3
    assert all(type(variant[k]) is float for k in ("l", "lower", "delta"))
    assert [int(variant[k]) for k in ("l", "lower", "delta")] == [2, 0, -3]


def test_c018_trivial_bounds_counts_negative_edges_only() -> None:
    case = {
        "id": "g1",
        "vertices": ["0", "1", "2"],
        "edges": [["0", "1", -1], ["1", "2", 1], ["2", "0", -1]],
    }
    answer = responders.c018_unknown_with_trivial_bounds(case, "id")
    assert answer == {
        "id": "g1",
        "status": "UNKNOWN",
        "refusal": "OPTIMALITY_UNCERTIFIED",
        "upper": 2,
        "lower": 0,
    }
    strategies = responders.case_derived_strategies("C018", [case, case], "id")
    assert [s["id"] for s in strategies] == ["case_derived:unknown_trivial_bounds"]
    assert len(strategies[0]["per_case"]) == 2 and strategies[0]["template"] is None
    assert responders.case_derived_strategies("C011", [case], "id") == []


def test_answer_tokens_ignore_identifier_echoes() -> None:
    # counterexample: a trace line that repeats the case ID must not make the ID "name" the answer
    ref = {
        "case_id": "c045_base_identify_03_5_1",
        "status": "SOLVED",
        "identified_knot": "5_1",
        "trace": [{"detail": "Received task for case c045_base_identify_03_5_1"}],
    }
    tokens = worker.answer_tokens(ref, "c045_base_identify_03_5_1")
    assert "identify" not in tokens and "c045" not in tokens
    assert {"solved", "received", "task"} <= set(tokens)


def test_worker_path_holds_both_roots_in_import_style_order(tmp_path) -> None:
    # counterexample: C042 after repair imports absolutely but its solver uses top-level
    # ``from reference_solver...`` imports, which need the package root on the path
    from argparse import Namespace

    from omega_engine_woland.tests.pilots.judge_packet_audit import audit

    options = Namespace(call_timeout=1, solver_timeout=1)
    desc = {
        "import_style": "absolute",
        "import_prefix": "x.",
        "checkers": [],
        "gate": {"kind": "all_accept"},
        "solver": None,
        "cases": [],
        "unwrap_input": False,
    }
    job = audit._job_base(tmp_path / "repo", tmp_path / "repo" / "pkg", desc, options)
    assert job["sys_path"] == [str(tmp_path / "repo"), str(tmp_path / "repo" / "pkg")]
    job = audit._job_base(
        tmp_path / "repo", tmp_path / "repo" / "pkg", dict(desc, import_style="toplevel"), options
    )
    assert job["sys_path"] == [str(tmp_path / "repo" / "pkg"), str(tmp_path / "repo")]
