"""Hermetic negative controls for recreation custody and source adaptation."""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import os
import py_compile
import shutil
import sys
import types
from pathlib import Path

import pytest


def local_module(name, filename):
    path = Path(__file__).resolve().parents[1] / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


replay = local_module("paper011_replay_tests", "recreate_demos.py")
catalog = local_module("paper011_catalog_tests", "demo_catalog.py")


def test_phi2_binding_requires_actual_native_pass_and_explicit_engine_root(tmp_path):
    source = tmp_path / "source"
    folder = source / "dossier"
    folder.mkdir(parents=True)
    (folder / "input.yaml").write_bytes(b"declared: input\n")
    (folder / "witness_valid.json").write_bytes(b"{}")
    (folder / "witness_near_miss.json").write_bytes(
        replay.canonical([{"case_name": f"bad_{i}"} for i in range(4)])
    )
    engine = tmp_path / "explicit_engine"
    output = tmp_path / "output"
    output.mkdir()
    calls = []
    capture = {"enabled": False}

    def check(inp, witness, root):
        calls.append(root)
        assert inp == {"declared": "input"} and root == engine
        if witness:
            return {"status": "REFUSED"}
        if capture["enabled"]:
            event = {
                "binary_key": "verify_phi2",
                "process_exit": 0,
                "stdout_bytes_hex": replay.canonical(
                    {"status": "PASS", "reported_value": "1", "duality_gap": "0"}
                ).hex(),
                "request_bytes_hex": replay.canonical({"reported_value": "1"}).hex(),
            }
            with (output / "native_transport_calls.jsonl").open("ab") as stream:
                stream.write(replay.canonical(event) + b"\n")
        # The retained source's unconditional label must not supply a native pass.
        return {"status": "CERTIFIED", "rust_engine_coupled": "PASS", "phi2_val": "1", "betti_2": 1}

    module = types.SimpleNamespace(check_exact_phi2_certificate=check)
    result = replay.phi2_dossier_recreation(module, folder, source, engine, output)
    assert not result["native_valid_witness_verified"]
    assert len(calls) == 5 and len(result["result"]["near_miss_results"]) == 4
    assert result["betti_scope"] == "DECLARED_SOURCE_METADATA_NOT_A_RANK_PROOF"
    capture["enabled"] = True
    result = replay.phi2_dossier_recreation(module, folder, source, engine, output)
    assert result["native_valid_witness_verified"]


def test_phi2_composition_preserves_production_deficit_and_requires_both_native_witnesses():
    diagnostic = {
        "dispatch_return": 2,
        "actual_engine_payloads": {"receipt": {"code": "NO_NATIVE_PORT"}},
    }
    original = replay.canonical(diagnostic)
    audits = [
        {
            "status": "AUDIT_EXECUTED",
            "outputs": [
                {
                    "native_valid_witness_verified": True,
                    "result": {
                        "near_miss_results": [
                            {"result": {"status": "REFUSED_INVALID"}} for _ in range(4)
                        ]
                    },
                }
            ],
        }
        for _ in range(2)
    ]
    result = replay.compose_phi2_port(diagnostic, audits)
    assert result["composition_port"]["verified"] and result["dispatch_return"] == 0
    assert replay.canonical(result["canonical_adapter_diagnostic"]) == original
    assert replay.demo_execution_status(result, audits) == "DEMO_EXECUTION_RECORDED"
    audits[0]["outputs"][0]["native_valid_witness_verified"] = False
    result = replay.compose_phi2_port(diagnostic, audits)
    assert not result["composition_port"]["verified"] and result["dispatch_return"] == 2
    assert replay.demo_execution_status(result, audits) == "DEMO_RECREATION_RESIDUAL"


@pytest.mark.parametrize("degree", [3, 4])
def test_higher_degree_audits_require_native_bytes_and_all_original_controls(tmp_path, degree):
    source = tmp_path / "source"
    folder = source / "dossier"
    folder.mkdir(parents=True)
    (folder / "input.yaml").write_bytes(b"original: carrier\n")
    (folder / "witness_valid.json").write_bytes(b'{"original":"witness"}')
    cases = [{"case_id": f"bad_{i}", "expected_refusal": "BAD_WITNESS"} for i in range(4)]
    (folder / "witness_near_miss.json").write_bytes(replay.canonical({"cases": cases}))
    engine = tmp_path / "explicit_engine"
    output = tmp_path / "output"
    output.mkdir()
    mode = {"native": None, "controls": 4}

    def original_audit(*, dossier_dir, repo_root):
        assert dossier_dir == folder and repo_root == engine
        if mode["native"]:
            event = {
                "binary_key": f"verify_phi{degree}",
                "process_exit": 0,
                "request_bytes_hex": replay.canonical({"reported_value": "1"}).hex(),
                "stdout_bytes_hex": replay.canonical(
                    {"status": "PASS", "reported_value": mode["native"], "duality_gap": "0"}
                ).hex(),
            }
            with (output / "native_transport_calls.jsonl").open("ab") as stream:
                stream.write(replay.canonical(event) + b"\n")
        return {
            "valid_audit": {
                "status": "PASS",
                f"phi{degree}_certified_value": "1",
                "duality_gap": "0",
                "rust_verification": {"status": "PASS", "available": True},
            },
            "near_miss_count": mode["controls"],
            "near_miss_details": [
                {
                    **case,
                    "actual_status": "REFUSED_BAD_WITNESS",
                    "rejected_as_expected": True,
                }
                for case in cases[: mode["controls"]]
            ],
            "scope_status": "REFUSED_DECLARED_TOPOLOGY_MISMATCH",
            "topology_audit": {"status": "REFUSED_DECLARED_TOPOLOGY_MISMATCH"},
            "exact_gauge_pairing_status": "UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER",
            "exact_gauge_pontryagin_pairing": None,
        }

    module = types.SimpleNamespace(run_dossier_audit=original_audit)
    audit = replay.higher_degree_dossier_recreation(module, folder, source, engine, output, degree)
    assert not audit["native_valid_witness_verified"] and audit["source_control_coverage_complete"]
    mode["native"] = "2"
    audit = replay.higher_degree_dossier_recreation(module, folder, source, engine, output, degree)
    assert not audit["native_valid_witness_verified"]
    mode["native"] = "1"
    audit = replay.higher_degree_dossier_recreation(module, folder, source, engine, output, degree)
    assert audit["native_valid_witness_verified"] and len(audit["input_bindings"]) == 3
    assert len(audit["scope_residuals"]) == 2
    mode["controls"] = 3
    audit = replay.higher_degree_dossier_recreation(module, folder, source, engine, output, degree)
    assert audit["native_valid_witness_verified"] and not audit["source_control_coverage_complete"]


