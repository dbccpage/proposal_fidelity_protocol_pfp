"""Original-carrier and hostile-certificate checks for the integer replay."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
PAPER = CODE.parent
RUN = PAPER / "docs/native_dossier_integral/run_v3"
BUILD = PAPER / "docs/native_dossier_integral/build_v2"
spec = importlib.util.spec_from_file_location("paper011_integral_helper", CODE / "replay_dossier_homology.py")
helper = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helper
spec.loader.exec_module(helper)
runner_spec = importlib.util.spec_from_file_location("paper011_integral_runner", CODE / "replay_dossier_integral.py")
runner = importlib.util.module_from_spec(runner_spec)
sys.modules[runner_spec.name] = runner
runner_spec.loader.exec_module(runner)


def retained(name):
    return helper.strict((RUN / name).read_bytes())


def recorded_path(name: str) -> Path:
    """Resolve a receipt key from the repository root when it is not absolute.

    The integral run receipt stores the build receipt as a cwd-relative path.
    Hashing that key from the pytest working directory misses the file.
    """
    path = Path(name)
    if path.is_absolute():
        return path
    for candidate in (PAPER, *PAPER.parents):
        if (candidate / ".git").exists():
            return candidate / path
    return path


def test_all_original_integral_groups_and_mod2_crosscheck():
    outcomes = retained("compute_stdout.bin")["cases"]
    assert [row["case_id"] for row in outcomes[:8]] == list(helper.DOSSIERS)
    expected = [[1, 0, 0], [1, 0, 0], [1, 0, 1], [1, 0, 2],
                [1, 0, 0, 1], [1, 0, 0, 0], [1, 0, 0, 0, 1], [1, 0, 1, 2, 1]]
    for index, row in enumerate(outcomes[:8]):
        assert row["success"] is True
        result = row["result"]
        groups = result["integral_homology"]
        assert [h["free_rank"] for h in groups] == expected[index]
        assert all(h["mod2_dimension"] == h["uct_dimension"] for h in groups)
        assert result["boundary_law_verified"] is True
        assert result["uct_verified"] is True
        for h in groups:
            assert h["torsion"] == (["2"] if index == 5 and h["degree"] == 2 else [])
    assert [h["mod2_dimension"] for h in outcomes[5]["result"]["integral_homology"]] == [1, 0, 1, 1]


def test_entire_original_signed_carriers_are_preserved():
    import yaml  # noqa: PLC0415

    receipt = retained("receipt.json")
    helper.check_source_pins(receipt["sources_before"])
    helper.check_source_pins(receipt["sources_after"])
    source_root = Path(receipt["source_root"])
    requests = retained("compute_request.json")["cases"][:8]
    for name, request in zip(helper.DOSSIERS, requests, strict=True):
        original = helper.prepare_case(name, yaml.safe_load((source_root / name / "input.yaml").read_bytes()))
        assert request["matrices"] == original["matrices"]
        assert request["homology"] == original["homology"]
        assert request["carrier_dimensions"] == [len(original["matrices"][0][0]),
                                                  *[len(m) for m in original["matrices"]]]


def test_all_22_physical_smith_certificates_replay_against_the_same_carriers():
    computed = retained("compute_stdout.bin")["cases"][:8]
    requests = retained("replay_request.json")["cases"][:8]
    replays = retained("replay_stdout.bin")["cases"][:8]
    count = 0
    for original, request, replay in zip(computed, requests, replays, strict=True):
        assert original["case_id"] == request["case_id"] == replay["case_id"]
        assert replay["success"] is True
        assert replay["result"]["certificates_verified"] is True
        certificates = original["result"]["certificates"]
        assert request["certificates"] == [item["certificate"] for item in certificates]
        assert len(certificates) == len(request["matrices"])
        for degree, (item, report) in enumerate(zip(certificates, replay["result"]["reports"], strict=True), 1):
            assert item["certificate"]["degree"] == degree
            assert item["replay"] == report
            assert report["verified"] is True
            assert report["det_u"] in ("1", "-1")
            assert report["det_v"] in ("1", "-1")
            count += 1
    assert count == 22


def test_retained_controls_reject_specific_failures():
    boundaries = retained("compute_stdout.bin")["cases"][8:]
    certificates = retained("replay_stdout.bin")["cases"][8:]
    assert [(row["case_id"], row["error"]) for row in boundaries] == [
        ("NONZERO_BOUNDARY", "boundary maps do not compose to zero: d_1 d_2 != 0"),
        ("FRACTIONAL_BOUNDARY", "NONINTEGER"), ("RAGGED_BOUNDARY", "RAGGED_MATRIX"),
        ("DROPPED_BOUNDARY", "DECLARED_CARRIER_MISMATCH"),
    ]
    assert [(row["case_id"], row["error"]) for row in certificates] == [
        ("ZERO_U_ROW", "NONUNIMODULAR_BASIS"), ("CORRUPT_D", "UAV_NE_D"),
        ("MISSING_CERTIFICATE", "CERTIFICATE_COMPLETENESS"),
        ("FRACTIONAL_CERTIFICATE", "NONINTEGER"), ("WRONG_CARRIER", "UAV_NE_D"),
    ]
    assert all(row["success"] is False for row in [*boundaries, *certificates])


def test_physical_output_and_machinery_custody():
    receipt = retained("receipt.json")
    assert receipt["custody_before"] == receipt["custody_after"]
    assert receipt["sources_before"] == receipt["sources_after"]
    assert receipt["helper_verified_before_import"] is True
    assert receipt["yaml_and_source_custody_before_import_and_parsing"] is True
    for name, expected in receipt["outputs"].items():
        assert helper.digest(RUN / name) == expected
    for name, expected in receipt["custody_before"].items():
        assert helper.digest(recorded_path(name)) == expected
    build = helper.strict((BUILD / "receipt.json").read_bytes())
    assert build["returncode"] == 0
    assert build["libraries_before"] == build["libraries_after"]
    assert helper.digest(BUILD / "source.rs") == build["source_sha256"]
    assert helper.digest(BUILD / "paper011_native_dossier_integral.exe") == build["executable_sha256"]


def test_prior_runs_keep_their_actual_machinery_bytes():
    for name in ("run_v1", "run_v2"):
        snapshot = PAPER / f"docs/native_dossier_integral/execution_machinery_{name}"
        manifest = helper.strict((snapshot / "receipt.json").read_bytes())
        receipt_path = PAPER / f"docs/native_dossier_integral/{name}/receipt.json"
        assert helper.digest(receipt_path) == manifest["run_receipt_sha256"]
        receipt = helper.strict(receipt_path.read_bytes())
        for item in manifest["files"]:
            assert helper.digest(snapshot / item["snapshot"]) == item["sha256"]
            assert receipt["custody_before"][item["original_path"]] == item["sha256"]


def test_altered_helper_is_rejected_before_module_execution(tmp_path):
    receipt = helper.strict((BUILD / "receipt.json").read_bytes())
    receipt["helper_sha256"] = "f" * 64
    path = tmp_path / "bad_build.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="PRE_IMPORT_HELPER_PIN_MISMATCH"):
        runner.pinned_helper(path)


@pytest.mark.parametrize("raw,error", [(b'{"returncode":0,"returncode":0}', "DUPLICATE_BUILD_KEY"),
                                       (b'{"returncode":NaN}', "NONFINITE_BUILD_VALUE")])
def test_malformed_build_cannot_authorize_helper_execution(tmp_path, raw, error):
    path = tmp_path / "malformed.json"
    path.write_bytes(raw)
    with pytest.raises(ValueError, match=error):
        runner.pinned_helper(path)


@pytest.mark.parametrize("part,field,error", [("compute", "case_id", "BOUNDARY_CONTROL_BINDING"),
    ("compute", "error", "BOUNDARY_CONTROL_BINDING"), ("replay", "case_id", "CERTIFICATE_CONTROL_BINDING"),
    ("replay", "error", "CERTIFICATE_CONTROL_BINDING")])
def test_outer_gate_rejects_false_results_for_the_wrong_control(part, field, error):
    compute = retained("compute_stdout.bin")
    replay = retained("replay_stdout.bin")
    (compute if part == "compute" else replay)["cases"][8][field] = "WRONG_CONTROL"
    with pytest.raises(ValueError, match=error):
        runner.inspect_results(compute, replay, helper.DOSSIERS)


@pytest.mark.parametrize("attack,error", [
    ("degree", "CERTIFICATE_DEGREE_BINDING"),
    ("carrier_dimension", "DECLARED_CARRIER_MISMATCH"),
    ("drop_certificate", "CERTIFICATE_COMPLETENESS"),
    ("noncanonical_integer", "NONCANONICAL_INTEGER"),
    ("float", "INTEGER_STRING_REQUIRED"),
    ("negative_smith", "UAV_NE_D"),
])
def test_native_replay_refuses_additional_binding_and_type_attacks(attack, error):
    case = copy.deepcopy(retained("replay_request.json")["cases"][0])
    match attack:
        case "degree":
            case["certificates"][0]["degree"] = 2
        case "carrier_dimension":
            case["carrier_dimensions"][0] += 1
        case "drop_certificate":
            case["certificates"].pop()
        case "noncanonical_integer":
            case["certificates"][0]["u"][0][0] = "01"
        case "float":
            case["certificates"][0]["u"][0][0] = 1.0
        case "negative_smith":
            case["certificates"][0]["d"][0][0] = "-1"
    execution = subprocess.run([str(BUILD / "paper011_native_dossier_integral.exe")],
                               input=json.dumps({"cases": [case]}).encode(), capture_output=True,
                               check=False, timeout=30, cwd=PAPER)
    assert execution.returncode == 0
    outcome = helper.strict(execution.stdout)["cases"][0]
    assert outcome["case_id"] == case["case_id"]
    assert outcome["success"] is False
    assert outcome["error"] == error
