# AuthorityEffect: None.
"""
Deterministic Case & Mutation Suite Generator for C042.
Generates:
1. 64 Judge cases (40 base + 16 relabel/gauge + 8 poisoned)
2. 48 Corrupted mutation cases (for checker mutation testing)
3. 10 Public participant examples
"""

from __future__ import annotations

import json
from pathlib import Path

from c042_sat_with_drat_certificates.reference_solver.solver import solve

PKG_ROOT = Path(__file__).resolve().parent.parent
JUDGE_CASES_DIR = PKG_ROOT / "judge_packet" / "cases"
MUTATION_DIR = PKG_ROOT / "judge_packet" / "mutation_suite"
EXAMPLES_DIR = PKG_ROOT / "participant_packet" / "examples"

JUDGE_CASES_DIR.mkdir(parents=True, exist_ok=True)
MUTATION_DIR.mkdir(parents=True, exist_ok=True)
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def build_base_cases() -> list[dict]:
    cases = []

    # Family 1: Coloring (8 cases: 4 SAT, 4 UNSAT)
    # Triangle (K3) with k=3 (SAT)
    cases.append(
        {
            "case_id": "c042_base_01",
            "family": "coloring",
            "n": 3,
            "k": 3,
            "edges": [[0, 1], [1, 2], [0, 2]],
            "expected_kind": "SAT",
        }
    )
    # Triangle (K3) with k=2 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_02",
            "family": "coloring",
            "n": 3,
            "k": 2,
            "edges": [[0, 1], [1, 2], [0, 2]],
            "expected_kind": "UNSAT",
        }
    )
    # C5 (5-cycle) with k=3 (SAT)
    cases.append(
        {
            "case_id": "c042_base_03",
            "family": "coloring",
            "n": 5,
            "k": 3,
            "edges": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
            "expected_kind": "SAT",
        }
    )
    # C5 (5-cycle) with k=2 (UNSAT - odd cycle)
    cases.append(
        {
            "case_id": "c042_base_04",
            "family": "coloring",
            "n": 5,
            "k": 2,
            "edges": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
            "expected_kind": "UNSAT",
        }
    )
    # Complete bipartite K2,3 with k=2 (SAT)
    cases.append(
        {
            "case_id": "c042_base_05",
            "family": "coloring",
            "n": 5,
            "k": 2,
            "edges": [[0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4]],
            "expected_kind": "SAT",
        }
    )
    # K4 with k=3 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_06",
            "family": "coloring",
            "n": 4,
            "k": 3,
            "edges": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]],
            "expected_kind": "UNSAT",
        }
    )
    # Petersen-like small graph with k=3 (SAT)
    cases.append(
        {
            "case_id": "c042_base_07",
            "family": "coloring",
            "n": 6,
            "k": 3,
            "edges": [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3], [0, 3], [1, 4]],
            "expected_kind": "SAT",
        }
    )
    # K4 + vertex with k=3 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_08",
            "family": "coloring",
            "n": 5,
            "k": 3,
            "edges": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3], [3, 4]],
            "expected_kind": "UNSAT",
        }
    )

    # Family 2: PHP (8 cases: 4 SAT, 4 UNSAT)
    # PHP(2, 2) (SAT)
    cases.append(
        {
            "case_id": "c042_base_09",
            "family": "php",
            "pigeons": 2,
            "holes": 2,
            "expected_kind": "SAT",
        }
    )
    # PHP(3, 2) (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_10",
            "family": "php",
            "pigeons": 3,
            "holes": 2,
            "expected_kind": "UNSAT",
        }
    )
    # PHP(3, 3) (SAT)
    cases.append(
        {
            "case_id": "c042_base_11",
            "family": "php",
            "pigeons": 3,
            "holes": 3,
            "expected_kind": "SAT",
        }
    )
    # PHP(4, 3) (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_12",
            "family": "php",
            "pigeons": 4,
            "holes": 3,
            "expected_kind": "UNSAT",
        }
    )
    # PHP(2, 3) with blocked holes (SAT)
    cases.append(
        {
            "case_id": "c042_base_13",
            "family": "php",
            "pigeons": 2,
            "holes": 3,
            "blocked": [[0, 0]],
            "expected_kind": "SAT",
        }
    )
    # PHP(3, 3) with heavily blocked holes (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_14",
            "family": "php",
            "pigeons": 3,
            "holes": 3,
            "blocked": [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]],
            "expected_kind": "UNSAT",
        }
    )
    # PHP(4, 4) (SAT)
    cases.append(
        {
            "case_id": "c042_base_15",
            "family": "php",
            "pigeons": 4,
            "holes": 4,
            "expected_kind": "SAT",
        }
    )
    # PHP(5, 4) (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_16",
            "family": "php",
            "pigeons": 5,
            "holes": 4,
            "expected_kind": "UNSAT",
        }
    )

    # Family 3: Latin Square (8 cases: 4 SAT, 4 UNSAT)
    # Order 2 with (0,0)=0 (SAT)
    cases.append(
        {
            "case_id": "c042_base_17",
            "family": "latin_square",
            "order": 2,
            "prefilled": [[0, 0, 0]],
            "expected_kind": "SAT",
        }
    )
    # Order 2 with contradiction in row (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_18",
            "family": "latin_square",
            "order": 2,
            "prefilled": [[0, 0, 0], [0, 1, 0]],
            "expected_kind": "UNSAT",
        }
    )
    # Order 3 with partial (SAT)
    cases.append(
        {
            "case_id": "c042_base_19",
            "family": "latin_square",
            "order": 3,
            "prefilled": [[0, 0, 0], [1, 1, 1]],
            "expected_kind": "SAT",
        }
    )
    # Order 3 with contradiction in col (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_20",
            "family": "latin_square",
            "order": 3,
            "prefilled": [[0, 0, 1], [1, 0, 1]],
            "expected_kind": "UNSAT",
        }
    )
    # Order 3 diagonal (SAT)
    cases.append(
        {
            "case_id": "c042_base_21",
            "family": "latin_square",
            "order": 3,
            "prefilled": [[0, 0, 0], [1, 1, 1], [2, 2, 2]],
            "expected_kind": "SAT",
        }
    )
    # Order 3 contradictory constraints (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_22",
            "family": "latin_square",
            "order": 3,
            "prefilled": [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]],
            "expected_kind": "UNSAT",
        }
    )
    # Order 4 partial (SAT)
    cases.append(
        {
            "case_id": "c042_base_23",
            "family": "latin_square",
            "order": 4,
            "prefilled": [[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]],
            "expected_kind": "SAT",
        }
    )
    # Order 4 row clash (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_24",
            "family": "latin_square",
            "order": 4,
            "prefilled": [[0, 0, 2], [0, 3, 2]],
            "expected_kind": "UNSAT",
        }
    )

    # Family 4: Tseitin (8 cases: 4 SAT, 4 UNSAT)
    # Triangle even total charge = 0 (SAT)
    cases.append(
        {
            "case_id": "c042_base_25",
            "family": "tseitin",
            "vertices": 3,
            "edges": [[0, 1], [1, 2], [2, 0]],
            "charges": [0, 0, 0],
            "expected_kind": "SAT",
        }
    )
    # Triangle odd total charge = 1 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_26",
            "family": "tseitin",
            "vertices": 3,
            "edges": [[0, 1], [1, 2], [2, 0]],
            "charges": [1, 0, 0],
            "expected_kind": "UNSAT",
        }
    )
    # Square C4 even charge = 2 (SAT)
    cases.append(
        {
            "case_id": "c042_base_27",
            "family": "tseitin",
            "vertices": 4,
            "edges": [[0, 1], [1, 2], [2, 3], [3, 0]],
            "charges": [1, 1, 0, 0],
            "expected_kind": "SAT",
        }
    )
    # Square C4 odd charge = 1 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_28",
            "family": "tseitin",
            "vertices": 4,
            "edges": [[0, 1], [1, 2], [2, 3], [3, 0]],
            "charges": [1, 0, 0, 0],
            "expected_kind": "UNSAT",
        }
    )
    # K4 even charge = 0 (SAT)
    cases.append(
        {
            "case_id": "c042_base_29",
            "family": "tseitin",
            "vertices": 4,
            "edges": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]],
            "charges": [0, 0, 0, 0],
            "expected_kind": "SAT",
        }
    )
    # K4 odd charge = 3 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_30",
            "family": "tseitin",
            "vertices": 4,
            "edges": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]],
            "charges": [1, 1, 1, 0],
            "expected_kind": "UNSAT",
        }
    )
    # 5-cycle even charge (SAT)
    cases.append(
        {
            "case_id": "c042_base_31",
            "family": "tseitin",
            "vertices": 5,
            "edges": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
            "charges": [1, 0, 1, 0, 0],
            "expected_kind": "SAT",
        }
    )
    # 5-cycle odd charge (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_32",
            "family": "tseitin",
            "vertices": 5,
            "edges": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
            "charges": [1, 1, 1, 0, 0],
            "expected_kind": "UNSAT",
        }
    )

    # Family 5: Tiling (8 cases: 4 SAT, 4 UNSAT)
    # 2x2 board, 2 dominoes (SAT)
    cases.append(
        {
            "case_id": "c042_base_33",
            "family": "tiling",
            "rows": 2,
            "cols": 2,
            "tiles": [[[0, 0], [0, 1]], [[1, 0], [1, 1]], [[0, 0], [1, 0]], [[0, 1], [1, 1]]],
            "expected_kind": "SAT",
        }
    )
    # 2x2 board with 1 blocked square -> odd 3 squares with dominoes (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_34",
            "family": "tiling",
            "rows": 2,
            "cols": 2,
            "tiles": [[[0, 0], [0, 1]], [[1, 0], [1, 1]]],
            "blocked": [[0, 0]],
            "expected_kind": "UNSAT",
        }
    )
    # 2x3 board with 3 horizontal dominoes (SAT)
    cases.append(
        {
            "case_id": "c042_base_35",
            "family": "tiling",
            "rows": 2,
            "cols": 3,
            "tiles": [[[0, 0], [0, 1]], [[0, 2], [1, 2]], [[1, 0], [1, 1]]],
            "expected_kind": "SAT",
        }
    )
    # 2x3 board with no valid partition (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_36",
            "family": "tiling",
            "rows": 2,
            "cols": 3,
            "tiles": [[[0, 0], [0, 1]], [[1, 0], [1, 1]]],
            "expected_kind": "UNSAT",
        }
    )
    # 3x3 board with center blocked (8 squares) by 4 dominoes (SAT)
    cases.append(
        {
            "case_id": "c042_base_37",
            "family": "tiling",
            "rows": 3,
            "cols": 3,
            "blocked": [[1, 1]],
            "tiles": [[[0, 0], [0, 1]], [[0, 2], [1, 2]], [[2, 2], [2, 1]], [[2, 0], [1, 0]]],
            "expected_kind": "SAT",
        }
    )
    # 3x3 board without center blocked (9 squares) with dominoes of size 2 (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_38",
            "family": "tiling",
            "rows": 3,
            "cols": 3,
            "tiles": [
                [[0, 0], [0, 1]],
                [[0, 1], [0, 2]],
                [[1, 0], [1, 1]],
                [[1, 1], [1, 2]],
                [[2, 0], [2, 1]],
                [[2, 1], [2, 2]],
            ],
            "expected_kind": "UNSAT",
        }
    )
    # 4x2 board (SAT)
    cases.append(
        {
            "case_id": "c042_base_39",
            "family": "tiling",
            "rows": 4,
            "cols": 2,
            "tiles": [[[0, 0], [0, 1]], [[1, 0], [1, 1]], [[2, 0], [2, 1]], [[3, 0], [3, 1]]],
            "expected_kind": "SAT",
        }
    )
    # 4x2 board with isolated cell uncovered (UNSAT)
    cases.append(
        {
            "case_id": "c042_base_40",
            "family": "tiling",
            "rows": 4,
            "cols": 2,
            "tiles": [[[0, 0], [0, 1]], [[1, 0], [1, 1]]],
            "expected_kind": "UNSAT",
        }
    )

    return cases