@pytest.mark.parametrize("degree", [3, 4])
def test_higher_degree_composition_keeps_topology_refusals_separate(tmp_path, degree):
    diagnostic = {"dispatch_return": 0, "actual_engine_payloads": {"old": {"code": "NO_NATIVE_PORT"}}}
    original = replay.canonical(diagnostic)
    audits = [
        {
            "checker_path": f"original/dossier_{i}/checker.py",
            "status": "AUDIT_EXECUTED",
            "outputs": [
                {
                    "native_valid_witness_verified": True,
                    "source_control_coverage_complete": True,
                    "declared_near_miss_count": 4,
                    "scope_residuals": [
                        {"kind": "DECLARED_TOPOLOGY_REFUSED", "status": "REFUSED_TOPOLOGY"}
                    ],
                }
            ],
        }
        for i in range(2)
    ]
    result = replay.compose_higher_degree_port(diagnostic, audits, degree)
    assert result["composition_port"]["verified"] and result["dispatch_return"] == 0
    assert not result["composition_port"]["manifold_or_intersection_claim_verified"]
    assert not result["all_original_claims_supported"] and len(result["scope_residuals"]) == 2
    assert replay.canonical(result["canonical_adapter_diagnostic"]) == original
    audits[1]["outputs"][0]["source_control_coverage_complete"] = False
    result = replay.compose_higher_degree_port(diagnostic, audits, degree)
    assert not result["composition_port"]["verified"] and result["dispatch_return"] == 2


def test_supplemental_candidates_bind_original_targets_and_separate_controls(tmp_path, monkeypatch):
    cases = [
        {
            "case_id": "c041_base_16",
            "expected_kind": "REFUTATION",
            "statement": "original false target",
        },
        {"case_id": "c041_ctrl_08", "expected_kind": "PROOF", "statement": "original true target"},
    ]
    refs = []
    proposals = []
    for i, case in enumerate(cases):
        raw = replay.canonical(case)
        (tmp_path / f"case{i}.json").write_bytes(raw)
        refs.append({"path": f"case{i}.json", "index": None, "sha256": replay.digest(raw)})
        proposals.append(
            {
                "original_case_sha256": replay.digest(raw),
                "original_case": case,
                "candidate": {
                    "case_id": case["case_id"],
                    "proof": "valid",
                    "kind": case["expected_kind"],
                    "status": "SOLVED",
                },
            }
        )
    path = tmp_path / "proposals.json"
    document = {"schema_version": "paper011.c041-supplemental-proposals.v1", "rows": proposals}
    path.write_bytes(replay.canonical(document))
    binding = {"path": str(path), "sha256": replay.digest(path.read_bytes())}
    row = {
        "id": "C041",
        "package": ".",
        "module": "fixture",
        "cases": refs,
        "checkers": [{}, {}],
        "mutations": [{}] * 48,
    }
    monkeypatch.setattr(
        replay,
        "_callable",
        lambda *args: lambda case, answer: answer["proof"] == "valid"
        and answer["kind"] == case["expected_kind"],
    )
    result = replay.supplemental_c041(row, tmp_path, io.BytesIO(), binding)
    assert result["accepted_selected_candidates"] == 2
    assert result["supplemental_control_count"] == result["supplemental_dual_rejections"] == 4
    assert result["original_catalog_mutation_count"] == 48
    assert (
        not result["original_reference_solver_invoked"] and not result["full_source_case_execution"]
    )
    document["rows"][0]["original_case"]["statement"] = "easier replacement"
    path.write_bytes(replay.canonical(document))
    binding["sha256"] = replay.digest(path.read_bytes())
    with pytest.raises(replay.ReplayError, match="SUPPLEMENTAL_INTERPRETATION_CHANGED"):
        replay.supplemental_c041(row, tmp_path, io.BytesIO(), binding)


