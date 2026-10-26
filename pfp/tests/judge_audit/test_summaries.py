"""Solvability by reference and by witness, and the escape measures."""

from __future__ import annotations

from omega_engine_woland.tests.pilots.judge_packet_audit import summaries

DESC = {
    "checkers": [{"role": "exact"}, {"role": "independent"}],
    "cases": [{"key": "a"}, {"key": "b"}, {"key": "c"}],
}
STRATEGIES = [
    {"id": "empty", "family": "empty", "template": {}},
    {
        "id": "abstain:UNKNOWN",
        "family": "abstain",
        "template": {"id": "<case id>", "status": "UNKNOWN"},
    },
    {
        "id": "template_example:ex1",
        "family": "template_example",
        "template": {"id": "<case id>", "status": "SOLVED", "x": "1"},
    },
]


def _row(case: str, responder: str, family: str, gate: str, exact: str, independent: str) -> dict:
    return {
        "kind": "responder",
        "case": case,
        "responder": responder,
        "family": family,
        "calls": {"gate": [gate, ""], "exact": [exact, ""], "independent": [independent, ""]},
    }


def test_witnessed_solvable_case_counts_as_escape_without_a_reference() -> None:
    # counterexample in the style of C057 before repair: the reference solver cannot be imported,
    # yet a participant example's network passes on case b, and UNKNOWN also passes on case b
    rows = [
        _row("a", "abstain:UNKNOWN", "abstain", "ACCEPT", "ACCEPT", "ACCEPT"),
        _row("b", "abstain:UNKNOWN", "abstain", "ACCEPT", "ACCEPT", "ACCEPT"),
        _row("c", "abstain:UNKNOWN", "abstain", "REJECT", "REJECT", "ACCEPT"),
        _row("b", "template_example:ex1", "template_example", "ACCEPT", "ACCEPT", "ACCEPT"),
        _row("c", "template_example:ex1", "template_example", "ACCEPT", "ACCEPT", "ACCEPT"),
        _row("a", "empty", "empty", "REJECT", "REJECT", "ACCEPT"),
    ]
    summary = summaries.summarize(DESC, rows, STRATEGIES)
    assert summary["reference_returned"] == 0
    assert summary["solvable_by_reference"] == 0
    assert summary["solvable_by_witness"] == 2
    assert summary["refusal"]["union_on_solvable"] == 1
    assert summary["refusal"]["best_fixed_overall"] == {"count": 2, "strategy": "abstain:UNKNOWN"}
    assert summary["refusal"]["per_checker_union_on_solvable"] == {"exact": 1, "independent": 2}
    assert summary["empty"] == {
        "gate_accept": 0,
        "per_checker_accept": {"exact": 0, "independent": 1},
    }


def test_reference_rejected_by_its_own_gate_is_not_solvable() -> None:
    rows = [
        {
            "kind": "reference",
            "case": "a",
            "solver": {"outcome": "RETURNED", "status": "SOLVED"},
            "calls": {
                "gate": ["REJECT", "bad"],
                "exact": ["REJECT", ""],
                "independent": ["ACCEPT", ""],
            },
        },
        {
            "kind": "reference",
            "case": "b",
            "solver": {"outcome": "RETURNED", "status": "UNKNOWN"},
            "calls": {
                "gate": ["ACCEPT", ""],
                "exact": ["ACCEPT", ""],
                "independent": ["ACCEPT", ""],
            },
        },
        _row("a", "abstain:UNKNOWN", "abstain", "ACCEPT", "ACCEPT", "ACCEPT"),
    ]
    summary = summaries.summarize(DESC, rows, STRATEGIES)
    assert summary["reference_returned"] == 2
    assert summary["reference_gate_accept"] == 1
    assert summary["solvable_cases"] == 0
    assert summary["refusal"]["union_on_solvable"] == 0
