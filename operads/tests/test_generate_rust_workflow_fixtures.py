"""Freeze workflow findings from the unchanged Python oracle.

The first 28 vectors predate native validation; subsequent boundary vectors
extend that corpus after implementation.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from operads.domain.planar_substitution import OperadOperation
from operads.domain.workflow_graph import (
    WorkflowError,
    unknown_operations,
    validate_workflow,
)


def report(value):
    return {
        **dataclasses.asdict(value),
        "is_valid": value.is_valid,
        "signature_matches": value.signature_matches,
    }


def main():
    garden = {
        "identity": OperadOperation("identity", ("State",), "State"),
        "grow": OperadOperation("grow", ("State", "Audit"), "State"),
        "wrong": OperadOperation("wrong", ("State",), "Proof"),
    }
    base = {
        "workflow_id": "wf",
        "name": "Fixture workflow",
        "source_colours": ["State"],
        "target_colour": "State",
        "pipeline": [{"slot": 0, "operation": "identity"}],
        "authority_effect": "None",
    }
    cases = [
        base,
        {**base, "authority_effect": "none"},
        {**base, "authority_effect": "StateTransition"},
        {**base, "authority_effect": True},
        {**base, "pipeline": []},
        {**base, "pipeline": None},
        {**base, "pipeline": "steps"},
        {**base, "pipeline": [{"slot": 0, "operation": "missing"}]},
        {**base, "pipeline": [{"slot": 0}]},
        {**base, "pipeline": [{"slot": 0, "operation": "z"}, {"slot": 0, "operation": "a"}]},
        {**base, "pipeline": [{"slot": -1, "operation": "identity"}]},
        {**base, "pipeline": [{"slot": True, "operation": "identity"}]},
        {**base, "pipeline": [{"slot": 1, "operation": "identity"}]},
        {**base, "pipeline": [{"slot": 0, "operation": "wrong"}]},
        {**base, "pipeline": [{"slot": 0, "operation": "grow"}]},
        {**base, "pipeline": [{"slot": 0, "operation": "identity"}] * 3},
        {
            **base,
            "source_colours": ["State", "State"],
            "pipeline": [
                {"slot": 0, "operation": "identity"},
                {"slot": 1, "operation": "identity"},
            ],
        },
        {**base, "source_colours": ["Unknown"]},
        {**base, "target_colour": "Unknown"},
        {**base, "workflow_id": ""},
        None,
        [],
    ]
    for key in base:
        missing = dict(base)
        del missing[key]
        cases.append(missing)
    cases.extend(
        [
            {**base, "authority_effect": False},
            {**base, "authority_effect": None},
            {**base, "source_colours": "State"},
            {**base, "source_colours": ""},
            {**base, "workflow_id": 7},
            {**base, "workflow_id": False},
            {**base, "pipeline": [{"operation": "identity"}]},
            {**base, "pipeline": [{"slot": 0, "operation": ""}]},
            {
                **base,
                "pipeline": [
                    {"slot": 0, "operation": "missing"},
                    {"slot": 0, "operation": "identity"},
                    {"slot": 0, "operation": "missing"},
                ],
            },
            {},
            {"workflow_id": "fallback-name"},
        ]
    )
    rows = []
    for value in cases:
        try:
            result = validate_workflow(value, garden)
            expected = {"ok": report(result)}
            unknown = unknown_operations((result,))
        except WorkflowError as exc:
            expected = {"error": {"code": exc.code, "message": str(exc)}}
            unknown = ()
        rows.append({"input": value, "expected": expected, "unknown_operations": unknown})
    path = (
        Path(__file__).resolve().parents[2]
        / "engine/crates_rs/tests/core_operads/fixtures/python_workflow_v1.json"
    )
    path.write_text(
        json.dumps(
            {
                "garden": {
                    name: dataclasses.asdict(operation) for name, operation in garden.items()
                },
                "vectors": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Frozen {len(rows)} workflow vectors from the unchanged Python oracle.")


if __name__ == "__main__":
    main()
