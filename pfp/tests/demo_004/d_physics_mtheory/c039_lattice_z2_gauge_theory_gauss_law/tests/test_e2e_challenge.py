"""End-to-End Multi-Tier Integration Test for Challenge C039 (Lattice Z2 Gauge Theory Gauss Law).

AuthorityEffect: None.

Verifies:
  Tier 1: Participant packet integrity and schema conformity.
  Tier 2: Reference solver accuracy across all 10 canonical examples.
  Tier 3: 100% dual checker concordance across all 48 judge cases.
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

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.governance.commit_reveal_runner import (
    COMMITMENT_STATUS_REGENERATED,
    RECEIPT_BINDS_CURRENT_COMMITMENT,
    RECEIPT_BINDS_SUPERSEDED_COMMITMENT,
    inspect_commitments,
    verify_commitments,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.homology_cohomology_checker import (
    verify_homology_cohomology_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.stabilizer_tableau_checker import (
    verify_stabilizer_tableau_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
MUT_DIR = JUDGE_DIR / "mutation_suite" / "mutations"
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
PREFIX = "c039"


class TestE2EChallenge(unittest.TestCase):
    """End-to-end integration test exercising all layers of C039 challenge suite."""

    def test_tier1_participant_packet_conformance(self) -> None:
        """Tier 1: Validates participant artifacts and CLI runner."""
        task_file = PARTICIPANT_DIR / "TASK.md"
        self.assertTrue(task_file.is_file())

        acc_file = PARTICIPANT_DIR / "accounting.json"
        self.assertTrue(acc_file.is_file())
        acc_data = json.loads(acc_file.read_text(encoding="utf-8"))
        self.assertEqual(acc_data["tier"], "T3")
        self.assertEqual(acc_data["cost_ceiling_usd"], 1.00)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "runner_out.json"
            cmd = [
                sys.executable,
                str(PARTICIPANT_DIR / "runner.py"),
                "--cases",
                str(PARTICIPANT_DIR / "examples" / "ex01_sphere_tetrahedron.json"),
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
        examples = sorted(
            (PARTICIPANT_DIR / "examples").glob("*.json"), key=lambda p: p.name.encode("utf-8")
        )
        self.assertEqual(len(examples), 10)

        expected_statuses = {
            "ex01_sphere_tetrahedron.json": "SOLVED",
            "ex02_torus_one_vertex.json": "SOLVED",
            "ex03_torus_2x2_square.json": "SOLVED",
            "ex04_projective_plane_rp2.json": "SOLVED",
            "ex05_klein_bottle.json": "SOLVED",
            "ex06_genus2_double_torus.json": "SOLVED",
            "ex07_sector_even_charges.json": "SOLVED",
            "ex08_sector_odd_charges.json": "SOLVED",
            "ex09_non_manifold_pinch.json": "OUT_OF_SCOPE",
            "ex10_oversized_complex.json": "UNKNOWN",
        }

        for ex in examples:
            case = json.loads(ex.read_text(encoding="utf-8"))
            actual = solve(case)
            exp_status = expected_statuses[ex.name]
            self.assertEqual(actual["status"], exp_status, f"Status mismatch on {ex.name}")

    def test_tier3_dual_checker_concordance_48_cases(self) -> None:
        """Tier 3: Asserts 100% agreement and pass rate on all 48 judge cases."""
        case_dirs = [CASES_DIR / "base", CASES_DIR / "controls", CASES_DIR / "poisoned"]
        all_cases = []
        for cd in case_dirs:
            all_cases.extend(sorted(cd.glob("*.json"), key=lambda p: p.name.encode("utf-8")))

        self.assertEqual(len(all_cases), 48)

        for cf in all_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            eval_res = evaluate_dual(case, ans)
            self.assertTrue(
                eval_res["agreed"],
                f"Checkers disagreed on {cf.name}: {eval_res}",
            )
            self.assertEqual(
                eval_res["verdict"],
                "PASS",
                f"Dual evaluation failed on {cf.name}: {eval_res}",
            )

    def test_tier4_hostile_mutation_kill_rate_100_percent(self) -> None:
        """Tier 4: Asserts 100% kill rate across all 48 hostile mutations."""
        mut_files = sorted(MUT_DIR.glob("*.json"), key=lambda p: p.name.encode("utf-8"))
        self.assertEqual(len(mut_files), 48)

        escapes_c1 = []
        escapes_c2 = []
        for mf in mut_files:
            mdata = json.loads(mf.read_text(encoding="utf-8"))
            case = mdata["case"]
            result = mdata["result"]
            ok1, _ = verify_stabilizer_tableau_certificate(case, result)
            ok2, _ = verify_homology_cohomology_certificate(case, result)
            if ok1:
                escapes_c1.append(mf.name)
            if ok2:
                escapes_c2.append(mf.name)

        self.assertEqual(escapes_c1, [], f"Checker 1 permitted escapes: {escapes_c1}")
        self.assertEqual(escapes_c2, [], f"Checker 2 permitted escapes: {escapes_c2}")

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
