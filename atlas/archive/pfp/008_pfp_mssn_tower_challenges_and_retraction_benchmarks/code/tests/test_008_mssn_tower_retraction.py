"""Tests for the Paper 008 package code.

Part 1 keeps the historical teaching toy: a record whose level field changes
and a string-prefix rule that returns None for a "new" term. It is not the
MSS-0/MSS-1 context-map implementation discussed in Section 2 of the paper.

Parts 2-4 test the single-shot runner: exact host verdicts, the offline stub,
the output-directory rule, and the absence of network calls. No test calls a
provider.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import retraction_benchmark_runner as runner  # noqa: E402
from retraction_benchmark_runner import (  # noqa: E402
    BENCHMARK_INSTANCES,
    PACKAGE_ROOT,
    BudgetController,
    OfflineStubClient,
    compute_opcode_base,
    detect_stationary_loops,
    exact_host_evaluate,
    format_prompt,
    host_certificate,
    inconsistency_witness,
    main,
    parse_verdict,
    run_benchmark,
    verify_inconsistency_witness,
    verify_potential,
)

# Part 1: historical teaching toy (not the domain maps of Section 2).


@dataclass(frozen=True)
class TowerElement:
    level: int
    payload: str
    weight: Fraction


def up_map_u(elem: TowerElement, target_level: int) -> TowerElement:
    if target_level != elem.level + 1:
        raise ValueError("Invalid target level for up-map")
    return TowerElement(level=target_level, payload=elem.payload, weight=elem.weight)


def down_map_d(elem: TowerElement, target_level: int) -> TowerElement | None:
    if target_level != elem.level - 1:
        raise ValueError("Invalid target level for down-map")
    if elem.payload.startswith("NEW_STAGE_TERM"):
        return None
    return TowerElement(level=target_level, payload=elem.payload, weight=elem.weight)


def test_opcode_base_progression() -> None:
    assert compute_opcode_base(21) == 0
    assert compute_opcode_base(22) == 128
    assert compute_opcode_base(23) == 136
    assert compute_opcode_base(24) == 144
    assert compute_opcode_base(30) == 192


def test_opcode_blocks_are_disjoint_for_stages_22_to_100() -> None:
    blocks = [range(compute_opcode_base(n), compute_opcode_base(n) + 8) for n in range(22, 101)]
    for earlier, later in zip(blocks, blocks[1:]):
        assert earlier.stop <= later.start
    assert all(block.start >= 128 for block in blocks)


def test_toy_round_trip_on_an_old_term() -> None:
    elem = TowerElement(level=5, payload="cycle_edge_01", weight=Fraction(1, 1))
    assert down_map_d(up_map_u(elem, 6), 5) == elem


def test_toy_prefix_rule_returns_none_for_a_new_term() -> None:
    new_term = TowerElement(level=6, payload="NEW_STAGE_TERM_42", weight=Fraction(2, 1))
    assert down_map_d(new_term, 5) is None


# Part 2: exact host verdicts.


def test_host_evaluates_clean_tree() -> None:
    verdict, potentials, residual_sum, residual_edges = exact_host_evaluate(BENCHMARK_INSTANCES[0])
    assert verdict == "CONSISTENT"
    assert residual_sum == 0
    assert residual_edges == []
    assert potentials == {"A": 0, "B": 2, "C": 5}


def test_host_verdicts_match_declared_labels() -> None:
    for instance in BENCHMARK_INSTANCES:
        verdict, _, residual_sum, residual_edges = exact_host_evaluate(instance)
        assert verdict == instance.expected_verdict
        assert (residual_sum == 0) == (verdict == "CONSISTENT")
        assert (residual_edges == []) == (verdict == "CONSISTENT")


def test_host_reports_the_poisoned_triangle_gap() -> None:
    verdict, _, residual_sum, residual_edges = exact_host_evaluate(BENCHMARK_INSTANCES[2])
    assert verdict == "CONTRADICTION"
    assert residual_sum == 1
    assert len(residual_edges) == 1
    assert "gap=1" in residual_edges[0]


def test_host_refuses_a_disconnected_instance() -> None:
    broken = runner.GraphInstance("disconnected", ["A", "B", "C"], [("A", "B", 1)], "CONSISTENT", "")
    with pytest.raises(ValueError, match="unreachable"):
        exact_host_evaluate(broken)


def test_every_host_verdict_carries_a_checkable_certificate() -> None:
    for instance in BENCHMARK_INSTANCES:
        certificate = host_certificate(instance)
        assert certificate["verdict"] == instance.expected_verdict
        if instance.expected_verdict == "CONSISTENT":
            assert verify_potential(instance, certificate["potential"])
            assert inconsistency_witness(instance) is None
        else:
            recorded_walk = certificate["dual_witness_walk"]
            assert isinstance(recorded_walk, list)
            walk = [tuple(step) for step in recorded_walk]
            assert verify_inconsistency_witness(instance, walk)
            assert certificate["signed_claim_sum"] != 0


def test_tampered_dual_witnesses_are_rejected() -> None:
    k4 = BENCHMARK_INSTANCES[5]
    walk = inconsistency_witness(k4)
    assert walk is not None and verify_inconsistency_witness(k4, walk)
    first_index, first_orientation = walk[0]
    assert not verify_inconsistency_witness(k4, walk[:-1])
    assert not verify_inconsistency_witness(k4, [(first_index, -first_orientation)] + walk[1:])
    assert not verify_inconsistency_witness(k4, [(True, 1)] + walk[1:])
    assert not verify_inconsistency_witness(k4, [(len(k4.edges), 1)])
    assert not verify_inconsistency_witness(k4, [])
    assert not verify_inconsistency_witness(k4, [(0, 1), (0, -1)])


def test_potential_check_rejects_wrong_or_partial_values() -> None:
    tree = BENCHMARK_INSTANCES[0]
    assert verify_potential(tree, {"A": 0, "B": 2, "C": 5})
    assert verify_potential(tree, {"A": 7, "B": 9, "C": 12})
    assert not verify_potential(tree, {"A": 0, "B": 2, "C": 6})
    assert not verify_potential(tree, {"A": 0, "B": 2})
    assert not verify_potential(tree, {"A": 0, "B": 2.0, "C": 5})


def test_hinted_prompt_contains_the_answer_bearing_residuals() -> None:
    poisoned = format_prompt(BENCHMARK_INSTANCES[2], "hinted")
    clean = format_prompt(BENCHMARK_INSTANCES[1], "hinted")
    assert "gap=1" in poisoned
    assert "Edges with nonzero residual: none" in clean


# Part 3: helpers.


def test_stationary_loop_detection() -> None:
    looping = ["ASSERT pi(B)=2"] * 4
    assert detect_stationary_loops(looping, threshold=3) == (True, 3)
    descending = ["ASSERT pi(B)=2", "ASSERT pi(C)=5", "ASSERT pi(D)=7"]
    assert detect_stationary_loops(descending, threshold=3) == (False, 0)


def test_budget_gate_refuses_before_the_call() -> None:
    budget = BudgetController(ceiling_usd=0.0001)
    budget.record_cost(0.00008)
    with pytest.raises(RuntimeError, match="BudgetGate"):
        budget.check_pre_call(estimated_cost_usd=0.00005)


def test_parse_verdict_prefers_the_explicit_line() -> None:
    assert parse_verdict("VERDICT: CONTRADICTION\nnot CONSISTENT") == "CONTRADICTION"
    assert parse_verdict("reasoning\nVERDICT: CONSISTENT") == "CONSISTENT"
    assert parse_verdict("no answer") == "UNKNOWN"


@pytest.mark.parametrize("text", [
    "VERDICT: INCONSISTENT", "VERDICT: NOT CONSISTENT", "not CONSISTENT",
    "VERDICT: CONSISTENT or CONTRADICTION", "VERDICT: CONSISTENT\nVERDICT: CONTRADICTION",
])
def test_malformed_or_conflicting_verdicts_are_not_scored_as_answers(text: str) -> None:
    assert parse_verdict(text) == "UNKNOWN"


def test_separate_repeat_runs_do_not_form_one_consecutive_loop() -> None:
    assert detect_stationary_loops(["a", "a", "b", "b", "c", "c"], threshold=3) == (False, 1)


def test_receipt_digest_binds_the_raw_reply_prompt_case_and_certificate() -> None:
    receipt = run_benchmark(condition="hinted")[0]
    assert runner.receipt_digest(receipt) == receipt.digest_sha256
    row = json.loads(json.dumps(asdict(receipt)))
    assert runner.receipt_digest(row) == receipt.digest_sha256
    for field, forged in (
        ("raw_content", "different response with the same verdict"),
        ("prompt", "different prompt"),
        ("instance", {"task_id": receipt.task_id, "edges": []}),
        ("host_certificate", {"verdict": "CONSISTENT", "potential": {}}),
        ("provider", "different-provider"),
        ("source_sha256", "0" * 64),
    ):
        changed = dict(row, **{field: forged})
        assert runner.receipt_digest(changed) != receipt.digest_sha256


def test_distinct_raw_replies_with_the_same_verdict_have_distinct_digests() -> None:
    class Reply(OfflineStubClient):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

        def complete(self, prompt: str, max_tokens: int = 128) -> tuple[str, int, float, float]:
            return self.text, 1, 0.0, 0.0

    first = run_benchmark(client=Reply("VERDICT: CONSISTENT\nfirst reason"))[0]
    second = run_benchmark(client=Reply("VERDICT: CONSISTENT\nsecond reason"))[0]
    assert first.verdict_emitted == second.verdict_emitted
    assert first.digest_sha256 != second.digest_sha256


def test_json_loaded_walks_remain_checkable() -> None:
    instance = BENCHMARK_INSTANCES[2]
    certificate = json.loads(json.dumps(host_certificate(instance)))
    assert verify_inconsistency_witness(instance, certificate["dual_witness_walk"])
    certificate["dual_witness_walk"][0][1] = True
    assert not verify_inconsistency_witness(instance, certificate["dual_witness_walk"])


def test_a_changed_case_label_is_refused_before_any_model_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "BENCHMARK_INSTANCES", [replace(BENCHMARK_INSTANCES[0], expected_verdict="CONTRADICTION")])
    with pytest.raises(ValueError, match="label disagrees"):
        run_benchmark()


# Part 4: offline runs, output location, and network isolation.


@pytest.mark.parametrize(
    ("condition", "expected_matches"),
    [("baseline", 3), ("hinted", 6), ("scratchpad", 3), ("exact_oracle", 6)],
)
def test_offline_stub_match_counts(condition: str, expected_matches: int) -> None:
    receipts = run_benchmark(condition=condition, client=OfflineStubClient())
    assert len(receipts) == len(BENCHMARK_INSTANCES) == 6
    assert sum(r.matched_ground_truth for r in receipts) == expected_matches
    assert all(len(r.digest_sha256) == 64 for r in receipts)


def test_offline_run_opens_no_network_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setenv("OPENROUTER_API_KEY", "placeholder-not-a-key")
    receipts = run_benchmark(condition="hinted", client=OfflineStubClient())
    assert sum(r.matched_ground_truth for r in receipts) == 6


def test_cli_mock_hinted_writes_receipts_to_explicit_dir(tmp_path: Path) -> None:
    out = tmp_path / "run"
    assert main(["--mock", "--condition", "hinted", "--output-dir", str(out)]) == 0
    rows = [json.loads(line) for line in (out / "receipts.jsonl").read_text(encoding="utf-8").splitlines()]
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert len(rows) == 6
    assert summary == {
        "condition": "hinted",
        "instances": 6,
        "matched": 6,
        "mode": "offline-stub",
        "model": "meta-llama/llama-3.1-8b-instruct",
    }


def test_cli_refuses_output_inside_the_package() -> None:
    assert main(["--mock", "--output-dir", str(PACKAGE_ROOT / "code" / "results")]) == 2
    assert not (PACKAGE_ROOT / "code" / "results").exists()


def test_cli_live_without_key_is_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    assert main(["--live", "--output-dir", str(tmp_path / "live")]) == 2


def test_module_does_not_load_dotenv() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "dotenv" not in source
