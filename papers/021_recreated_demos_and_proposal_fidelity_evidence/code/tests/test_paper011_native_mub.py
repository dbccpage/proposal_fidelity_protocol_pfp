"""Native catalog custody controls, separate from native mathematical tests."""

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parents[1] / "replay_native_mub.py"
_spec = importlib.util.spec_from_file_location("paper011_native_mub", _path)
native = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = native
_spec.loader.exec_module(native)


def report_fixture():
    ids = [
        "T0_canonical",
        "Dita_F6_0_8_Y2Q1",
        "Dita_F6_8_0_Y2Q1",
        "Dita_F6_16_16_Y2Q1",
        "Dita_F6_0_16_Y2Q2",
        "Dita_F6_8_8_Y2Q2",
        "Dita_F6_16_0_Y2Q2",
    ]
    results = []
    for identifier in ids:
        row = {"triple_id": identifier}
        for matrix in ("h12", "h23", "h31"):
            row[matrix] = {
                "matrix_id": identifier + "_" + matrix.upper(),
                "gamma1_all_zero": True,
                "gamma1_failures": 0,
                "gamma2_product_all_zero": True,
                "gamma2_failures": 0,
                "conjecture_2_holds": True,
            }
        row["all_hold"] = True
        results.append(row)
    payload = {
        "schema": "core.mub6.conj2-verification.v3",
        "total_triples_tested": 7,
        "total_triples_passed": 7,
        "total_triples_failed": 0,
        "results": results,
    }
    return {**payload, "sha256": native.sha(native.canonical(payload))}


def seal(value):
    value = copy.deepcopy(value)
    value.pop("sha256", None)
    return native.canonical({**value, "sha256": native.sha(native.canonical(value))})


def test_catalog_positive_and_changed_digest():
    baseline = native.canonical(report_fixture())
    assert native.validate_report(baseline, baseline)["transition_matrices"] == 21
    bad = report_fixture()
    bad["results"][0]["h12"]["gamma1_failures"] = 1
    with pytest.raises(native.ReplayFailure, match="PAYLOAD_DIGEST_MISMATCH"):
        native.validate_report(native.canonical(bad), baseline)


@pytest.mark.parametrize(
    "change", ["omit", "duplicate", "boolean_count", "truthy_flag", "negative"]
)
def test_resealed_invalid_catalog_cannot_pass(change):
    bad = report_fixture()
    if change == "omit":
        bad["results"].pop()
    elif change == "duplicate":
        bad["results"][1] = copy.deepcopy(bad["results"][0])
    elif change == "boolean_count":
        bad["results"][0]["h12"]["gamma1_failures"] = False
    elif change == "truthy_flag":
        bad["results"][0]["h12"]["gamma1_all_zero"] = "true"
    else:
        bad["results"][0]["all_hold"] = False
    raw = seal(bad)
    with pytest.raises(native.ReplayFailure):
        native.validate_report(raw, raw)


def test_resealed_different_retained_input_cannot_pass():
    baseline = native.canonical(report_fixture())
    bad = report_fixture()
    bad["total_triples_failed"] = 1
    with pytest.raises(native.ReplayFailure, match="RETAINED_CATALOG_RESULT_MISMATCH"):
        native.validate_report(seal(bad), baseline)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_duplicate_and_nonfinite_report_bytes_refuse(raw):
    with pytest.raises(native.ReplayFailure):
        native.strict_json(raw)


def test_adaptation_only_changes_destination_and_preserves_line_endings(monkeypatch):
    original = b"// input\r\n" + native.OLD_DESTINATION.encode() + b"\r\n// math\r\n"
    monkeypatch.setattr(native, "SOURCE_SHA256", native.sha(original))
    result = native.adapted_source(original)
    assert (
        result.replace(native.NEW_DESTINATION.encode(), native.OLD_DESTINATION.encode()) == original
    )
    with pytest.raises(native.ReplayFailure, match="SOURCE_DIGEST_MISMATCH"):
        native.adapted_source(original + b"drift")


def test_output_ancestor_symlink_refuses(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "alias"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    child = target / "report.json"
    child.write_bytes(b"{}")
    with pytest.raises(native.ReplayFailure, match="REDIRECTED_PATH"):
        native.regular(link / child.name)
