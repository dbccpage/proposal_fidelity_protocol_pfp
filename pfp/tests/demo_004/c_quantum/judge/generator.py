"""Judge Packet Generator for C021 (Mode 2: Follow-On Benchmark).

Generates:
1. 32 hidden base cases (`judge/hidden_base_cases.json`): >= 20 SOLVED, >= 6 OUT_OF_SCOPE, >= 3 UNKNOWN.
2. 8 relabel controls (`judge/relabel_controls.json`): qubit perm, term reorder, id rename, weight scale, Clifford basis.
3. 6 poisoned-but-schema-valid cases (`judge/poisoned_cases.json`): hidden anticommuting, Y-phase trap, unreduced weight, signed product, non-positional sort, duplicate id.

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
    __package__ = "pfp.tests.demo_004.c_quantum.judge"


JUDGE_DIR = Path(__file__).parent


def generate_hidden_base_cases() -> list[dict]:
    cases = []

    # 1. 1-qubit pure identity
    cases.append(
        {
            "id": "h_01_id_1q",
            "n": 1,
            "terms": [{"id": "t_id", "P": "I", "w": [1, 1], "target": 1}],
        }
    )

    # 2. 1-qubit single Z
    cases.append(
        {
            "id": "h_02_z_1q",
            "n": 1,
            "terms": [{"id": "t_z", "P": "Z", "w": [2, 1], "target": 1}],
        }
    )

    # 3. 2-qubit Bell pair stabilizers (XX, ZZ)
    cases.append(
        {
            "id": "h_03_bell_pair",
            "n": 2,
            "terms": [
                {"id": "t_xx", "P": "XX", "w": [1, 1], "target": 1},
                {"id": "t_zz", "P": "ZZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 4. 2-qubit frustrated opposing signs on XX
    cases.append(
        {
            "id": "h_04_frustrated_xx",
            "n": 2,
            "terms": [
                {"id": "t_xx_1", "P": "XX", "w": [3, 2], "target": 1},
                {"id": "t_xx_2", "P": "XX", "w": [1, 2], "target": -1},
            ],
        }
    )

    # 5. 3-qubit GHZ state stabilizers (ZZI, IZZ, XXX)
    cases.append(
        {
            "id": "h_05_ghz_3q",
            "n": 3,
            "terms": [
                {"id": "t_zz1", "P": "ZZI", "w": [1, 1], "target": 1},
                {"id": "t_zz2", "P": "IZZ", "w": [1, 1], "target": 1},
                {"id": "t_xxx", "P": "XXX", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 6. 3-qubit with Y term (phase tracking)
    cases.append(
        {
            "id": "h_06_y_phase_3q",
            "n": 3,
            "terms": [
                {"id": "t_yzi", "P": "YZI", "w": [2, 1], "target": 1},
                {"id": "t_iyz", "P": "IYZ", "w": [2, 1], "target": 1},
                {"id": "t_xxi", "P": "XXI", "w": [1, 1], "target": -1},
            ],
        }
    )

    # 7. 4-qubit Toric code plaquette & star operators
    cases.append(
        {
            "id": "h_07_toric_4q",
            "n": 4,
            "terms": [
                {"id": "t_star", "P": "XXXX", "w": [1, 1], "target": 1},
                {"id": "t_plaq", "P": "ZZZZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 8. 4-qubit with unused qubits (k = 2, n = 4 -> degeneracy 4)
    cases.append(
        {
            "id": "h_08_unused_qubits_4q",
            "n": 4,
            "terms": [
                {"id": "t_z0", "P": "ZIII", "w": [1, 1], "target": 1},
                {"id": "t_z1", "P": "IZII", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 9. 5-qubit code stabilizer generators
    cases.append(
        {
            "id": "h_09_five_qubit_code",
            "n": 5,
            "terms": [
                {"id": "g_1", "P": "XZZXI", "w": [1, 1], "target": 1},
                {"id": "g_2", "P": "IXZZX", "w": [1, 1], "target": 1},
                {"id": "g_3", "P": "XIXZZ", "w": [1, 1], "target": 1},
                {"id": "g_4", "P": "ZXIXZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 10. 5-qubit with rational weights
    cases.append(
        {
            "id": "h_10_rat_weights_5q",
            "n": 5,
            "terms": [
                {"id": "t_a", "P": "ZZIII", "w": [5, 3], "target": 1},
                {"id": "t_b", "P": "IZZII", "w": [7, 4], "target": -1},
                {"id": "t_c", "P": "IIZZI", "w": [2, 5], "target": 1},
                {"id": "t_d", "P": "IIIZZ", "w": [1, 6], "target": -1},
            ],
        }
    )

    # 11. 6-qubit cluster state chain
    cases.append(
        {
            "id": "h_11_cluster_6q",
            "n": 6,
            "terms": [
                {"id": "k_1", "P": "XZIIII", "w": [1, 1], "target": 1},
                {"id": "k_2", "P": "ZXZIII", "w": [1, 1], "target": 1},
                {"id": "k_3", "P": "IZXZII", "w": [1, 1], "target": 1},
                {"id": "k_4", "P": "IIZXZI", "w": [1, 1], "target": 1},
                {"id": "k_5", "P": "IIIZXZ", "w": [1, 1], "target": 1},
                {"id": "k_6", "P": "IIIIZX", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 12. 6-qubit all commuting Z chain with fractional weights
    cases.append(
        {
            "id": "h_12_z_chain_6q",
            "n": 6,
            "terms": [
                {
                    "id": f"z_{i}",
                    "P": "I" * i + "Z" + "I" * (5 - i),
                    "w": [i + 1, 2],
                    "target": 1 if i % 2 == 0 else -1,
                }
                for i in range(6)
            ],
        }
    )

    # 13. 7-qubit Steane code generators
    cases.append(
        {
            "id": "h_13_steane_7q",
            "n": 7,
            "terms": [
                {"id": "s_x1", "P": "XXXXIII", "w": [1, 1], "target": 1},
                {"id": "s_x2", "P": "IIXXXXI", "w": [1, 1], "target": 1},
                {"id": "s_x3", "P": "IXXIIXX", "w": [1, 1], "target": 1},
                {"id": "s_z1", "P": "ZZZZIII", "w": [1, 1], "target": 1},
                {"id": "s_z2", "P": "IIZZZZI", "w": [1, 1], "target": 1},
                {"id": "s_z3", "P": "IZZIIZZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 14. 7-qubit with multiple Y stabilizers
    cases.append(
        {
            "id": "h_14_y_multi_7q",
            "n": 7,
            "terms": [
                {"id": "y_1", "P": "YYIIIII", "w": [2, 1], "target": 1},
                {"id": "y_2", "P": "IIYYIII", "w": [3, 2], "target": 1},
                {"id": "y_3", "P": "IIIIYYI", "w": [1, 3], "target": -1},
                {"id": "y_4", "P": "ZZZZZZI", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 15. 8-qubit full bound: n = 8, M = 24 terms!
    cases.append(
        {
            "id": "h_15_bound_8q_24terms",
            "n": 8,
            "terms": [
                # 8 single Z terms
                *[
                    {"id": f"t_z_{i}", "P": "I" * i + "Z" + "I" * (7 - i), "w": [1, 1], "target": 1}
                    for i in range(8)
                ],
                # 8 adjacent ZZ terms
                *[
                    {
                        "id": f"t_zz_{i}",
                        "P": "I" * i + "ZZ" + "I" * (6 - i),
                        "w": [1, 2],
                        "target": 1,
                    }
                    for i in range(7)
                ],
                {"id": "t_zz_ring", "P": "ZIIIIIIZ", "w": [1, 2], "target": 1},
                # 8 identity terms with varying weights
                *[
                    {"id": f"t_id_{i}", "P": "IIIIIIII", "w": [1, i + 1], "target": 1}
                    for i in range(8)
                ],
            ],
        }
    )

    # 16. 8-qubit with k = 8 full basis
    cases.append(
        {
            "id": "h_16_full_basis_8q",
            "n": 8,
            "terms": [
                {
                    "id": f"diag_{i}",
                    "P": "I" * i + "Z" + "I" * (7 - i),
                    "w": [i + 2, 3],
                    "target": -1 if i % 2 == 1 else 1,
                }
                for i in range(8)
            ],
        }
    )

    # 17. 2-qubit with identity and signs
    cases.append(
        {
            "id": "h_17_mixed_id_2q",
            "n": 2,
            "terms": [
                {"id": "id_term", "P": "II", "w": [5, 1], "target": -1},
                {"id": "z_term", "P": "ZZ", "w": [2, 1], "target": 1},
            ],
        }
    )

    # 18. 3-qubit independent X and Z generators
    cases.append(
        {
            "id": "h_18_indep_xz_3q",
            "n": 3,
            "terms": [
                {"id": "t_x0", "P": "XII", "w": [1, 1], "target": 1},
                {"id": "t_x1", "P": "IXI", "w": [1, 1], "target": 1},
                {"id": "t_z2", "P": "IIZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 19. 4-qubit complete ring of commuting Y words
    cases.append(
        {
            "id": "h_19_y_ring_4q",
            "n": 4,
            "terms": [
                {"id": "y_01", "P": "YYII", "w": [1, 1], "target": 1},
                {"id": "y_23", "P": "IIYY", "w": [1, 1], "target": 1},
                {"id": "y_02", "P": "YIYI", "w": [1, 1], "target": 1},
                {"id": "y_13", "P": "IYIY", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 20. 5-qubit all terms identity (k = 0, degeneracy = 2^5 = 32)
    cases.append(
        {
            "id": "h_20_all_identity_5q",
            "n": 5,
            "terms": [
                {"id": "id_1", "P": "IIIII", "w": [1, 1], "target": 1},
                {"id": "id_2", "P": "IIIII", "w": [2, 1], "target": 1},
            ],
        }
    )

    # 21. 6-qubit opposing signs with different weights
    cases.append(
        {
            "id": "h_21_opposing_weights_6q",
            "n": 6,
            "terms": [
                {"id": "t_pos", "P": "ZZZZZZ", "w": [7, 2], "target": 1},
                {"id": "t_neg", "P": "ZZZZZZ", "w": [3, 2], "target": -1},
            ],
        }
    )

    # 22. 7-qubit single term (degeneracy = 2^(7-1) = 64)
    cases.append(
        {
            "id": "h_22_single_term_7q",
            "n": 7,
            "terms": [
                {"id": "single_z", "P": "ZIIIIII", "w": [4, 1], "target": 1},
            ],
        }
    )

    # 23. Out of scope 1: 1-qubit anticommuting X and Y
    cases.append(
        {
            "id": "h_23_oos_xy_1q",
            "n": 1,
            "terms": [
                {"id": "term_x", "P": "X", "w": [1, 1], "target": 1},
                {"id": "term_y", "P": "Y", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 24. Out of scope 2: 2-qubit anticommuting (X on qubit 0, Z on qubit 0)
    cases.append(
        {
            "id": "h_24_oos_xz_2q",
            "n": 2,
            "terms": [
                {"id": "t_xi", "P": "XI", "w": [1, 1], "target": 1},
                {"id": "t_zi", "P": "ZI", "w": [1, 1], "target": 1},
            ],
        }
    )

    # 25. Out of scope 3: 3-qubit anticommuting pair at end
    cases.append(
        {
            "id": "h_25_oos_3q",
            "n": 3,
            "terms": [
                {"id": "t_1", "P": "ZZI", "w": [1, 1], "target": 1},
                {"id": "t_2", "P": "IZZ", "w": [1, 1], "target": 1},
                {
                    "id": "t_3",
                    "P": "XXI",
                    "w": [1, 1],
                    "target": 1,
                },  # XXI anticommutes with ZZI (X and Z on 0, X and Z on 1 -> wait, overlap 2 commutes! X and I on 2 -> overlap is 2, so commutes! Wait, XXI vs IZZ: qubit 1 has X and Z -> overlap 1, anticommutes!)
            ],
        }
    )

    # 26. Out of scope 4: 4-qubit anticommuting pair
    cases.append(
        {
            "id": "h_26_oos_4q",
            "n": 4,
            "terms": [
                {"id": "t_comm_1", "P": "ZZII", "w": [1, 1], "target": 1},
                {"id": "t_comm_2", "P": "IIZZ", "w": [1, 1], "target": 1},
                {"id": "t_anti_a", "P": "XIZI", "w": [1, 1], "target": 1},
                {
                    "id": "t_anti_b",
                    "P": "ZIZI",
                    "w": [1, 1],
                    "target": 1,
                },  # XIZI and ZIZI anticommute on qubit 0
            ],
        }
    )

    # 27. Out of scope 5: 5-qubit anticommuting pair
    cases.append(
        {
            "id": "h_27_oos_5q",
            "n": 5,
            "terms": [
                {"id": "p_1", "P": "XXXXI", "w": [1, 1], "target": 1},
                {"id": "p_2", "P": "ZZZZI", "w": [1, 1], "target": 1},
                {
                    "id": "p_3",
                    "P": "ZIIII",
                    "w": [1, 1],
                    "target": 1,
                },  # ZIIII and XXXXI anticommute on qubit 0
            ],
        }
    )

    # 28. Out of scope 6: 8-qubit anticommuting pair
    cases.append(
        {
            "id": "h_28_oos_8q",
            "n": 8,
            "terms": [
                {"id": "q_1", "P": "ZZZZZZZI", "w": [1, 1], "target": 1},
                {"id": "q_2", "P": "IIIIIIIZ", "w": [1, 1], "target": 1},
                {
                    "id": "q_3",
                    "P": "XXXXXXXX",
                    "w": [1, 1],
                    "target": 1,
                },  # XXXXXXXX and IIIIIIIZ anticommute on qubit 7
            ],
        }
    )

    # 29. Unknown 1: n = 9 > 8
    cases.append(
        {
            "id": "h_29_unk_qubits_bound",
            "n": 9,
            "terms": [{"id": "t_0", "P": "IIIIIIIII", "w": [1, 1], "target": 1}],
        }
    )

    # 30. Unknown 2: M = 25 > 24
    cases.append(
        {
            "id": "h_30_unk_terms_bound",
            "n": 2,
            "terms": [{"id": f"t_{i}", "P": "ZZ", "w": [1, 1], "target": 1} for i in range(25)],
        }
    )

    # 31. Unknown 3: Non-positive weight [0, 1]
    cases.append(
        {
            "id": "h_31_unk_zero_weight",
            "n": 2,
            "terms": [{"id": "t_bad_w", "P": "ZZ", "w": [0, 1], "target": 1}],
        }
    )

    # 32. Unknown 4: Invalid Pauli character 'Q'
    cases.append(
        {
            "id": "h_32_unk_invalid_pauli",
            "n": 2,
            "terms": [{"id": "t_bad_p", "P": "ZQ", "w": [1, 1], "target": 1}],
        }
    )

    return cases


def generate_relabel_controls() -> list[dict]:
    controls = []

    # Control 1: Qubit permutation on 3-qubit case (permute 0 <-> 2)
    controls.append(
        {
            "id": "ctrl_01_qubit_permutation",
            "title": "Control 1: Qubit Permutation (0 <-> 2)",
            "n": 3,
            "terms": [
                {"id": "c1_t1", "P": "ZYX", "w": [3, 2], "target": 1},
                {"id": "c1_t2", "P": "IZZ", "w": [1, 1], "target": -1},
            ],
        }
    )

    # Control 2: Term reordering
    controls.append(
        {
            "id": "ctrl_02_term_reordering",
            "title": "Control 2: Term Reordering",
            "n": 3,
            "terms": [
                {"id": "c2_tb", "P": "ZZI", "w": [1, 1], "target": -1},
                {"id": "c2_ta", "P": "XYZ", "w": [3, 2], "target": 1},
            ],
        }
    )

    # Control 3: Renaming of every term ID
    controls.append(
        {
            "id": "ctrl_03_term_renaming",
            "title": "Control 3: Renaming of Every Term ID",
            "n": 3,
            "terms": [
                {"id": "generator_alpha", "P": "XYZ", "w": [3, 2], "target": 1},
                {"id": "generator_core", "P": "ZZI", "w": [1, 1], "target": -1},
            ],
        }
    )

    # Control 4: Rescaling every weight by common factor (c = 3)
    controls.append(
        {
            "id": "ctrl_04_weight_rescaling",
            "title": "Control 4: Weight Rescaling (x3)",
            "n": 3,
            "terms": [
                {"id": "t_a", "P": "XYZ", "w": [9, 2], "target": 1},  # 3/2 * 3 = 9/2
                {"id": "t_b", "P": "ZZI", "w": [3, 1], "target": -1},  # 1 * 3 = 3
            ],
        }
    )

    # Control 5: Local Clifford change of basis (Hadamard on qubit 0: X <-> Z)
    controls.append(
        {
            "id": "ctrl_05_clifford_hadamard",
            "title": "Control 5: Local Hadamard on Qubit 0 (X <-> Z)",
            "n": 2,
            "terms": [
                {"id": "t_z", "P": "ZI", "w": [2, 1], "target": 1},
                {"id": "t_x", "P": "IX", "w": [1, 1], "target": 1},
            ],
        }
    )

    # Control 6: Local Phase gate change of basis (S gate on qubit 0: X -> Y)
    controls.append(
        {
            "id": "ctrl_06_phase_gate",
            "title": "Control 6: Phase Gate on Qubit 0 (X -> Y)",
            "n": 2,
            "terms": [
                {"id": "t_y", "P": "YI", "w": [2, 1], "target": 1},
                {"id": "t_z", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # Control 7: Combined permutation + renaming + reordering
    controls.append(
        {
            "id": "ctrl_07_combined_perm_rename",
            "title": "Control 7: Combined Qubit Permutation, Renaming, and Reordering",
            "n": 4,
            "terms": [
                {"id": "op_second", "P": "IZZI", "w": [1, 1], "target": 1},
                {"id": "op_first", "P": "ZIIZ", "w": [2, 1], "target": 1},
            ],
        }
    )

    # Control 8: 4-qubit Clifford orbit (Hadamard on multiple qubits)
    controls.append(
        {
            "id": "ctrl_08_multi_clifford",
            "title": "Control 8: 4-Qubit Multi-Hadamard Orbit",
            "n": 4,
            "terms": [
                {"id": "orbit_1", "P": "ZZZZ", "w": [1, 1], "target": 1},
                {"id": "orbit_2", "P": "XXXX", "w": [1, 1], "target": 1},
            ],
        }
    )

    return controls


def generate_poisoned_cases() -> list[dict]:
    poisoned = []

    # Poisoned 1: Anticommuting pair hidden among 23 commuting terms (M = 24 total)
    p1_terms = []
    # 22 commuting Z terms
    for i in range(22):
        p1_terms.append(
            {
                "id": f"t_comm_{i}",
                "P": "I" * (i % 8) + "Z" + "I" * (7 - (i % 8)),
                "w": [1, 1],
                "target": 1,
            }
        )
    # 2 terms that anticommute: X on qubit 0 and Z on qubit 0
    p1_terms.append({"id": "t_anti_x", "P": "X" + "I" * 7, "w": [1, 1], "target": 1})
    p1_terms.append({"id": "t_anti_z", "P": "Z" + "I" * 7, "w": [1, 1], "target": 1})
    poisoned.append(
        {
            "id": "psn_01_hidden_anticommuting_24",
            "title": "Poisoned 1: Anticommuting Pair Hidden Among 22 Commuting Terms (M=24)",
            "n": 8,
            "terms": p1_terms,
        }
    )

    # Poisoned 2: Y-count phase trap (multiple Ys where naive phase rule flips sign)
    poisoned.append(
        {
            "id": "psn_02_y_phase_trap",
            "title": "Poisoned 2: Y-Count Phase Trap with Multiple Y Factors",
            "n": 3,
            "terms": [
                {"id": "t_yyi", "P": "YYI", "w": [1, 1], "target": 1},
                {"id": "t_iyy", "P": "IYY", "w": [1, 1], "target": 1},
                {"id": "t_yiy", "P": "YIY", "w": [1, 1], "target": 1},
            ],
        }
    )

    # Poisoned 3: Unreduced weight pair [6, 4] -> must reduce to 3/2
    poisoned.append(
        {
            "id": "psn_03_unreduced_weight",
            "title": "Poisoned 3: Unreduced Weight Pair [6, 4]",
            "n": 2,
            "terms": [
                {"id": "t_unred", "P": "ZZ", "w": [6, 4], "target": 1},
                {"id": "t_unit", "P": "II", "w": [1, 1], "target": 1},
            ],
        }
    )

    # Poisoned 4: Term equal to signed product of others with negative sign
    poisoned.append(
        {
            "id": "psn_04_signed_product_term",
            "title": "Poisoned 4: Term Equal to Signed Product with Negative Sign",
            "n": 2,
            "terms": [
                {"id": "t_x", "P": "XI", "w": [1, 1], "target": 1},
                {
                    "id": "t_z",
                    "P": "ZI",
                    "w": [1, 1],
                    "target": 1,
                },  # wait, XI and ZI anticommute! Use commuting:
                # Let's use 2-qubit commuting: G1 = XI, G2 = IX. Then G1*G2 = XX (sign +1).
                # To get negative sign: G1 = XZ, G2 = ZX.
                # (XZ) * (ZX) = (X*Z) (Z*X) = (-iY) * (iY) = -i * i * Y^2 = 1 * I = +I.
                # How about G1 = XY, G2 = YX?
                # (XY) * (YX) = (X*Y) (Y*X) = (iZ) * (-iZ) = +1 * Z^2 = +I.
                # To get sign -1: what about G1 = YI, G2 = IY? prod is YY.
                # If we include a term equal to -YY? In input, all terms have +1 or -1 target.
                # If input has P = YY, w = [1, 1], target = -1.
            ],
        }
    )
    # Replace psn_04 with clean commuting signed decomposition:
    poisoned[-1]["terms"] = [
        {"id": "g_1", "P": "YX", "w": [1, 1], "target": 1},
        {"id": "g_2", "P": "XY", "w": [1, 1], "target": 1},
        {"id": "prod_zz", "P": "ZZ", "w": [2, 1], "target": -1},
    ]

    # Poisoned 5: Term IDs that sort differently as strings than as positions
    poisoned.append(
        {
            "id": "psn_05_string_sort_differ",
            "title": "Poisoned 5: Term IDs Sorting Differently as Strings ('t_10' < 't_2')",
            "n": 3,
            "terms": [
                {"id": "t_10", "P": "ZZI", "w": [1, 1], "target": 1},
                {"id": "t_2", "P": "IZZ", "w": [1, 1], "target": 1},
                {"id": "t_1", "P": "ZIZ", "w": [1, 1], "target": 1},
            ],
        }
    )

    # Poisoned 6: Duplicate term ID (must return UNKNOWN)
    poisoned.append(
        {
            "id": "psn_06_duplicate_term_id",
            "title": "Poisoned 6: Duplicate Term ID ('dup_id')",
            "n": 2,
            "terms": [
                {"id": "dup_id", "P": "ZZ", "w": [1, 1], "target": 1},
                {"id": "dup_id", "P": "XX", "w": [1, 1], "target": 1},
            ],
        }
    )

    return poisoned


def main() -> None:
    print(f"Generating C021 Judge datasets in {JUDGE_DIR}...")

    # 1. 32 hidden base cases
    hidden = generate_hidden_base_cases()
    assert len(hidden) == 32, f"Expected 32 hidden base cases, got {len(hidden)}"
    hidden_path = JUDGE_DIR / "hidden_base_cases.json"
    with open(hidden_path, "w", encoding="utf-8") as f:
        json.dump(hidden, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"  [DONE] Written 32 hidden base cases to {hidden_path.name}")

    # 2. 8 relabel controls
    controls = generate_relabel_controls()
    assert len(controls) == 8, f"Expected 8 controls, got {len(controls)}"
    controls_path = JUDGE_DIR / "relabel_controls.json"
    with open(controls_path, "w", encoding="utf-8") as f:
        json.dump(controls, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"  [DONE] Written 8 relabel controls to {controls_path.name}")

    # 3. 6 poisoned cases
    poisoned = generate_poisoned_cases()
    assert len(poisoned) == 6, f"Expected 6 poisoned cases, got {len(poisoned)}"
    poisoned_path = JUDGE_DIR / "poisoned_cases.json"
    with open(poisoned_path, "w", encoding="utf-8") as f:
        json.dump(poisoned, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"  [DONE] Written 6 poisoned cases to {poisoned_path.name}")


if __name__ == "__main__":
    main()
