"""Wire admission: the adversarial input table for every contract (RULE_PY_001).

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:contracts:v1
"""

from __future__ import annotations

import json
from fractions import Fraction
from typing import Any

import pytest
from pydantic import ValidationError

from pfp_lab.core.admission import AdmissionError
from pfp_lab.core.contracts import (
    MAX_JSON_BYTES,
    MAX_MOVES,
    AssertIn,
    CutIn,
    RetractIn,
    ScenarioIn,
    VerifyIn,
    admit_json,
    to_graph,
    to_move,
)
from pfp_lab.core.governor import AssertMove, CutMove, RetractMove, VerifyMove


def scenario(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": "pfp-lab.scenario.v1",
        "title": "t",
        "vertices": ["a", "b"],
        "edges": [{"source": "a", "target": "b", "weight": 2}],
        "moves": [{"move": "ASSERT", "source": "a", "target": "b", "value": "1/2"}],
    }
    body.update(changes)
    return body


def admit(body: dict[str, Any]) -> ScenarioIn:
    return admit_json(ScenarioIn, json.dumps(body))


def test_valid_scenario_admits_and_converts() -> None:
    admitted = admit(scenario())
    assert admitted.schema_id == "pfp-lab.scenario.v1"
    graph = to_graph(admitted)
    assert graph.vertices == ("a", "b")
    assert graph.edges[0].weight == 2
    move = to_move(admitted.moves[0])
    assert move == AssertMove("a", "b", Fraction(1, 2))
    assert admit(scenario(edges=[{"source": "a", "target": "b"}])).edges[0].weight == 1


BAD_SCENARIOS = [
    pytest.param({"schema": "pfp-lab.scenario.v2"}, id="wrong-schema"),
    pytest.param({"extra": 1}, id="unknown-field"),
    pytest.param({"vertices": []}, id="no-vertices"),
    pytest.param({"vertices": ["a", "a"]}, id="duplicate-vertex"),
    pytest.param({"vertices": ["a", "b c"]}, id="bad-name"),
    pytest.param({"vertices": "ab"}, id="vertices-not-array"),
    pytest.param({"edges": [{"source": "a", "target": "b", "weight": True}]}, id="bool-weight"),
    pytest.param({"edges": [{"source": "a", "target": "b", "weight": 1.0}]}, id="float-weight"),
    pytest.param({"edges": [{"source": "a", "target": "b", "weight": "1"}]}, id="string-weight"),
    pytest.param({"edges": [{"source": "a", "target": "b", "weight": 0}]}, id="zero-weight"),
    pytest.param({"edges": [{"source": "a", "target": "a"}]}, id="self-loop"),
    pytest.param({"edges": [{"source": "a", "target": "q"}]}, id="edge-off-carrier"),
    pytest.param({"edges": [{"source": "a", "target": "b"}, {"source": "a", "target": "b"}]}, id="dup-edge"),
    pytest.param({"moves": [{"move": "ASSERT", "source": "a", "target": "b", "value": 0.5}]}, id="float-value"),
    pytest.param({"moves": [{"move": "ASSERT", "source": "a", "target": "b", "value": 1}]}, id="int-value"),
    pytest.param({"moves": [{"move": "ASSERT", "source": "a", "target": "b", "value": "0.5"}]}, id="decimal"),
    pytest.param({"moves": [{"move": "ASSERT", "source": "a", "target": "b", "value": "2/4"}]}, id="unreduced"),
    pytest.param(
        {"moves": [{"move": "ASSERT", "source": "a", "target": "b", "value": "1", "provisional": 1}]}, id="int-as-bool"
    ),
    pytest.param({"moves": [{"move": "JUMP"}]}, id="unknown-move"),
    pytest.param({"moves": [{"source": "a"}]}, id="no-discriminator"),
    pytest.param(
        {
            "moves": [
                {
                    "move": "CUT",
                    "claims": [
                        {"source": "a", "target": "b", "value": "1"},
                        {"source": "a", "target": "b", "value": "2"},
                    ],
                }
            ]
        },
        id="duplicate-claim",
    ),
    pytest.param({"moves": [{"move": "CUT", "section": {"a": "x"}}]}, id="bad-section-value"),
    pytest.param({"moves": [{"move": "VERIFY", "obligation": "x" * 201}]}, id="long-obligation"),
    pytest.param({"moves": [{"move": "RETRACT", "target_step_id": "bad id"}]}, id="bad-step-id"),
    pytest.param({"moves": [{"move": "VERIFY", "obligation": "ZERO_DEFECT"}] * (MAX_MOVES + 1)}, id="too-many"),
]


