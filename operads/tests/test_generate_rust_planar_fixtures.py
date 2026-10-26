"""Freeze workflow planar substitution before its native domain slice."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from omega_engine_operads.domain.planar_substitution import (
    OPERAD_COLOURS,
    OperadOperation,
    SubstitutionError,
    admissible_substitutions,
    associativity_witness,
    is_admissible,
    substitute,
)


def outcome(call):
    try:
        value = call()
        return {"ok": dataclasses.asdict(value) if dataclasses.is_dataclass(value) else value}
    except SubstitutionError as exc:
        return {"error": {"code": exc.code, "message": str(exc)}}


def main():
    rows = [{"op": "vocabulary", "expected": sorted(OPERAD_COLOURS)}]
    operations = [
        OperadOperation("id_" + colour, (colour,), colour) for colour in sorted(OPERAD_COLOURS)
    ]
    operations.extend(
        (
            OperadOperation("combine", ("Audit", "Code"), "Proof"),
            OperadOperation("split", ("State", "Receipt"), "Audit"),
            OperadOperation("nullary", (), "State"),
            OperadOperation(" whitespace name ", ("State",), "State"),
        )
    )
    for operation in operations:
        rows.append(
            {
                "op": "construct",
                "input": dataclasses.asdict(operation),
                "expected": {"ok": dataclasses.asdict(operation)},
                "arity": operation.arity,
            }
        )
    for name, sources, target in (
        ("", (), "State"),
        (7, (), "State"),
        ("bad", "State", "State"),
        ("bad", ("Unknown",), "State"),
        ("bad", ("Z", "A", "Z"), "State"),
        ("bad", ("quoted'colour",), "State"),
        ("bad", ("line\ncolour",), "State"),
        ("bad", ("slash\\colour",), "State"),
        ("bad", ("tab\tcarriage\rcolour",), "State"),
        ("bad", ("both'\"quotes",), "State"),
        ("bad", ("control\x00colour",), "State"),
        ("bad", (), "unknown"),
    ):
        rows.append(
            {
                "op": "construct",
                "input": {"name": name, "source_colours": sources, "target_colour": target},
                "expected": outcome(lambda: OperadOperation(name, sources, target)),
            }
        )
    for first in operations:
        for second in operations:
            for index in range(first.arity):
                rows.append(
                    {
                        "op": "substitute",
                        "theta": dataclasses.asdict(first),
                        "phi": dataclasses.asdict(second),
                        "index": index,
                        "expected": outcome(lambda: substitute(first, index, second)),
                        "admissible": is_admissible(first, index, second),
                    }
                )
    for index in (-1, 2, 10**60, True, 1.0, "0", None):
        first, second = operations[-4], operations[-3]
        rows.append(
            {
                "op": "substitute",
                "theta": dataclasses.asdict(first),
                "phi": dataclasses.asdict(second),
                "index": index,
                "expected": outcome(lambda: substitute(first, index, second)),
                "admissible": is_admissible(first, index, second),
            }
        )
    theta, phi, psi = operations[-4], operations[-3], operations[-2]
    for i, j in ((0, 0), (0, 1), (-1, 0), (0, -1), (True, 0), (0, True)):
        rows.append(
            {
                "op": "associativity",
                "theta": dataclasses.asdict(theta),
                "phi": dataclasses.asdict(phi),
                "psi": dataclasses.asdict(psi),
                "i": i,
                "j": j,
                "expected": outcome(lambda: associativity_witness(theta, i, phi, j, psi)),
            }
        )
    rows.append(
        {
            "op": "admissible_substitutions",
            "operations": [dataclasses.asdict(operation) for operation in operations],
            "expected": admissible_substitutions(tuple(operations)),
        }
    )
    path = (
        Path(__file__).resolve().parents[2]
        / "omega_engine/crates_rs/tests/omega_operads/fixtures/python_planar_v1.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"vectors": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Frozen {len(rows)} planar vectors from the unchanged Python oracle.")


if __name__ == "__main__":
    main()
