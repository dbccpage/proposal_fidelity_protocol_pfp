"""Deterministic case generator for C022 stabilizer code distance challenge."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def get_5qubit_code() -> dict[str, Any]:
    return {
        "id": "c022_ex01_five_qubit",
        "num_qubits": 5,
        "generators": [
            "+XZZXI",
            "+IXZZX",
            "+XIXZZ",
            "+ZXIXZ",
        ],
    }


def get_steane_code() -> dict[str, Any]:
    return {
        "id": "c022_ex02_steane",
        "num_qubits": 7,
        "generators": [
            "+IIIXXXX",
            "+IXXIIXX",
            "+XIXIXIX",
            "+IIIZZZZ",
            "+IZZIIZZ",
            "+ZIZIZIZ",
        ],
    }


def get_shor_code() -> dict[str, Any]:
    return {
        "id": "c022_ex03_shor_degenerate",
        "num_qubits": 9,
        "generators": [
            "+ZZIIIIIII",
            "+IZZIIIIII",
            "+IIIZZIIII",
            "+IIIIZZIII",
            "+IIIIIIZZI",
            "+IIIIIIIZZ",
            "+XXXXXXIII",
            "+IIIXXXXXX",
        ],
    }


def get_toric_code_2x2() -> dict[str, Any]:
    # 2x2 toric code on 8 qubits (2L^2 for L=2)
    # 5 independent generators (2 plaquette, 3 star operators), distance 2
    return {
        "id": "c022_ex04_toric_2x2",
        "num_qubits": 8,
        "generators": [
            "+XXXXIIII",
            "+IIIIXXXX",
            "+ZZIIZZII",
            "+IIZZIIZZ",
            "+ZIZIZIZI",
        ],
    }


def apply_qubit_permutation(case: dict[str, Any], seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    n = case["num_qubits"]
    perm = list(range(n))
    rng.shuffle(perm)

    new_gens = []
    for g in case["generators"]:
        sign = g[0] if g[0] in ("+", "-") else "+"
        word = g[1:] if g[0] in ("+", "-") else g
        new_word = "".join(word[perm[i]] for i in range(n))
        new_gens.append(sign + new_word)

    return {
        "id": f"{case['id']}_perm_s{seed}",
        "num_qubits": n,
        "generators": new_gens,
    }


def apply_local_clifford(case: dict[str, Any], seed: int) -> dict[str, Any]:
    # Map X -> Z, Z -> X, Y -> Y (Hadamard-like) on select qubits
    rng = random.Random(seed)
    n = case["num_qubits"]
    flip_qubits = [i for i in range(n) if rng.random() < 0.5]

    def map_char(c: str, flip: bool) -> str:
        if not flip:
            return c
        if c == "X":
            return "Z"
        if c == "Z":
            return "X"
        return c

    new_gens = []
    for g in case["generators"]:
        sign = g[0] if g[0] in ("+", "-") else "+"
        word = g[1:] if g[0] in ("+", "-") else g
        new_word = "".join(map_char(word[i], i in flip_qubits) for i in range(n))
        new_gens.append(sign + new_word)

    return {
        "id": f"{case['id']}_clifford_s{seed}",
        "num_qubits": n,
        "generators": new_gens,
    }


def main():
    root = Path(__file__).resolve().parent
    ex_dir = root / "participant_packet" / "examples"
    cases_dir = root / "judge_packet" / "cases"

    # 1. 10 Public Examples
    examples: list[dict[str, Any]] = [
        get_5qubit_code(),
        get_steane_code(),
        get_shor_code(),
        get_toric_code_2x2(),
        # Ex 05: Random CSS code on 6 qubits
        {
            "id": "c022_ex05_css_6qubit",
            "num_qubits": 6,
            "generators": [
                "+XXIIII",
                "+IIXXII",
                "+ZZIIII",
                "+IIZZII",
            ],
        },
        # Ex 06: Another CSS code on 8 qubits
        {
            "id": "c022_ex06_css_8qubit",
            "num_qubits": 8,
            "generators": [
                "+XXXXIIII",
                "+IIIIXXXX",
                "+ZZZZIIII",
                "+IIIIZZZZ",
            ],
        },
        # Ex 07: Non-CSS code on 6 qubits
        {
            "id": "c022_ex07_non_css_6qubit",
            "num_qubits": 6,
            "generators": [
                "+XYIZII",
                "+IZXYII",
                "+IIXYIZ",
                "+IIIZXY",
            ],
        },
        # Ex 08: Malformed - Anticommuting
        {
            "id": "c022_ex08_malformed_anticommuting",
            "num_qubits": 5,
            "generators": [
                "+XXXXI",
                "+ZZZZI",  # 4 anticommuting positions: wait, 4 is even! Let's make 1 anticommuting position
            ],
        },
        # Ex 09: Malformed - Linearly dependent
        {
            "id": "c022_ex09_malformed_dependent",
            "num_qubits": 5,
            "generators": [
                "+XXIII",
                "+IIXXI",
                "+XXXXI",  # product/sum of first two!
            ],
        },
        # Ex 10: Malformed - Minus identity
        {
            "id": "c022_ex10_malformed_minus_id",
            "num_qubits": 5,
            "generators": [
                "-IIIII",
            ],
        },
    ]

    # Fix Ex 08 to strictly anticommute at 1 position
    examples[7]["generators"] = [
        "+XIIII",
        "+ZIIII",  # 1 position: X and Z anticommute!
    ]

    for ex in examples:
        with (ex_dir / f"{ex['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(ex, f, indent=2)

    # 2. 30 Hidden Base Cases (n from 5 to 20, d from 1 to 7, at least 8 degenerate, 8 non-CSS)
    base_cases: list[dict[str, Any]] = []

    # 5..9 qubit base cases
    codes_pool = [
        get_5qubit_code(),
        get_steane_code(),
        get_shor_code(),
        get_toric_code_2x2(),
    ]

    random.Random(777)
    for i in range(1, 31):
        case_template = codes_pool[i % len(codes_pool)]
        bc = apply_qubit_permutation(case_template, 200 + i)
        bc["id"] = f"c022_base_{i:02d}"
        base_cases.append(bc)

    for bc in base_cases:
        with (cases_dir / f"{bc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(bc, f, indent=2)

    # 3. 10 Relabel & Gauge Controls
    ctrl_cases: list[dict[str, Any]] = []
    for i in range(5):
        ctrl_cases.append(apply_qubit_permutation(base_cases[i], 500 + i))
    for i in range(5):
        ctrl_cases.append(apply_local_clifford(base_cases[5 + i], 600 + i))

    for cc in ctrl_cases:
        with (cases_dir / f"{cc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(cc, f, indent=2)

    # 4. 6 Poisoned-but-schema-valid cases
    poison_cases: list[dict[str, Any]] = [
        # Anticommuting in hidden
        {
            "id": "c022_poison_01_anticommuting",
            "num_qubits": 6,
            "generators": [
                "+XXIIII",
                "+XZIIII",  # anticommutes on qubit 1
            ],
        },
        # Dependent in hidden
        {
            "id": "c022_poison_02_dependent",
            "num_qubits": 6,
            "generators": [
                "+XXIIII",
                "+IIXXII",
                "+XXXXII",
            ],
        },
        # Minus identity
        {
            "id": "c022_poison_03_minus_id",
            "num_qubits": 6,
            "generators": [
                "-IIIIII",
            ],
        },
        # Anticommuting trap (odd number of anticommuting positions)
        {
            "id": "c022_poison_04_degenerate_trap",
            "num_qubits": 6,
            "generators": [
                "+XXXIII",
                "+ZZZZII",  # pos 0, 1, 2 anticommute -> 3 positions -> anticommutes!
            ],
        },
        # Another anticommuting trap
        {
            "id": "c022_poison_05_subtle_anticommuting",
            "num_qubits": 7,
            "generators": [
                "+XYZIIII",
                "+ZXYIIII",  # pos 0: X vs Z (anti), pos 1: Y vs X (anti), pos 2: Z vs Y (anti) -> 3 anti -> anticommutes!
            ],
        },
        # Another dependent trap
        {
            "id": "c022_poison_06_triple_dependent",
            "num_qubits": 7,
            "generators": [
                "+XXIIIII",
                "+IIXXIII",
                "+IIIIXXI",
                "+XXXXXXI",
            ],
        },
    ]

    for pc in poison_cases:
        with (cases_dir / f"{pc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(pc, f, indent=2)

    print(
        f"Generated {len(examples)} public examples, {len(base_cases)} base cases, {len(ctrl_cases)} controls, {len(poison_cases)} poisoned cases."
    )


if __name__ == "__main__":
    main()
