"""Actual pinned Egglog execution, with an independent loss counterexample."""
from copy import deepcopy

import pytest

from pfp.infrastructure.adapters import egglog_prompt_rewriter as owner


def test_actual_hostile_rule_cannot_drop_a_constraint(monkeypatch):
    monkeypatch.setattr(owner, "RULES", owner.RULES + '''
    (rewrite (Next (Occurrence id boundary (Role "constraint") payload slot) tail) tail
             :ruleset mode13 :name "hostile-drop-constraint")
    ''')
    result = owner.rewrite_prompt(owner.declared_preservation_cases()[0])
    assert result["executed"] is True
    assert result["rule_matches"].get("hostile-drop-constraint", 0) > 0
    assert result["status"] == "REFUSED"
    assert result["reason"] == "EGRAPH_CONSTRAINT_LOSS"


@pytest.fixture(scope="module")
def measured_suite():
    return owner.run_preservation_suite()


def test_fifty_actual_executions_preserve_order_roles_spans_and_duplicate_constraints(measured_suite):
    assert measured_suite["status"] == "VERIFIED", measured_suite.get("reason")
    assert len(measured_suite["observations"]) == 50
    payload = measured_suite["native_payload"]
    assert payload["total_rewrites"] == 50
    assert payload["dropped_constraints"] == 0
    assert payload["constraints_before"] == payload["constraints_after"]
    for row, request in zip(measured_suite["observations"], owner.declared_preservation_cases(), strict=True):
        assert row["executed"] is True
        assert row["engine"]["version"] == "14.0.0"
        assert row["engine"]["num_threads"] == 1
        assert 1 <= row["iterations"] <= 10
        assert max(row["node_counts"]) <= 1024
        assert all(row["rule_matches"][name] > 0 for name in
            ("share-payload", "role-canonical", "identity-compact"))
        occurrences = row["occurrences"]
        assert len(occurrences) == len(request.segments) == 8
        assert len({entry["genome_id"] for entry in occurrences}) == 8
        assert [entry["role"] for entry in occurrences] == [segment.role for segment in request.segments]
        assert [entry["slot"] for entry in occurrences] == [f"s{i}" for i in range(8)]
        assert row["payload_count"] == 7
        assert occurrences[1]["text"] == occurrences[4]["text"]
        assert occurrences[1]["genome_id"] != occurrences[4]["genome_id"]
        source = request.raw_prompt.encode("utf-8")
        assert b"\r\n" in source and "𓂀".encode() in source
        assert "".join(entry["text"] for entry in occurrences).encode() == source
        for entry in occurrences:
            start, end = entry["byte_span"]
            assert source[start:end] == entry["text"].encode()


def test_replay_recomputes_metrics_without_engine_or_stored_verdict(monkeypatch, measured_suite):
    observations = deepcopy(measured_suite["observations"])
    for row in observations:
        row["status"] = "made up"
        row["constraints_before"] = {"invented": "claim"}
        row["constraints_after"] = {}
    def forbidden():
        raise AssertionError("Replay must not load or execute Egglog")
    monkeypatch.setattr(owner, "_runtime", forbidden)
    result = owner.replay_preservation_suite(observations)
    assert result["status"] == "REPLAYED", result.get("reason")
    assert result["engine_executions"] == 0
    assert result["native_payload"] == measured_suite["native_payload"]
    assert "not authenticated" in result["scope"]


@pytest.mark.parametrize("mutation", ["role", "order", "duplicate", "constraint", "input", "rule", "version", "span"])
def test_replay_refuses_mutated_source_or_output_even_with_resealed_hashes(measured_suite, mutation):
    observations = deepcopy(measured_suite["observations"])
    row = observations[0]
    if mutation == "role":
        row["output_ast"][1][3][1] = "context"
    elif mutation == "order":
        row["output_ast"][1], row["output_ast"][2][1] = row["output_ast"][2][1], row["output_ast"][1]
    elif mutation == "duplicate":
        row["output_ast"][2][1][1] = row["output_ast"][1][1]
    elif mutation == "constraint":
        row["output_ast"][2] = row["output_ast"][2][2]
    elif mutation == "input":
        row["request"]["raw_prompt"] += "unrepresented context"
    elif mutation == "rule":
        row["rules"] += '\n(rewrite (Next occurrence tail) tail :ruleset mode13)'
        row["rules_sha256"] = owner._hash(row["rules"])
    elif mutation == "version":
        row["engine"]["version"] = "15.0.0"
    elif mutation == "span":
        row["input_ast"][0]["byte_span"][1] += 1
        row["input_sha256"] = owner._hash(owner._json(row["input_ast"]))
    row["output_sha256"] = owner._hash(owner._json(row["output_ast"]))
    cost = owner._ast_cost(row["output_ast"])
    row["output_wire"], row["extraction_cost"] = cost[3], list(cost[:3])
    result = owner.replay_preservation_suite(observations)
    assert result["status"] == "REFUSED"
    assert result["native_payload"] is None


def test_missing_runtime_is_unavailable_and_never_an_empirical_payload(monkeypatch):
    monkeypatch.setattr(owner, "_runtime", lambda: (None, "EGGLOG_UNAVAILABLE"))
    result = owner.run_preservation_suite()
    assert result["status"] == "UNAVAILABLE"
    assert result["reason"] == "EGGLOG_UNAVAILABLE"
    assert result["native_payload"] is None
    assert result["observations"][0]["executed"] is False


def test_partial_demo_executes_and_replays_without_fifty_case_gate_payload():
    result = owner.run_preservation_suite(owner.declared_preservation_cases()[:1])
    assert result["status"] == "PARTIAL"
    assert result["reason"] == "EGGLOG_COVERAGE_INCOMPLETE"
    assert len(result["observations"]) == 1
    assert result["observations"][0]["executed"] is True
    assert result["native_payload"] is None
    replay = owner.replay_preservation_suite(result["observations"])
    assert replay["status"] == "PARTIAL"
    assert replay["engine_executions"] == 0
    assert replay["native_payload"] is None


def test_duplicate_or_out_of_bounds_suite_cannot_emit_empirical_payload():
    cases = owner.declared_preservation_cases()
    for selected in ((), cases + (cases[0],), (cases[0],) * 50):
        result = owner.run_preservation_suite(selected)
        assert result["reason"] == "EGGLOG_ONE_TO_FIFTY_DISTINCT_COMPLEX_CASES_REQUIRED"
        assert result["observations"] == []
        assert result["native_payload"] is None


def test_source_partition_and_unsupported_shapes_refuse_before_execution():
    request = owner.declared_preservation_cases()[0]
    bad_partition = request.model_copy(update={"raw_prompt": request.raw_prompt + "hidden"})
    oversized = request.model_copy(update={"segments": request.segments * 5,
        "raw_prompt": request.raw_prompt * 5})
    for candidate, reason in ((bad_partition, "EGGLOG_SOURCE_PARTITION_MISMATCH"),
            (oversized, "EGGLOG_INPUT_SHAPE_UNSUPPORTED")):
        result = owner.rewrite_prompt(candidate)
        assert result["status"] == "REFUSED"
        assert result["reason"] == reason
        assert result["executed"] is False


def test_actual_measured_node_bound_refuses_without_payload(monkeypatch):
    monkeypatch.setattr(owner, "MAX_NODES", 90)
    result = owner.rewrite_prompt(owner.declared_preservation_cases()[0])
    assert result["executed"] is True
    assert result["node_counts"][0] <= 90 < result["node_counts"][-1]
    assert result["reason"] == "EGGLOG_NODE_BOUND"
    assert result["native_payload"] is None
