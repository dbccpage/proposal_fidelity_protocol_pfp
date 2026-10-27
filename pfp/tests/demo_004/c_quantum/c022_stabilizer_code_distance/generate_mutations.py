"""Generate the C022 hostile checker mutations (each payload distinct).

Earlier versions wrote eight identical copies of each mutant and corrupted a
synthetic LRAT object that no checker could verify. This version derives each
mutant from a different code or defect and adds trivial responders (empty
object, refusal, constant answer, Boolean or float distance).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.reference_solver.solver import (  # noqa: E402
    solve,
)

EXAMPLES = Path(__file__).resolve().parent / "participant_packet" / "examples"
SOLVED_EXAMPLES = (
    "c022_ex01_five_qubit",
    "c022_ex02_steane",
    "c022_ex03_shor_degenerate",
    "c022_ex04_toric_2x2",
)


def _load(stem: str) -> dict[str, Any]:
    return json.loads((EXAMPLES / f"{stem}.json").read_text(encoding="utf-8"))


def _mutants() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for stem in SOLVED_EXAMPLES:
        case = _load(stem)
        cert = solve(case)
        d = cert["distance"]
        cid = case["id"]
        stab = case["generators"][0][1:]
        out.append(
            (
                "stabilizer generator offered as logical",
                case,
                {**cert, "logical": stab, "distance": sum(ch != "I" for ch in stab)},
            )
        )
        heavier = list(cert["logical"])
        heavier[heavier.index("I")] = "X"
        out.append(
            (
                "logical of weight d + 1 reported with distance d",
                case,
                {**cert, "logical": "".join(heavier)},
            )
        )
        out.append(
            (
                "distance underclaimed with an anticommuting weight-1 operator",
                case,
                {**cert, "distance": 1, "logical": "Z" + "I" * (case["num_qubits"] - 1)},
            )
        )
        out.append(
            (
                "synthetic LRAT object in lower_bound",
                case,
                {
                    **cert,
                    "lower_bound": {
                        "format": "lrat",
                        "encoding_sha256": "0" * 64,
                        "proof_b64gz": "H4sIAAAAAAAA/wMAAAAAAAAAAAA=",
                    },
                },
            )
        )
        out.append(("Boolean distance", case, {**cert, "distance": True}))
        out.append(("float distance", case, {**cert, "distance": float(d)}))
        out.append(("trivial responder: empty object", case, {}))
        out.append(
            (
                "trivial responder: UNKNOWN refusal",
                case,
                {"id": cid, "status": "UNKNOWN", "refusal_code": "BUDGET_EXHAUSTED"},
            )
        )
        out.append(
            (
                "trivial responder: false anticommuting witness",
                case,
                {
                    "id": cid,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"kind": "anticommuting", "pair": [0, 1]},
                },
            )
        )
        out.append(
            (
                "trivial responder: false dependency",
                case,
                {
                    "id": cid,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "kind": "dependent",
                        "linear_combination": [1] + [0] * (len(case["generators"]) - 1),
                    },
                },
            )
        )
    steane = _load("c022_ex02_steane")
    out.append(
        (
            "constant answer: five-qubit certificate on the Steane code",
            steane,
            {**solve(_load("c022_ex01_five_qubit")), "id": steane["id"]},
        )
    )
    out.append(
        ("distance d + 1 with a valid weight-d logical", steane, {**solve(steane), "distance": 4})
    )

    anti = _load("c022_ex08_malformed_anticommuting")
    dep = _load("c022_ex09_malformed_dependent")
    minus = _load("c022_ex10_malformed_minus_id")
    out.append(
        (
            "SOLVED on an anticommuting generator set",
            anti,
            {
                "id": anti["id"],
                "status": "SOLVED",
                "distance": 1,
                "logical": "YIIII",
                "lower_bound": None,
            },
        )
    )
    out.append(
        (
            "anticommuting witness names one generator twice",
            anti,
            {
                "id": anti["id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "anticommuting", "pair": [0, 0]},
            },
        )
    )
    out.append(
        (
            "anticommuting witness with Boolean indices",
            anti,
            {
                "id": anti["id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "anticommuting", "pair": [False, True]},
            },
        )
    )
    out.append(
        (
            "dependent witness is the zero combination",
            dep,
            {
                "id": dep["id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "dependent", "linear_combination": [0, 0, 0]},
            },
        )
    )
    out.append(
        (
            "dependent witness combination does not vanish",
            dep,
            {
                "id": dep["id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "dependent", "linear_combination": [1, 1, 0]},
            },
        )
    )
    out.append(
        (
            "minus_identity witness on a product that is not -I",
            dep,
            {
                "id": dep["id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "minus_identity", "subset": [0, 1, 2]},
            },
        )
    )
    out.append(
        (
            "minus_identity witness with an out-of-range index",
            minus,
            {
                "id": minus["id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "minus_identity", "subset": [1]},
            },
        )
    )
    out.append(
        (
            "OUT_OF_SCOPE with an empty witness",
            minus,
            {"id": minus["id"], "status": "OUT_OF_SCOPE", "witness": {}},
        )
    )
    five = _load("c022_ex01_five_qubit")
    out.append(
        (
            "full_rank witness on a code with a logical qubit",
            five,
            {"id": five["id"], "status": "OUT_OF_SCOPE", "witness": {"kind": "full_rank"}},
        )
    )
    out.append(
        (
            "full_rank witness on an anticommuting pair",
            anti,
            {"id": anti["id"], "status": "OUT_OF_SCOPE", "witness": {"kind": "full_rank"}},
        )
    )
    return out


def main() -> None:
    mut_dir = Path(__file__).resolve().parent / "judge_packet" / "mutation_suite" / "mutations"
    mut_dir.mkdir(parents=True, exist_ok=True)
    for old in mut_dir.glob("mut_*.json"):
        old.unlink()
    seen: set[str] = set()
    count = 0
    for description, case, certificate in _mutants():
        key = json.dumps([case, certificate], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        count += 1
        record = {
            "id": f"mut_{count:02d}",
            "description": description,
            "case": case,
            "certificate": certificate,
        }
        (mut_dir / f"mut_{count:02d}.json").write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(f"Generated {count} distinct hostile checker mutations.")


if __name__ == "__main__":
    main()
