"""Tests for C038 Governance and Cryptographic Commit-Reveal State Machine.

Every phase runs on a temporary copy of this package and every run folder goes
under a temporary directory, so running this file never writes into the
package's commitments/ or into a real _intelligence/ tree.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.governance import (
    woland_gate as woland_gate_module,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.governance.budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.governance.commit_reveal_runner import (
    ManifestCustodyError,
    lf_normalized_bytes,
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    verify_commitments,
    verify_manifest_entries,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.governance.woland_gate import (
    CANONICAL_OUTPUT_FILES,
    RunFolderExistsError,
    WolandGate,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
CONSISTENT = "REFERENCE_SELF_CONSISTENT"
INCONSISTENT = "REFERENCE_SELF_INCONSISTENT"


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def _temp_package(base: Path) -> Path:
    """Copy this package under base; rebuild the copy's judge manifest over LF bytes if it does not verify."""
    root = base / CHALLENGE_DIR.name
    shutil.copytree(CHALLENGE_DIR, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    manifest_file = root / "judge_packet" / "manifest.json"
    try:
        verify_manifest_entries(manifest_file, root)
    except ManifestCustodyError:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            data = lf_normalized_bytes(manifest_file.parent / entry["path"])
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            if "size_bytes" in entry:
                entry["size_bytes"] = len(data)
        manifest_file.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
    return root


class _Frozen(woland_gate_module.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 9, 29, 12, 0, 0, tzinfo=woland_gate_module.timezone.utc)


class TestGovernanceAndCommitReveal(unittest.TestCase):
    """Verifies governance gates and the commit-reveal state machine."""

    def test_budget_gate_enforces_tier_t2(self) -> None:
        """Asserts BudgetGate enforces $0.50 ceiling, $0.05 target, and disallows fallbacks."""
        gate = BudgetGate()
        self.assertEqual(gate.ceiling_usd, 0.50)
        self.assertEqual(gate.target_usd, 0.05)
        self.assertEqual(gate.ceiling_microusd, 500_000)
        self.assertFalse(gate.allow_fallbacks)

        with self.assertRaises(BudgetCeilingExceededError):
            BudgetGate(ceiling_usd=1.00)

        with self.assertRaises(FallbackNotAllowedError):
            BudgetGate(allow_fallbacks=True)

    def test_budget_gate_accumulates_exact_micro_usd(self) -> None:
        """Counterexample: spend was accumulated as float USD, so $0.10 + $0.20 became
        0.30000000000000004, and float or bool amounts were accepted. Spend is int micro-USD now."""
        gate = BudgetGate()
        for amount in (100_000, 200_000):
            gate.check_pre_call(amount)
            gate.record_call_cost(amount)
        self.assertEqual(gate.accumulated_cost_usd, Fraction(3, 10))
        gate.check_pre_call(200_000)  # exactly at the 500,000 micro-USD ceiling
        with self.assertRaises(BudgetCeilingExceededError):
            gate.check_pre_call(200_001)
        for bad in (0.1, True):
            with self.assertRaises(TypeError):
                gate.record_call_cost(bad)
            with self.assertRaises(TypeError):
                gate.check_pre_call(bad)

    def test_budget_gate_audit_accounting_config(self) -> None:
        """Audits participant accounting.json against Tier T2 requirements."""
        acc_file = CHALLENGE_DIR / "participant_packet" / "accounting.json"
        self.assertTrue(acc_file.is_file())

        gate = BudgetGate()
        data = json.loads(acc_file.read_text(encoding="utf-8"))
        audit = gate.audit_accounting_config(data)

        self.assertTrue(audit["valid"], f"Accounting audit violations: {audit['violations']}")
        self.assertIn(audit["tier"], ("T2", "T3"))
        self.assertEqual(audit["ceiling_usd"], 0.50)
        self.assertEqual(audit["target_usd"], 0.05)

    def test_woland_gate_quad_persistence(self) -> None:
        """Asserts WolandGate writes all 4 bundle files and a report of the measured values.

        Counterexample: the report used to be a fixed seven-act narrative ("Act I: Patriarch's
        Ponds" ... "Act VII") that printed 46 cases and 'Divergences: 0' whatever it was given."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            gate = WolandGate(task_key="c038_regge_combinatorial_curvature", base_dir=Path(tmp_dir))
            novella = gate.generate_novella(CONSISTENT, {"total_cases": 46, "agreements_count": 46})

            receipt = {"challenge_id": "c038_regge_combinatorial_curvature", "verdict": CONSISTENT}
            summary = {"challenge_id": "c038_regge_combinatorial_curvature", "cases": 46}
            dda_actions = [{"step": 1, "verdict": "PASS"}]

            targets = gate.persist_run_bundle(
                receipt=receipt,
                summary=summary,
                dda_actions=dda_actions,
                novella=novella,
            )

            for run_dir in (targets["woland_run_dir"], targets["symgam_run_dir"]):
                self.assertTrue(run_dir.is_dir())
                self.assertIn(Path(tmp_dir), run_dir.parents)
                for fname in CANONICAL_OUTPUT_FILES:
                    f = run_dir / fname
                    self.assertTrue(f.is_file(), f"Missing quad file: {fname} in {run_dir}")

                novella_content = (run_dir / "novella.md").read_text(encoding="utf-8")
                self.assertIn("| Judge cases scored | 46 |", novella_content)
                self.assertIn("| Cases with checker agreement | 46 |", novella_content)
                self.assertIn("| Cases with verdict PASS | not reported |", novella_content)
                self.assertNotIn("Act ", novella_content)

            unreported = gate.generate_novella(CONSISTENT, {})
            self.assertIn("| Judge cases scored | not reported |", unreported)
            self.assertNotIn("Divergences", unreported)

    def test_woland_gate_labels_come_from_exact_counts(self) -> None:
        """Counterexamples: an empty suite, one checker disagreement and a float Phi_1 must not be consistent,
        and a PASS_TO_MASTER label must be refused."""
        gate = WolandGate(base_dir=Path("unused"))
        self.assertEqual(gate.determine_terminal_verdict(0, 0, 0), INCONSISTENT)
        self.assertEqual(gate.determine_terminal_verdict(46, 46, 45), INCONSISTENT)
        self.assertEqual(gate.determine_terminal_verdict(46, 46, 46), CONSISTENT)
        with self.assertRaises(TypeError):
            gate.determine_terminal_verdict(46, 46, 46, phi1=0.0)
        with self.assertRaises(ValueError):
            gate.generate_novella("PASS_TO_MASTER", {})

    def test_woland_gate_never_replaces_a_run_folder(self) -> None:
        """Counterexample: every run wrote into the same runs/<task_key> folder and overwrote the previous bundle."""
        with (
            tempfile.TemporaryDirectory() as tmp_dir,
            mock.patch.object(woland_gate_module, "datetime", _Frozen),
        ):
            gate = WolandGate(task_key="c038_collision", base_dir=Path(tmp_dir))
            first = gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="first")
            with self.assertRaises(RunFolderExistsError):
                gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="second")
            self.assertEqual(
                (first["woland_run_dir"] / "novella.md").read_text(encoding="utf-8"), "first"
            )

    def test_commit_reveal_workflow(self) -> None:
        """Validates the Phase 1 -> Phase 2 -> Phase 3 pipeline on a temporary copy of the package."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            root = _temp_package(tmp_path)
            commitments = root / "commitments"

            p1 = phase1_commit_judge(challenge_dir=root)
            self.assertEqual(p1["phase"], "PHASE_1_JUDGE_COMMITMENT")
            self.assertEqual(p1["digest_normalization"], "CRLF_TO_LF")
            self.assertTrue((commitments / "c038_judge_commitment.json").is_file())

            p2 = phase2_freeze_solver(challenge_dir=root)
            self.assertEqual(p2["phase"], "PHASE_2_SOLVER_FREEZE")
            self.assertEqual(p2["phase1_binding_sha256"], p1["manifest_sha256"])
            self.assertTrue((commitments / "c038_freeze_record.json").is_file())

            p3 = phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
            self.assertEqual(p3["phase"], "PHASE_3_SCORING_RECEIPT")
            self.assertEqual(p3["verdict"], CONSISTENT)
            self.assertEqual(p3["gate_scope"], "REFERENCE_SOLVER_SELF_CHECK")
            self.assertTrue(p3["all_agreed"])
            self.assertTrue(p3["all_passed"])
            self.assertEqual(p3["total_cases"], 46)

            self.assertTrue(verify_commitments(challenge_dir=root))

    def test_phase3_refuses_a_case_file_missing_from_the_manifest(self) -> None:
        """Counterexample: Phase 3 scored every *.json under cases/, so a case file added after the
        judge commitment was scored and receipted. It must be refused with CASE_FILE_NOT_IN_MANIFEST."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            root = _temp_package(tmp_path)
            phase1_commit_judge(challenge_dir=root)
            phase2_freeze_solver(challenge_dir=root)
            base_cases = root / "judge_packet" / "cases" / "base"
            shutil.copyfile(sorted(base_cases.glob("*.json"))[0], base_cases / "zz_unlisted.json")
            with self.assertRaises(ManifestCustodyError) as info:
                phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
            self.assertEqual(info.exception.code, "CASE_FILE_NOT_IN_MANIFEST")
            self.assertFalse((tmp_path / "_intelligence").exists())

    def test_manifest_cryptographic_integrity_and_commit_sync(self) -> None:
        """Asserts judge_packet/manifest.json matches disk state and agrees with the Phase 1 commitment.

        Counterexample: digests were taken over raw bytes, so a CRLF checkout of an LF blob hashed
        differently; every digest here is over LF-normalised bytes, as the runner computes them."""
        manifest_file = CHALLENGE_DIR / "judge_packet" / "manifest.json"
        self.assertTrue(manifest_file.is_file())

        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        files_entry = manifest_data.get("files", [])
        self.assertEqual(len(files_entry), 100)

        # Ordinal UTF-8 ordering
        paths = [item["path"] for item in files_entry]
        self.assertEqual(paths, sorted(paths, key=lambda s: s.encode("utf-8")))

        # Check disk agreement over LF-normalised bytes
        judge_dir = CHALLENGE_DIR / "judge_packet"
        for item in files_entry:
            fpath = judge_dir / item["path"]
            self.assertTrue(fpath.is_file())
            data = lf_normalized_bytes(fpath)
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
            self.assertEqual(len(data), item["size_bytes"])

        # Check Phase 1 commitment if sealed
        commit_file = COMMITMENTS_DIR / "c038_judge_commitment.json"
        if commit_file.is_file():
            commit_data = json.loads(commit_file.read_text(encoding="utf-8"))
            self.assertEqual(
                commit_data.get("manifest_sha256"),
                _lf_sha256(manifest_file),
                "Phase 1 commitment sealed a manifest hash that differs from manifest.json on disk!",
            )

    def test_crlf_copy_hashes_like_the_lf_blob(self) -> None:
        """Counterexample: a CRLF copy of the manifest must hash like the LF blob it came from."""
        manifest_file = CHALLENGE_DIR / "judge_packet" / "manifest.json"
        with tempfile.TemporaryDirectory() as tmp_dir:
            crlf_copy = Path(tmp_dir) / "manifest.json"
            crlf_copy.write_bytes(lf_normalized_bytes(manifest_file).replace(b"\n", b"\r\n"))
            self.assertEqual(_lf_sha256(crlf_copy), _lf_sha256(manifest_file))


if __name__ == "__main__":
    unittest.main()
