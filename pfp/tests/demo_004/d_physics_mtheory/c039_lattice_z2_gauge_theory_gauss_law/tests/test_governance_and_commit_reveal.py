"""Tests for C039 Governance Gates & Cryptographic Commit-Reveal Protocol.

Verifies:
  1. BudgetGate enforcing Tier T3 ($1.00 ceiling, $0.10 target, zero fallbacks) in integer micro-USD.
  2. The reference self-consistency gate: a measured-values report and the four-file run bundle.
  3. Commit-Reveal protocol stages (Phase 1, Phase 2, Phase 3, verify) on a temporary package copy.
  4. Manifest disk agreement and Phase 1 commit synchronization over LF-normalised bytes.

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

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.governance import (
    adversary_gate as adversary_gate_module,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.governance.budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.governance.commit_reveal_runner import (
    ManifestCustodyError,
    lf_normalized_bytes,
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    verify_commitments,
    verify_manifest_entries,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.governance.adversary_gate import (
    RunFolderExistsError,
    AdversaryGate,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
ACCOUNTING_FILE = CHALLENGE_DIR / "participant_packet" / "accounting.json"
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


class _Frozen(adversary_gate_module.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 9, 29, 12, 0, 0, tzinfo=adversary_gate_module.timezone.utc)


class TestGovernanceAndCommitReveal(unittest.TestCase):
    """Verifies governance compliance and commit-reveal custody."""

    def test_budget_gate_t3_bounds(self) -> None:
        """BudgetGate must enforce Tier T3 bounds in integer micro-USD and disallow fallbacks.

        Counterexample: spend was accumulated as float USD and floats were accepted; a float or
        bool amount must now raise TypeError, and spend up to the exact ceiling is admitted."""
        gate = BudgetGate(ceiling_usd=1.00, target_usd=0.10, allow_fallbacks=False)
        self.assertEqual(gate.ceiling_usd, 1.00)
        self.assertEqual(gate.target_usd, 0.10)
        self.assertEqual(gate.ceiling_microusd, 1_000_000)
        self.assertEqual(gate.target_microusd, 100_000)

        # Pre-call ceiling enforcement (950,000 + 100,000 > 1,000,000 micro-USD)
        gate.record_call_cost(950_000)
        with self.assertRaises(BudgetCeilingExceededError):
            gate.check_pre_call(100_000)
        gate.check_pre_call(50_000)  # exactly at the ceiling
        self.assertEqual(gate.accumulated_cost_usd, Fraction(19, 20))
        for bad in (0.95, True):
            with self.assertRaises(TypeError):
                gate.record_call_cost(bad)
            with self.assertRaises(TypeError):
                gate.check_pre_call(bad)

        # Fallbacks strictly disallowed
        with self.assertRaises(FallbackNotAllowedError):
            BudgetGate(allow_fallbacks=True)

        # Above ceiling disallowed
        with self.assertRaises(BudgetCeilingExceededError):
            BudgetGate(ceiling_usd=1.50)

    def test_budget_gate_audits_accounting_json(self) -> None:
        """BudgetGate must audit participant accounting.json successfully."""
        self.assertTrue(ACCOUNTING_FILE.is_file())
        acc_data = json.loads(ACCOUNTING_FILE.read_text(encoding="utf-8"))
        gate = BudgetGate()
        audit = gate.audit_accounting_config(acc_data)
        self.assertTrue(audit["valid"], f"Accounting audit failed: {audit.get('violations')}")
        self.assertEqual(audit["tier"], "T3")
        self.assertEqual(audit["ceiling_usd"], 1.00)
        self.assertEqual(audit["target_usd"], 0.10)

    def test_adversary_gate_novella_and_quad_bundle(self) -> None:
        """The gate must render the measured values and persist the four-file bundle.

        Counterexample: the report used to be a fixed seven-act narrative that printed '48 hostile
        mutations', 'Kill rate certified: exactly 100%' and '(100.0% concordance)' whatever it was given."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            gate = AdversaryGate(
                task_key="c039_lattice_z2_gauge_theory_gauss_law",
                base_dir=tmp_root,
            )
            novella = gate.generate_novella(
                verdict=CONSISTENT,
                stats={
                    "total_cases": 48,
                    "agreements_count": 48,
                    "phi_1": 0,
                    "gamma_2": 0,
                    "defect_count": 0,
                },
            )
            for row in (
                "| Judge cases scored | 48 |",
                "| Cases with checker agreement | 48 |",
                "| Defect count | 0 |",
                "| Phi_1 (exact) | 0 |",
                "| Gamma_2 (exact) | 0 |",
            ):
                self.assertIn(row, novella)
            for narrative in ("Act ", "Kill rate", "100.0% concordance"):
                self.assertNotIn(narrative, novella)

            bundle_paths = gate.persist_run_bundle(
                receipt={"verdict": CONSISTENT, "cases": 48},
                summary={"verdict": CONSISTENT},
                dda_actions=[{"step": 1, "action": "test"}],
                novella=novella,
            )

            for key, run_dir in bundle_paths.items():
                self.assertTrue(run_dir.is_dir(), f"Run directory missing: {run_dir}")
                self.assertIn(tmp_root, run_dir.parents)
                self.assertTrue((run_dir / "novella.md").is_file())
                self.assertTrue((run_dir / "dda_actions.jsonl").is_file())
                self.assertTrue((run_dir / "summary.json").is_file())
                self.assertTrue((run_dir / "receipt.json").is_file())

    def test_adversary_gate_labels_come_from_exact_counts(self) -> None:
        """Counterexamples: an empty suite, one checker disagreement and a float Phi_1 must not be consistent,
        and a PASS_TO_MASTER label must be refused."""
        gate = AdversaryGate(base_dir=Path("unused"))
        self.assertEqual(gate.determine_terminal_verdict(0, 0, 0), INCONSISTENT)
        self.assertEqual(gate.determine_terminal_verdict(48, 48, 47), INCONSISTENT)
        self.assertEqual(gate.determine_terminal_verdict(48, 48, 48), CONSISTENT)
        with self.assertRaises(TypeError):
            gate.determine_terminal_verdict(48, 48, 48, phi1=0.0)
        with self.assertRaises(TypeError):
            gate.generate_novella(CONSISTENT, {"phi_1": 0.0})
        with self.assertRaises(ValueError):
            gate.generate_novella("PASS_TO_MASTER", {})

    def test_adversary_gate_never_replaces_a_run_folder(self) -> None:
        """Counterexample: every run wrote into the same runs/<task_key> folder and overwrote the previous bundle."""
        with (
            tempfile.TemporaryDirectory() as tmp_dir,
            mock.patch.object(adversary_gate_module, "datetime", _Frozen),
        ):
            gate = AdversaryGate(task_key="c039_collision", base_dir=Path(tmp_dir))
            first = gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="first")
            with self.assertRaises(RunFolderExistsError):
                gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="second")
            self.assertEqual(
                (first["adversary_run_dir"] / "novella.md").read_text(encoding="utf-8"), "first"
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
            self.assertTrue((commitments / "c039_judge_commitment.json").is_file())

            p2 = phase2_freeze_solver(challenge_dir=root)
            self.assertEqual(p2["phase"], "PHASE_2_SOLVER_FREEZE")
            self.assertEqual(p2["phase1_binding_sha256"], p1["manifest_sha256"])
            self.assertTrue((commitments / "c039_freeze_record.json").is_file())

            p3 = phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
            self.assertEqual(p3["phase"], "PHASE_3_SCORING_RECEIPT")
            self.assertEqual(p3["verdict"], CONSISTENT)
            self.assertEqual(p3["gate_scope"], "REFERENCE_SOLVER_SELF_CHECK")
            self.assertTrue(p3["all_agreed"])
            self.assertTrue(p3["all_passed"])
            self.assertEqual(p3["total_cases"], 48)

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
        self.assertEqual(len(files_entry), 102)

        # Ordinal UTF-8 ordering
        paths = [item["path"] for item in files_entry]
        self.assertEqual(paths, sorted(paths, key=lambda s: s.encode("utf-8")))

        # Check disk agreement over LF-normalised bytes
        judge_dir = CHALLENGE_DIR / "judge_packet"
        for item in files_entry:
            fpath = judge_dir / item["path"]
            self.assertTrue(fpath.is_file(), f"File {item['path']} missing on disk")
            data = lf_normalized_bytes(fpath)
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
            self.assertEqual(len(data), item["size_bytes"])

        # Check Phase 1 commitment if sealed
        commit_file = COMMITMENTS_DIR / "c039_judge_commitment.json"
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
