"""
test_cross_domain_bouts.py
--------------------------
Unit and regression tests for multi_domain_symbol_game_bouts.py.
Verifies that the Symbol Game governor operates consistently, inexpensively,
across four labeled finite-graph fixtures.
"""

from multi_domain_symbol_game_bouts import (
    UniversalCemeteryDAG,
    run_cross_domain_symbol_game_suite,
    run_domain_1_quantum_r4,
    run_domain_2_distributed_deadlock,
    run_domain_3_clean_architecture,
    run_domain_4_economic_arbitrage,
    validate_bout_trace,
)


def test_domain_1_quantum_labeled_fixture_repair(native_functional):
    cemetery = UniversalCemeteryDAG()
    metric, move_log = run_domain_1_quantum_r4(cemetery)

    assert metric.initial_phi == "5"
    assert metric.intermediate_phi == "5"
    assert metric.final_phi == "0"
    assert metric.terminal_status == "ILLUSTRATIVE_GRAPH_REPAIRED"
    assert metric.governed_tokens_actual == 0
    assert validate_bout_trace(metric.domain_id, move_log) is True


def test_domain_2_distributed_deadlock_preemption(native_functional):
    cemetery = UniversalCemeteryDAG()
    metric, move_log = run_domain_2_distributed_deadlock(cemetery)

    assert metric.initial_phi == "4"
    assert metric.final_phi == "0"
    assert metric.terminal_status == "ACCEPTED_ZERO_DEFECT"
    assert metric.governed_tokens_actual == 0
    assert validate_bout_trace(metric.domain_id, move_log) is True


def test_domain_3_clean_architecture_port_inversion(native_functional):
    cemetery = UniversalCemeteryDAG()
    metric, move_log = run_domain_3_clean_architecture(cemetery)

    assert metric.initial_phi == "3"
    assert metric.final_phi == "0"
    assert metric.terminal_status == "ACCEPTED_ZERO_DEFECT"
    assert metric.governed_tokens_actual == 0
    assert validate_bout_trace(metric.domain_id, move_log) is True


def test_domain_4_economic_arbitrage_clearing(native_functional):
    cemetery = UniversalCemeteryDAG()
    metric, move_log = run_domain_4_economic_arbitrage(cemetery)

    assert metric.initial_phi == "3"
    assert metric.final_phi == "0"
    assert metric.terminal_status == "ACCEPTED_ZERO_DEFECT"
    assert metric.governed_tokens_actual == 0
    assert validate_bout_trace(metric.domain_id, move_log) is True


def test_cemetery_dag_cryptographic_chain(native_functional):
    cemetery = UniversalCemeteryDAG()
    run_domain_1_quantum_r4(cemetery)
    run_domain_2_distributed_deadlock(cemetery)

    assert len(cemetery.entries) >= 4
    # Verify hash chain continuity: entries[i].prev_hash == entries[i-1].entry_hash
    for i in range(1, len(cemetery.entries)):
        assert cemetery.entries[i]["prev_hash"] == cemetery.entries[i - 1]["entry_hash"]


def test_full_suite_receipt_emission(tmp_path, native_functional):
    receipt_path = tmp_path / "cross_domain_symbol_game_receipt.json"
    receipt = run_cross_domain_symbol_game_suite(receipt_path)
    assert receipt_path.is_file()
    assert receipt["summary"]["domains_evaluated"] == 4
    assert receipt["summary"]["all_trace_invariants_valid"] is True
    assert receipt["summary"]["total_governed_tokens_actual"] == 0
