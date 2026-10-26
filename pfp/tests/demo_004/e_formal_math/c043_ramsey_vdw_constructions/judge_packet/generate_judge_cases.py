"""
Judge Case & Mutation Generator for Challenge C043.
Generates:
- 64 hidden cases (40 base, 16 gauge/relabel, 8 poisoned)
- 48 hostile mutations for Lev Landau falsification testing
"""

import json
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = PKG_ROOT / "judge_packet" / "cases"
MUT_DIR = PKG_ROOT / "judge_packet" / "mutation_suite"

CASES_DIR.mkdir(parents=True, exist_ok=True)
MUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_all():
    # --- 1. BASE CASES (40) ---
    base_cases = []

    # Ramsey2 cases (16)
    # R(3,3)
    base_cases.append(
        {"case_id": "c043_base_01", "type": "ramsey2", "s": 3, "t": 3, "n": 3, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_02", "type": "ramsey2", "s": 3, "t": 3, "n": 4, "fixed": [[0, 1, 0]]}
    )
    base_cases.append(
        {"case_id": "c043_base_03", "type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_04", "type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": [[0, 1, 1]]}
    )
    base_cases.append(
        {
            "case_id": "c043_base_05",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[0, 1, 0], [2, 3, 1]],
        }
    )

    # R(3,4) (bound is 9)
    base_cases.append(
        {"case_id": "c043_base_06", "type": "ramsey2", "s": 3, "t": 4, "n": 6, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_07", "type": "ramsey2", "s": 3, "t": 4, "n": 7, "fixed": [[0, 1, 0]]}
    )
    base_cases.append(
        {"case_id": "c043_base_08", "type": "ramsey2", "s": 3, "t": 4, "n": 8, "fixed": []}
    )

    # R(4,4) (bound is 18)
    base_cases.append(
        {"case_id": "c043_base_09", "type": "ramsey2", "s": 4, "t": 4, "n": 8, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_10", "type": "ramsey2", "s": 4, "t": 4, "n": 10, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_11", "type": "ramsey2", "s": 4, "t": 4, "n": 12, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_12", "type": "ramsey2", "s": 4, "t": 4, "n": 14, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_13", "type": "ramsey2", "s": 4, "t": 4, "n": 16, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_14", "type": "ramsey2", "s": 4, "t": 4, "n": 17, "fixed": []}
    )
    base_cases.append(
        {
            "case_id": "c043_base_15",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 17,
            "fixed": [[0, 1, 1]],
        }
    )
    base_cases.append(
        {
            "case_id": "c043_base_16",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 17,
            "fixed": [[0, 1, 1], [0, 2, 1]],
        }
    )

    # Ramsey3 cases (8)
    base_cases.append({"case_id": "c043_base_17", "type": "ramsey3", "n": 4, "fixed": []})
    base_cases.append({"case_id": "c043_base_18", "type": "ramsey3", "n": 6, "fixed": []})
    base_cases.append({"case_id": "c043_base_19", "type": "ramsey3", "n": 8, "fixed": []})
    base_cases.append({"case_id": "c043_base_20", "type": "ramsey3", "n": 10, "fixed": []})
    base_cases.append({"case_id": "c043_base_21", "type": "ramsey3", "n": 12, "fixed": []})
    base_cases.append({"case_id": "c043_base_22", "type": "ramsey3", "n": 14, "fixed": []})
    base_cases.append({"case_id": "c043_base_23", "type": "ramsey3", "n": 16, "fixed": []})
    base_cases.append({"case_id": "c043_base_24", "type": "ramsey3", "n": 16, "fixed": [[0, 1, 0]]})

    # Van der Waerden cases (16)
    # W(2,3)=9
    base_cases.append(
        {"case_id": "c043_base_25", "type": "vdw", "r": 2, "k": 3, "n": 5, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_26", "type": "vdw", "r": 2, "k": 3, "n": 6, "fixed": [[0, 0]]}
    )
    base_cases.append(
        {"case_id": "c043_base_27", "type": "vdw", "r": 2, "k": 3, "n": 7, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_28", "type": "vdw", "r": 2, "k": 3, "n": 8, "fixed": []}
    )
    base_cases.append(
        {
            "case_id": "c043_base_29",
            "type": "vdw",
            "r": 2,
            "k": 3,
            "n": 8,
            "fixed": [[0, 0], [7, 1]],
        }
    )

    # W(2,4)=35
    base_cases.append(
        {"case_id": "c043_base_30", "type": "vdw", "r": 2, "k": 4, "n": 10, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_31", "type": "vdw", "r": 2, "k": 4, "n": 15, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_32", "type": "vdw", "r": 2, "k": 4, "n": 20, "fixed": [[0, 0]]}
    )
    base_cases.append(
        {"case_id": "c043_base_33", "type": "vdw", "r": 2, "k": 4, "n": 25, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_34", "type": "vdw", "r": 2, "k": 4, "n": 30, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_35", "type": "vdw", "r": 2, "k": 4, "n": 34, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_36", "type": "vdw", "r": 2, "k": 4, "n": 34, "fixed": [[0, 0]]}
    )

    # W(2,5)=178
    base_cases.append(
        {"case_id": "c043_base_37", "type": "vdw", "r": 2, "k": 5, "n": 40, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_38", "type": "vdw", "r": 2, "k": 5, "n": 50, "fixed": []}
    )

    # W(3,3)=27
    base_cases.append(
        {"case_id": "c043_base_39", "type": "vdw", "r": 3, "k": 3, "n": 10, "fixed": []}
    )
    base_cases.append(
        {"case_id": "c043_base_40", "type": "vdw", "r": 3, "k": 3, "n": 15, "fixed": []}
    )

    for c in base_cases:
        with open(CASES_DIR / f"{c['case_id']}.json", "w") as f:
            json.dump(c, f, indent=2)

    # --- 2. GAUGE & RELABEL INVARIANCE CASES (16) ---
    gauge_cases = []
    # Permuting vertices in Ramsey2
    gauge_cases.append(
        {
            "case_id": "c043_gauge_01",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[1, 2, 0]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_02",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[2, 3, 0]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_03",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[3, 4, 0]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_04",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[4, 0, 0]],
        }
    )
    # Colour swaps where s = t
    gauge_cases.append(
        {
            "case_id": "c043_gauge_05",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[0, 1, 1]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_06",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 17,
            "fixed": [[0, 1, 0]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_07",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 17,
            "fixed": [[1, 2, 1]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_08",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 17,
            "fixed": [[2, 3, 0]],
        }
    )
    # vdW reflections: i -> n - 1 - i
    gauge_cases.append(
        {"case_id": "c043_gauge_09", "type": "vdw", "r": 2, "k": 3, "n": 8, "fixed": [[7, 0]]}
    )
    gauge_cases.append(
        {"case_id": "c043_gauge_10", "type": "vdw", "r": 2, "k": 3, "n": 8, "fixed": [[6, 0]]}
    )
    gauge_cases.append(
        {"case_id": "c043_gauge_11", "type": "vdw", "r": 2, "k": 4, "n": 34, "fixed": [[33, 0]]}
    )
    gauge_cases.append(
        {"case_id": "c043_gauge_12", "type": "vdw", "r": 2, "k": 4, "n": 34, "fixed": [[33, 1]]}
    )
    # Reordered fixed edge lists
    gauge_cases.append(
        {
            "case_id": "c043_gauge_13",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 10,
            "fixed": [[0, 1, 1], [2, 3, 0]],
        }
    )
    gauge_cases.append(
        {
            "case_id": "c043_gauge_14",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 10,
            "fixed": [[2, 3, 0], [0, 1, 1]],
        }
    )
    gauge_cases.append(
        {"case_id": "c043_gauge_15", "type": "ramsey3", "n": 16, "fixed": [[0, 2, 1]]}
    )
    gauge_cases.append(
        {"case_id": "c043_gauge_16", "type": "ramsey3", "n": 16, "fixed": [[1, 3, 2]]}
    )

    for c in gauge_cases:
        with open(CASES_DIR / f"{c['case_id']}.json", "w") as f:
            json.dump(c, f, indent=2)

    # --- 3. POISONED / INFEASIBLE CASES (8) ---
    poison_cases = []
    # Exceeding Ramsey bound
    poison_cases.append(
        {
            "case_id": "c043_poison_01",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 6,
            "fixed": [],
            "note": "R(3,3)=6 is known to be impossible",
        }
    )
    poison_cases.append(
        {
            "case_id": "c043_poison_02",
            "type": "ramsey2",
            "s": 4,
            "t": 4,
            "n": 18,
            "fixed": [],
            "note": "R(4,4)=18 is impossible",
        }
    )
    poison_cases.append(
        {
            "case_id": "c043_poison_03",
            "type": "ramsey3",
            "n": 17,
            "fixed": [],
            "note": "R(3,3,3)=17 is impossible",
        }
    )
    # Exceeding vdW bound
    poison_cases.append(
        {
            "case_id": "c043_poison_04",
            "type": "vdw",
            "r": 2,
            "k": 3,
            "n": 9,
            "fixed": [],
            "note": "W(2,3)=9 is impossible",
        }
    )
    poison_cases.append(
        {
            "case_id": "c043_poison_05",
            "type": "vdw",
            "r": 2,
            "k": 4,
            "n": 35,
            "fixed": [],
            "note": "W(2,4)=35 is impossible",
        }
    )
    # Fixed constraints directly containing monochromatic structure
    poison_cases.append(
        {
            "case_id": "c043_poison_06",
            "type": "ramsey2",
            "s": 3,
            "t": 3,
            "n": 5,
            "fixed": [[0, 1, 0], [1, 2, 0], [0, 2, 0]],
        }
    )
    poison_cases.append(
        {
            "case_id": "c043_poison_07",
            "type": "vdw",
            "r": 2,
            "k": 3,
            "n": 8,
            "fixed": [[0, 0], [1, 0], [2, 0]],
        }
    )
    poison_cases.append(
        {
            "case_id": "c043_poison_08",
            "type": "ramsey3",
            "n": 5,
            "fixed": [[0, 1, 2], [1, 2, 2], [0, 2, 2]],
        }
    )

    for c in poison_cases:
        with open(CASES_DIR / f"{c['case_id']}.json", "w") as f:
            json.dump(c, f, indent=2)

    print(
        f"Generated 64 judge cases ({len(base_cases)} base, {len(gauge_cases)} gauge, {len(poison_cases)} poison)"
    )

    # --- 4. MUTATION SUITE (48) ---
    # Generate corrupted outputs that checkers must reject
    mutations = []
    # M01-M10: Truncated strings / wrong length
    for i in range(1, 11):
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": []},
                "answer": {
                    "case_id": "test",
                    "status": "SOLVED",
                    "kind": "COLOURING",
                    "colours": "0" * (10 - (i % 3 + 1)),
                },
                "expected_rejection": "Wrong length",
            }
        )
    # M11-M20: Non-binary / invalid alphabet characters
    for i in range(11, 21):
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": []},
                "answer": {
                    "case_id": "test",
                    "status": "SOLVED",
                    "kind": "COLOURING",
                    "colours": "011001101" + str(i % 5 + 2),
                },
                "expected_rejection": "Invalid alphabet",
            }
        )
    # M21-M28: Flipped edge creating monochromatic clique in Ramsey2
    for i in range(21, 29):
        # All 0s has monochromatic K3
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": []},
                "answer": {
                    "case_id": "test",
                    "status": "SOLVED",
                    "kind": "COLOURING",
                    "colours": "0" * 10,
                },
                "expected_rejection": "Monochromatic clique in colour 0",
            }
        )
    # M29-M36: Flipped element creating monochromatic AP in vdW
    for i in range(29, 37):
        # All 0s has monochromatic AP
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "vdw", "r": 2, "k": 3, "n": 8, "fixed": []},
                "answer": {
                    "case_id": "test",
                    "status": "SOLVED",
                    "kind": "COLOURING",
                    "colours": "0" * 8,
                },
                "expected_rejection": "Monochromatic AP",
            }
        )
    # M37-M42: Fixed edge/element violation
    for i in range(37, 43):
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "vdw", "r": 2, "k": 3, "n": 8, "fixed": [[0, 0]]},
                "answer": {
                    "case_id": "test",
                    "status": "SOLVED",
                    "kind": "COLOURING",
                    "colours": "1" + "0110011"[:7],
                },
                "expected_rejection": "Fixed element violation at 0",
            }
        )
    # M43-M46: Fake OUT_OF_SCOPE witness without genuine monochromatic structure
    for i in range(43, 47):
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": [[0, 1, 0]]},
                "answer": {
                    "case_id": "test",
                    "status": "OUT_OF_SCOPE",
                    "witness": {"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": [0, 1, 2]},
                },
                "expected_rejection": "Fixed edges do not contain clique [0, 1, 2]",
            }
        )
    # M47-M48: Fake DRAT proof
    for i in range(47, 49):
        mutations.append(
            {
                "mut_id": f"c043_mut_{i:02d}",
                "case": {"type": "ramsey2", "s": 3, "t": 3, "n": 6, "fixed": []},
                "answer": {
                    "case_id": "test",
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "reason": "PROVABLY_INFEASIBLE_SAT",
                        "proof_type": "DRAT",
                        "drat_proof": ["1 2 0", "d 1 0"],
                    },
                },
                "expected_rejection": "DRAT proof does not derive empty clause",
            }
        )

    for m in mutations:
        with open(MUT_DIR / f"{m['mut_id']}.json", "w") as f:
            json.dump(m, f, indent=2)

    print(f"Generated {len(mutations)} hostile mutations in {MUT_DIR}")


if __name__ == "__main__":
    generate_all()
