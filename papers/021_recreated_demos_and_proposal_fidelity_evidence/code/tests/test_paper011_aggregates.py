"""Targeted aggregate scope, actual-byte custody and counterexample controls."""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import sys
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

CODE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "paper011_aggregates_tests", CODE / "aggregate_recreations.py"
)
aggregate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = aggregate
spec.loader.exec_module(aggregate)


@pytest.fixture
def context(tmp_path):
    source = tmp_path / "engine"
    output = tmp_path / "replay"
    source.mkdir()
    output.mkdir()
    data = b'{"candidate":"preserve-original-carrier"}\r\n'
    (source / "input.json").write_bytes(data)
    replay = aggregate.local_module("paper011_aggregate_test_boundary", "recreate_demos.py")
    ctx = aggregate.Context(
        {"engine_root": str(source), "files": {"input.json": aggregate.digest(data)}},
        output,
        {"aggregate_demo_families": []},
        replay,
    )
    return ctx


def test_aggregate_jsonable_does_not_emit_bare_floats():
    assert aggregate.jsonable(1.5) == {"inexact_float_repr": "1.5"}
    assert aggregate.jsonable({"x": 1.0}) == {"x": {"inexact_float_repr": "1.0"}}
    assert aggregate.jsonable([True, 1, Fraction(1, 2)]) == [True, 1, "1/2"]
    parsed = json.loads(aggregate.canonical(aggregate.jsonable(0.1)))
    assert parsed == {"inexact_float_repr": "0.1"}


def test_paper011_aggregate_scope_contains_every_named_family() -> None:
    inventory = json.loads((CODE.parent / "docs/findings_demo_inventory.json").read_bytes())
    assert len(aggregate.AGGREGATES) == 13
    assert tuple(row["id"] for row in inventory["aggregate_demo_families"]) == aggregate.AGGREGATES
    assert "EIGHT_BEAT_DIALOGUE" in aggregate.AGGREGATES
    assert "GENESIS_G01_G25" not in aggregate.AGGREGATES
    assert set(aggregate.HANDLERS) == set(aggregate.AGGREGATES)


@pytest.mark.parametrize("families", [aggregate.AGGREGATES, (), ("CHALLENGE_MUTATION_SUITES",)])
def test_paper011_topology_extension_cannot_claim_other_or_full_family_scopes(families):
    with pytest.raises(
        aggregate.AggregateReplayError, match="EXACT_REMAINING_TOPOLOGY_FAMILY_SCOPE"
    ):
        aggregate.validate_execution_variant(families, "remaining-topologies")


def test_paper011_explicit_topology_variant_does_not_replace_default_family_execution():
    aggregate.validate_execution_variant(("DISCRETE_GEOMETRY_PROBES",), "remaining-topologies")
    aggregate.validate_execution_variant(aggregate.AGGREGATES, "main")
    with pytest.raises(aggregate.AggregateReplayError, match="UNKNOWN_EXECUTION_VARIANT"):
        aggregate.validate_execution_variant(("DISCRETE_GEOMETRY_PROBES",), "extend-carrier")


@pytest.mark.parametrize("families", [aggregate.AGGREGATES, (), ("DISCRETE_GEOMETRY_PROBES",)])
def test_paper011_original_ast_fixture_cannot_claim_historical_or_full_scopes(families):
    with pytest.raises(aggregate.AggregateReplayError, match="EXACT_ORIGINAL_LIVE_AST_FAMILY"):
        aggregate.validate_execution_variant(families, "original-live-ast")


def original_ast_source():
    root = (next((p for p in CODE.parents if (p / ".git").exists()), None) or CODE.parents[6])
    return (root / "omega_engine_pfp/controllers/symbol_game_controller.py").read_bytes()


def test_paper011_original_ast_data_uses_original_callback_without_controller_side_effects():
    fixture, extraction = aggregate.original_ast_fixture(original_ast_source())
    assert fixture["task_id"] == "live_ast_refactor_clean_arch"
    assert len(fixture["progression"]) == 4
    assert all(set(stage) == {
        "domain.order_aggregate", "infrastructure.database_adapter", "use_cases.checkout_service"
    } for stage in fixture["progression"])
    assert "OrderRepoPort" in fixture["progression"][-1]["use_cases.checkout_service"]
    assert extraction["original_method_sha256"] == aggregate.digest(
        bytes.fromhex(extraction["original_method_bytes_hex"])
    )
    aggregate.validate_execution_variant(("AST_REFACTORING_RETRACTION",), "original-live-ast")


