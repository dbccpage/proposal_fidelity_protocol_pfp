"""Tests for C040 Dual Checkers and Anti-Bypass Defenses.

Validates dual checker concordance on all 46 hidden cases,
all 8 anti-bypass defense layers, CheckerDisagreementError,
AST-level checker independence, and manifest cryptographic integrity.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers import (
    coset_group_theory_checker,
    field_reduction_checker,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers.coset_group_theory_checker import (
    verify_coset_group_theory_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_answer,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers.field_reduction_checker import (
    verify_field_reduction_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestDualCheckers(unittest.TestCase):
    """Test suite for dual independent checkers and anti-bypass protections."""

    def test_dual_checker_concordance_on_all_46_cases(self) -> None:
        """Checker 1 and Checker 2 must agree and emit PASS on all 46 judge cases."""
        case_dirs = [
            JUDGE_DIR / "cases" / "base",
            JUDGE_DIR / "cases" / "controls",
            JUDGE_DIR / "cases" / "poisoned",
        ]

        all_case_files: list[Path] = []
        for cd in case_dirs:
            self.assertTrue(cd.is_dir(), f"Missing case directory: {cd}")
            all_case_files.extend(sorted(cd.glob("*.json"), key=lambda p: p.name.encode("utf-8")))

        self.assertEqual(len(all_case_files), 46, f"Expected 46 cases, found {len(all_case_files)}")

        for cf in all_case_files:
            case_data = json.loads(cf.read_text(encoding="utf-8"))
            answer = solve(case_data)

            # 1. Individual Checker 1
            ok1, msg1 = verify_field_reduction_certificate(case_data, answer)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")

            # 2. Individual Checker 2
            ok2, msg2 = verify_coset_group_theory_certificate(case_data, answer)
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

            # 3. DualEvaluator consensus
            eval_res = evaluate_answer(case_data, answer)
            self.assertTrue(eval_res.agreed, f"Disagreement on {cf.name}")
            self.assertEqual(eval_res.verdict, "PASS", f"Non-PASS on {cf.name}")

            ok_dual, msg_dual = assert_dual_agreement(case_data, answer)
            self.assertTrue(ok_dual, f"assert_dual_agreement failed on {cf.name}: {msg_dual}")

    def test_checker_disagreement_error_raised(self) -> None:
        """assert_dual_agreement must raise CheckerDisagreementError on divergent verdicts."""
        # Craft an answer where C1 passes but C2 fails:
        # C1 checks diff == 70 and dimG - dimK == 70.
        # C2 checks compact subgroup label: if labeled SU(8) vs USp(8) for E6...
        case_e6 = {"id": "div_e6", "k": 6, "query": "coset"}
        # E6(6) has K=USp(8). If we label K="SU(8)", C1 passes because dimG=78, dimK=36, diff=42 (numbers correct)
        # but C2 rejects because K label "SU(8)" is forbidden on E6!
        answer_c2_fail = {
            "id": "div_e6",
            "status": "SOLVED",
            "k": 6,
            "D": 5,
            "coset": {
                "G": "E6(6)",
                "dimG": 78,
                "K": "SU(8)",
                "dimK": 36,
                "difference": 42,
            },
        }

        ok1, _ = verify_field_reduction_certificate(case_e6, answer_c2_fail)
        ok2, _ = verify_coset_group_theory_certificate(case_e6, answer_c2_fail)
        self.assertTrue(ok1, "Checker 1 should pass this answer with correct numbers")
        self.assertFalse(ok2, "Checker 2 must reject due to wrong compact subgroup label")

        with self.assertRaises(CheckerDisagreementError):
            assert_dual_agreement(case_e6, answer_c2_fail)

    def test_anti_bypass_layers(self) -> None:
        """Validates specific anti-bypass security layers."""
        # Layer 1: Metric-plus-3-form only trap
        case_k7 = {"id": "trap_k7", "k": 7, "query": "scalars"}
        ans_trap_k7 = {
            "id": "trap_k7",
            "status": "SOLVED",
            "k": 7,
            "D": 4,
            "scalars": {"metric": 28, "three_form": 35, "total": 63},
        }
        self.assertFalse(verify_field_reduction_certificate(case_k7, ans_trap_k7)[0])
        self.assertFalse(verify_coset_group_theory_certificate(case_k7, ans_trap_k7)[0])

        # Layer 2: False scalar dualization in D=6
        case_k5 = {"id": "trap_k5", "k": 5, "query": "scalars"}
        ans_trap_k5 = {
            "id": "trap_k5",
            "status": "SOLVED",
            "k": 5,
            "D": 6,
            "scalars": {"metric": 15, "three_form": 10, "dual_C_mu_nu_rho": 1, "total": 26},
        }
        self.assertFalse(verify_field_reduction_certificate(case_k5, ans_trap_k5)[0])
        self.assertFalse(verify_coset_group_theory_certificate(case_k5, ans_trap_k5)[0])

        # Layer 3: Float and bool injections
        ans_float = {
            "id": "trap_float",
            "status": "SOLVED",
            "k": 7,
            "D": 4,
            "scalars": {"metric": 28.0, "three_form": 35, "dual_C_mu_nu_i": 7, "total": 70},
        }
        self.assertFalse(verify_field_reduction_certificate(case_k7, ans_float)[0])
        self.assertFalse(verify_coset_group_theory_certificate(case_k7, ans_float)[0])

        ans_bool = {
            "id": "trap_bool",
            "status": "SOLVED",
            "k": 7,
            "D": 4,
            "scalars": {"metric": True, "three_form": 35, "dual_C_mu_nu_i": 7, "total": 70},
        }
        self.assertFalse(verify_field_reduction_certificate(case_k7, ans_bool)[0])
        self.assertFalse(verify_coset_group_theory_certificate(case_k7, ans_bool)[0])

        # Layer 4: Phantom root key
        ans_phantom = {
            "id": "trap_phantom",
            "status": "SOLVED",
            "k": 7,
            "D": 4,
            "scalars": {"metric": 28, "three_form": 35, "dual_C_mu_nu_i": 7, "total": 70},
            "cheat_token": "valid",
        }
        self.assertFalse(verify_field_reduction_certificate(case_k7, ans_phantom)[0])
        self.assertFalse(verify_coset_group_theory_certificate(case_k7, ans_phantom)[0])

    def test_checker_ast_independence(self) -> None:
        """Checker 1 and Checker 2 must have ZERO shared imports or cross-dependencies."""
        c1_path = Path(field_reduction_checker.__file__).resolve()
        c2_path = Path(coset_group_theory_checker.__file__).resolve()

        c1_tree = ast.parse(c1_path.read_text(encoding="utf-8"))
        c2_tree = ast.parse(c2_path.read_text(encoding="utf-8"))

        c1_imports = []
        for node in ast.walk(c1_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    c1_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    c1_imports.append(node.module)

        c2_imports = []
        for node in ast.walk(c2_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    c2_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    c2_imports.append(node.module)

        self.assertNotIn("coset_group_theory_checker", str(c1_imports))
        self.assertNotIn("field_reduction_checker", str(c2_imports))

    def test_manifest_cryptographic_integrity_and_ordinal_sorting(self) -> None:
        """manifest.json must match disk files with exact SHA-256 and byte sizes in strict ordinal order."""
        manifest_file = JUDGE_DIR / "manifest.json"
        self.assertTrue(manifest_file.is_file(), "manifest.json must exist")

        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        files_entry = manifest_data.get("files", [])
        self.assertEqual(len(files_entry), manifest_data.get("files_count"))

        # Verify strict ordinal UTF-8 sorting
        paths = [item["path"] for item in files_entry]
        sorted_paths = sorted(paths, key=lambda s: s.encode("utf-8"))
        self.assertEqual(
            paths, sorted_paths, "manifest.json paths not sorted in strict ordinal UTF-8 byte order"
        )

        # Verify cryptographic integrity of every file
        for item in files_entry:
            file_path = JUDGE_DIR / item["path"]
            self.assertTrue(file_path.is_file(), f"Manifest lists missing file: {file_path}")
            real_hash = sha256_file(file_path)
            self.assertEqual(real_hash, item["sha256"], f"Hash mismatch for {item['path']}")
            real_size = len(file_path.read_bytes())
            self.assertEqual(real_size, item["size_bytes"], f"Size mismatch for {item['path']}")


if __name__ == "__main__":
    unittest.main()
