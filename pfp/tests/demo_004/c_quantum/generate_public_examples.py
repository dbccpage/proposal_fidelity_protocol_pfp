"""Generator for the 12 C021 Public Examples.

Generates the full 12-case public test set under examples/ per C021 Specification §5:
- 5 SOLVED (including one Y-heavy phase case and one opposing-sign case)
- 3 OUT_OF_SCOPE (anticommuting terms with witnesses)
- 2 UNKNOWN (one duplicate term id, one out of bounds)
- 2 relabel pairs (qubit permutation and local Clifford basis change)

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

if __package__ in (None, ""):
    __package__ = "pfp.tests.demo_004.c_quantum"

from pfp.domain.quantum.certificate_checker import check_certificate
from pfp.infrastructure.adapters.stabilizer_rust_adapter import (
    StabilizerRustAdapter,
)

from .solve import solve

_STABILIZER = StabilizerRustAdapter()

EXAMPLES_DIR = Path(__file__).parent / "examples"
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_all_public_examples() -> list[dict]:
    cases = []

    # 1. Simple 2-qubit commuting
    cases.append(
        {
            "id": "c021_ex01_commuting_2q",
            "title": "2-Qubit Simple Commuting Stabilizer",
            "n": 2,
            "terms": [
                {"id": "term_z0", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "term_z1", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 2. 3-Qubit spec example (h_07 from C021 §4)
    cases.append(
        {
            "id": "c021_ex02_three_qubit",
            "title": "3-Qubit Specification Example from Section 4",
            "n": 3,
            "terms": [
                {"id": "t_a", "P": "XYZ", "w": [3, 2], "target": 1},
                {"id": "t_b", "P": "ZZI", "w": [1, 1], "target": -1},
            ],
        }
    )

    # 3. Y-heavy phase case (tests Y = iXZ phase tracking)
    cases.append(
        {
            "id": "c021_ex03_y_heavy_phase",
            "title": "2-Qubit Y-Heavy Commuting Stabilizer with Explicit Phase Tracking",
            "n": 2,
            "terms": [
                {"id": "t_yx", "P": "YX", "w": [1, 1], "target": 1},
                {"id": "t_xy", "P": "XY", "w": [1, 1], "target": 1},
                {"id": "t_zz", "P": "ZZ", "w": [2, 1], "target": 1},
            ],
        }
    )

    # 4. Opposing-sign / frustrated case (same Pauli with conflicting targets)
    cases.append(
        {
            "id": "c021_ex04_opposing_signs",
            "title": "2-Qubit Irreducible Frustration (Opposing Target Signs on Same Word)",
            "n": 2,
            "terms": [
                {"id": "t_zz_pos", "P": "ZZ", "w": [1, 1], "target": 1},
                {"id": "t_zz_neg", "P": "ZZ", "w": [1, 1], "target": -1},
            ],
        }
    )

    # 5. Identity terms and unused qubits
    cases.append(
        {
            "id": "c021_ex05_identity_terms",
            "title": "2-Qubit Identity Terms and Unused Qubits",
            "n": 2,
            "terms": [
                {"id": "t_id_pos", "P": "II", "w": [2, 1], "target": 1},
                {"id": "t_id_neg", "P": "II", "w": [1, 1], "target": -1},
                {"id": "t_z0", "P": "ZI", "w": [3, 1], "target": 1},
            ],
        }
    )

    # 6. Out of scope: 1-qubit anticommuting X and Z
    cases.append(
        {
            "id": "c021_ex06_anticommuting_xz",
            "title": "1-Qubit Anticommuting X and Z Terms",
            "n": 1,
            "terms": [
                {"id": "t_x", "P": "X", "w": [1, 1], "target": 1},
                {"id": "t_z", "P": "Z", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 7. Out of scope: 2-qubit anticommuting XI and YI
    cases.append(
        {
            "id": "c021_ex07_anticommuting_xy",
            "title": "2-Qubit Anticommuting XI and YI",
            "n": 2,
            "terms": [
                {"id": "t_xi", "P": "XI", "w": [2, 1], "target": 1},
                {"id": "t_yi", "P": "YI", "w": [1, 1], "target": 1},
                {"id": "t_iz", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 8. Out of scope: 3-qubit with multiple terms, one anticommuting pair
    cases.append(
        {
            "id": "c021_ex08_anticommuting_multi",
            "title": "3-Qubit Multiple Terms with Hidden Anticommuting Pair",
            "n": 3,
            "terms": [
                {"id": "t_1", "P": "ZZI", "w": [1, 1], "target": 1},
                {"id": "t_2", "P": "IZZ", "w": [1, 1], "target": 1},
                {"id": "t_3", "P": "XXI", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 9. Unknown: Duplicate term id
    cases.append(
        {
            "id": "c021_ex09_duplicate_term_id",
            "title": "Malformed Case: Duplicate Term ID",
            "n": 2,
            "terms": [
                {"id": "t_dup", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "t_dup", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 10. Unknown: Qubits out of bounds (n = 9 > 8)
    cases.append(
        {
            "id": "c021_ex10_qubits_out_of_bounds",
            "title": "Malformed Case: n = 9 Exceeds Bound (n <= 8)",
            "n": 9,
            "terms": [
                {"id": "t_0", "P": "IIIIIIIII", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 11. Relabel pair: Qubit permutation
    cases.append(
        {
            "id": "c021_ex11_relabel_orig",
            "title": "Relabel Pair 1: Original 3-Qubit Case",
            "n": 3,
            "terms": [
                {"id": "t_a", "P": "XIZ", "w": [1, 1], "target": 1},
                {"id": "t_b", "P": "ZIX", "w": [2, 1], "target": -1},
            ],
        }
    )
    cases.append(
        {
            "id": "c021_ex11_relabel_perm",
            "title": "Relabel Pair 1: Permuted Qubits (0 <-> 2) and Renamed Terms",
            "n": 3,
            "terms": [
                {"id": "term_alpha", "P": "ZIX", "w": [1, 1], "target": 1},
                {"id": "term_beta", "P": "XIZ", "w": [2, 1], "target": -1},
            ],
        }
    )

    # 12. Relabel pair: Local Clifford change of basis (Hadamard on qubit 0: X <-> Z)
    cases.append(
        {
            "id": "c021_ex12_relabel_orig",
            "title": "Relabel Pair 2: Original 2-Qubit Case",
            "n": 2,
            "terms": [
                {"id": "t_x0", "P": "XI", "w": [3, 2], "target": 1},
                {"id": "t_z1", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
    )
    cases.append(
        {
            "id": "c021_ex12_relabel_clifford",
            "title": "Relabel Pair 2: Local Hadamard Basis Change on Qubit 0 (X -> Z)",
            "n": 2,
            "terms": [
                {"id": "t_z0_h", "P": "ZI", "w": [3, 2], "target": 1},
                {"id": "t_z1_h", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    return cases


def main() -> None:
    cases = generate_all_public_examples()
    manifest = []
    print(f"Generating {len(cases)} public examples for C021 in {EXAMPLES_DIR}...")

    for case in cases:
        case_id = case["id"]
        # Solve with frozen solve
        expected_output = solve(case)

        # Check with primary certificate checker
        verdict = check_certificate(case, expected_output, port=_STABILIZER)
        if verdict.get("verdict") != "PASS":
            raise RuntimeError(f"Public example {case_id} failed verification: {verdict}")

        case_file = EXAMPLES_DIR / f"{case_id}.json"
        expected_file = EXAMPLES_DIR / f"{case_id}_expected.json"

        with open(case_file, "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, sort_keys=True)
            f.write("\n")

        with open(expected_file, "w", encoding="utf-8") as f:
            json.dump(expected_output, f, indent=2, sort_keys=True)
            f.write("\n")

        manifest.append(
            {
                "id": case_id,
                "status": expected_output["status"],
                "file": case_file.name,
                "expected_file": expected_file.name,
            }
        )
        print(f"  [PASS] {case_id}: status={expected_output['status']}")

    manifest_file = EXAMPLES_DIR / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Successfully generated {len(cases)} public examples with manifest at {manifest_file}.")


if __name__ == "__main__":
    main()