def test_import_relocation_preserves_algorithm_body_and_records_change():
    source = b"from projects.mssn_sn_symgam.challenges.x import exact\ndef evaluate(x):\n    return x * 3 + 1\n"
    transformed, changes = replay.relocate_source(source, "sample.py")
    original_function = ast.parse(source).body[1]
    recreated_function = ast.parse(transformed).body[1]
    assert ast.dump(original_function) == ast.dump(recreated_function)
    assert changes == [
        {
            "kind": "RELOCATE_IMPORT",
            "line": 1,
            "before": "projects.mssn_sn_symgam.challenges.x",
            "after": "paper011_source.challenges.x",
        }
    ]


def test_obsolete_path_bootstrap_removed_without_changing_other_guards():
    source = b"import sys\nfor p in [1]:\n    sys.path.insert(0,p)\nif 3 > 2:\n    result=7\nif __name__ == '__main__':\n    raise SystemExit(4)\n"
    transformed, changes = replay.relocate_source(source, "sample.py")
    assert b"sys.path" not in transformed
    assert b"if 3 > 2" in transformed
    assert [row["kind"] for row in changes] == [
        "REMOVE_OBSOLETE_SYS_PATH_BOOTSTRAP",
        "REMOVE_SCRIPT_MAIN",
    ]


def test_unaliased_old_absolute_import_requires_review():
    with pytest.raises(replay.ReplayError, match="REQUIRES_REVIEW"):
        replay.relocate_source(
            b"import projects.mssn_sn_symgam.challenges.foo\n", "x.py"
        )


@pytest.mark.parametrize("value", [0, 1, "PASS", {"passed": 1}, (1, "looks passing")])
def test_truthy_checker_metadata_cannot_be_acceptance(value):
    assert replay.checker_accepts(value) is None


@pytest.mark.parametrize("value", [True, (True, "verified"), {"passed": True}])
def test_literal_boolean_acceptance(value):
    assert replay.checker_accepts(value) is True


def test_duplicate_or_nonfinite_inputs_refuse():
    with pytest.raises(replay.ReplayError, match="DUPLICATE"):
        replay.load(b'{"answer":0,"answer":1}')
    with pytest.raises(replay.ReplayError, match="NONFINITE"):
        replay.load(b'{"answer":NaN}')


def test_missing_source_cannot_be_an_empty_verified_inventory(tmp_path):
    with pytest.raises(OSError):
        replay.source_files(tmp_path / "missing")


def test_nonregular_source_entry_refuses(tmp_path):
    path = tmp_path / "input.json"
    path.mkdir()
    with pytest.raises(replay.ReplayError, match="NONREGULAR"):
        replay.regular(path)


def test_input_digest_mismatch_refuses_before_call(tmp_path):
    (tmp_path / "case.json").write_bytes(b'{"value":2}')
    with pytest.raises(replay.ReplayError, match="INPUT_DIGEST_MISMATCH"):
        replay._case(
            tmp_path, {"path": "case.json", "index": None, "sha256": replay.digest(b'{"value":1}')}
        )


