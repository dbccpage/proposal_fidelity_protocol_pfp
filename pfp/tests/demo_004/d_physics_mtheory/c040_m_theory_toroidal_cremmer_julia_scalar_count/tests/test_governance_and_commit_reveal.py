"""Tests for C040 Governance and Cryptographic Commit-Reveal Protocol.

Validates BudgetGate (integer micro-USD), the reference self-consistency gate
and its run bundle, the commit-reveal pipeline, and manifest integrity.

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

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.governance import (
    woland_gate as woland_gate_module,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.governance.budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.governance.commit_reveal_runner import (
    ManifestCustodyError,
    lf_normalized_bytes,
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    sha256_file,
    verify_commitments,
    verify_manifest_entries,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.governance.woland_gate import (
    CANONICAL_OUTPUT_FILES,
    RunFolderExistsError,
    WolandGate,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
CONSISTENT = "REFERENCE_SELF_CONSISTENT"
INCONSISTENT = "REFERENCE_SELF_INCONSISTENT"


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
    """Test suite for Tier T4 governance and commit-reveal runner."""

    def test_budget_gate_tier_t4_enforcement(self) -> None:
        """BudgetGate must enforce ceiling $2.00, target $0.20, no fallbacks, <= 70B, in integer micro-USD.

        Counterexample: spend was accumulated as float USD and floats were accepted; a float or
        bool amount must now raise TypeError."""
        gate = BudgetGate(ceiling_usd=2.00, target_usd=0.20, allow_fallbacks=False)
        self.assertEqual(gate.ceiling_usd, 2.00)
        self.assertEqual(gate.target_usd, 0.20)
        self.assertEqual(gate.ceiling_microusd, 2_000_000)
        self.assertFalse(gate.allow_fallbacks)

        # Pre-call checks
        gate.check_pre_call(150_000)
        gate.record_call_cost(150_000)

        # Near ceiling call
        gate.check_pre_call(1_800_000)
        gate.record_call_cost(1_800_000)
        self.assertEqual(gate.accumulated_cost_usd, Fraction(39, 20))

        # Breaching call (1,950,000 + 100,000 > 2,000,000 micro-USD)
        with self.assertRaises(BudgetCeilingExceededError):
            gate.check_pre_call(100_000)
        gate.check_pre_call(50_000)  # exactly at the ceiling

        for bad in (0.15, True):
            with self.assertRaises(TypeError):
                gate.check_pre_call(bad)
            with self.assertRaises(TypeError):
                gate.record_call_cost(bad)

        # Fallback rejected
        with self.assertRaises(FallbackNotAllowedError):
            BudgetGate(allow_fallbacks=True)

        # Audit accounting.json
        accounting_file = CHALLENGE_DIR / "participant_packet" / "accounting.json"
        accounting_data = json.loads(accounting_file.read_text(encoding="utf-8"))
        audit_res = gate.audit_accounting_config(accounting_data)
        self.assertTrue(audit_res["valid"], f"Accounting audit failed: {audit_res['violations']}")

    def test_woland_gate_novella_and_quad_bundle(self) -> None:
        """The gate must render the measured values and persist the four-file bundle to both run stores.

        Counterexample: the report used to be a fixed seven-act narrative that printed 'forty-eight
        hostile mutations' and 'Kill rate certified: exactly 100%' whatever it was given."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_repo = Path(tmp_dir)
            gate = WolandGate(task_key="c040_test_run", base_dir=test_repo)

            novella = gate.generate_novella(
                verdict=CONSISTENT,
                stats={
                    "total_cases": 46,
                    "agreements_count": 46,
                    "phi_1": 0,
                    "gamma_2": 0,
                    "defect_count": 0,
                },
            )
            for row in (
                "| Judge cases scored | 46 |",
                "| Cases with checker agreement | 46 |",
                "| Defect count | 0 |",
                "| Phi_1 (exact) | 0 |",
                "| Gamma_2 (exact) | 0 |",
            ):
                self.assertIn(row, novella)
            for narrative in ("Act ", "Kill rate", "concordance"):
                self.assertNotIn(narrative, novella)

            receipt = {"challenge_id": "c040_test", "verdict": CONSISTENT}
            summary = {"total_cases": 46, "verdict": CONSISTENT}
            dda_actions = [{"step": 1, "verdict": "PASS"}]

            res_paths = gate.persist_run_bundle(
                receipt=receipt,
                summary=summary,
                dda_actions=dda_actions,
                novella=novella,
            )

            for key in ["woland_run_dir", "symgam_run_dir"]:
                d = res_paths[key]
                self.assertTrue(d.is_dir(), f"Sink dir not created: {d}")
                self.assertIn(test_repo, d.parents)
                for fname in CANONICAL_OUTPUT_FILES:
                    f = d / fname
                    self.assertTrue(f.is_file(), f"Quad bundle file missing: {f}")

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
            gate = WolandGate(task_key="c040_collision", base_dir=Path(tmp_dir))
            first = gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="first")
            with self.assertRaises(RunFolderExistsError):
                gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="second")
            self.assertEqual(
                (first["woland_run_dir"] / "novella.md").read_text(encoding="utf-8"), "first"
            )

    def test_commit_reveal_state_machine_and_verification(self) -> None:
        """Runs the 3 phases of commit-reveal on a temporary copy of the package and verifies the records."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            root = _temp_package(tmp_path)

            # Phase 1
            p1 = phase1_commit_judge(challenge_dir=root)
            self.assertEqual(p1["phase"], "PHASE_1_JUDGE_COMMITMENT")
            self.assertEqual(
                p1["manifest_sha256"], sha256_file(root / "judge_packet" / "manifest.json")
            )

            # Phase 2
            p2 = phase2_freeze_solver(challenge_dir=root)
            self.assertEqual(p2["phase"], "PHASE_2_SOLVER_FREEZE")
            self.assertIn("solver_freeze_sha256", p2)
            self.assertEqual(p2["phase1_binding_sha256"], p1["manifest_sha256"])

            # Phase 3
            p3 = phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
            self.assertEqual(p3["phase"], "PHASE_3_SCORING_RECEIPT")
            self.assertEqual(p3["case_count"], 46)
            self.assertEqual(p3["dual_passes"], 46)
            self.assertEqual(p3["dual_agreements"], 46)
            self.assertEqual(p3["verdict"], CONSISTENT)
            self.assertEqual(p3["gate_scope"], "REFERENCE_SOLVER_SELF_CHECK")

            # Verify command
            ok = verify_commitments(challenge_dir=root)
            self.assertTrue(ok, "Commit-reveal verification failed")

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
        """Asserts c040_judge_commitment.json records the manifest_sha256 of manifest.json (LF-normalised)."""
        manifest_file = JUDGE_DIR / "manifest.json"
        p1_file = COMMITMENTS_DIR / "c040_judge_commitment.json"
        self.assertTrue(manifest_file.is_file())
        self.assertTrue(p1_file.is_file())

        real_hash = sha256_file(manifest_file)
        p1_data = json.loads(p1_file.read_text(encoding="utf-8"))
        self.assertEqual(
            real_hash,
            p1_data["manifest_sha256"],
            "Commitment record manifest_sha256 does not match disk manifest.json",
        )

    def test_crlf_copy_hashes_like_the_lf_blob(self) -> None:
        """Counterexample: a CRLF copy of the manifest must hash like the LF blob it came from."""
        manifest_file = JUDGE_DIR / "manifest.json"
        with tempfile.TemporaryDirectory() as tmp_dir:
            crlf_copy = Path(tmp_dir) / "manifest.json"
            crlf_copy.write_bytes(lf_normalized_bytes(manifest_file).replace(b"\n", b"\r\n"))
            self.assertEqual(sha256_file(crlf_copy), sha256_file(manifest_file))


if __name__ == "__main__":
    unittest.main()
