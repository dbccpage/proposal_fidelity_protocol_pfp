"""Audit the complete retained G03 finite run without invoking either oracle."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("_paper011_test_g03", PAPER / "code/genesis_g03_replay.py")
assert spec and spec.loader
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay
spec.loader.exec_module(replay)
bridge_spec = importlib.util.spec_from_file_location("_paper011_test_g03_bridge", PAPER / "code/genesis_g03_key_bridge.py")
assert bridge_spec and bridge_spec.loader
bridge = importlib.util.module_from_spec(bridge_spec)
sys.modules[bridge_spec.name] = bridge
bridge_spec.loader.exec_module(bridge)


@pytest.fixture(scope="module")
def evidence():
    area = replay.AREA
    return {name: json.loads((area / file).read_bytes()) for name, file in
            (("receipt", "receipt.json"), ("request", "full_native_request.json"),
             ("response", "full_native_stdout.json"), ("reference", "reference_rows.json"),
             ("log", "source_call_log.json"), ("carriers", "carriers.json"), ("witnesses", "key_correspondences.json"))}


def test_fixed_source_blobs_and_preoracle_declaration(evidence):
    manifest = replay.verify_sources()
    declared = replay.declaration()
    receipt = evidence["receipt"]
    assert len(manifest["entries"]) == 4
    assert declared["no_g03_engine_oracle_invoked_before_this_declaration"]
    assert declared["operator_written_new_structure"] and not declared["historical_adapter_reconstruction"]
    assert receipt["preregistration_sha256"] == replay.sha((replay.AREA / "preregistration.json").read_bytes())
    assert "excluded from collapse but included in canonical keys" in declared["structural_effect"]


def test_all_original_pairs_reached_each_engine_with_actual_arguments(evidence):
    request, response, log = (evidence[name] for name in ("request", "response", "log"))
    replay.check_calls(request["cases"], response["calls"])
    assert len(response["calls"]) == 9792 and len(log) == 3264
    base = [r for r in response["calls"] if r["variant"] == "base"]
    primary = [r for r in base if r["n"] <= 15]
    held = [r for r in base if r["n"] >= 16]
    assert len(primary) == 1820 and len(held) == 1444
    assert len({(replay.wire(r["base_canonical_key"]), tuple(r["target"]), r["measure"]) for r in primary}) == 1820
    for reading in ("L", "F"):
        for measure in ("mu1", "mu2"):
            rows = [r for r in base if r["reading"] == reading and r["measure"] == measure]
            for n in range(3, 19):
                actual = {(r["i"], r["j"]) for r in rows if r["n"] == n}
                assert actual == {(i, j) for i in range(1, n) for j in range(i + 1, n)}
    assert {r["id"] for r in log} == {r["id"] for r in base}
    by_id = {r["id"]: r for r in base}
    key_map = {replay.wire(r["native_key"]): r["sealed_key"] for r in evidence["witnesses"]}
    for call in log:
        row = by_id[call["id"]]
        assert call["base_canonical_key"] == key_map[replay.wire(row["base_canonical_key"])]
        assert call["target"] == row["target"] and call["measure"] == row["measure"]
        assert call["bounds"] == {"max_items": 2, "max_arity": 2}


def test_independent_complete_certificates_and_relabel_controls(evidence):
    modules = replay.original()
    for witness in evidence["witnesses"]:
        bridge.verify_witness(modules, witness)
    indices = [0, 2, 4]  # Original n3 L mu1 base, token rename, and reversal.
    response = dict(evidence["response"], calls=[evidence["response"]["calls"][i] for i in indices])
    cases = [evidence["request"]["cases"][i] for i in indices]
    keys = {replay.wire(k) for row in response["calls"] for k in [row["base_canonical_key"], *(c["key"] for c in row["classes"]) ]}
    witnesses = [r for r in evidence["witnesses"] if replay.wire(r["native_key"]) in keys]
    bridge.check(modules, cases, response, evidence["reference"][:1], witnesses)
    rows = evidence["response"]["calls"]
    assert sum(r["variant"] == "token_renaming" for r in rows) == 3264
    assert sum(r["variant"] == "reversal" for r in rows) == 3264


def test_failed_strict_label_comparison_is_retained(evidence):
    failure = json.loads((replay.AREA / "strict_label_failure.json").read_bytes())
    assert failure["original_worker_reported_exit_code"] == 1
    assert failure["status"] == "UNVERIFIED_STRICT_LABEL_COMPARISON" and not failure["passing_fallback_used"]
    with pytest.raises(ValueError, match="INDEPENDENT_SOURCE_NATIVE_DISAGREEMENT"):
        replay.match_native(evidence["request"]["cases"], evidence["response"], evidence["reference"])
    assert not evidence["receipt"]["original_worker_completed"]
    assert not evidence["receipt"]["original_worker_final_runtime_receipt_emitted"]


@pytest.mark.parametrize("mutation", ["duplicate_image", "altered_sealed_key", "native_key_digest"])
def test_key_bridge_cannot_certify_corrupt_bijections_or_bytes(evidence, mutation):
    record = copy.deepcopy(evidence["witnesses"][0])
    if mutation == "duplicate_image":
        record["data_bijection"][0] = record["data_bijection"][1]
    elif mutation == "altered_sealed_key":
        record["sealed_key"][0] += 1
    else:
        record["native_key_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        bridge.verify_witness(replay.original(), record)


def test_sealed_isomorphism_budget_error_remains_typed(evidence):
    modules = replay.original()
    actual = bridge.key_regime(modules, evidence["witnesses"][0]["native_key"])
    with pytest.raises(modules["iso"].IsoBudgetError, match="declared budget"):
        modules["iso"].canonical_witness(actual, perm_budget=0)


def test_original_prefixes_all_pair_collapse_and_injectivity(evidence):
    modules = replay.original()
    adapter = replay.adapter
    for n in range(3, 19):
        for reading in ("L", "F"):
            regime, history = adapter.construct(modules, n, reading)
            prefix = getattr(modules["engine"], "READING_" + reading).genesis
            assert tuple(history[:len(prefix)]) == prefix
            recorded = evidence["carriers"][f"{n}:{reading}:base"]
            assert recorded["state"] == replay.source.state(regime)
            observed = set(modules["observe"].collapsed_pairs(regime))
            images = set()
            for i in range(n + 1):
                for j in range(i + 1, n + 1):
                    image = tuple(sorted((adapter.coordinate(n, reading, i), adapter.coordinate(n, reading, j))))
                    assert image not in images
                    images.add(image)
                    assert (image in observed) == (1 <= i < j < n)
            assert not regime.rules


@pytest.mark.parametrize("mutation", ["drop", "duplicate", "fixed_target", "wrong_domain"])
def test_forged_call_logs_cannot_pass(evidence, mutation):
    cases = evidence["request"]["cases"][:1]
    calls = copy.deepcopy(evidence["response"]["calls"][:1])
    if mutation == "drop":
        calls.clear()
    elif mutation == "duplicate":
        calls += copy.deepcopy(calls)
    elif mutation == "fixed_target":
        calls[0]["target"] = [0, 1]
    else:
        calls[0]["predicate_domain"] = "raw_deltas"
    with pytest.raises(ValueError):
        replay.check_calls(cases, calls)


def test_raw_deltas_and_forged_class_certificate_are_refused(evidence):
    calls = evidence["response"]["calls"]
    index = next(i for i, row in enumerate(calls) if any(c["size"] > 1 for c in row["classes"]))
    cases = evidence["request"]["cases"][index:index + 1]
    mutated = copy.deepcopy(calls[index:index + 1])
    mutated[0]["classes"] = [dict(c, size=1, members=[m], representative=m)
                             for c in mutated[0]["classes"] for m in c["members"]]
    with pytest.raises(ValueError, match="RAW_DELTAS_USED_AS_CLASSES"):
        replay.check_calls(cases, mutated)
    response = dict(evidence["response"])
    response["calls"] = copy.deepcopy(calls[:1])
    response["calls"][0]["classes"][0]["key"][0] += 1
    with pytest.raises((ValueError, KeyError)):
        bridge.check(replay.original(), evidence["request"]["cases"][:1], response,
                     evidence["reference"][:1], evidence["witnesses"])


def test_actual_named_native_mutations_and_restoration(evidence):
    controls = {row["mutation"]: row for row in evidence["receipt"]["mutations"]}
    expected = {"FIXED_TARGET_REUSE": "FIXED_TARGET_REUSE",
                "POISONED_COLLAPSE_ADAPTER": "CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH",
                "PREDICATES_NOT_ON_CLASSES": "PREDICATES_NOT_ON_CLASSES", "DUPLICATED_PAIR": "DUPLICATE_PAIR_CASE"}
    for name, reason in expected.items():
        control = controls[name]
        assert control["reason"] == reason and control["process"]["returncode"] != 0
        raw = (replay.AREA / (name.lower() + "_stderr.txt")).read_bytes()
        assert replay.sha(raw) == control["process"]["stderr_sha256"]
        assert raw.decode().strip() == reason
    assert controls["RESTORED_TARGET"]["process"]["returncode"] == 0
    restored = json.loads((replay.AREA / "restored_target_stdout.json").read_bytes())
    assert restored["calls"] == evidence["response"]["calls"][:1]
    assert {"DROPPED_PAIR", "DUPLICATED_CALL_LOG", "RAW_DELTAS_AS_CLASSES", "STALE_SCRIPT_RECEIPT"} <= set(controls)


def test_original_count_preserving_poison_and_actual_restoration(evidence):
    completion = json.loads((replay.AREA / "completion_receipt.json").read_bytes())
    assert completion["primary_receipt_sha256"] == replay.sha((replay.AREA / "receipt.json").read_bytes())
    assert len(completion["original_collapse_pairs"]) == len(completion["poisoned_collapse_pairs"]) == 3
    assert completion["original_collapse_pairs"] != completion["poisoned_collapse_pairs"]
    assert completion["all_chain_pair_correspondence_violations"]
    assert completion["count_preserving_poison_process"]["returncode"] == 2
    assert completion["count_preserving_poison_reason"] == "CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH"
    assert completion["restoration_process"]["returncode"] == 0
    restored = json.loads((replay.AREA / "count_preserving_poison_restoration_stdout.json").read_bytes())
    original = next(row for row in evidence["response"]["calls"] if row["id"] == "4:1:2:L:mu1:base")
    assert restored["calls"] == [original]
    assert completion["inputs_before"] == completion["inputs_after"]
    for path, expected in completion["inputs_after"].items():
        assert replay.sha(Path(path).read_bytes()) == expected
    assert not completion["full_G03_model_experiment_completed"] and not completion["original_Arm_E_success"]


def test_source_manifest_and_stale_script_corruption_are_refused(tmp_path, monkeypatch):
    original = json.loads((replay.AREA / "source_manifest.json").read_bytes())
    original["entries"].append(copy.deepcopy(original["entries"][0]))
    (tmp_path / "source_manifest.json").write_bytes(replay.wire(original))
    monkeypatch.setattr(replay, "AREA", tmp_path)
    with pytest.raises(ValueError, match="G03_SOURCE_SET_CHANGED"):
        replay.verify_sources()
    declared = json.loads((PAPER / "docs/history_recovery/g03/preregistration.json").read_bytes())
    declared["registered_files"]["code/genesis_g03_adapter.py"] = "0" * 64
    (tmp_path / "preregistration.json").write_bytes(replay.wire(declared))
    with pytest.raises(ValueError, match="PREREGISTERED_ADAPTER_OR_PREDICATE_CHANGED"):
        replay.declaration()


def test_false_predicates_are_retained_and_no_model_arm_is_promoted(evidence):
    receipt = evidence["receipt"]
    rows = [r for r in evidence["response"]["calls"] if r["n"] <= 15 and r["variant"] == "base"]
    for reading in ("L", "F"):
        for measure in ("mu1", "mu2"):
            selected = [r for r in rows if r["reading"] == reading and r["measure"] == measure]
            terminal = receipt["terminal_per_reading_measure"][reading + ":" + measure]
            for predicate in ("weak", "strong"):
                expected = next(([r["n"], r["i"], r["j"]] for r in selected if not r[predicate]), "holds on all 455")
                assert terminal[predicate] == expected
    assert receipt["complete_provider_free_finite_gate"]
    assert not receipt["full_G03_model_experiment_completed"]
    assert not receipt["entire_external_estate_workflow_executed"] and not receipt["external_owner_PR_created"]
    declaration = replay.declaration()
    assert declaration["original_model_arms_executed"] == [] and not declaration["original_Arm_E_success"]


def test_actual_raw_artifacts_runtime_and_dependency_custody(evidence):
    receipt = evidence["receipt"]
    assert receipt["inputs_before"] == receipt["inputs_after"]
    for path, expected in receipt["inputs_after"].items():
        assert replay.sha(Path(path).read_bytes()) == expected
    for name, expected in receipt["artifacts"].items():
        raw = (replay.AREA / name).read_bytes()
        assert replay.sha(raw) == expected
        assert replay.sha(raw + b"corruption") != expected
    for control in receipt["mutations"]:
        if "mutation_path" in control:
            assert replay.sha((PAPER / control["mutation_path"]).read_bytes()) == control["mutation_sha256"]
    assert receipt["dont_write_bytecode"] and receipt["cache_prefix"].endswith("runtime_cache_bridge_2")
    assert receipt["native_process"]["returncode"] == 0
    assert receipt["primary_distinct_calls"] == 1820