@pytest.mark.parametrize("changes", BAD_SCENARIOS)
def test_bad_scenarios_are_refused(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        admit(scenario(**changes))


def test_max_moves_is_admitted() -> None:
    moves = [{"move": "VERIFY", "obligation": "ZERO_DEFECT"}] * MAX_MOVES
    assert len(admit(scenario(moves=moves)).moves) == MAX_MOVES


def test_oversized_json_is_refused_before_parsing() -> None:
    text = json.dumps(scenario(title="x" * MAX_JSON_BYTES))
    with pytest.raises(AdmissionError, match="limit"):
        admit_json(ScenarioIn, text)
    with pytest.raises(AdmissionError, match="limit"):
        admit_json(ScenarioIn, text.encode("utf-8"))


def test_size_is_measured_in_utf8_bytes() -> None:
    title = "é" * (MAX_JSON_BYTES // 2)
    with pytest.raises(AdmissionError, match="limit"):
        admit_json(ScenarioIn, json.dumps(scenario(title=title), ensure_ascii=False))


def test_malformed_json_is_a_validation_error() -> None:
    with pytest.raises(ValidationError):
        admit_json(ScenarioIn, "{not json")


def test_models_are_frozen() -> None:
    admitted = admit(scenario())
    with pytest.raises(ValidationError):
        admitted.title = "changed"  # type: ignore[misc]


def test_every_move_converts() -> None:
    cut_claims = CutIn(move="CUT", claims=())
    assert to_move(cut_claims) == CutMove(section=None, claims=(), step_id=None)
    body = scenario(
        moves=[
            {"move": "CUT", "section": {"a": "1/3"}, "step_id": "s1"},
            {"move": "CUT", "claims": [{"source": "a", "target": "b", "value": "-2"}]},
            {"move": "VERIFY", "obligation": "ZERO_DEFECT", "step_id": "v"},
            {"move": "RETRACT", "target_step_id": "s1", "reason": "why"},
            {
                "move": "ASSERT",
                "source": "a",
                "target": "b",
                "value": "3",
                "provisional": True,
                "enforce_monotonicity": True,
                "step_id": "x",
            },
        ]
    )
    moves = [to_move(item) for item in admit(body).moves]
    assert moves[0] == CutMove(section=(("a", Fraction(1, 3)),), claims=None, step_id="s1")
    assert moves[1] == CutMove(section=None, claims=((("a", "b"), Fraction(-2)),))
    assert moves[2] == VerifyMove("ZERO_DEFECT", step_id="v")
    assert moves[3] == RetractMove("s1", reason="why")
    assert moves[4] == AssertMove("a", "b", Fraction(3), step_id="x", provisional=True, enforce_monotonicity=True)


def test_move_models_reject_python_bool_for_int_and_float() -> None:
    with pytest.raises(ValidationError):
        AssertIn.model_validate({"move": "ASSERT", "source": "a", "target": "b", "value": 1.5})
    with pytest.raises(ValidationError):
        VerifyIn.model_validate({"move": "VERIFY", "obligation": 3})
    with pytest.raises(ValidationError):
        RetractIn.model_validate({"move": "RETRACT", "target_step_id": True})