def test_closed_demo_catalog_does_not_drop_omitted_obligations(tmp_path):
    (tmp_path / "demos").mkdir()
    (tmp_path / "demos/demos_runner.py").write_text(
        'DEMO_DISPATCH: dict = {"demo_1": None}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="27 obligations"):
        catalog.build_catalog(tmp_path)


def test_complete_discovery_retains_spec_only_entries_and_real_checker_contract(tmp_path):
    demos = tmp_path / "demos"
    demos.mkdir()
    (demos / "demos_runner.py").write_text(
        "DEMO_DISPATCH: dict = " + repr(dict.fromkeys(catalog.DEMO_IDS)), encoding="utf-8"
    )
    root = tmp_path / "challenges/theme/c011_fixture"
    for folder in ["governance", "judge_packet/cases", "judge_packet/checkers", "reference_solver"]:
        (root / folder).mkdir(parents=True)
    (root / "governance/commit_reveal_runner.py").write_text(
        "from ..judge_packet.checkers.primary import check\n"
        "from ..judge_packet.checkers.independent import verify\n"
        "from ..reference_solver.solver import solve\n",
        encoding="utf-8",
    )
    (root / "judge_packet/checkers/primary.py").write_text(
        "def check(case,answer):\n    return True\n", encoding="utf-8"
    )
    (root / "judge_packet/checkers/independent.py").write_text(
        "def verify(case,answer):\n    return False\n", encoding="utf-8"
    )
    (root / "judge_packet/cases/case.json").write_text('{"id":"test","value":1}', encoding="utf-8")
    result = catalog.build_catalog(tmp_path)
    assert len(result["demos"]) == 27
    assert len(result["challenges"]) == 60
    row = result["challenges"][10]
    assert row["id"] == "C011"
    assert row["solver"] == {"module": "reference_solver.solver", "function": "solve"}
    assert len(row["checkers"]) == 2
    assert len(row["cases"]) == 1
    assert result["challenges"][1]["kind"] == "SPECIFICATION_ONLY"


def test_receipt_custody_detects_changed_output_and_inventory(tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    (output / "answer.json").write_bytes(b'{"answer":1}')
    receipt = {
        "schema_version": replay.SCHEMA,
        "id": "fixture",
        "artifacts_sha256": replay.source_files(output),
    }
    receipt["receipt_sha256"] = replay.digest(replay.canonical(receipt))
    (output / "recreation_receipt.json").write_bytes(replay.canonical(receipt))
    assert replay.verify_receipt(output)["status"] == "INTEGRITY_VERIFIED"
    (output / "answer.json").write_bytes(b'{"answer":2}')
    with pytest.raises(replay.ReplayError, match="ARTIFACT_CUSTODY"):
        replay.verify_receipt(output)
    (output / "answer.json").write_bytes(b'{"answer":1}')
    (output / "extra.json").write_bytes(b"{}")
    with pytest.raises(replay.ReplayError, match="ARTIFACT_CUSTODY"):
        replay.verify_receipt(output)


def test_source_finder_imports_only_owned_namespace_and_retains_source_digest(tmp_path):
    path = tmp_path / "sample.py"
    path.write_bytes(b"value = 42\n")
    journal = []
    finder = replay.SourceFinder(tmp_path, journal)
    assert finder.find_spec("unowned.sample") is None
    spec = finder.find_spec("paper011_source.sample")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.value == 42
    assert journal[0]["source_sha256"] == replay.digest(path.read_bytes())
    assert journal[0]["allowed_changes"] == []


def test_engine_capability_cannot_be_implicit_or_empty():
    with pytest.raises(replay.ReplayError, match="CAPABILITY_MISSING"):
        replay.verify_engine({"schema_version": "paper011.engine-capability.v1", "files": {}})


def test_catalog_and_receipts_are_reproducible_json_bytes():
    assert replay.canonical({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert json.loads(replay.canonical({"b": 2, "a": 1})) == {"a": 1, "b": 2}


def test_unbound_mutation_cannot_satisfy_complete_recreation(tmp_path, monkeypatch):
    (tmp_path / "case.json").write_bytes(b'{"id":"case"}')
    (tmp_path / "mutation.json").write_bytes(b'{"unsupported":"shape"}')

    def descriptor(name):
        return {
            "path": name,
            "index": None,
            "sha256": replay.digest((tmp_path / name).read_bytes()),
        }

    row = {
        "id": "C051",
        "kind": "REFERENCE_PACKAGE",
        "package": ".",
        "module": "fixture",
        "solver": {"function": "solve"},
        "checkers": [{"function": "first"}, {"function": "second"}],
        "cases": [descriptor("case.json")],
        "mutations": [descriptor("mutation.json")],
    }
    monkeypatch.setattr(
        replay,
        "_callable",
        lambda _, entry: (lambda case: {"status": "OUT_OF_SCOPE"})
        if entry["function"] == "solve"
        else (lambda case, answer: True),
    )
    stream = io.BytesIO()
    result = replay.reference_challenge(row, tmp_path, stream)
    assert result["status"] == "REFERENCE_RESIDUAL"
    assert not result["complete_mutation_execution"]
    assert result["counts"]["accepted_typed_refusals"] == 1
    assert result["counts"]["accepted_non_refusal_outputs"] == 0
    assert result["counts"]["unbound_mutation_records"] == 1
    assert b"UNBOUND_MUTATION_RECORD" in stream.getvalue()


def test_top_level_sys_path_call_is_removed():
    adapted, changes = replay.relocate_source(
        b"import sys\nsys.path.append('ambient')\nvalue = 4\n", "mutants.py"
    )
    assert b"sys.path" not in adapted
    assert changes[0]["kind"] == "REMOVE_OBSOLETE_SYS_PATH_BOOTSTRAP"


def test_build_receipt_bytes_are_rechecked(tmp_path):
    (tmp_path / "engine.py").write_bytes(b"value = 1\n")
    (tmp_path / "build.json").write_bytes(b"{}")
    lock = {
        "schema_version": "paper011.engine-capability.v1",
        "engine_root": str(tmp_path),
        "files": {"engine.py": replay.digest((tmp_path / "engine.py").read_bytes())},
        "binaries": {},
        "build_receipt": {"path": str(tmp_path / "build.json"), "sha256": replay.digest(b"{}")},
    }
    assert replay.verify_engine(lock) == tmp_path
    (tmp_path / "build.json").write_bytes(b'{"changed":true}')
    with pytest.raises(replay.ReplayError, match="BUILD_RECEIPT_CHANGED"):
        replay.verify_engine(lock)


def test_c024_declared_input_envelope_is_unwrapped_without_changing_graph():
    graph = {"num_vertices": 2, "g": [[0, 1]], "g_prime": [[0, 1]]}
    envelope = {"input": graph, "historical_metadata": "not a graph constraint"}
    assert replay.declared_input({"id": "C024"}, envelope) is graph
    assert replay.declared_input({"id": "C024"}, graph) is graph
    assert replay.declared_input({"id": "C017"}, envelope) is envelope


@pytest.mark.parametrize(
    "answer, expected",
    [
        ({"status": "SOLVED", "kind": "EXISTS"}, "CANDIDATE"),
        ({"status": "SOLVED", "kind": "DOES_NOT_EXIST"}, "NEGATIVE_CLAIM"),
        ({"status": "SOLVED", "kind": "NOT_ADJOINT"}, "NEGATIVE_CLAIM"),
        ({"verdict": "ACCEPT"}, "CLASSIFIER_DECISION"),
        ({"status": "OUT_OF_SCOPE"}, "TYPED_REFUSAL"),
    ],
)
def test_task_specific_negative_and_classifier_outcomes(answer, expected):
    assert replay.candidate_class(answer) == expected


def test_nonzero_dispatch_and_nested_audit_gaps_cannot_pass():
    assert replay.demo_execution_status({"dispatch_return": 2}, []) == "CURRENT_ENGINE_REFUSAL"
    assert (
        replay.demo_execution_status({"dispatch_return": 0}, [{"status": "REPRODUCTION_GAP"}])
        == "DEMO_RECREATION_RESIDUAL"
    )
    assert (
        replay.demo_execution_status(
            {
                "actual_engine_payloads": {
                    "receipt.json": {
                        "result": {"code": "NO_NATIVE_PORT", "status": "TYPED_REFUSAL"}
                    }
                }
            },
            [],
        )
        == "CURRENT_ENGINE_REFUSAL"
    )
    assert (
        replay.demo_execution_status({"receipt": {"verdict": "INCOMPLETE"}}, [])
        == "DEMO_RECREATION_RESIDUAL"
    )


def test_unreadable_engine_json_is_retained_and_blocks_execution(tmp_path):
    output = tmp_path / "engine_run"
    output.mkdir()
    (output / "ok.json").write_bytes(b'{"status":"PASS"}')
    (output / "bad.json").write_bytes(b"{not json")
    (output / "bom.json").write_bytes(b"\xef\xbb\xbf{}")
    payloads, refused = replay.engine_json_payloads(output)
    assert payloads == {"ok.json": {"status": "PASS"}}
    assert [row["path"] for row in refused] == ["bad.json", "bom.json"]
    assert [row["exception"] for row in refused] == ["JSONDecodeError", "ReplayError"]
    assert (
        replay.demo_execution_status(
            {
                "dispatch_return": 0,
                "actual_engine_payloads": payloads,
                "unreadable_engine_payloads": refused,
            },
            [],
        )
        == "DEMO_RECREATION_RESIDUAL"
    )
    assert (
        replay.demo_execution_status(
            {
                "dispatch_return": 0,
                "actual_engine_payloads": {
                    "receipt.json": {
                        "result": {"code": "NO_NATIVE_PORT", "status": "TYPED_REFUSAL"}
                    }
                },
                "unreadable_engine_payloads": refused,
            },
            [],
        )
        == "CURRENT_ENGINE_REFUSAL"
    )
    audits = [
        {
            "status": "AUDIT_EXECUTED",
            "outputs": [
                {
                    "native_valid_witness_verified": True,
                    "result": {
                        "near_miss_results": [
                            {"result": {"status": "REFUSED_INVALID"}} for _ in range(4)
                        ]
                    },
                }
            ],
        }
        for _ in range(2)
    ]
    diagnostic = {
        "dispatch_return": 0,
        "actual_engine_payloads": {},
        "unreadable_engine_payloads": refused,
    }
    composed = replay.compose_phi2_port(diagnostic, audits)
    assert composed["unreadable_engine_payloads"] == refused
    assert composed["canonical_adapter_diagnostic"]["unreadable_engine_payloads"] == refused
    assert replay.demo_execution_status(composed, audits) == "DEMO_RECREATION_RESIDUAL"
    missing_payloads, missing_refused = replay.engine_json_payloads(tmp_path / "missing")
    assert missing_payloads == {} and missing_refused == []


def test_native_trace_reads_result_boolean_property(tmp_path):
    mod_name = "operating_system.python.adapters.rust_host.ffi"
    module = types.ModuleType(mod_name)

    class Host:
        def invoke_runtime(self, action, payload):
            return types.SimpleNamespace(
                is_ok=True, unwrap=lambda: {"success": True, "action": action}
            )

    module.RustSymbolGameHost = Host
    previous = sys.modules.get(mod_name)
    sys.modules[mod_name] = module
    try:
        replay.trace_native_calls(tmp_path)
        assert Host().invoke_runtime("fixture", {}).is_ok is True
        tape = replay.load((tmp_path / "native_calls.jsonl").read_bytes().strip())
        assert tape["response"] == {"success": True, "action": "fixture"}
    finally:
        if previous is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = previous


def test_package_local_import_routing_does_not_use_ambient_namespace():
    raw = b"from reference_solver.lean_compiler import check\ndef math(x):\n    return x + 1\n"
    adapted, changes = replay.relocate_source(
        raw, "challenges/e_formal_math/c041_fixture/judge_packet/checker.py"
    )
    assert (
        b"from paper011_source.challenges.e_formal_math.c041_fixture.reference_solver.lean_compiler"
        in adapted
    )
    assert changes[0]["kind"] == "BIND_PACKAGE_LOCAL_IMPORT"
    assert ast.dump(ast.parse(raw).body[1]) == ast.dump(ast.parse(adapted).body[1])


def test_relative_imports_are_preserved_even_with_package_local_module_names():
    raw = b"from ..reference_solver.solver import solve\n"
    adapted, changes = replay.relocate_source(
        raw, "challenges/c_quantum/c024_fixture/judge_packet/checker.py"
    )
    assert ast.dump(ast.parse(raw)) == ast.dump(ast.parse(adapted))
    assert changes == []


def test_branching_original_gate_is_not_counted_as_two_independent_checkers(tmp_path, monkeypatch):
    for name, raw in {
        "case.json": b"{}",
        "mutation.json": b'{"case":{},"answer":{"invalid":true}}',
    }.items():
        (tmp_path / name).write_bytes(raw)

    def ref(name):
        return {
            "path": name,
            "index": None,
            "sha256": replay.digest((tmp_path / name).read_bytes()),
        }

    row = {
        "id": "C042",
        "kind": "REFERENCE_AND_CHECKER_RECREATION",
        "package": ".",
        "module": "fixture",
        "checker_contract": "DECLARED_BRANCH_EVALUATOR",
        "solver": {"function": "solve"},
        "checkers": [{"function": "evaluate_dual"}],
        "cases": [ref("case.json")],
        "mutations": [ref("mutation.json")],
    }
    monkeypatch.setattr(
        replay,
        "_callable",
        lambda _, entry: (lambda case: {"status": "SOLVED", "kind": "SAT"})
        if entry["function"] == "solve"
        else (lambda case, answer: "invalid" not in answer),
    )
    result = replay.reference_challenge(row, tmp_path, io.BytesIO())
    assert result["counts"]["all_declared_accept"] == result["counts"]["all_declared_reject"] == 1
    assert result["counts"]["both_accept"] == result["counts"]["both_reject"] == 0
    assert result["declared_checker_count"] == 1
    assert result["algorithm_independence"] == "NOT_ESTABLISHED_BY_AGREEMENT"


def test_lean_discovery_requires_the_explicit_pinned_capability(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda command, *args, **kwargs: "ambient_lean.exe")
    monkeypatch.setattr(replay.socket, "socket", replay.socket.socket)
    monkeypatch.setattr(replay.socket, "create_connection", replay.socket.create_connection)
    monkeypatch.setattr(replay.socket, "getaddrinfo", replay.socket.getaddrinfo)
    monkeypatch.setattr(replay.subprocess, "run", replay.subprocess.run)
    monkeypatch.setattr(sys, "meta_path", list(sys.meta_path))
    monkeypatch.setenv("CORE_SYMBOL_GAME_HOST", "before")
    monkeypatch.setenv("PAPER011_ENGINE_ROOT", "before")
    lock = {"engine_root": str(tmp_path), "binaries": {"symbol_game": {"path": "host.exe"}}}
    replay.configure_worker(tmp_path, lock, [])
    assert shutil.which("lean") is None
    lock["binaries"]["lean"] = {"path": "explicit_kernel.exe"}
    assert shutil.which("lean") == "explicit_kernel.exe"


def test_lean_file_mode_tape_retains_proof_judge_and_generated_module(tmp_path, monkeypatch):
    kernel = tmp_path / "lean.exe"
    kernel.write_bytes(b"explicit kernel fixture")
    work = tmp_path / "compiler_work"
    work.mkdir()
    proof = b"theorem bound : True := by trivial\n"
    judge = b"import Submission\n#print axioms bound\n"
    (work / "Submission.lean").write_bytes(proof)
    (work / "Judge.lean").write_bytes(judge)
    output = tmp_path / "output"
    output.mkdir()
    corrupt = {"proof": False}

    def compiler(command, *args, **kwargs):
        if corrupt["proof"]:
            (work / "Submission.lean").write_bytes(b"changed during native call")
        (work / "Submission.olean").write_bytes(b"generated module bytes")
        return replay.subprocess.CompletedProcess(command, 0, stdout=b"checked", stderr=b"")

    monkeypatch.setattr(shutil, "which", shutil.which)
    monkeypatch.setattr(replay.socket, "socket", replay.socket.socket)
    monkeypatch.setattr(replay.socket, "create_connection", replay.socket.create_connection)
    monkeypatch.setattr(replay.socket, "getaddrinfo", replay.socket.getaddrinfo)
    monkeypatch.setattr(replay.subprocess, "run", compiler)
    monkeypatch.setattr(sys, "meta_path", list(sys.meta_path))
    monkeypatch.setenv("CORE_SYMBOL_GAME_HOST", "before")
    monkeypatch.setenv("PAPER011_ENGINE_ROOT", "before")
    lock = {
        "engine_root": str(tmp_path),
        "binaries": {
            "symbol_game": {"path": "host.exe"},
            "lean": {"path": str(kernel), "sha256": replay.digest(kernel.read_bytes())},
        },
    }
    replay.configure_worker(tmp_path, lock, [], output)
    command = [str(kernel), "-o", "Submission.olean", "Submission.lean"]
    replay.subprocess.run(command, cwd=str(work), capture_output=True, text=True)
    call = replay.load((output / "native_transport_calls.jsonl").read_bytes())
    assert call["command"] == command
    assert call["work_files_before"]["Submission.lean"]["bytes_hex"] == proof.hex()
    assert call["work_files_before"]["Judge.lean"]["sha256"] == replay.digest(judge)
    assert (
        call["work_files_after"]["Submission.olean"]["bytes_hex"] == b"generated module bytes".hex()
    )
    assert call["process_exit"] == 0 and call["stdout_bytes_hex"] == b"checked".hex()
    corrupt["proof"] = True
    with pytest.raises(replay.ReplayError, match="LEAN_INPUT_BYTES_CHANGED"):
        replay.subprocess.run(command, cwd=str(work), capture_output=True, text=True)


def test_native_tape_captures_physical_bytes_and_returns_original_text_view(tmp_path, monkeypatch):
    binary = tmp_path / "native.exe"
    binary.write_bytes(b"explicit native fixture")
    stdout = "é\r\n".encode("utf-8")
    stderr = b"\xff\r\n"

    def native(command, *args, **kwargs):
        assert kwargs["text"] is False and "encoding" not in kwargs and "errors" not in kwargs
        assert kwargs["input"] == "λ\r\n".encode("utf-8")
        return replay.subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(shutil, "which", shutil.which)
    monkeypatch.setattr(replay.socket, "socket", replay.socket.socket)
    monkeypatch.setattr(replay.socket, "create_connection", replay.socket.create_connection)
    monkeypatch.setattr(replay.socket, "getaddrinfo", replay.socket.getaddrinfo)
    monkeypatch.setattr(replay.subprocess, "run", native)
    monkeypatch.setattr(sys, "meta_path", list(sys.meta_path))
    monkeypatch.setenv("CORE_SYMBOL_GAME_HOST", "before")
    monkeypatch.setenv("PAPER011_ENGINE_ROOT", "before")
    lock = {
        "engine_root": str(tmp_path),
        "binaries": {
            "symbol_game": {"path": str(binary), "sha256": replay.digest(binary.read_bytes())}
        },
    }
    replay.configure_worker(tmp_path, lock, [], tmp_path)
    result = replay.subprocess.run(
        [str(binary)],
        input="λ\r\n",
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    assert result.stdout == "é\n" and result.stderr == "\ufffd\n"
    event = replay.load((tmp_path / "native_transport_calls.jsonl").read_bytes())
    assert event["stdout_bytes_hex"] == stdout.hex() and event["stderr_bytes_hex"] == stderr.hex()
    assert event["request_bytes_hex"] == "λ\r\n".encode("utf-8").hex()
    assert event["stdio_capture"] == "RAW_SUBPROCESS_BYTES"
    assert event["source_text_view"]["errors"] == "replace"


def test_fresh_cache_prefix_reads_source_instead_of_existing_stale_bytecode(tmp_path, monkeypatch):
    path = tmp_path / "cached.py"
    path.write_bytes(b"value = 1\n")
    info = path.stat()
    py_compile.compile(str(path), doraise=True)
    path.write_bytes(b"value = 2\n")
    os.utime(path, (info.st_atime, info.st_mtime))
    cached = importlib.util.spec_from_file_location("stale_fixture", path)
    module = importlib.util.module_from_spec(cached)
    cached.loader.exec_module(module)
    assert module.value == 1
    prefix = tmp_path / "fresh_cache"
    prefix.mkdir()
    monkeypatch.setattr(sys, "pycache_prefix", str(prefix))
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    fresh = importlib.util.spec_from_file_location("fresh_fixture", path)
    module = importlib.util.module_from_spec(fresh)
    fresh.loader.exec_module(module)
    assert module.value == 2
    assert list(prefix.iterdir()) == []


def test_worker_refuses_an_ambient_cache_prefix_before_engine_import(tmp_path, monkeypatch):
    prefix = tmp_path / "fresh"
    prefix.mkdir()
    monkeypatch.setattr(sys, "pycache_prefix", "ambient")
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    with pytest.raises(replay.ReplayError, match="FRESH_BYTECODE_CACHE"):
        replay.worker(
            {
                "source_root": str(tmp_path),
                "output_dir": str(tmp_path),
                "pycache_prefix": str(prefix),
            }
        )


def test_runtime_profile_and_verifier_bytes_are_bound_before_validation(tmp_path):
    profile = tmp_path / "runtime.json"
    profile.write_bytes(b'{"schema_version":"paper011.runtime-environment.v1"}')
    verifier = tmp_path / "verify.py"
    verifier.write_bytes(
        b"def verify(profile):\n    return {'status':'DECLARED_RUNTIME_FILES_UNCHANGED'}\n"
    )
    lock = {
        "runtime_environment": {
            "schema_version": "paper011.runtime-environment.v1",
            "profile_path": str(profile),
            "profile_sha256": replay.digest(profile.read_bytes()),
            "verifier_path": str(verifier),
            "verifier_sha256": replay.digest(verifier.read_bytes()),
        }
    }
    replay.verify_runtime_environment(lock, full_runtime=True)
    verifier.write_bytes(b"changed")
    with pytest.raises(replay.ReplayError, match="RUNTIME_ENVIRONMENT_BYTES_CHANGED"):
        replay.verify_runtime_environment(lock, full_runtime=False)


def test_c060_dual_rejection_is_distinct_from_detection_crash_and_incomparability(
    tmp_path, monkeypatch
):
    (tmp_path / "case.json").write_bytes(b'{"case":{},"cert":{}}')
    row = {
        "id": "C060",
        "kind": "REFERENCE_AND_CHECKER_RECREATION",
        "package": ".",
        "module": "fixture",
        "solver": {"function": "solve"},
        "checkers": [{"function": "first"}, {"function": "second"}],
        "cases": [
            {
                "path": "case.json",
                "index": None,
                "sha256": replay.digest((tmp_path / "case.json").read_bytes()),
            }
        ],
        "mutations": [],
    }

    def checker(which):
        def check(case, answer):
            if answer["kind"] == "incomparable":
                return "PASS"
            return answer["kind"] == "valid" or (
                answer["kind"] == "disagreement" and which == "second"
            )

        return check

    monkeypatch.setattr(
        replay,
        "_callable",
        lambda _, entry: (lambda case, cert: {"kind": "valid", "verdict": "ACCEPT"})
        if entry["function"] == "solve"
        else checker(entry["function"]),
    )

    def crash(case, cert):
        raise ValueError("mutant failure")

    module = types.SimpleNamespace(
        get_mutants=lambda: {
            "dual": lambda case, cert: {"kind": "dual"},
            "disagreement": lambda case, cert: {"kind": "disagreement"},
            "crash": crash,
            "incomparable": lambda case, cert: {"kind": "incomparable"},
        }
    )
    monkeypatch.setattr(importlib, "import_module", lambda name: module)
    result = replay.reference_challenge(row, tmp_path, io.BytesIO())
    counts = result["counts"]
    assert counts["both_reject"] == 1
    assert counts["mutation_joint_detections"] == 2
    assert counts["mutation_checker_disagreements"] == 1
    assert counts["mutation_execution_errors"] == 1
    assert counts["mutation_incomparable_records"] == 1
    assert counts["source_gate_mutant_detections"] == 3
    assert counts["mutation_both_accept"] == 0


def test_nonfinite_mutation_bytes_refuse_without_aborting_remaining_mutations(
    tmp_path, monkeypatch
):
    for name, raw in {
        "case.json": b"{}",
        "bad.json": b'{"answer":NaN}',
        "good.json": b'{"case":{},"answer":{"invalid":true}}',
    }.items():
        (tmp_path / name).write_bytes(raw)

    def descriptor(name):
        return {
            "path": name,
            "index": None,
            "sha256": replay.digest((tmp_path / name).read_bytes()),
        }

    row = {
        "id": "C057",
        "kind": "REFERENCE_AND_CHECKER_RECREATION",
        "package": ".",
        "module": "fixture",
        "solver": {"function": "solve"},
        "checkers": [{"function": "first"}, {"function": "second"}],
        "cases": [descriptor("case.json")],
        "mutations": [descriptor("bad.json"), descriptor("good.json")],
    }
    monkeypatch.setattr(
        replay,
        "_callable",
        lambda _, entry: (lambda case: {"status": "SOLVED"})
        if entry["function"] == "solve"
        else (lambda case, answer: "invalid" not in answer),
    )
    stream = io.BytesIO()
    result = replay.reference_challenge(row, tmp_path, stream)
    assert result["counts"]["malformed_mutation_records"] == 1
    assert result["counts"]["mutations"] == result["counts"]["both_reject"] == 1
    assert b"MALFORMED_SOURCE_BYTES_REFUSED" in stream.getvalue()
    assert not result["complete_mutation_execution"]


def test_coverage_requires_closed_batch_and_every_receipts_actual_artifacts(tmp_path):
    primary = tmp_path / "batch"
    primary.mkdir()
    rows = []
    for number in range(87):
        cid = "C041" if number == 0 else f"fixture_{number}"
        folder = primary / cid
        folder.mkdir()
        receipt = {
            "schema_version": replay.SCHEMA,
            "id": cid,
            "kind": "challenge",
            "result": {"status": "REFERENCE_RESIDUAL", "counts": {"cases": 64, "mutations": 48}}
            if number == 0
            else {"status": "FINITE_MECHANISM_REPLAY"},
            "process_exit": 0,
            "runner_sha256": "a" * 64,
            "capability_sha256": "b" * 64,
            "artifacts_sha256": {},
        }
        receipt["receipt_sha256"] = replay.digest(replay.canonical(receipt))
        (folder / "recreation_receipt.json").write_bytes(replay.canonical(receipt))
        rows.append({"id": cid, "receipt_sha256": receipt["receipt_sha256"]})
    batch = {
        "runs": rows,
        "full_catalog_requested": True,
        "source_inventory_sha256": "c" * 64,
        "custody_recheck": "ENTIRE_DECLARED_SOURCE_AND_ENGINE_REHASHED_AFTER_ALL_SUBPROCESSES",
    }
    batch["receipt_sha256"] = replay.digest(replay.canonical(batch))
    (primary / "batch_receipt.json").write_bytes(replay.canonical(batch))
    result = replay.coverage_matrix(primary, [], tmp_path / "coverage.json")
    assert len(result["rows"]) == 87
    assert not result["all_recreations_completed"]
    supplementary = tmp_path / "supplement"
    leaf = supplementary / "C041"
    leaf.mkdir(parents=True)
    receipt = {
        "schema_version": replay.SCHEMA,
        "id": "C041",
        "kind": "challenge",
        "result": {
            "execution_scope": "SUPPLEMENTAL_SELECTED_CANDIDATES",
            "selected_case_count": 2,
            "supplemental_control_count": 4,
        },
        "artifacts_sha256": {},
    }
    receipt["receipt_sha256"] = replay.digest(replay.canonical(receipt))
    (leaf / "recreation_receipt.json").write_bytes(replay.canonical(receipt))
    batch["runs"] = [{"id": "C041", "receipt_sha256": receipt["receipt_sha256"]}]
    batch["full_catalog_requested"] = False
    del batch["receipt_sha256"]
    batch["receipt_sha256"] = replay.digest(replay.canonical(batch))
    (supplementary / "batch_receipt.json").write_bytes(replay.canonical(batch))
    result = replay.coverage_matrix(primary, [supplementary], tmp_path / "joined.json")
    original = next(row for row in result["rows"] if row["id"] == "C041")
    assert original["counts"]["cases"] == 64 and original["counts"]["mutations"] == 48
    assert result["supplemental_candidate_checks"][0]["result"]["selected_case_count"] == 2
    (primary / "C041" / "unreceipted.txt").write_bytes(b"changed")
    with pytest.raises(replay.ReplayError, match="ARTIFACT_CUSTODY"):
        replay.coverage_matrix(primary, [], tmp_path / "invalid.json")
