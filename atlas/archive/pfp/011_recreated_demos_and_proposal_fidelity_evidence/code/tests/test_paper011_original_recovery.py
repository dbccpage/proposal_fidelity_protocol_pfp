"""Corruption controls for the bounded original source and narrative recovery."""

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "aggregate_original_recovery_v1.py"
SPEC = importlib.util.spec_from_file_location("paper011_original_recovery_tests", PATH)
RECOVERY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RECOVERY
SPEC.loader.exec_module(RECOVERY)
REPO = (next((p for p in PATH.parents if (p / ".git").exists()), None) or PATH.parents[7])
RUN = REPO / "_intelligence/symbol_game/runs/09232026_042645_specimen_mt000_reduction"
MD = RUN / "09232026_042645_specimen_mt000_reduction_uns_trace.md"
LEDGER = RUN / "09232026_042645_packets_specimen_mt000_reduction.jsonl"


def test_undeclared_top_level_side_effect_refused():
    with pytest.raises(RECOVERY.RecoveryError, match="UNDECLARED_TOP_LEVEL_SIDE_EFFECT"):
        RECOVERY.adapt(b"if True:\n    open('side-effect', 'w')\n", "run_demo2")


def test_unknown_sibling_import_refused():
    with pytest.raises(RECOVERY.RecoveryError, match="UNDECLARED_IMPORT"):
        RECOVERY.adapt(b"import unpinned_sibling\n", "sign_switching")


def test_source_loader_refuses_corrupted_bytes_before_execution(tmp_path):
    source = tmp_path / "sign_switching.py"
    original = b"raise AssertionError('must not run')\n"
    source.write_bytes(original + b"# damaged\n")
    loader = RECOVERY.RecoveredLoader(
        source, RECOVERY.digest(original), "sign_switching", [], tmp_path
    )
    with pytest.raises(RECOVERY.RecoveryError, match="SOURCE_DIGEST_MISMATCH"):
        loader.exec_module(type(sys)("paper011_corrupt_source"))


def test_original_three_rounds_join_actual_packets_and_detect_aliases():
    rows = RECOVERY.narrative_packet_checks(MD.read_bytes(), LEDGER.read_bytes())
    assert len(rows) == 3
    assert all(row["audit_id_is_task_alias"] and not row["audit_id_is_packet_id"] for row in rows)
    assert all(row["state_prefix_matches"] for row in rows)
    assert rows[0]["child_instruction_matches"] is True
    assert rows[1]["child_instruction_matches"] is False
    assert all(row["native_measurement_verified"] is False for row in rows)


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("task", "MISSING_CORRESPONDING_PACKET"),
        ("outer", "OUTER_PACKET_ID_MISMATCH"),
        ("parent", "PARENT_EVENT_MISMATCH"),
        ("missing", "NARRATIVE_PACKET_CARDINALITY_MISMATCH"),
    ],
)
def test_packet_synchronization_mutations_fail_closed(mutation, error):
    rows = [json.loads(line) for line in LEDGER.read_bytes().splitlines()]
    if mutation == "task":
        rows[1]["packet"]["task_id"] = "easier_other_task"
    elif mutation == "outer":
        rows[1]["packet_id"] = "0" * 64
    elif mutation == "parent":
        rows[1]["packet"]["parent_event_id"] = "0" * 64
    else:
        rows.pop()
    raw = b"\n".join(RECOVERY.canonical(row) for row in rows)
    with pytest.raises(RECOVERY.RecoveryError, match=error):
        RECOVERY.narrative_packet_checks(MD.read_bytes(), raw)


def test_missing_role_is_not_truncated_into_a_passing_zip():
    raw = MD.read_bytes().replace(b"##### Round 1 Beat 8: Adversary", b"##### omitted role: Adversary")
    with pytest.raises(RECOVERY.RecoveryError, match="COMPLETE_ORIGINAL_ROLE_ORDER_REQUIRED"):
        RECOVERY.parse_rounds(raw)


def test_existing_output_is_never_overwritten(tmp_path):
    with pytest.raises(RECOVERY.RecoveryError, match="FRESH_OUTPUT_REQUIRED"):
        RECOVERY.run(REPO, tmp_path)


def source_progression():
    path = PATH.with_name("aggregate_original_recovery_progression_v1.py")
    spec = importlib.util.spec_from_file_location("paper011_original_progression_tests", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    root = PATH.parent.parent / "docs/aggregate_recreated_run/original_recovery_v1"
    raw = (root / "progression_v1/original_symbol_game_runner.py").read_bytes()
    model_raw = (root / "final_v4/source_files/pfp/domain/bridge/symbol_game_models.py").read_bytes()
    model = types.ModuleType("paper011_original_score_controls")
    sys.modules[model.__name__] = model
    tree, _ = RECOVERY.adapt(model_raw, "symbol_game_models")
    exec(compile(tree, "<original-score-controls>", "exec"), model.__dict__)
    return module, raw, model.ObstructionScore


def test_original_ast_terminal_is_false_despite_literal_pass():
    module, raw, score = source_progression()
    stages, _ = module.extract(raw, "run_refactoring_packet", 2, score)
    assert (stages[-1]["score"].phi_1, stages[-1]["score"].gamma_2, stages[-1]["score"].active_count) == (4.0, 1.0, 4)
    assert stages[-1]["score"].is_exact is False
    assert stages[-1]["source_action"] == "EXACT_REPAIR"
    assert stages[-1]["source_status"] == "PASS_TO_MASTER"


def test_specimen_original_synthetic_progression_and_active_count_descent():
    module, raw, score = source_progression()
    stages, _ = module.extract(raw, "run_problem", 3, score)
    assert [(r["score"].phi_1, r["score"].gamma_2, r["score"].active_count) for r in stages] == [(0.4, 0.25, 1), (0.0, 0.0, 1), (0.0, 0.0, 0)]
    assert stages[-1]["score"].strictly_improves(stages[-1]["prior_score"]) is True


def test_original_source_projection_does_not_execute_injected_side_effect():
    module, raw, score = source_progression()
    damaged = raw.replace(b"gamma_2=gamma_progression[step_idx],", b"gamma_2=__import__('socket').create_connection(('example.com', 80)),")
    with pytest.raises(ValueError, match="SIDE_EFFECT_CALL_REFUSED"):
        module.extract(damaged, "run_refactoring_packet", 2, score)


def test_original_source_projection_refuses_budget_widening():
    module, raw, score = source_progression()
    with pytest.raises(ValueError, match="ORIGINAL_BOUNDED_STEP_RANGE_REQUIRED"):
        module.extract(raw, "run_problem", 100, score)
