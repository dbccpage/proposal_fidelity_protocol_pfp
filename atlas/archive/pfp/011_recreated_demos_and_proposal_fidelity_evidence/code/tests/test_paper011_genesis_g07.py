"""G07 custody and contract controls, using retained actual replay artifacts."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("_paper011_g07_test", PAPER / "code/genesis_g07_replay.py")
assert spec and spec.loader
g07 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g07
spec.loader.exec_module(g07)
AREA = PAPER / "docs/history_recovery/g07"


@pytest.fixture(scope="module")
def artifacts():
    base = AREA / "run_v1"
    return (json.loads((base / "native_request.json").read_bytes()),
            json.loads((base / "native_stdout.json").read_bytes()),
            json.loads((base / "result.json").read_bytes()))


def test_fixed_original_source_closure():
    manifest = g07.verify_sources()
    assert len(manifest["entries"]) == 82
    assert sum(row["bytes"] for row in manifest["entries"]) == 715794
    assert sum(row["repository"] == "19L57G1" for row in manifest["entries"]) == 10


def test_rehashed_manifest_cannot_substitute_source(tmp_path, monkeypatch):
    manifest = json.loads(g07.MANIFEST.read_bytes())
    manifest["entries"][0]["sha256"] = "0" * 64
    replacement = tmp_path / "manifest.json"
    replacement.write_bytes(g07.wire(manifest))
    monkeypatch.setattr(g07, "MANIFEST", replacement)
    with pytest.raises(ValueError, match="FIXED_SOURCE_MANIFEST_CHANGED"):
        g07.verify_sources()


def test_corrupt_raw_source_fails_without_repinning(tmp_path, monkeypatch):
    entry = json.loads(g07.MANIFEST.read_bytes())["entries"][0]
    replacement = tmp_path / entry["local"]
    replacement.parent.mkdir(parents=True)
    replacement.write_bytes((PAPER / entry["local"]).read_bytes() + b"corrupt")
    monkeypatch.setattr(g07, "PAPER", tmp_path)
    with pytest.raises(ValueError, match="SOURCE_BYTES_CHANGED"):
        g07.verify_sources()


def test_actual_complete_native_cases_agree(artifacts):
    payload, response, result = artifacts
    g07.check_native(payload, response, result["trees"], result["trajectories"])
    assert len(payload["cases"]) == len(response["cases"]) == 3617
    assert sum(row["population"] == "P2" for row in payload["cases"]) == 87
    assert all(row["all_responses_valid_naive"] is True for row in response["cases"])


@pytest.mark.parametrize("mutation", ["width", "depth", "state", "class_sizes", "dropped", "duplicate"])
def test_case_and_certificate_mutations_rejected(artifacts, mutation):
    payload, original, result = artifacts
    response = copy.deepcopy(original)
    row = response["cases"][0]
    if mutation in ("width", "depth"):
        row[mutation] += 1
    elif mutation == "state":
        row["state"]["data"][0] += "corrupt"
    elif mutation == "class_sizes":
        row["class_sizes"][0] += 1
    elif mutation == "dropped":
        response["cases"].pop()
    else:
        response["cases"].append(response["cases"][0])
    with pytest.raises(ValueError, match="NATIVE_CASE"):
        g07.check_native(payload, response, result["trees"], result["trajectories"])


def test_all_original_heldouts_and_poison(artifacts):
    _, _, result = artifacts
    cases = {(row["case"]["reading"], row["case"]["population"], row["case"]["depth"]) for row in result["heldouts"]}
    expected = {(reading, population, depth) for reading in ("L", "F")
                for population, depths in (("P1", range(4, 16)), ("P2", range(51, 61))) for depth in depths}
    assert cases == expected
    for row in result["heldouts"]:
        assert row["case_sha256"] == g07.sha(g07.wire(row["case"]))
        assert g07.solve(row["case"], result) == row["response"]
    assert result["poisoned_request"]["status"] == "OUT_OF_SCOPE"
    assert g07.solve({"reading": "L", "population": "P1", "depth": 16}, result)["status"] == "OUT_OF_SCOPE"
    assert g07.solve({"reading": "F", "population": "P2", "depth": 61}, result)["status"] == "OUT_OF_SCOPE"
    with pytest.raises(ValueError, match="MALFORMED_CASE"):
        g07.solve({"reading": "L", "population": "P1", "depth": True}, result)


def test_complete_reconciliation_relabel_and_actual_controls(artifacts):
    payload, response, result = artifacts
    assert [tree["expanded_ties"] for tree in result["trees"]] == [236, 236, 422, 422]
    assert result["trees"][0]["histograms"] == result["trees"][1]["histograms"]
    assert result["trees"][2]["histograms"] == result["trees"][3]["histograms"]
    controls = g07.mutation_controls(payload, response, result["trees"], result["trajectories"])
    assert len(controls) == 6 and all(row["rejected"] is True for row in controls)
    rows = [row for entry in [*result["trees"], *result["trajectories"]] for row in entry["rows"]]
    assert max(row["width"] for row in rows) == 11
    assert g07.valid_conjecture(rows, 11, "OPEN", True, "width > 11")
    assert not g07.valid_conjecture(rows, 0, "OPEN", True, "width > 0")
    assert not g07.valid_conjecture(rows, 11, "PROVED", True, "width > 11")


def test_native_quiet_census_custody_and_no_vacuous_widths(artifacts):
    _, _, result = artifacts
    request = json.loads((AREA / "quiet_v1/request.json").read_bytes())
    response = json.loads((AREA / "quiet_v1/stdout.json").read_bytes())
    expected_ids = {(row["reading"], quiet["depth"]) for row in result["trajectories"] for quiet in row["quiet_states"]}
    actual_ids = {(row["id"].split(":")[1], row["depth"]) for row in request["cases"]}
    assert len(request["cases"]) == len(response["cases"]) == 35
    assert actual_ids == expected_ids
    assert ("L", 60) in actual_ids
    for want, got in zip(request["cases"], response["cases"], strict=True):
        assert all(want[key] == got[key] for key in ("id", "depth", "state"))
        assert got["width"] is None and got["offered_challenges"] == []
    receipt = json.loads((AREA / "quiet_v1/receipt.json").read_bytes())
    assert all(row["returncode"] != 0 for row in receipt["controls"])
    assert {row["mutation"] for row in receipt["controls"]} == {"NONQUIET_STATE", "UNKNOWN_EVENT", "MALFORMED_HISTORY", "DUPLICATE_CASE"}


def test_process_streams_native_libraries_and_executable_byte_identity():
    base = AREA / "run_v1"
    receipt = json.loads((base / "receipt.json").read_bytes())
    build = json.loads((AREA / "build/receipt.json").read_bytes())
    for name, key in [("result.json", "result_sha256"), ("native_request.json", "native_request_sha256"),
                      ("native_stdout.json", "native_stdout_sha256"), ("native_stderr.txt", "native_stderr_sha256")]:
        assert g07.sha((base / name).read_bytes()) == receipt[key]
    assert receipt["runner_sha256"] == g07.sha((PAPER / "code/genesis_g07_replay.py").read_bytes())
    assert receipt["build_receipt_sha256"] == g07.sha((AREA / "build/receipt.json").read_bytes())
    assert receipt["native_executable_sha256_before"] == receipt["native_executable_sha256_after"] == build["native_executable_sha256"]
    assert g07.sha(Path(receipt["native_executable"]).read_bytes()) == build["native_executable_sha256"]
    assert build["existing_hosts_before"] == build["existing_hosts_after"]
    assert build["registry_files_before"] == build["registry_files_after"]
    for name, digest in build["existing_hosts_after"].items():
        assert g07.sha((Path(build["existing_host_directory"]) / name).read_bytes()) == digest
    assert receipt["runtime"]["dont_write_bytecode"] is True
    assert list(Path(receipt["runtime"]["cache_prefix"]).iterdir()) == []
    completion = json.loads((AREA / "provider_free_completion.json").read_bytes())
    assert completion["base_receipt_sha256"] == g07.sha((base / "receipt.json").read_bytes())
    assert completion["quiet_receipt_sha256"] == g07.sha((AREA / "quiet_v1/receipt.json").read_bytes())
    assert completion["finite_computation_gate"] is True
    assert completion["model_arms_executed"] == [] and completion["empirical_differentiation_gate"] is False
    assert result_no_model_claims(base)


def result_no_model_claims(base):
    result = json.loads((base / "result.json").read_bytes())
    return (result["model_arms_executed"] == [] and result["empirical_differentiation_gate"] is False
            and result["full_g07_experiment_completed"] is False and result["conjecture"]["proved"] is False)
