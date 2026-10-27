"""Case generator for C023: Clifford Circuit Synthesis from Tableaux."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from c023_clifford_tableau_synthesis.reference_solver.synthesis import synthesize_clifford_circuit
from c023_clifford_tableau_synthesis.reference_solver.tableau import Tableau


def generate_random_tableau(n: int, num_gates: int, seed: int) -> tuple[Tableau, list[list[Any]]]:
    rng = random.Random(seed)
    tab = Tableau(n)
    raw_gates: list[list[Any]] = []
    for _ in range(num_gates):
        g = rng.choice(["H", "S", "CNOT"])
        if g in ("H", "S"):
            q = rng.randint(0, n - 1)
            tab.apply_gate(g, q)
            raw_gates.append([g, q])
        else:
            c = rng.randint(0, n - 1)
            t = rng.randint(0, n - 1)
            while t == c:
                t = rng.randint(0, n - 1)
            tab.apply_gate("CNOT", c, t)
            raw_gates.append(["CNOT", c, t])
    return tab, raw_gates


def apply_qubit_permutation(case: dict[str, Any], seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    n = case["num_qubits"]
    perm = list(range(n))
    rng.shuffle(perm)
    inv_perm = [0] * n
    for i, p in enumerate(perm):
        inv_perm[p] = i

    old_images = case["images"]
    new_images: dict[str, str] = {}
    for j in range(n):
        orig_key = f"X{perm[j]}"
        s = old_images[orig_key]
        sign = s[0] if s[0] in ("+", "-") else "+"
        word = s[1:] if s[0] in ("+", "-") else s
        new_word = "".join(word[perm[i]] for i in range(n))
        new_images[f"X{j}"] = sign + new_word

    for j in range(n):
        orig_key = f"Z{perm[j]}"
        s = old_images[orig_key]
        sign = s[0] if s[0] in ("+", "-") else "+"
        word = s[1:] if s[0] in ("+", "-") else s
        new_word = "".join(word[perm[i]] for i in range(n))
        new_images[f"Z{j}"] = sign + new_word

    perm_tab = Tableau.from_images_dict(n, new_images)
    synth = synthesize_clifford_circuit(perm_tab)
    return {
        "id": f"{case['id']}_perm_s{seed}",
        "num_qubits": n,
        "gate_budget": len(synth),
        "images": new_images,
    }


def apply_pauli_conjugation(case: dict[str, Any], seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    n = case["num_qubits"]
    # Conjugate by a random Pauli on each qubit (flips signs)
    tab = Tableau.from_images_dict(n, case["images"])
    for q in range(n):
        choice = rng.choice(["I", "X", "Y", "Z"])
        if choice == "X":
            # X = H S^2 H
            tab.apply_H(q)
            tab.apply_S(q)
            tab.apply_S(q)
            tab.apply_H(q)
        elif choice == "Z":
            # Z = S^2
            tab.apply_S(q)
            tab.apply_S(q)
        elif choice == "Y":
            # Y = S X S^\dagger
            tab.apply_S(q)
            tab.apply_H(q)
            tab.apply_S(q)
            tab.apply_S(q)
            tab.apply_H(q)
            tab.apply_S(q)
            tab.apply_S(q)
            tab.apply_S(q)

    # Re-synthesize to find new gate budget
    synth = synthesize_clifford_circuit(tab)
    return {
        "id": f"{case['id']}_pauli_s{seed}",
        "num_qubits": n,
        "gate_budget": len(synth),
        "images": tab.to_images_dict(),
    }


def main():
    root = Path(__file__).resolve().parent
    ex_dir = root / "participant_packet" / "examples"
    cases_dir = root / "judge_packet" / "cases"

    # 1. 10 Public Examples
    examples: list[dict[str, Any]] = []

    # Ex 01: Identity on 2 qubits
    tab_id = Tableau(2)
    examples.append(
        {
            "id": "c023_ex01_identity",
            "num_qubits": 2,
            "gate_budget": 0,
            "images": tab_id.to_images_dict(),
        }
    )

    # Ex 02: Pauli Z on qubit 0 (sign flip on X0)
    tab_z = Tableau(2)
    tab_z.apply_S(0)
    tab_z.apply_S(0)
    examples.append(
        {
            "id": "c023_ex02_pauli_z",
            "num_qubits": 2,
            "gate_budget": 4,
            "images": tab_z.to_images_dict(),
        }
    )

    # Ex 03: SWAP on 2 qubits
    tab_swap = Tableau(2)
    tab_swap.apply_CNOT(0, 1)
    tab_swap.apply_CNOT(1, 0)
    tab_swap.apply_CNOT(0, 1)
    examples.append(
        {
            "id": "c023_ex03_swap",
            "num_qubits": 2,
            "gate_budget": 6,
            "images": tab_swap.to_images_dict(),
        }
    )

    # Ex 04: CNOT on 2 qubits
    tab_cnot = Tableau(2)
    tab_cnot.apply_CNOT(0, 1)
    examples.append(
        {
            "id": "c023_ex04_cnot",
            "num_qubits": 2,
            "gate_budget": 2,
            "images": tab_cnot.to_images_dict(),
        }
    )

    # Ex 05: 3-qubit GHZ encoder (H0 then CNOT 0->1, CNOT 0->2)
    tab_ghz = Tableau(3)
    tab_ghz.apply_H(0)
    tab_ghz.apply_CNOT(0, 1)
    tab_ghz.apply_CNOT(0, 2)
    synth_ghz = synthesize_clifford_circuit(tab_ghz)
    examples.append(
        {
            "id": "c023_ex05_ghz_encoder",
            "num_qubits": 3,
            "gate_budget": len(synth_ghz),
            "images": tab_ghz.to_images_dict(),
        }
    )

    # Ex 06: Sign-only case on 2 qubits (all signs -1)
    tab_signs = Tableau(2)
    tab_signs.r = [1, 1, 1, 1]
    synth_signs = synthesize_clifford_circuit(tab_signs)
    examples.append(
        {
            "id": "c023_ex06_sign_only",
            "num_qubits": 2,
            "gate_budget": len(synth_signs),
            "images": tab_signs.to_images_dict(),
        }
    )

    # Ex 07: 4-qubit random Clifford
    tab_4a, _ = generate_random_tableau(4, 15, 401)
    synth_4a = synthesize_clifford_circuit(tab_4a)
    examples.append(
        {
            "id": "c023_ex07_random_4q_a",
            "num_qubits": 4,
            "gate_budget": len(synth_4a),
            "images": tab_4a.to_images_dict(),
        }
    )

    # Ex 08: 4-qubit random Clifford B
    tab_4b, _ = generate_random_tableau(4, 20, 402)
    synth_4b = synthesize_clifford_circuit(tab_4b)
    examples.append(
        {
            "id": "c023_ex08_random_4q_b",
            "num_qubits": 4,
            "gate_budget": len(synth_4b),
            "images": tab_4b.to_images_dict(),
        }
    )

    # Ex 09: Malformed - non-symplectic pair (X0 and Z1 anticommute when they must commute)
    tab_mal = Tableau(2)
    mal_images = tab_mal.to_images_dict()
    mal_images["X0"] = "+XZ"  # anticommutes with Z1 which is +IZ
    examples.append(
        {
            "id": "c023_ex09_malformed_anticommuting",
            "num_qubits": 2,
            "gate_budget": 10,
            "images": mal_images,
        }
    )

    # Ex 10: Out of bounds (n = 13 > 12)
    tab_13 = Tableau(13)
    examples.append(
        {
            "id": "c023_ex10_out_of_bounds_13q",
            "num_qubits": 13,
            "gate_budget": 20,
            "images": tab_13.to_images_dict(),
        }
    )

    for ex in examples:
        with (ex_dir / f"{ex['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(ex, f, indent=2)

    # 2. 30 Hidden Base Cases (n in {2, 3, 4, 6, 8, 12})
    base_cases: list[dict[str, Any]] = []
    qubit_sizes = [
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        6,
        6,
        6,
        6,
        6,
        6,
        8,
        8,
        8,
        8,
        8,
        8,
        12,
        12,
        12,
        12,
        12,
        12,
    ]

    for i, n in enumerate(qubit_sizes):
        seed = 1000 + i
        num_gates = 5 * n
        tab, _ = generate_random_tableau(n, num_gates, seed)
        synth = synthesize_clifford_circuit(tab)
        bc = {
            "id": f"c023_base_{i + 1:02d}",
            "num_qubits": n,
            "gate_budget": len(synth),
            "images": tab.to_images_dict(),
        }
        base_cases.append(bc)
        with (cases_dir / f"{bc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(bc, f, indent=2)

    # 3. 10 Relabel & Gauge Controls
    ctrl_cases: list[dict[str, Any]] = []
    # 5 qubit permutations
    for i in range(5):
        ctrl_cases.append(apply_qubit_permutation(base_cases[i], 2000 + i))
    # 5 Pauli conjugations
    for i in range(5):
        ctrl_cases.append(apply_pauli_conjugation(base_cases[5 + i], 3000 + i))

    for cc in ctrl_cases:
        with (cases_dir / f"{cc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(cc, f, indent=2)

    # 4. 6 Poisoned-but-schema-valid cases
    poison_cases: list[dict[str, Any]] = []

    # Poison 01: Non-symplectic X pair
    p1_tab = Tableau(3)
    p1_images = p1_tab.to_images_dict()
    p1_images["X0"] = (
        "+ZII"  # anticommutes with X0 (wait: X0 vs X0 is reflexive). Let's make X0 and X1 anticommute:
    )
    p1_images["X0"] = "+XIZ"
    p1_images["X1"] = "+IXX"  # Pos 2: Z vs X -> anticommutes!
    poison_cases.append(
        {
            "id": "c023_poison_01_nonsymplectic_xx",
            "num_qubits": 3,
            "gate_budget": 10,
            "images": p1_images,
        }
    )

    # Poison 02: Non-symplectic Z pair
    p2_tab = Tableau(3)
    p2_images = p2_tab.to_images_dict()
    p2_images["Z0"] = "+XZI"
    p2_images["Z1"] = (
        "+ZXI"  # Pos 0: X vs Z (anti), Pos 1: Z vs X (anti) -> 2 anti (commute). Let's add Pos 2:
    )
    p2_images["Z0"] = "+XZX"
    p2_images["Z1"] = "+ZXZ"  # Pos 0 anti, Pos 1 anti, Pos 2 anti -> 3 anti -> anticommutes!
    poison_cases.append(
        {
            "id": "c023_poison_02_nonsymplectic_zz",
            "num_qubits": 3,
            "gate_budget": 10,
            "images": p2_images,
        }
    )

    # Poison 03: Non-symplectic X-Z cross pair (X0 and Z0 commute instead of anticommute!)
    p3_tab = Tableau(3)
    p3_images = p3_tab.to_images_dict()
    p3_images["X0"] = "+XII"
    p3_images["Z0"] = "+XII"  # X and X commute!
    poison_cases.append(
        {
            "id": "c023_poison_03_commuting_xz_pair",
            "num_qubits": 3,
            "gate_budget": 10,
            "images": p3_images,
        }
    )

    # Poison 04: Out of bounds n=14
    p4_tab = Tableau(14)
    poison_cases.append(
        {
            "id": "c023_poison_04_out_of_bounds_14q",
            "num_qubits": 14,
            "gate_budget": 20,
            "images": p4_tab.to_images_dict(),
        }
    )

    # Poison 05: Image length mismatch
    p5_tab = Tableau(4)
    p5_images = p5_tab.to_images_dict()
    p5_images["X0"] = "+XIIIII"  # length 6 for 4 qubits!
    poison_cases.append(
        {
            "id": "c023_poison_05_length_mismatch",
            "num_qubits": 4,
            "gate_budget": 10,
            "images": p5_images,
        }
    )

    # Poison 06: Invalid Pauli character
    p6_tab = Tableau(4)
    p6_images = p6_tab.to_images_dict()
    p6_images["X1"] = "+XAQI"
    poison_cases.append(
        {
            "id": "c023_poison_06_invalid_pauli_char",
            "num_qubits": 4,
            "gate_budget": 10,
            "images": p6_images,
        }
    )

    for pc in poison_cases:
        with (cases_dir / f"{pc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(pc, f, indent=2)

    print(
        f"Generated {len(examples)} examples, {len(base_cases)} base cases, {len(ctrl_cases)} controls, {len(poison_cases)} poisoned cases."
    )


if __name__ == "__main__":
    main()
