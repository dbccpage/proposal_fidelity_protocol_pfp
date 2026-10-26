"""Focused fidelity and refusal controls for G04's original finite scope."""
from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

CODE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("paper011_g04_controls", CODE / "genesis_g04_replay.py")
assert SPEC is not None and SPEC.loader is not None
G04 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = G04
SPEC.loader.exec_module(G04)


def test_same_mapping_must_preserve_every_prefix_range():
    trace = [SimpleNamespace(n_data=lambda: 1, forms=()), SimpleNamespace(n_data=lambda: 2, forms=())]
    assert G04.legal_prefix_permutation(trace, (0, 1), ())
    assert not G04.legal_prefix_permutation(trace, (1, 0), ())


def test_form_mapping_is_independently_prefix_bound():
    trace = [SimpleNamespace(n_data=lambda: 0, forms=(1,)), SimpleNamespace(n_data=lambda: 0, forms=(1, 1))]
    assert not G04.legal_prefix_permutation(trace, (), (1, 0))


def test_token_signature_preserves_equality_and_non_token_event_fields():
    h = [{"kind": "Supply", "token": "a"}, {"kind": "AdmitDatum", "token": "a"}]
    renamed = [{"kind": "Supply", "token": "other"}, {"kind": "AdmitDatum", "token": "other"}]
    nonbijective = [{"kind": "Supply", "token": "other"}, {"kind": "AdmitDatum", "token": "different"}]
    assert G04.token_signature([], h) == G04.token_signature([], renamed)
    assert G04.token_signature([], h) != G04.token_signature([], nonbijective)
    assert G04.token_signature([], [{"kind": "AdmitInst", "form": 0, "args": [0]}]) != G04.token_signature([], [{"kind": "AdmitInst", "form": 0, "args": [1]}])


def test_import_relocation_retains_function_and_exact_stake_expression():
    raw = b"import sys\nif 'x' not in sys.path:\n sys.path.insert(0,'x')\nfrom derivation.model import Regime\ndef rule(i,j):\n return 'same' if (i-j)%3 == 0 else 'apart'\n"
    adapted, receipt = G04.relocate(raw, "fixture.py")
    original = ast.parse(raw)
    assert ast.dump(adapted.body[-1], include_attributes=False) == ast.dump(original.body[-1], include_attributes=False)
    assert len(receipt["removed_import_rails"]) == 1
    assert receipt["qualified_imports"][0]["after"] == G04.NAMESPACE + ".derivation.model"


def test_manifest_is_literal_and_covers_original_prerequisites():
    manifest = G04.verify_sources()
    assert len(manifest["files"]) == 18
    paths = {row["source_path"] for row in manifest["files"]}
    assert "research/second_index/index.py" in paths
    assert "research/second_nofirst/nofirst.py" in paths
    assert "code/derivation/iso.py" in paths


@pytest.fixture(scope="module")
def original():
    return G04.load_original()[0]


@pytest.mark.parametrize("name,expected", [("EMPTY", 577), ("L", 3928), ("F", 14293)])
def test_full_original_population_not_replaced_by_fixture(original, name, expected):
    rectangle = original["index"].build_rectangle(name, original["nofirst"].ALPHABET)
    assert len(rectangle.nodes) == expected
    assert original["index"].crosscheck(name, original["nofirst"].ALPHABET, 3)["reach_agrees"]


def test_original_endpoint_poison_has_unequal_first_counts(original):
    model, index, nf = (original[name] for name in ("model", "index", "nofirst"))
    stake = next(s for s in nf.declared_stakes() if s.name == "total_apart")
    a = (model.AdmitDatum("<n0>"), model.AdmitDatum("<n1>"))
    b = (model.Supply("<z>"),) + a
    assert model.replay(a) == model.replay(b)
    seen = index.Observations()
    assert index.first_index_forward(model.EMPTY, a, stake, seen) == 2
    assert index.first_index_scan(model.EMPTY, b, stake, seen) == 3


@pytest.fixture(scope="module")
def native():
    receipt = json.loads((G04.AREA / "native_build_v1/receipt.json").read_bytes())
    executable = Path(receipt["executable"])
    assert receipt["returncode"] == 0 and G04.sha(executable.read_bytes()) == receipt["executable_sha256"]
    return executable


def call(native, request):
    process = subprocess.run([str(native)], input=G04.wire(request), capture_output=True, timeout=30)
    return process.returncode, json.loads(process.stdout)


@pytest.mark.parametrize("pi", [[0, 0], [1], [0, 2]])
def test_native_refuses_nonbijection_with_literal_id(native, pi):
    code, result = call(native, {"action": "audit", "id": "bad-data", "mutation": "untransported_stake", "pi": pi})
    assert code == 2
    assert result == {"status": "REFUSED", "id": "bad-data", "error": "DATA_BIJECTION"}