@pytest.mark.parametrize("mutation", ["callback", "executable_source", "decorator", "extra_statement"])
def test_paper011_original_ast_capture_refuses_executable_or_reinterpreted_fixture(mutation):
    raw = original_ast_source()
    if mutation == "callback":
        raw = raw.replace(b"self.use_case.run_live_ast_refactoring(", b"self.use_case.run_problem(")
    elif mutation == "executable_source":
        raw = raw.replace(b"step_1_sources = {", b"step_1_sources = unknown_side_effect() or {")
    elif mutation == "decorator":
        raw = raw.replace(b"    def run_live_ast_refactoring_specimen(", b"    @unknown_side_effect\n    def run_live_ast_refactoring_specimen(")
    else:
        raw = raw.replace(b"        progression = [step_1_sources", b"        unknown_side_effect()\n        progression = [step_1_sources")
    with pytest.raises((aggregate.AggregateReplayError, SyntaxError)):
        aggregate.original_ast_fixture(raw)


@pytest.mark.parametrize("envelope", [{"success": False}, {"success": True}, {"success": 1, "result": {}}])
def test_paper011_injected_ast_port_has_no_passing_fallback(envelope):
    outcome = SimpleNamespace(is_ok=True, unwrap=lambda: envelope)
    host = SimpleNamespace(invoke_runtime=lambda action, payload: outcome)
    port = aggregate.BoundNativeFunctionalPort(host, None, None)
    with pytest.raises(aggregate.AggregateReplayError, match="NATIVE_FUNCTIONAL"):
        port.invoke("functional_evaluate", {"actual_input": "retained by outer tape"})


def test_paper011_woland_import_refuses_unpinned_owner_instead_of_ambient_import(context):
    with pytest.raises(aggregate.AggregateReplayError, match="UNPINNED_INPUT"):
        aggregate.PinnedWolandFinder(context).find_spec("omega_engine_woland")


