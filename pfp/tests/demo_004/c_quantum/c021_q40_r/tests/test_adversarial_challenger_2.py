"""Adversarial Mutation Generator and Stress-Test Harness for C021 Dual Checkers.

Challenger 2 (Milestone 2).
Adversarially stress-tests Checker 1 (Exact Algebraic) and Checker 2 (Exact Dense Spectral LDL^H)
against 7 insidious corruption families:
1. Inverted phase decomposition (sigma = +1 when true phase is -1, e.g. Y-phase trap).
2. Imbalanced dual witness / false ground state (claiming E0 lower than true minimum, or higher).
3. Linearly dependent generator basis disguised as independent.
4. Generator basis with non-commuting elements.
5. Minimizers list missing true minimizers or containing non-minimizers.
6. Off-by-factor-of-2 degeneracy errors (forgetting 2^(n-k) factor).
7. Malformed types: floats (1.0), strings ("0"), booleans (True), null, complex numbers, lists as dicts.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import unittest
from fractions import Fraction
from typing import Any

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.algebraic_checker import (
    verify_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.spectral_checker import (
    verify_spectral_optimality,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.solver import (
    solve,
)


class AdversarialMutationGenerator:
    """Generates corrupted certificates spanning all 7 insidious corruption modes."""

    @staticmethod
    def get_seed_cases() -> list[dict[str, Any]]:
        """Returns standard seed cases covering various n, k, frustration, and Y phases."""
        cases = []

        # Case A: Bell state with Y-phase (n=2, k=2, E0=0, deg=1)
        # G1 = XX, G2 = ZZ -> G1*G2 = -YY. Term P3 = YY with target -1.
        cases.append(
            {
                "id": "seed_bell_y",
                "n": 2,
                "terms": [
                    {"id": "t_xx", "P": "XX", "w": [1, 1], "target": 1},
                    {"id": "t_zz", "P": "ZZ", "w": [1, 1], "target": 1},
                    {"id": "t_yy", "P": "YY", "w": [1, 1], "target": -1},
                ],
            }
        )

        # Case B: Frustrated triangle (n=3, k=2, E0=1, deg=6)
        # P1=ZII, P2=IZI, P3=ZZI (all target +1, but opposing signs)
        cases.append(
            {
                "id": "seed_frust_triangle",
                "n": 3,
                "terms": [
                    {"id": "t_01", "P": "ZII", "w": [1, 1], "target": 1},
                    {"id": "t_02", "P": "IZI", "w": [1, 1], "target": 1},
                    {"id": "t_03", "P": "ZZI", "w": [1, 1], "target": -1},
                ],
            }
        )

        # Case C: 4-qubit Y-count phase trap (n=4, k=2, E0=0, deg=4)
        # G1 = XXXX, G2 = ZZZZ -> G1*G2 = YYYY.
        cases.append(
            {
                "id": "seed_4q_yyyy",
                "n": 4,
                "terms": [
                    {"id": "t_xxxx", "P": "XXXX", "w": [2, 1], "target": 1},
                    {"id": "t_zzzz", "P": "ZZZZ", "w": [2, 1], "target": 1},
                    {"id": "t_yyyy", "P": "YYYY", "w": [2, 1], "target": 1},
                ],
            }
        )

        # Case D: Unused qubit scaling (n=4, k=1, E0=0, deg=8)
        # 1 active qubit, 3 unused qubits -> deg = 1 * 2^3 = 8
        cases.append(
            {
                "id": "seed_unused_qubits",
                "n": 4,
                "terms": [
                    {"id": "t_z", "P": "ZIII", "w": [1, 1], "target": 1},
                ],
            }
        )

        # Case E: Pure Identity (n=2, k=0, E0=0, deg=4)
        cases.append(
            {
                "id": "seed_all_identity",
                "n": 2,
                "terms": [
                    {"id": "t_id1", "P": "II", "w": [1, 1], "target": 1},
                    {"id": "t_id2", "P": "II", "w": [3, 2], "target": 1},
                ],
            }
        )

        # Case F: 6-qubit toric-like plaquette (n=6, k=3, E0=0, deg=8)
        cases.append(
            {
                "id": "seed_6q_commute",
                "n": 6,
                "terms": [
                    {"id": "t_p1", "P": "ZZIIII", "w": [1, 1], "target": 1},
                    {"id": "t_p2", "P": "IIZZII", "w": [1, 1], "target": 1},
                    {"id": "t_p3", "P": "IIIIZZ", "w": [1, 1], "target": 1},
                    {"id": "t_p4", "P": "ZZZZII", "w": [1, 1], "target": 1},
                ],
            }
        )

        return cases

    @classmethod
    def generate_family_1_inverted_phase(cls) -> list[dict[str, Any]]:
        """Family 1: Inverted phase decomposition (e.g. sigma = +1 when true phase is -1)."""
        mutations = []
        for case in cls.get_seed_cases():
            sol = solve(case)
            if sol["status"] != "SOLVED":
                continue
            for d_idx, decomp in enumerate(sol["decomposition"]):
                corrupted = copy.deepcopy(sol)
                orig_phase = decomp["phase"]
                corrupted["decomposition"][d_idx]["phase"] = -orig_phase
                mutations.append(
                    {
                        "family": "1_inverted_phase",
                        "id": f"mut_phase_inv_{case['id']}_term_{decomp['id']}",
                        "description": f"Inverted phase for term {decomp['id']} from {orig_phase} to {-orig_phase}",
                        "case": case,
                        "result": corrupted,
                    }
                )
        return mutations

    @classmethod
    def generate_family_2_imbalanced_dual_witness(cls) -> list[dict[str, Any]]:
        """Family 2: Imbalanced dual witness / false ground state (claiming E0 lower or higher)."""
        mutations = []
        for case in cls.get_seed_cases():
            sol = solve(case)
            if sol["status"] != "SOLVED":
                continue
            e_num, e_den = sol["energy"]
            e_frac = Fraction(e_num, e_den)

            # Subfamily 2A: Claiming E0 higher than true minimum
            higher_fracs = [
                e_frac + Fraction(1, 1),
                e_frac + Fraction(1, 2),
                e_frac + Fraction(5, 3),
            ]
            for h_idx, hf in enumerate(higher_fracs):
                corrupted = copy.deepcopy(sol)
                corrupted["energy"] = [hf.numerator, hf.denominator]
                mutations.append(
                    {
                        "family": "2A_higher_energy",
                        "id": f"mut_energy_high_{case['id']}_{h_idx}",
                        "description": f"Claimed E0 {hf} higher than true E0 {e_frac}",
                        "case": case,
                        "result": corrupted,
                    }
                )

            # Subfamily 2B: Claiming E0 lower than true minimum
            lower_fracs = []
            if e_frac > 0:
                lower_fracs.append(Fraction(0, 1))
                lower_fracs.append(e_frac / 2)
            lower_fracs.append(e_frac - Fraction(1, 1))
            lower_fracs.append(Fraction(-1, 2))

            for l_idx, lf in enumerate(lower_fracs):
                corrupted = copy.deepcopy(sol)
                corrupted["energy"] = [lf.numerator, lf.denominator]
                mutations.append(
                    {
                        "family": "2B_lower_energy",
                        "id": f"mut_energy_low_{case['id']}_{l_idx}",
                        "description": f"Claimed E0 {lf} lower than true E0 {e_frac}",
                        "case": case,
                        "result": corrupted,
                    }
                )

        return mutations

    @classmethod
    def generate_family_3_linearly_dependent_basis(cls) -> list[dict[str, Any]]:
        """Family 3: Linearly dependent generator basis disguised as independent."""
        mutations = []

        # Scenario 1: n=3, 3 commuting terms where t3 = t1 * t2 (rank 2, but k claimed 3)
        case_3q = {
            "id": "lin_dep_3q",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "ZII", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZI", "w": [1, 1], "target": 1},
                {"id": "t3", "P": "ZZI", "w": [1, 1], "target": 1},
            ],
        }
        res_3q = {
            "id": "lin_dep_3q",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 2,  # True degeneracy is 2^(3-2) = 2
            "basis": ["t1", "t2", "t3"],  # Linearly dependent!
            "decomposition": [
                {"id": "t1", "mask": 1, "phase": 1},
                {"id": "t2", "mask": 2, "phase": 1},
                {"id": "t3", "mask": 4, "phase": 1},
            ],
            "minimizers": [0, 7],  # 2 minimizers, 2 * 2^(3-3) = 2 == degeneracy
        }
        mutations.append(
            {
                "family": "3_linearly_dependent_basis",
                "id": "mut_lin_dep_3q_disguised",
                "description": "Basis [t1, t2, t3] is linearly dependent over GF(2) (t3=t1*t2), disguised with k=3",
                "case": case_3q,
                "result": res_3q,
            }
        )

        # Scenario 2: n=4, 4 commuting terms where t4 = t1 * t2 * t3 (rank 3, but k claimed 4)
        case_4q = {
            "id": "lin_dep_4q",
            "n": 4,
            "terms": [
                {"id": "t1", "P": "ZIII", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZII", "w": [1, 1], "target": 1},
                {"id": "t3", "P": "IIZI", "w": [1, 1], "target": 1},
                {"id": "t4", "P": "ZZZI", "w": [1, 1], "target": 1},
            ],
        }
        res_4q = {
            "id": "lin_dep_4q",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 2,
            "basis": ["t1", "t2", "t3", "t4"],
            "decomposition": [
                {"id": "t1", "mask": 1, "phase": 1},
                {"id": "t2", "mask": 2, "phase": 1},
                {"id": "t3", "mask": 4, "phase": 1},
                {"id": "t4", "mask": 8, "phase": 1},
            ],
            "minimizers": [0, 15],
        }
        mutations.append(
            {
                "family": "3_linearly_dependent_basis",
                "id": "mut_lin_dep_4q_disguised",
                "description": "Basis [t1, t2, t3, t4] is linearly dependent (t4=t1*t2*t3), disguised with k=4",
                "case": case_4q,
                "result": res_4q,
            }
        )

        # Scenario 3: n=6, 3 generators where g2 = g1
        case_6q = {
            "id": "lin_dep_6q",
            "n": 6,
            "terms": [
                {"id": "t1", "P": "ZZIIII", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "ZZIIII", "w": [1, 1], "target": 1},
                {"id": "t3", "P": "IIIIZZ", "w": [1, 1], "target": 1},
            ],
        }
        res_6q = {
            "id": "lin_dep_6q",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 16,
            "basis": ["t1", "t2", "t3"],
            "decomposition": [
                {"id": "t1", "mask": 1, "phase": 1},
                {"id": "t2", "mask": 2, "phase": 1},
                {"id": "t3", "mask": 4, "phase": 1},
            ],
            "minimizers": [0, 3],
        }
        mutations.append(
            {
                "family": "3_linearly_dependent_basis",
                "id": "mut_lin_dep_6q_identical_terms",
                "description": "Basis contains two distinct IDs with identical Pauli string",
                "case": case_6q,
                "result": res_6q,
            }
        )

        return mutations

    @classmethod
    def generate_family_4_noncommuting_basis(cls) -> list[dict[str, Any]]:
        """Family 4: Generator basis with non-commuting elements."""
        mutations = []
        case_nc = {
            "id": "case_noncom_basis",
            "n": 2,
            "terms": [
                {"id": "t_x", "P": "XI", "w": [1, 1], "target": 1},
                {"id": "t_z", "P": "ZI", "w": [1, 1], "target": 1},
            ],
        }
        res_nc = {
            "id": "case_noncom_basis",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 1,
            "basis": ["t_x", "t_z"],  # Anticommuting!
            "decomposition": [
                {"id": "t_x", "mask": 1, "phase": 1},
                {"id": "t_z", "mask": 2, "phase": 1},
            ],
            "minimizers": [0],
        }
        mutations.append(
            {
                "family": "4_noncommuting_basis",
                "id": "mut_noncom_basis_xi_zi",
                "description": "Basis elements t_x (XI) and t_z (ZI) anticommute on qubit 0",
                "case": case_nc,
                "result": res_nc,
            }
        )

        case_nc3 = {
            "id": "case_noncom_basis_3q",
            "n": 3,
            "terms": [
                {"id": "t_xx", "P": "XXI", "w": [1, 1], "target": 1},
                {"id": "t_zz", "P": "ZZI", "w": [1, 1], "target": 1},
                {"id": "t_yy", "P": "YYI", "w": [1, 1], "target": 1},
                {"id": "t_bad", "P": "XZI", "w": [1, 1], "target": 1},  # Anticommutes with ZZ!
            ],
        }
        res_nc3 = {
            "id": "case_noncom_basis_3q",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 2,
            "basis": ["t_zz", "t_bad"],  # Anticommuting!
            "decomposition": [
                {"id": "t_xx", "mask": 1, "phase": 1},
                {"id": "t_zz", "mask": 1, "phase": 1},
                {"id": "t_yy", "mask": 1, "phase": 1},
                {"id": "t_bad", "mask": 2, "phase": 1},
            ],
            "minimizers": [0],
        }
        mutations.append(
            {
                "family": "4_noncommuting_basis",
                "id": "mut_noncom_basis_zz_xz",
                "description": "Basis elements t_zz and t_bad anticommute",
                "case": case_nc3,
                "result": res_nc3,
            }
        )

        return mutations

    @classmethod
    def generate_family_5_minimizers_corruption(cls) -> list[dict[str, Any]]:
        """Family 5: Minimizers list missing true minimizers or containing non-minimizers."""
        mutations = []

        # 5A: Missing true minimizers (from frustrated triangle which has 3 minimizers)
        case_frust = {
            "id": "frust_triangle",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "ZII", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZI", "w": [1, 1], "target": 1},
                {"id": "t3", "P": "ZZI", "w": [1, 1], "target": -1},
            ],
        }
        sol_frust = solve(case_frust)
        assert len(sol_frust["minimizers"]) == 3

        corrupted_missing = copy.deepcopy(sol_frust)
        corrupted_missing["minimizers"] = sol_frust["minimizers"][:2]
        mutations.append(
            {
                "family": "5A_missing_minimizers",
                "id": "mut_minimizers_missing_one",
                "description": "Minimizers list has 2 instead of all 3 true minimizers",
                "case": case_frust,
                "result": corrupted_missing,
            }
        )

        # 5B: Containing non-minimizers (swapping true minimizer for non-minimizing state)
        case_simple = {
            "id": "simple_2q",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
        sol_simple = solve(case_simple)
        corrupted_nonmin = copy.deepcopy(sol_simple)
        corrupted_nonmin["minimizers"] = [3]  # Non-minimizing bitmask (energy = 2 != 0)
        mutations.append(
            {
                "family": "5B_containing_non_minimizers",
                "id": "mut_minimizers_swap_non_minimizer",
                "description": "Minimizer [0] swapped with non-minimizer [3] with equal count",
                "case": case_simple,
                "result": corrupted_nonmin,
            }
        )

        # 5C: Minimizers list contains duplicates
        corrupted_dups = copy.deepcopy(sol_simple)
        corrupted_dups["minimizers"] = [0, 0]
        mutations.append(
            {
                "family": "5C_minimizers_duplicates",
                "id": "mut_minimizers_duplicates",
                "description": "Minimizers list contains duplicate mask [0, 0]",
                "case": case_simple,
                "result": corrupted_dups,
            }
        )

        # 5D: Minimizers mask out of bounds for k
        corrupted_oob = copy.deepcopy(sol_simple)
        corrupted_oob["minimizers"] = [9999]
        mutations.append(
            {
                "family": "5D_minimizers_out_of_bounds",
                "id": "mut_minimizers_mask_oob",
                "description": "Minimizer mask 9999 exceeds 2^k - 1 (k=2)",
                "case": case_simple,
                "result": corrupted_oob,
            }
        )

        # 5E: Minimizers mask out of bounds when k=0!
        case_k0 = {
            "id": "identity_k0",
            "n": 1,
            "terms": [{"id": "t1", "P": "I", "w": [1, 1], "target": 1}],
        }
        sol_k0 = solve(case_k0)
        corrupted_k0 = copy.deepcopy(sol_k0)
        corrupted_k0["minimizers"] = [999999]
        mutations.append(
            {
                "family": "5E_minimizers_k0_out_of_bounds",
                "id": "mut_minimizers_k0_oob",
                "description": "Minimizer mask 999999 on k=0 system where only mask 0 is valid",
                "case": case_k0,
                "result": corrupted_k0,
            }
        )

        # 5F: Decomposition mask out of bounds when k=0!
        corrupted_k0_decomp = copy.deepcopy(sol_k0)
        corrupted_k0_decomp["decomposition"][0]["mask"] = 999999
        mutations.append(
            {
                "family": "5F_decomp_k0_mask_out_of_bounds",
                "id": "mut_decomp_k0_mask_oob",
                "description": "Decomposition mask 999999 on k=0 system where only mask 0 is valid",
                "case": case_k0,
                "result": corrupted_k0_decomp,
            }
        )

        return mutations

    @classmethod
    def generate_family_6_degeneracy_errors(cls) -> list[dict[str, Any]]:
        """Family 6: Off-by-factor-of-2 degeneracy errors (forgetting 2^(n-k) factor)."""
        mutations = []
        for case in cls.get_seed_cases():
            sol = solve(case)
            if sol["status"] != "SOLVED":
                continue
            n = case["n"]
            k = len(sol["basis"])
            true_deg = sol["degeneracy"]

            # 6A: Forgetting 2^(n-k) factor: degeneracy = len(minimizers)
            if n > k:
                corrupted_subspace = copy.deepcopy(sol)
                corrupted_subspace["degeneracy"] = len(sol["minimizers"])
                mutations.append(
                    {
                        "family": "6A_missing_2_n_minus_k_factor",
                        "id": f"mut_deg_missing_subspace_{case['id']}",
                        "description": f"Degeneracy forgot 2^({n}-{k}) factor: reported {len(sol['minimizers'])} vs true {true_deg}",
                        "case": case,
                        "result": corrupted_subspace,
                    }
                )

            # 6B: Off by factor of 2 (doubled)
            corrupted_2x = copy.deepcopy(sol)
            corrupted_2x["degeneracy"] = true_deg * 2
            mutations.append(
                {
                    "family": "6B_off_by_factor_2",
                    "id": f"mut_deg_doubled_{case['id']}",
                    "description": f"Degeneracy doubled from {true_deg} to {true_deg * 2}",
                    "case": case,
                    "result": corrupted_2x,
                }
            )

            # 6C: Off by factor of 2 (halved, if even)
            if true_deg % 2 == 0:
                corrupted_half = copy.deepcopy(sol)
                corrupted_half["degeneracy"] = true_deg // 2
                mutations.append(
                    {
                        "family": "6C_off_by_factor_2_halved",
                        "id": f"mut_deg_halved_{case['id']}",
                        "description": f"Degeneracy halved from {true_deg} to {true_deg // 2}",
                        "case": case,
                        "result": corrupted_half,
                    }
                )

            # 6D: Degeneracy is 0 or negative
            for bad_d in [0, -1, -true_deg]:
                corrupted_neg = copy.deepcopy(sol)
                corrupted_neg["degeneracy"] = bad_d
                mutations.append(
                    {
                        "family": "6D_non_positive_degeneracy",
                        "id": f"mut_deg_bad_{case['id']}_{bad_d}",
                        "description": f"Non-positive degeneracy {bad_d}",
                        "case": case,
                        "result": corrupted_neg,
                    }
                )

        return mutations

    @classmethod
    def generate_family_7_malformed_types(cls) -> list[dict[str, Any]]:
        """Family 7: Malformed types: floats, strings, booleans, null, complex, lists as dicts."""
        mutations = []
        seed = cls.get_seed_cases()[0]
        sol = solve(seed)

        type_attacks = [
            ("float_energy_num", lambda s: s.update({"energy": [1.0, 1]})),
            ("float_energy_den", lambda s: s.update({"energy": [1, 2.0]})),
            ("float_energy_scalar", lambda s: s.update({"energy": 0.0})),
            ("float_degeneracy", lambda s: s.update({"degeneracy": 1.0})),
            ("float_phase", lambda s: s["decomposition"][0].update({"phase": 1.0})),
            ("float_mask", lambda s: s["decomposition"][0].update({"mask": 1.0})),
            ("float_minimizer", lambda s: s.update({"minimizers": [0.0]})),
            ("str_energy_num", lambda s: s.update({"energy": ["0", 1]})),
            ("str_energy_den", lambda s: s.update({"energy": [0, "1"]})),
            ("str_energy_scalar", lambda s: s.update({"energy": "0/1"})),
            ("str_degeneracy", lambda s: s.update({"degeneracy": "1"})),
            ("str_phase", lambda s: s["decomposition"][0].update({"phase": "1"})),
            ("str_mask", lambda s: s["decomposition"][0].update({"mask": "1"})),
            ("str_minimizer", lambda s: s.update({"minimizers": ["0"]})),
            ("bool_energy_num", lambda s: s.update({"energy": [True, 1]})),
            ("bool_energy_den", lambda s: s.update({"energy": [0, True]})),
            ("bool_degeneracy_true", lambda s: s.update({"degeneracy": True})),
            ("bool_degeneracy_false", lambda s: s.update({"degeneracy": False})),
            ("bool_phase", lambda s: s["decomposition"][0].update({"phase": True})),
            ("bool_mask", lambda s: s["decomposition"][0].update({"mask": False})),
            ("bool_minimizer", lambda s: s.update({"minimizers": [False]})),
            ("null_energy", lambda s: s.update({"energy": None})),
            ("null_energy_elem", lambda s: s.update({"energy": [None, 1]})),
            ("null_degeneracy", lambda s: s.update({"degeneracy": None})),
            ("null_basis", lambda s: s.update({"basis": None})),
            ("null_decomposition", lambda s: s.update({"decomposition": None})),
            ("null_minimizers", lambda s: s.update({"minimizers": None})),
            ("complex_energy_num", lambda s: s.update({"energy": [complex(0, 1), 1]})),
            ("complex_degeneracy", lambda s: s.update({"degeneracy": complex(1, 0)})),
            ("complex_phase", lambda s: s["decomposition"][0].update({"phase": complex(1, 0)})),
            ("complex_minimizer", lambda s: s.update({"minimizers": [complex(0, 0)]})),
            ("dict_as_energy", lambda s: s.update({"energy": {"num": 0, "den": 1}})),
            ("dict_as_basis", lambda s: s.update({"basis": {"t1": True}})),
            (
                "dict_as_decomposition",
                lambda s: s.update({"decomposition": {"t1": {"mask": 1, "phase": 1}}}),
            ),
            ("dict_as_minimizers", lambda s: s.update({"minimizers": {"0": True}})),
            ("list_as_decomposition_entry", lambda s: s.update({"decomposition": [[1, 1]]})),
        ]

        for name, attack_fn in type_attacks:
            corrupted = copy.deepcopy(sol)
            attack_fn(corrupted)
            mutations.append(
                {
                    "family": "7_malformed_types",
                    "id": f"mut_type_{name}",
                    "description": f"Malformed type attack: {name}",
                    "case": seed,
                    "result": corrupted,
                }
            )

        return mutations

    @classmethod
    def generate_all(cls) -> list[dict[str, Any]]:
        """Generates the full comprehensive corpus of corrupted certificates."""
        all_mutations = []
        all_mutations.extend(cls.generate_family_1_inverted_phase())
        all_mutations.extend(cls.generate_family_2_imbalanced_dual_witness())
        all_mutations.extend(cls.generate_family_3_linearly_dependent_basis())
        all_mutations.extend(cls.generate_family_4_noncommuting_basis())
        all_mutations.extend(cls.generate_family_5_minimizers_corruption())
        all_mutations.extend(cls.generate_family_6_degeneracy_errors())
        all_mutations.extend(cls.generate_family_7_malformed_types())
        return all_mutations


class TestAdversarialChallenger2(unittest.TestCase):
    """Adversarial stress-test suite executing mutation generator against dual checkers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = AdversarialMutationGenerator()
        cls.all_mutations = cls.generator.generate_all()

    def test_mutation_corpus_size_and_diversity(self) -> None:
        """Verifies that the generated mutation corpus is sufficiently large and diverse."""
        total = len(self.all_mutations)
        self.assertGreaterEqual(
            total, 100, f"Expected at least 100 generated mutations, got {total}"
        )

        families = {m["family"] for m in self.all_mutations}
        expected_prefixes = {"1_", "2A_", "2B_", "3_", "4_", "5A_", "5B_", "6A_", "6B_", "7_"}
        for prefix in expected_prefixes:
            matching = [f for f in families if f.startswith(prefix)]
            self.assertTrue(len(matching) > 0, f"Missing mutation family matching {prefix}")

    def test_total_parsing_safety_zero_crashes(self) -> None:
        """Verifies that neither Checker 1 nor Checker 2 crashes (throws unhandled exception) on ANY mutation."""
        crashes_checker1 = []
        crashes_checker2 = []

        for m in self.all_mutations:
            case = m["case"]
            res = m["result"]
            m_id = m["id"]

            try:
                verify_certificate(case, res)
            except Exception as exc:
                crashes_checker1.append((m_id, str(exc)))

            try:
                verify_spectral_optimality(case, res)
            except Exception as exc:
                crashes_checker2.append((m_id, str(exc)))

        self.assertEqual(
            crashes_checker1, [], f"Checker 1 crashed on mutations: {crashes_checker1}"
        )
        self.assertEqual(
            crashes_checker2, [], f"Checker 2 crashed on mutations: {crashes_checker2}"
        )

    def test_family_1_inverted_phase_rejection(self) -> None:
        """Verifies 100% rejection of inverted phase decompositions."""
        mutations = self.generator.generate_family_1_inverted_phase()
        for m in mutations:
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            self.assertFalse(ok1, f"Checker 1 FALSE PASS on {m['id']}: {msg1}")
            self.assertTrue(msg1.startswith("FAIL:"))

            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            self.assertFalse(ok2, f"Checker 2 FALSE PASS on {m['id']}: {msg2}")
            self.assertTrue(msg2.startswith("FAIL:"))

    def test_family_2_imbalanced_dual_witness_rejection(self) -> None:
        """Verifies 100% rejection of imbalanced dual witness / false ground state."""
        mutations = self.generator.generate_family_2_imbalanced_dual_witness()
        for m in mutations:
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            self.assertFalse(ok1, f"Checker 1 FALSE PASS on {m['id']}: {msg1}")
            self.assertTrue(msg1.startswith("FAIL:"))

            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            self.assertFalse(ok2, f"Checker 2 FALSE PASS on {m['id']}: {msg2}")
            self.assertTrue(msg2.startswith("FAIL:"))

    def test_family_4_noncommuting_basis_rejection(self) -> None:
        """Verifies 100% rejection of basis containing non-commuting elements."""
        mutations = self.generator.generate_family_4_noncommuting_basis()
        for m in mutations:
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            self.assertFalse(ok1, f"Checker 1 FALSE PASS on {m['id']}: {msg1}")
            self.assertTrue(msg1.startswith("FAIL:"))

            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            self.assertFalse(ok2, f"Checker 2 FALSE PASS on {m['id']}: {msg2}")
            self.assertTrue(msg2.startswith("FAIL:"))

    def test_family_6_degeneracy_errors_rejection(self) -> None:
        """Verifies 100% rejection of off-by-factor-of-2 degeneracy errors."""
        mutations = self.generator.generate_family_6_degeneracy_errors()
        for m in mutations:
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            self.assertFalse(ok1, f"Checker 1 FALSE PASS on {m['id']}: {msg1}")
            self.assertTrue(msg1.startswith("FAIL:"))

            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            self.assertFalse(ok2, f"Checker 2 FALSE PASS on {m['id']}: {msg2}")
            self.assertTrue(msg2.startswith("FAIL:"))

    def test_family_7_malformed_types_rejection(self) -> None:
        """Verifies 100% rejection of malformed types (floats, strings, booleans, complex, null, dicts)."""
        mutations = self.generator.generate_family_7_malformed_types()
        for m in mutations:
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            self.assertFalse(ok1, f"Checker 1 FALSE PASS on {m['id']}: {msg1}")
            self.assertTrue(msg1.startswith("FAIL:"))

            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            self.assertFalse(ok2, f"Checker 2 FALSE PASS on {m['id']}: {msg2}")
            self.assertTrue(msg2.startswith("FAIL:"))

    def test_family_3_checker_2_blindspot_linearly_dependent_basis(self) -> None:
        """Empirically demonstrates Checker 2's vulnerability to linearly dependent basis generators."""
        mutations = self.generator.generate_family_3_linearly_dependent_basis()
        for m in mutations:
            # Checker 1 correctly rejects via GF(2) symplectic rank
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            self.assertFalse(ok1, f"Checker 1 unexpectedly passed {m['id']}")
            self.assertIn("linearly dependent", msg1)

            # Checker 2 blindspot check: passes linearly dependent basis when disguised
            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            if ok2:
                print(
                    f"\n[CONFIRMED DEFECT] Checker 2 falsely passed {m['id']} ({m['description']}): {msg2}"
                )

    def test_family_5_checker_2_blindspot_non_minimizers(self) -> None:
        """Empirically demonstrates Checker 2's vulnerability to non-minimizer bitmasks."""
        mutations = self.generator.generate_family_5_minimizers_corruption()
        for m in mutations:
            ok1, msg1 = verify_certificate(m["case"], m["result"])
            ok2, msg2 = verify_spectral_optimality(m["case"], m["result"])
            if ok2 and m["family"] in (
                "5B_containing_non_minimizers",
                "5E_minimizers_k0_out_of_bounds",
                "5F_decomp_k0_mask_out_of_bounds",
            ):
                print(
                    f"\n[CONFIRMED DEFECT] Checker 2 falsely passed {m['id']} ({m['description']}): {msg2}"
                )
            if ok1 and m["family"] == "5F_decomp_k0_mask_out_of_bounds":
                print(
                    f"\n[CONFIRMED DEFECT] Checker 1 falsely passed {m['id']} ({m['description']}): {msg1}"
                )

    def test_adversarial_census_summary(self) -> None:
        """Computes and logs the comprehensive empirical scorecard across all mutations."""
        total = len(self.all_mutations)
        c1_rejections = sum(
            1 for m in self.all_mutations if not verify_certificate(m["case"], m["result"])[0]
        )
        c2_rejections = sum(
            1
            for m in self.all_mutations
            if not verify_spectral_optimality(m["case"], m["result"])[0]
        )

        c1_rate = (c1_rejections / total) * 100.0
        c2_rate = (c2_rejections / total) * 100.0

        print("\n=== CHALLENGER 2 EMPIRICAL ADVERSARIAL SCORECARD ===")
        print(f"Total Corrupted Certificates Generated: {total}")
        print(f"Checker 1 Rejections: {c1_rejections}/{total} ({c1_rate:.2f}%)")
        print(f"Checker 2 Rejections: {c2_rejections}/{total} ({c2_rate:.2f}%)")
        print(f"Zero Crashes Invariant: CONFIRMED (0 crashes / {total} tests on both checkers)")
        print("===================================================\n")


if __name__ == "__main__":
    unittest.main()
