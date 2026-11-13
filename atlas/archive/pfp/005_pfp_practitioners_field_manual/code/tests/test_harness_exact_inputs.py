"""The streaming harness refuses float and Boolean claim values instead of converting them.

`Fraction(0.1)` is the binary expansion of the float, not one tenth, and
`Fraction(True)` is 1, so accepting either would turn an inexact or mistyped model
output into a claimed exact value. Integers and exact rational strings are
accepted. The governor then scores the complete proposal on its Python path.
"""

import pytest

from llm_streaming_harness import MockLLMStreamingProposer, SymbolGameStreamingSession

VERTICES = ("a", "b", "c")
EDGES = (("a", "b", 1), ("b", "c", 2), ("c", "a", 2))
CLAIMS = {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1}


def _cut(claims):
    return {
        "schema": "TAU_SG_V1",
        "step_id": "s01",
        "parent_step_id": "root",
        "move_type": "CUT",
        "move_parameters": {"rule_id": "R1", "proposed_claims": claims},
        "expected_defect_delta": "-3",
    }


def _session(claims, monkeypatch):
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
    session = SymbolGameStreamingSession(VERTICES, EDGES, CLAIMS, MockLLMStreamingProposer([_cut(claims)]))
    session.initialize()
    return session


@pytest.mark.parametrize("bad", [0.5, True], ids=["float", "bool"])
def test_float_or_bool_claim_value_is_refused(monkeypatch, bad):
    session = _session({"a, b": bad, "b, c": 1, "c, a": 1}, monkeypatch)
    verdict = session.run_turn("repair")
    assert verdict["status"] == "FW-OP_Refusal"
    assert verdict["admitted"] is False
    assert "exact integer or rational string" in verdict["reason"]


def test_exact_values_are_scored(monkeypatch):
    session = _session({"a, b": "-2", "b, c": 1, "c, a": 1}, monkeypatch)
    verdict = session.run_turn("repair")
    assert verdict["admitted"] is True
    assert verdict["defect_after"] == "0"