def test_paper011_empty_prefix_prevents_loading_an_accepted_stale_pyc(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "candidate_algorithm.py"
    source.write_bytes(b"VALUE = 'old'\n")
    py_compile.compile(str(source), doraise=True)
    original = source.stat()
    source.write_bytes(b"VALUE = 'new'\n")
    os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setattr(sys, "pycache_prefix", None)

    def load_value(name):
        candidate_spec = importlib.util.spec_from_file_location(name, source)
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        return candidate.VALUE

    # The same-size, same-time changed source demonstrates why -B alone is insufficient.
    assert load_value("stale_candidate") == "old"
    cache = tmp_path / "fresh_cache"
    cache.mkdir()
    record = aggregate.empty_cache_configuration(cache, activate=True)
    assert load_value("current_candidate") == "new"
    assert record["initial_cache_entries"] == []
    assert list(cache.iterdir()) == []


def test_paper011_populated_bytecode_prefix_refuses_before_source_import(tmp_path, monkeypatch):
    cache = tmp_path / "fresh_cache"
    cache.mkdir()
    (cache / "previous-candidate.pyc").write_bytes(b"untrusted compiled bytes")
    monkeypatch.setattr(sys, "pycache_prefix", None)
    with pytest.raises(aggregate.AggregateReplayError, match="EMPTY_BYTECODE_CACHE_REQUIRED"):
        aggregate.empty_cache_configuration(cache, activate=True)
    assert sys.pycache_prefix is None


def test_paper011_cache_settings_must_match_the_declared_empty_prefix(tmp_path, monkeypatch):
    cache = tmp_path / "fresh_cache"
    cache.mkdir()
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setattr(sys, "pycache_prefix", str(tmp_path / "undeclared_cache"))
    with pytest.raises(aggregate.AggregateReplayError, match="FRESH_BYTECODE_CACHE_CONFIGURATION"):
        aggregate.empty_cache_configuration(cache)


def test_paper011_aggregate_pins_actual_raw_input_bytes(context) -> None:
    raw = context.read("input.json")
    record = json.loads((context.output / "actual_inputs.jsonl").read_bytes())
    assert bytes.fromhex(record["bytes_hex"]) == raw
    assert record["sha256"] == aggregate.digest(raw)
    assert raw.endswith(b"\r\n")
    assert context.data("input.json") == {"candidate": "preserve-original-carrier"}
    assert len((context.output / "actual_inputs.jsonl").read_bytes().splitlines()) == 1


def test_paper011_aggregate_unpinned_input_refuses(context) -> None:
    (context.engine / "unlicensed.json").write_bytes(b"{}")
    with pytest.raises(aggregate.AggregateReplayError, match="UNPINNED_INPUT"):
        context.read("unlicensed.json")


def test_paper011_aggregate_changed_input_refuses(context) -> None:
    (context.engine / "input.json").write_bytes(b"changed")
    with pytest.raises(aggregate.AggregateReplayError, match="INPUT_BYTES_CHANGED"):
        context.read("input.json")


def test_paper011_aggregate_nonregular_input_refuses(context) -> None:
    path = context.engine / "input.json"
    raw = path.read_bytes()
    path.unlink()
    path.mkdir()
    (path / "same-bytes").write_bytes(raw)
    with pytest.raises(ValueError):
        context.read("input.json")


def test_paper011_aggregate_duplicate_keys_refuse(context) -> None:
    raw = b'{"candidate":"a","candidate":"b"}'
    (context.engine / "input.json").write_bytes(raw)
    context.capability["files"]["input.json"] = aggregate.digest(raw)
    with pytest.raises(context.replay.ReplayError, match="DUPLICATE_JSON_KEY"):
        context.data("input.json")


def test_paper011_aggregate_failed_control_is_recorded_as_failed(context) -> None:
    assert (
        context.observe(
            "FAMILY", "corrupt_certificate", True, expected=False, grade="NEGATIVE_CONTROL"
        )
        is False
    )
    assert context.observations[-1]["passed"] is False
    assert context.observations[-1]["actual"] is True


def test_paper011_aggregate_truthy_integer_cannot_pass_boolean_check(context) -> None:
    assert context.observe("FAMILY", "native_validity", 1, expected=True) is False
    assert (
        context.observe("FAMILY", "nested_native_validity", {"valid": 1}, expected={"valid": True})
        is False
    )


def test_paper011_observation_without_expected_value_is_unverified(context) -> None:
    assert context.observe("FAMILY", "retained_model_claim", {"valid": True}) is None
    row = context.observations[-1]
    assert row["passed"] is None
    assert row["asserted"] is False
    assert row["verification_status"] == "OBSERVATION_ONLY"
    assert (
        aggregate.explicit_control_outcome(context.observations, "FAMILY")[
            "all_explicit_controls_passed"
        ]
        is False
    )
    assert context.observe("FAMILY", "expected_no_witness", None, expected=None) is True


def test_paper011_failed_explicit_control_cannot_hide_behind_other_passes(context) -> None:
    context.observe("FAMILY", "positive", True, expected=True)
    context.observe("FAMILY", "false_negative", True, expected=False)
    context.observe("FAMILY", "unchecked", 999)
    result = aggregate.explicit_control_outcome(context.observations, "FAMILY")
    assert result == {
        "asserted_controls": 2,
        "passed_controls": 1,
        "failed_controls": 1,
        "observation_only_records": 1,
        "all_explicit_controls_passed": False,
    }


def control_records():
    return [
        {
            "input": "positive",
            "checks": [True, True],
            "accepted": True,
            "coverage_class": "SOURCE_CHECKED_CANDIDATE",
        },
        {"mutation": "negative", "checks": [False, False]},
    ]


def test_paper011_mutation_execution_without_rejection_cannot_pass(context) -> None:
    records = control_records()
    records[1]["checks"] = [True, True]
    result = aggregate.mutation_control_census(records, 1, 1, 2, context.replay.checker_accepts)
    assert result["case_records"] == result["mutation_records"] == 1
    assert result["all_checkers_accept_mutation"] == 1
    assert result["expected_controls_succeeded"] is False


def test_paper011_joint_detection_is_separate_from_dual_rejection(context) -> None:
    records = control_records()
    records[1]["checks"] = [False, True]
    result = aggregate.mutation_control_census(records, 1, 1, 2, context.replay.checker_accepts)
    assert result["joint_mutant_detections"] == result["partial_checker_rejections"] == 1
    assert result["dual_checker_rejections"] == 0
    assert result["expected_controls_succeeded"] is False


@pytest.mark.parametrize(
    "bad", [{"error": {"type": "Crash"}}, {"checks": [False, None]}, {"checks": [False, 0]}]
)
def test_paper011_mutation_errors_and_uninterpretable_flags_cannot_pass(context, bad) -> None:
    records = control_records()
    records[1] = {"mutation": "negative", **bad}
    result = aggregate.mutation_control_census(records, 1, 1, 2, context.replay.checker_accepts)
    assert result["expected_controls_succeeded"] is False
    assert result["joint_mutant_detections"] == result["dual_checker_rejections"] == 0


def test_paper011_refusal_accepted_output_is_never_counted_as_positive_candidate(context) -> None:
    records = control_records()
    records[0]["coverage_class"] = "ACCEPTED_TYPED_REFUSAL"
    result = aggregate.mutation_control_census(records, 1, 1, 2, context.replay.checker_accepts)
    assert result["expected_controls_succeeded"] is True
    assert result["accepted_case_outputs"] == result["accepted_typed_refusals"] == 1
    assert result["accepted_non_refusal_outputs"] == 0


@pytest.mark.parametrize("claim", [True, 1.0, "1"])
def test_paper011_original_raw_move_requires_exact_integer_claims(claim) -> None:
    with pytest.raises(aggregate.AggregateReplayError, match="EXACT_DIRECTED_INTEGER_CLAIM"):
        aggregate.exact_move_claims({"proposed_claims": {"a->b": claim}})


def test_paper011_source_import_paths_are_bound_to_the_declared_root() -> None:
    row = {"path": "__init__.py", "source_sha256": "captured", "allowed_changes": []}
    bound = aggregate.bind_import_journal_root([row], aggregate.PFP)
    assert bound[0]["path"] == aggregate.PFP + "__init__.py"
    assert bound[0]["source_relative_path"] == "__init__.py"
    assert bound[0]["declared_import_root"] == aggregate.PFP
    assert row["path"] == "__init__.py"


@pytest.mark.parametrize(
    "path", ["../carrier.py", "/carrier.py", "a/../carrier.py", "C:/carrier.py", "a\\carrier.py"]
)
def test_paper011_source_import_root_cannot_authorize_escaped_paths(path) -> None:
    with pytest.raises(aggregate.AggregateReplayError, match="IMPORT_JOURNAL_PATH_ESCAPE"):
        aggregate.bind_import_journal_root([{"path": path}], aggregate.PFP)


def previous_diagnostic(tmp_path):
    previous = tmp_path / "previous"
    previous.mkdir()
    observations = [
        {
            "family": "FSP_BLIND_CLUSTER_RECOVERY",
            "actual": {"witness": "unverified"},
            "expected": None,
            "passed": True,
        },
        {"family": "FSP_BLIND_CLUSTER_RECOVERY", "actual": 1, "expected": True, "passed": True},
    ]
    raw = b"".join(aggregate.canonical(row) + b"\n" for row in observations)
    (previous / "observations.jsonl").write_bytes(raw)
    receipt = {
        "schema_version": "paper011.aggregate-recreated-run.v1",
        "artifacts_sha256": {"observations.jsonl": aggregate.digest(raw)},
        "result": {
            "families": [
                {
                    "id": "FSP_BLIND_CLUSTER_RECOVERY",
                    "finite_computation_passed": True,
                    "remaining": ["full task remains"],
                }
            ]
        },
    }
    receipt["receipt_sha256"] = aggregate.digest(aggregate.canonical(receipt))
    (previous / "aggregate_receipt.json").write_bytes(aggregate.canonical(receipt))
    return previous


def test_paper011_retained_review_corrects_unasserted_and_truthy_passes(tmp_path) -> None:
    previous = previous_diagnostic(tmp_path)
    original = (previous / "observations.jsonl").read_bytes()
    output = tmp_path / "review"
    result = aggregate.review_previous_run(previous, output)
    assert result["algorithm_executions"] == 0
    assert result["families"][0]["retained_scoped_controls_verified"] is False
    corrected = [
        json.loads(line)
        for line in (output / "reclassified_observations.jsonl").read_bytes().splitlines()
    ]
    assert corrected[0]["passed"] is None
    assert corrected[1]["passed"] is False
    assert (previous / "observations.jsonl").read_bytes() == original


@pytest.mark.parametrize("corruption", ["bytes", "extra_path"])
def test_paper011_retained_review_refuses_changed_inventory_or_bytes(tmp_path, corruption) -> None:
    previous = previous_diagnostic(tmp_path)
    if corruption == "bytes":
        (previous / "observations.jsonl").write_bytes(b"{}\n")
    else:
        (previous / "uncommitted_witness.json").write_bytes(b"{}")
    with pytest.raises(aggregate.AggregateReplayError, match="PREVIOUS_ARTIFACT"):
        aggregate.review_previous_run(previous, tmp_path / "review")


def test_paper011_aggregate_module_retains_math_and_logs_import_changes(context) -> None:
    raw = b'def existing_algorithm(x):\n    return x + 7\n\nif __name__ == "__main__":\n    raise RuntimeError("historical script side effect")\n'
    path = context.engine / "algorithm.py"
    path.write_bytes(raw)
    context.capability["files"]["algorithm.py"] = aggregate.digest(raw)
    module = context.module("algorithm.py")
    assert module.existing_algorithm(5) == 12
    assert context.journal[0]["source_sha256"] == aggregate.digest(raw)
    assert context.journal[0]["allowed_changes"] == [{"kind": "REMOVE_SCRIPT_MAIN", "line": 4}]


def test_paper011_aggregate_arbitrary_sibling_import_is_not_invented(context) -> None:
    raw = b"import nonexistent_unpinned_paper011_dependency\n"
    (context.engine / "algorithm.py").write_bytes(raw)
    context.capability["files"]["algorithm.py"] = aggregate.digest(raw)
    with pytest.raises(ModuleNotFoundError):
        context.module("algorithm.py")