def build_gauge_cases(base_cases: list[dict]) -> list[dict]:
    gauge = []
    # 16 gauge controls: permuting vertices/edges/symbols
    for i in range(16):
        src = base_cases[i % len(base_cases)]
        gc = json.loads(json.dumps(src))
        gc["case_id"] = f"c042_gauge_{i + 1:02d}"
        gc["gauge_of"] = src["case_id"]
        # Shuffled or permuted order
        if "edges" in gc:
            gc["edges"] = list(reversed(gc["edges"]))
        if "prefilled" in gc:
            gc["prefilled"] = list(reversed(gc["prefilled"]))
        if "tiles" in gc:
            gc["tiles"] = list(reversed(gc["tiles"]))
        gauge.append(gc)
    return gauge


def build_poison_cases() -> list[dict]:
    poison = []
    # Poison 1: Out of range vertex in coloring
    poison.append(
        {
            "case_id": "c042_poison_01",
            "family": "coloring",
            "n": 3,
            "k": 2,
            "edges": [[0, 5]],
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # Poison 2: Negative dimensions in PHP
    poison.append(
        {
            "case_id": "c042_poison_02",
            "family": "php",
            "pigeons": -1,
            "holes": 2,
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # Poison 3: Non-existent family. No canonical CNF exists, so a warranted OUT_OF_SCOPE is the
    # consistent answer; UNKNOWN never counts as consistent.
    poison.append(
        {
            "case_id": "c042_poison_03",
            "family": "quantum_field_colouring",
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # Poison 4: DIMACS clause count mismatch
    poison.append(
        {
            "case_id": "c042_poison_04",
            "family": "coloring",
            "cnf_text": "p cnf 2 5\n1 2 0\n",
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # Poison 5: Deceptive note
    poison.append(
        {
            "case_id": "c042_poison_05",
            "family": "coloring",
            "n": 3,
            "k": 2,
            "edges": [[0, 1], [1, 2], [0, 2]],
            "note": "Claiming SAT even though K3 is UNSAT for k=2",
            "expected_kind": "UNSAT",
        }
    )
    # Poison 6: Out of range edge in Tseitin
    poison.append(
        {
            "case_id": "c042_poison_06",
            "family": "tseitin",
            "vertices": 3,
            "edges": [[0, 10]],
            "charges": [0, 0, 0],
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # Poison 7: Tiling with non-list tile
    poison.append(
        {
            "case_id": "c042_poison_07",
            "family": "tiling",
            "rows": 2,
            "cols": 2,
            "tiles": ["not_a_tile"],
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # Poison 8: Blocked hole index negative
    poison.append(
        {
            "case_id": "c042_poison_08",
            "family": "php",
            "pigeons": 0,
            "holes": 0,
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    return poison


def generate_all():
    base = build_base_cases()
    gauge = build_gauge_cases(base)
    poison = build_poison_cases()
    all_64 = base + gauge + poison

    # Write judge cases
    for c in all_64:
        cpath = JUDGE_CASES_DIR / f"{c['case_id']}.json"
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2)

    # Public examples: 10 cases (1 SAT and 1 UNSAT for each of the 5 families)
    pub_indices = [
        0,
        1,  # Coloring SAT, UNSAT
        8,
        9,  # PHP SAT, UNSAT
        16,
        17,  # Latin square SAT, UNSAT
        24,
        25,  # Tseitin SAT, UNSAT
        32,
        33,  # Tiling SAT, UNSAT
    ]
    pub_answers = []
    for idx, bi in enumerate(pub_indices, 1):
        case_data = json.loads(json.dumps(base[bi]))
        case_data["case_id"] = f"c042_pub_{idx:02d}"
        ex_path = EXAMPLES_DIR / f"{case_data['case_id']}.json"
        with open(ex_path, "w", encoding="utf-8") as f:
            json.dump(case_data, f, indent=2)

        ans = solve(case_data)
        pub_answers.append(ans)

    # Write answers.jsonl
    ans_file = PKG_ROOT / "participant_packet" / "answers.jsonl"
    with open(ans_file, "w", encoding="utf-8") as f:
        for a in pub_answers:
            f.write(json.dumps(a) + "\n")

    # Generate 48 mutation cases
    for m_idx in range(1, 49):
        # Pick a base case
        target = base[(m_idx - 1) % len(base)]
        mut_case = json.loads(json.dumps(target))
        mut_case["case_id"] = f"c042_mut_{m_idx:02d}"

        # Corrupted answer
        ans = solve(target)
        ans["case_id"] = mut_case["case_id"]

        if ans["status"] == "SOLVED":
            if ans["kind"] == "SAT":
                sol = ans["solution"]
                if "colour" in sol:
                    # Mut 1: Violate edge coloring
                    sol["colour"] = [0] * len(sol["colour"])
                elif "assignment" in sol:
                    # Mut 2: Two pigeons same hole
                    sol["assignment"] = [0] * len(sol["assignment"])
                elif "grid" in sol:
                    # Mut 3: Duplicate in row
                    sol["grid"][0][1] = sol["grid"][0][0]
                elif "edge_values" in sol:
                    # Mut 4: Invert an edge
                    sol["edge_values"][0] = 1 - sol["edge_values"][0]
                elif "selected_tiles" in sol:
                    # Mut 5: Empty tile selection
                    sol["selected_tiles"] = []
                # Mut 6: Type corruption - use boolean instead of int
                if m_idx % 2 == 0:
                    sol["bogus_flag"] = True
            elif ans["kind"] == "UNSAT":
                # Mutate DRAT proof
                if m_idx % 4 == 0:
                    # Remove empty clause
                    ans["proof_text"] = ans["proof_text"].replace("0", "1 2 0")
                elif m_idx % 4 == 1:
                    # Invert hash
                    ans["cnf_sha256"] = "0" * 64
                elif m_idx % 4 == 2:
                    # Empty proof
                    ans["proof_text"] = ""
                else:
                    # Add bogus invalid lemma
                    ans["proof_text"] = "999 0\n" + ans["proof_text"]

        mut_payload = {
            "mutation_id": f"mut_{m_idx:02d}",
            "case": mut_case,
            "corrupted_answer": ans,
            "expected_rejection": True,
        }
        with open(MUTATION_DIR / f"mut_{m_idx:02d}.json", "w", encoding="utf-8") as f:
            json.dump(mut_payload, f, indent=2)

    print("Generated 64 judge cases, 10 public examples, and 48 mutations.")


if __name__ == "__main__":
    generate_all()