def test_native_refuses_modified_original_stake_matrix(native):
    labels = [[["free"] * 5 for _ in range(5)] for _ in range(7)]
    code, result = call(native, {"action": "census", "id": "weakened", "stake_names": G04.STAKE_NAMES, "labels": labels})
    assert code == 2 and result["error"] == "ORIGINAL_STAKE_BINDING"


def test_native_does_not_accept_endpoint_self_score(native):
    h = [{"kind": "AdmitDatum", "token": "a"}, {"kind": "AdmitDatum", "token": "b"}]
    code, result = call(native, {"action": "audit", "id": "endpoint", "mutation": "endpoint_only", "pi": [],
                                "histories": [h, [{"kind": "Supply", "token": "z"}] + h], "claimed_endpoint_first": 2})
    assert code == 2 and result["id"] == "endpoint" and result["error"] == "ENDPOINT_NOT_FIRST_INDEX:[2,3]"


def test_native_transport_refuses_untransported_labels_and_keeps_valid_control(native):
    pi = [1, 0, 2]
    labels = [["free", "apart", "same"], ["apart", "free", "apart"], ["same", "apart", "free"]]
    inv = [pi.index(i) for i in range(3)]
    proper = [[labels[inv[i]][inv[j]] for j in range(3)] for i in range(3)]
    request = {"action": "audit", "id": "transport", "mutation": "untransported_stake", "pi": pi, "stake": 3,
               "claimed_transported_labels": proper}
    assert call(native, request)[0] == 0
    request["claimed_transported_labels"] = labels
    code, result = call(native, request)
    assert code == 2 and result["error"] == "STAKE_TRANSPORT_MISMATCH"


def test_native_data_permutation_is_not_a_form_permutation(native):
    code, result = call(native, {"action": "audit", "id": "wrong-sort", "mutation": "pi_on_forms", "pi": [1, 0, 2], "forms": 0})
    assert code == 2 and result["error"] == "FORM_BIJECTION_DIMENSION"


@pytest.fixture(scope="module")
def supplement():
    root = G04.AREA / "universal_poison_v1"
    receipt = json.loads((root / "receipt.json").read_bytes())
    build = json.loads((G04.AREA / "universal_poison_build_v1/receipt.json").read_bytes())
    executable = Path(build["executable"])
    assert G04.sha(executable.read_bytes()) == build["executable_sha256"]
    control = receipt["native_controls"][0]
    raw = (G04.PAPER / control["request"]["path"]).read_bytes()
    assert G04.sha(raw) == control["request"]["sha256"]
    return executable, json.loads(raw), receipt


def test_supplement_computes_actual_original_history_counterexample(supplement):
    executable, request, receipt = supplement
    code, result = call(executable, request)
    assert code == 0 and result["fixed_first"] == [None, 3]
    assert result["transported_first"] == [None, None]
    assert result["source_prefixes_under_pi_phi"] == result["target_prefixes"]
    assert receipt["source_row_ids"] == request["original_row_ids"]
    assert receipt["historical_operator_heldout"] is False
    assert receipt["historical_heldout_gate_complete"] is False


def test_supplement_refuses_universal_claim_using_computed_counts(supplement):
    executable, request, _ = supplement
    request = {**request, "id": "false-universal", "mode": "assert_universal_fixed"}
    code, result = call(executable, request)
    assert code == 2 and result == {"status": "REFUSED", "id": "false-universal", "error": "UNIVERSAL_FIXED_STAKE_POISON:[null,3]"}


def test_supplement_refuses_wrong_common_mapping(supplement):
    executable, request, _ = supplement
    code, result = call(executable, {**request, "id": "wrong-mapping", "pi": [0, 1, 2]})
    assert code == 2 and result["error"] == "COMMON_PREFIX_ISOMORPHISM:2"


def test_supplement_refuses_datum_mapping_in_form_field(supplement):
    executable, request, _ = supplement
    code, result = call(executable, {**request, "id": "wrong-form-map", "phi": [1, 0, 2]})
    assert code == 2 and result["error"] == "FORM_BIJECTION"


def test_supplement_refuses_ragged_stake_matrix(supplement):
    executable, request, _ = supplement
    code, result = call(executable, {**request, "id": "ragged-stake", "labels": [["free"]]})
    assert code == 2 and result["error"] == "STAKE_DIMENSION"


def test_supplement_does_not_silently_extend_original_length(supplement):
    executable, request, _ = supplement
    long_h = request["histories"][0] + [{"kind": "Supply", "token": "<z>"}] * 2
    code, result = call(executable, {**request, "id": "length-five", "histories": [long_h, request["histories"][1]]})
    assert code == 2 and result["error"] == "ORIGINAL_LENGTH_BOUND"


def test_original_fixed_stake_verdict_is_preserved_separately():
    comparison = json.loads((G04.AREA / "full_rectangle_v2/comparison.json").read_bytes())
    assert comparison["X3c"] == "HOLDS_ON_RECTANGLE"
    assert sum(base["rows"] for base in comparison["bases"]) == 18798
