"""End-to-End Multi-Tier Integration Test for Challenge C038 (Regge Combinatorial Curvature).

AuthorityEffect: None.

Verifies:
  Tier 1: Participant packet integrity and schema conformity.
  Tier 2: Reference solver accuracy across all 10 canonical examples.
  Tier 3: 100% dual checker concordance across all 46 judge cases.
  Tier 4: 100% hostile mutation detection across all 48 corrupted certificates.
  Tier 5: Cryptographic commit-reveal integrity verification.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.governance.commit_reveal_runner import (
    COMMITMENT_STATUS_REGENERATED,
    RECEIPT_BINDS_CURRENT_COMMITMENT,
    RECEIPT_BINDS_SUPERSEDED_COMMITMENT,
    inspect_commitments,
    verify_commitments,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.combinatorial_primal_checker import (
    verify_combinatorial_primal_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.homology_dual_potential_checker import (
    verify_homology_dual_potential_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
MUT_DIR = JUDGE_DIR / "mutation_suite" / "mutations"
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
PREFIX = "c038"


class TestE2EChallenge(unittest.TestCase):
    """End-to-end integration test exercising all layers of C038 challenge suite."""

    def test_tier1_participant_packet_conformance(self) -> None:
        """Tier 1: Validates participant artifacts and CLI runner."""
        task_file = PARTICIPANT_DIR / "TASK.md"
        self.assertTrue(task_file.is_file())

        acc_file = PARTICIPANT_DIR / "accounting.json"
        self.assertTrue(acc_file.is_file())
        acc_data = json.loads(acc_file.read_text(encoding="utf-8"))
        self.assertIn(acc_data["tier"], ("T2", "T3"))
        self.assertEqual(acc_data["cost_ceiling_usd"], 0.50)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "runner_out.json"
            cmd = [
                sys.executable,
                str(PARTICIPANT_DIR / "runner.py"),
                "--cases",
                str(PARTICIPANT_DIR / "examples" / "ex01_octahedron.json"),
                "--solver",
                str(CHALLENGE_DIR / "reference_solver" / "solver.py"),
                "--output",
                str(out_file),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(out_file.is_file())

    def test_tier2_reference_solver_benchmarks(self) -> None:
        """Tier 2: Validates solver outputs across all 10 canonical examples."""
        examples = sorted((PARTICIPANT_DIR / "examples").glob("*.json"))
        self.assertEqual(len(examples), 10)

        expected_statuses = {
            "ex01_octahedron.json": "SOLVED",
            "ex02_csaszar_torus.json": "SOLVED",
            "ex03_projective_plane.json": "SOLVED",
            "ex04_pinched_sphere_refusal.json": "OUT_OF_SCOPE",
            "ex05_surface_with_boundary_refusal.json": "OUT_OF_SCOPE",
            "ex06_triangle_with_tail_alpha0.json": "SOLVED",
            "ex07_triangle_with_tail_alpha_half.json": "SOLVED",
            "ex08_star_graph.json": "SOLVED",
            "ex09_cycle_graph.json": "SOLVED",
            "ex10_oversized_surface_refusal.json": "UNKNOWN",
        }

        for ex in examples:
            case = json.loads(ex.read_text(encoding="utf-8"))
            actual = solve(case)
            exp_status = expected_statuses[ex.name]
            self.assertEqual(actual["status"], exp_status, f"Status mismatch on {ex.name}")

    def test_tier3_dual_checker_concordance_46_cases(self) -> None:
        """Tier 3: Asserts 100% agreement and pass rate on all 46 judge cases."""
        case_files = sorted(CASES_DIR.rglob("*.json"))
        self.assertEqual(len(case_files), 46)

        agreed = 0
        passed = 0
        for cf in case_files:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            eval_res = evaluate_dual(case, ans)
            if eval_res["agreed"]:
                agreed += 1
            if eval_res["verdict"] == "PASS":
                passed += 1

        self.assertEqual(agreed, 46, f"Disagreements detected: {agreed}/46")
        self.assertEqual(passed, 46, f"Failures detected: {passed}/46")

    def test_tier4_hostile_mutation_kill_rate_100_percent(self) -> None:
        """Tier 4: Asserts 100% kill rate across all 48 hostile mutations."""
        mut_files = sorted(MUT_DIR.glob("*.json"))
        self.assertEqual(len(mut_files), 48)

        killed_c1 = 0
        killed_c2 = 0
        for mf in mut_files:
            data = json.loads(mf.read_text(encoding="utf-8"))
            case = data["case"]
            corrupted = data.get("result", data.get("answer"))

            ok1, _ = verify_combinatorial_primal_certificate(case, corrupted)
            ok2, _ = verify_homology_dual_potential_certificate(case, corrupted)

            if not ok1:
                killed_c1 += 1
            if not ok2:
                killed_c2 += 1

        self.assertEqual(killed_c1, 48, f"Checker 1 missed mutations: killed {killed_c1}/48")
        self.assertEqual(killed_c2, 48, f"Checker 2 missed mutations: killed {killed_c2}/48")

    def _load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_tier5_commit_reveal_integrity(self) -> None:
        """Tier 5: Phases 1 and 2 match the files on disk; the scoring receipt is read as the record it is.

        The committed judge commitment and freeze record were regenerated after the judge cases were
        visible, so both must say that they are current and not a pre-run commitment. The historical
        scoring receipt must bind the superseded commitment it recorded, not the regenerated one."""
        commitment = self._load(COMMITMENTS_DIR / f"{PREFIX}_judge_commitment.json")
        freeze = self._load(COMMITMENTS_DIR / f"{PREFIX}_freeze_record.json")
        receipt = self._load(COMMITMENTS_DIR / f"{PREFIX}_scoring_receipt.json")
        for record in (commitment, freeze):
            self.assertEqual(record.get("commitment_status"), COMMITMENT_STATUS_REGENERATED)
            self.assertTrue(record.get("regeneration_note"))

        result = inspect_commitments()
        self.assertTrue(result.verified, f"{result.code}: {result.detail}")
        self.assertEqual(result.commitment_status, COMMITMENT_STATUS_REGENERATED)
        if "gate_scope" in receipt:
            self.assertEqual(result.receipt_binding, RECEIPT_BINDS_CURRENT_COMMITMENT)
            self.assertEqual(receipt["phase1_manifest_sha256"], commitment["manifest_sha256"])
        else:
            self.assertEqual(result.receipt_binding, RECEIPT_BINDS_SUPERSEDED_COMMITMENT)
            self.assertEqual(
                receipt["phase1_manifest_sha256"],
                commitment["superseded_commitment"]["manifest_sha256"],
            )
        self.assertTrue(verify_commitments(), "Commit-reveal protocol verification failed")

    def test_tier5_receipt_must_bind_the_commitment_it_recorded(self) -> None:
        """Counterexample: a historical receipt whose digest equals a commitment made after it verified,
        because only the current files were compared. On a temporary copy: with no superseded record the
        receipt binds nothing it recorded and is refused; a superseded record with another digest, a
        historical receipt relabelled REFERENCE_SELF_CONSISTENT without gate_scope, and a historical
        receipt that does not record every case passed are refused too."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / CHALLENGE_DIR.name
            shutil.copytree(
                CHALLENGE_DIR, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )
            commitments = root / "commitments"
            commitment_file = commitments / f"{PREFIX}_judge_commitment.json"
            freeze_file = commitments / f"{PREFIX}_freeze_record.json"
            receipt_file = commitments / f"{PREFIX}_scoring_receipt.json"
            regenerated_keys = (
                "commitment_status",
                "regeneration_note",
                "superseded_commitment",
                "superseded_freeze_record",
            )
            commitment = {
                k: v for k, v in self._load(commitment_file).items() if k not in regenerated_keys
            }
            freeze = {k: v for k, v in self._load(freeze_file).items() if k not in regenerated_keys}
            receipt = {
                **self._load(receipt_file),
                "phase1_manifest_sha256": commitment["manifest_sha256"],
            }
            superseded = {
                "path": f"commitments/{PREFIX}_judge_commitment.json",
                "file_sha256": "0" * 64,
                "manifest_sha256": commitment["manifest_sha256"],
            }
            regenerated_freeze = {
                **freeze,
                "commitment_status": COMMITMENT_STATUS_REGENERATED,
                "superseded_freeze_record": {
                    "path": f"commitments/{PREFIX}_freeze_record.json",
                    "file_sha256": "0" * 64,
                },
            }

            def write(path: Path, data: dict) -> None:
                path.write_text(
                    json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )

            def code() -> str:
                return inspect_commitments(challenge_dir=root).code

            # Positive control: the regenerated records name the superseded commitment the receipt recorded.
            write(receipt_file, receipt)
            write(
                commitment_file,
                {
                    **commitment,
                    "commitment_status": COMMITMENT_STATUS_REGENERATED,
                    "superseded_commitment": superseded,
                },
            )
            write(freeze_file, regenerated_freeze)
            self.assertEqual(code(), "VERIFIED")

            # 1. Same digest as the current commitment, but no record of what the receipt bound.
            write(commitment_file, commitment)
            write(freeze_file, freeze)
            self.assertEqual(code(), "RECEIPT_BINDS_NO_COMMITMENT")

            # 2. A superseded commitment with another digest.
            write(
                commitment_file,
                {
                    **commitment,
                    "commitment_status": COMMITMENT_STATUS_REGENERATED,
                    "superseded_commitment": {**superseded, "manifest_sha256": "f" * 64},
                },
            )
            write(freeze_file, regenerated_freeze)
            self.assertEqual(code(), "RECEIPT_BINDS_NO_COMMITMENT")

            # 3. A historical receipt relabelled with the current label but without gate_scope.
            write(
                commitment_file,
                {
                    **commitment,
                    "commitment_status": COMMITMENT_STATUS_REGENERATED,
                    "superseded_commitment": superseded,
                },
            )
            write(receipt_file, {**receipt, "verdict": "REFERENCE_SELF_CONSISTENT"})
            self.assertEqual(code(), "RECEIPT_SCOPE_MISSING")

            # 4. A historical receipt that does not record every case passed.
            write(receipt_file, {**receipt, "all_passed": False})
            self.assertEqual(code(), "HISTORICAL_RECEIPT_NOT_ALL_PASSED")


if __name__ == "__main__":
    unittest.main()
