"""Evidence-bound controls for the original rational dossier replay."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parents[1] / "replay_dossier_homology.py"
_spec = importlib.util.spec_from_file_location("paper011_dossier_homology", _path)
audit = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = audit
_spec.loader.exec_module(audit)
RUN = _path.parent.parent / "docs/native_dossier_homology/run_v4"


def retained():
    return audit.strict((RUN / "stdout.bin").read_bytes())


def test_all_original_native_maps_and_expected_falsifiers():
    result = audit.inspect_result(retained())
    assert result["original_dossiers"] == 8
    assert result["native_controls_passed"] == 4
    rows = result["results"]
    assert all(row["boundary_law_verified"] is True for row in rows)
    assert [row["betti_over_q"] for row in rows] == [
        [1, 0, 0], [1, 0, 0], [1, 0, 1], [1, 0, 2],
        [1, 0, 0, 1], [1, 0, 0, 0], [1, 0, 0, 0, 1], [1, 0, 1, 2, 1],
    ]
    mismatches = [(row["case_id"], c["degree"], c["declared"], c["actual"])
                  for row in rows for c in row["declared_betti_comparisons"] if c["matches"] is False]
    assert mismatches == [(audit.DOSSIERS[0], 1, 2, 0), (audit.DOSSIERS[1], 1, 4, 0),
                          (audit.DOSSIERS[7], 2, 2, 1), (audit.DOSSIERS[7], 3, 0, 2)]
    assert all(row["integer_torsion_verified"] is False for row in rows)


def test_nested_source_claim_location_is_retained():
    request = json.loads((RUN / "request.json").read_bytes())
    case = request["cases"][7]
    assert case["homology_claim_source"] == "topology.betti_numbers"
    assert case["homology"]["b2"] == 2
    assert case["homology"]["b3"] == 0


def test_missing_boundary_degree_cannot_be_dropped():
    with pytest.raises(ValueError, match="INCOMPLETE_BOUNDARY_MAPS"):
        audit.prepare_case("invalid", {"boundary_matrices": {"d0": [["0"]], "d2": [["0"]]}})


def test_missing_claims_cannot_be_vacuously_verified():
    with pytest.raises(ValueError, match="MISSING_DECLARED_BETTI_CLAIMS"):
        audit.prepare_case("invalid", {"boundary_matrices": {"d0": [["0"]]}, "homology": {}})


def test_changed_source_before_execution_cannot_be_an_original_dossier():
    known = dict(zip(audit.DOSSIERS, audit.SOURCE_DIGESTS, strict=True))
    audit.check_source_pins(known)
    known[audit.DOSSIERS[0]] = "f" * 64
    with pytest.raises(ValueError, match="ORIGINAL_SOURCE_PIN_MISMATCH"):
        audit.check_source_pins(known)


def test_raw_receipt_outputs_match_actual_retained_bytes():
    receipt = json.loads((RUN / "receipt.json").read_bytes())
    assert receipt["returncode"] == 0
    assert receipt["source_commit"] == audit.SOURCE_COMMIT
    audit.check_source_pins(receipt["sources_before"])
    audit.check_source_pins(receipt["sources_after"])
    for name, expected in receipt["outputs"].items():
        assert audit.digest(RUN / name) == expected


@pytest.mark.parametrize("attack", ["dropped", "reordered", "false_boolean", "malformed_accepted", "claim_accepted"])
def test_corrupted_native_outcomes_are_rejected(attack):
    value = copy.deepcopy(retained())
    match attack:
        case "dropped":
            value["cases"].pop(0)
        case "reordered":
            value["cases"].reverse()
        case "false_boolean":
            value["cases"][0]["success"] = 1
        case "malformed_accepted":
            value["cases"][9]["success"] = True
        case "claim_accepted":
            value["cases"][11]["result"]["declared_betti_comparisons"][0]["matches"] = True
    with pytest.raises(ValueError):
        audit.inspect_result(value)


@pytest.mark.parametrize("raw", [b'{"cases": [], "cases": []}', b'{"x": NaN}'])
def test_malformed_json_cannot_mint_evidence(raw):
    with pytest.raises(ValueError):
        audit.strict(raw)
