"""Finite interventions and corruption controls, from the paper package cwd."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("paper011_mechanisms", PAPER / "code/mechanism_recreations.py")
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


@pytest.fixture
def native():
    capability_path = os.environ.get("PAPER011_ENGINE_CAPABILITY")
    if not capability_path:
        pytest.skip("Explicit PAPER011_ENGINE_CAPABILITY required for native tests")
    capability = M.load(Path(capability_path).read_bytes())
    host = capability["binaries"]["symbol_game"]
    phi = capability["binaries"]["graph_functional"]
    return M.Native(Path(host["path"]), host["sha256"]), M.Native(Path(phi["path"]), phi["sha256"], True)


def test_torch_floor_refuses_the_vulnerable_pin():
    M.require_torch_version("2.13.0")
    M.require_torch_version("2.13.0+cu124")
    M.require_torch_version("2.14.1")
    with pytest.raises(M.MechanismError, match="TORCH_VERSION_MISMATCH"):
        M.require_torch_version("2.6.0+cu124")
    with pytest.raises(M.MechanismError, match="TORCH_VERSION_MISMATCH"):
        M.require_torch_version("2.12.1")
    with pytest.raises(M.MechanismError, match="TORCH_VERSION_MISMATCH"):
        M.require_torch_version("2.13.0rc1")


def _torch_or_skip():
    try:
        return M.torch_cpu()
    except M.MechanismError as exc:
        pytest.skip(str(exc))


def test_attention_mask_uses_positions_not_repeated_digit_identity():
    torch = _torch_or_skip()
    allowed = torch.ones((1, 3, 6, 6), dtype=torch.bool)
    result = M.attention_mask(allowed, [4], torch.arange(6))
    assert not result[..., 4].any()
    assert result[..., 1].all()
    assert allowed.all(), "Original attention mask is immutable to the reconstruction"
    with pytest.raises(M.MechanismError, match="POSITION_IDS"):
        M.attention_mask(allowed, [4], torch.arange(6) + 1)
    with pytest.raises(M.MechanismError, match="OUT_OF_RANGE"):
        M.attention_mask(allowed, [6], torch.arange(6))


def test_attention_steering_and_patching_are_actual_tensor_changes():
    _torch_or_skip()
    c2, c3 = M.c002(), M.c003()
    assert c2["mechanism"]["sweep"][-1]["carrier_mass"] > 0.99
    assert c3["mechanism"]["ranking"] == [0, 1]
    assert c3["mechanism"]["effects"][0]["patched_ld"] == c3["mechanism"]["clean_ld"]
    torch = _torch_or_skip()
    before = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    clean = torch.tensor([[9.0, 8.0], [7.0, 6.0]])
    after = M.patch_head(before, clean, 1)
    assert torch.equal(after[0], before[0])
    assert torch.equal(after[1], clean[1])
    assert torch.equal(before, torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    with pytest.raises(M.MechanismError, match="SHAPE_OR_HEAD"):
        M.patch_head(before, clean, 2)


@pytest.mark.parametrize("bad", ["007 1 -8", "-0 1 -1", "+1 1 -2", "1 1 -2 0", "1  1", "1 x -2"])
def test_bounded_grammar_rejects_noncanonical_and_wrong_arity(bad):
    assert M.integer_prefix(bad, 3)[0] is False


def test_grammar_checks_emitted_bytes_and_retains_rejected_proposals():
    output, trace = M.grammar_generate(list("1 1 -2"), 3)
    assert output == "1 1 -2"
    assert M.integer_prefix(output, 3) == (True, True)
    assert any(row["proposed"] == "x" and not row["admitted"] for row in trace)
    assert M.integer_prefix("1 1 -", 3) == (True, False)
    with pytest.raises(M.MechanismError, match="INCOMPLETE_GRAMMAR"):
        M.grammar_generate(list("1 1 -"), 3)


def test_native_cycle_certificate_replays_and_corrupted_dual_fails(native):
    result = M.c004(native[0])
    certificate = result["mechanism"]["certificate"]
    assert certificate["response"]["result"]["accepted"] is True
    assert certificate["response"]["result"]["certificate"]["dual_value"] == "3"
    assert certificate["request_sha256"] == M.sha(M.canonical(certificate["request"]))
    assert result["mechanism"]["corrupted_dual_control"]["response"]["result"]["accepted"] is False
    zero = result["mechanism"]["candidate_zero_certificate"]
    assert zero["request"]["payload"]["omega"] == result["mechanism"]["raw_output"].split(" ")
    assert zero["response"]["result"]["accepted"] is True
    assert result["mechanism"]["corrupted_candidate_control"]["response"]["result"]["accepted"] is False


def test_retained_c005_schema_accepts_false_contradiction_but_native_graph_has_zero_defect(native):
    capability = M.load(Path(os.environ["PAPER011_ENGINE_CAPABILITY"]).read_bytes())
    binding = M.load((PAPER / "docs/mechanism_recreated_run/source_bindings.json").read_bytes())
    result = M.c005(Path(capability["engine_root"]), binding, native[1])
    assert result["mechanism"]["retained_checker_accepts"] is True
    assert result["mechanism"]["native_graph"]["response"]["result"]["phi1"] == "0"
    assert result["challenge_gate_satisfied"] is False


def test_native_graph_and_attractor_session_require_explicit_capability(native):
    result = M.c006(*native)
    turns = result["mechanism"]["session"]
    assert turns[1]["outcome"] == "REFUSED_STATIONARY"
    assert turns[2]["evaluation"]["response"]["result"]["phi1"] == "0"
    assert result["mechanism"]["attractor"]["response"]["result"]["escalate"] is True
    wrong = M.Native(native[0].path, "0" * 64)
    with pytest.raises(M.MechanismError, match="NATIVE_BYTES_CHANGED"):
        wrong.call("detect_stationary_attractor", {})


def test_compaction_keeps_declared_content_and_refuses_restatements():
    declarations = [{"id": "early", "claim": "1", "repairable": False},
                    {"id": "late", "claim": "2", "repairable": True}]
    raw, refused = M.compact_ledger(declarations, [{"id": "early", "claim": "9", "repairable": False}])
    assert refused == ["early"]
    assert [json.loads(line) for line in raw.splitlines()] == declarations
    with pytest.raises(M.MechanismError, match="DUPLICATE_CONSTRAINT"):
        M.compact_ledger(declarations + declarations[:1], [])


def test_kv_eviction_preserves_constraint_positions_and_refuses_impossible_budget():
    assert M.retained_kv_positions(8, [0, 1, 3], 5) == [0, 1, 3, 6, 7]
    with pytest.raises(M.MechanismError, match="CANNOT_RETAIN"):
        M.retained_kv_positions(8, [0, 1, 3], 2)
    with pytest.raises(M.MechanismError, match="POSITION_INVALID"):
        M.retained_kv_positions(8, [9], 2)
    _torch_or_skip()
    result = M.c007()
    assert result["controls"]["kept_kv_values_identical"] is True


def test_residual_steering_preserves_orthogonal_component():
    _torch_or_skip()
    result = M.c008()
    before, after = result["mechanism"]["before"], result["mechanism"]["steered"]
    assert all(a[0] > b[0] and a[1] == b[1] for b, a in zip(before, after, strict=True))
    assert result["empirical_result"] is False
    assert result["challenge_gate_satisfied"] is False


def test_ladder_preserves_paired_discordances_and_rejects_duplicate_cases():
    rows = [{"case_id": "x", "A": True, "B": False}, {"case_id": "y", "A": True, "B": True}]
    assert M.paired_gap(rows) == {"n": 2, "A_successes": 2, "B_successes": 1,
                                  "gap": "1/2", "A_only": 1, "B_only": 0}
    with pytest.raises(M.MechanismError, match="DUPLICATE"):
        M.paired_gap(rows + rows[:1])
    with pytest.raises(M.MechanismError, match="BOOLEAN"):
        M.paired_gap([{**rows[0], "A": 1}])


def test_sampling_coverage_estimator_and_native_deduplication(native):
    assert M.coverage_at_k(4, 2, 1) == "1/2"
    assert M.coverage_at_k(4, 2, 2) == "5/6"
    with pytest.raises(M.MechanismError, match="COVERAGE_INPUT"):
        M.coverage_at_k(4, 2, 5)
    result = M.c010(native[1])
    assert len(result["mechanism"]["checker_calls"]) == 3
    assert len(result["mechanism"]["samples"]) == 4
    assert result["mechanism"]["first_verified_sample_index"] == 2


def test_terminal_packet_and_cemetery_view_refuse_corrupt_bytes():
    result = M.symbol_tui()["mechanism"]
    assert "PROTECTED_EDGE_EDIT" in result["rendered_terminal"]
    assert "CEMETERY" not in M.terminal_views(result["packet"], result["cemetery"], "packet")
    assert "PROTECTED_EDGE_EDIT" in M.terminal_views(result["packet"], result["cemetery"], "cemetery")
    assert M.terminal_views(result["packet"], result["cemetery"], "hodge").startswith("HODGE VIEW: unavailable")
    with pytest.raises(M.MechanismError, match="UNKNOWN_TERMINAL_VIEW"):
        M.terminal_views(result["packet"], result["cemetery"], "invented")
    packet = {**result["packet"], "payload": {"AB": "9"}}
    with pytest.raises(M.MechanismError, match="PACKET_PAYLOAD_DIGEST"):
        M.terminal_views(packet, result["cemetery"])
    entry = {**result["cemetery"][0], "raw_output": "lost"}
    with pytest.raises(M.MechanismError, match="CEMETERY_CHAIN"):
        M.terminal_views(result["packet"], [entry])


def test_source_bytes_and_duplicate_json_keys_fail_closed(tmp_path):
    source = tmp_path / "bound.py"
    source.write_bytes(b"pass\n")
    binding = {"schema_version": "paper011.mechanism-source-bindings.v1", "files": {"bound.py": M.sha(b"pass\n")}}
    M.verify_sources(tmp_path, binding)
    source.write_bytes(b"raise RuntimeError\n")
    with pytest.raises(M.MechanismError, match="SOURCE_BYTES_CHANGED"):
        M.verify_sources(tmp_path, binding)
    with pytest.raises(M.MechanismError, match="DUPLICATE_JSON"):
        M.load(b'{"verified":false,"verified":true}')
    with pytest.raises(M.MechanismError, match="SOURCE_PATH_ESCAPE"):
        M.verify_sources(tmp_path, {**binding, "files": {"../bound.py": "0" * 64}})


def _assert_offline_fixture(result):
    assert result["grade"] == "FRESH_OFFLINE_MECHANISM_FIXTURE"
    assert result["empirical_result"] is False
    assert result["challenge_gate_satisfied"] is False
    assert result["unperformed_obligations"]


def test_controls_do_not_turn_empirical_obligations_into_success():
    for execute in [M.c009, M.symbol_tui]:
        _assert_offline_fixture(execute())
    with pytest.raises(M.MechanismError, match="CONTROL_FAILED"):
        M.record("C002", {}, {"failed": False}, ["model study"])


def test_torch_fixtures_stay_offline_on_a_patched_torch():
    _torch_or_skip()
    for execute in [M.c001, M.c002, M.c003, M.c007, M.c008]:
        _assert_offline_fixture(execute())
