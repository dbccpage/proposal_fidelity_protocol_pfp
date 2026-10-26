"""Unit and integration tests for the Omega Autopoiesis Engine.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from omega_engine_operads.application.autopoiesis import AutopoieticHarvester
from omega_engine_operads.domain.autopoiesis.entities import (
    HarvestRecord,
    HarvestSnapshot,
    MinedAntibody,
    MinedSkillProposal,
)
from omega_engine_operads.frontend.cli.harvest_cli import run_harvest_cli
from omega_engine_operads.infrastructure.autopoiesis import (
    FileHarvestVault,
    JsonPharmacyAdapter,
    MarkdownSkillsAdapter,
)
from omega_engine_operads.infrastructure.autopoiesis.harvest_source import (
    FilesystemHarvestSource,
)


class TestAutopoieticHarvest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.vault_dir = self.root / "harvest"
        self.teamwork_dir = self.root / "teamwork"
        self.antibodies_dir = self.root / "antibodies"
        self.skills_dir = self.root / "skills"

        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.teamwork_dir.mkdir(parents=True, exist_ok=True)
        self.antibodies_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        self.register_path = self.skills_dir / "proposed_skills_register.md"
        self.register_path.write_text(
            "# Proposed Skills Register\n\n### Entry 0001: `existing-skill`\n- **Status:** `ADMITTED`\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_cas_vault_put_and_get(self) -> None:
        vault = FileHarvestVault(self.vault_dir)
        content = b"hello autopoiesis world"
        digest = hashlib.sha256(content).hexdigest()

        # First put
        written = vault.put_file(content, digest)
        self.assertTrue(written)

        # Second put (deduplicated)
        written_again = vault.put_file(content, digest)
        self.assertFalse(written_again)

        # Retrieval
        retrieved = vault.get_file(digest)
        self.assertEqual(retrieved, content)

    def test_snapshot_manifest_and_merkle(self) -> None:
        vault = FileHarvestVault(self.vault_dir)
        rec1 = HarvestRecord(relative_path="a.txt", sha256="abc", byte_size=10, file_type="txt")
        rec2 = HarvestRecord(relative_path="b.txt", sha256="def", byte_size=20, file_type="txt")

        snap = HarvestSnapshot.create("snap_test", "test_source", [rec1, rec2])
        self.assertIsNotNone(snap.merkle_root)
        self.assertEqual(len(snap.records), 2)

        vault.save_snapshot(snap)
        loaded = vault.get_snapshot("snap_test")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.snapshot_id, "snap_test")
        self.assertEqual(loaded.merkle_root, snap.merkle_root)
        self.assertEqual(len(loaded.records), 2)

    def test_pharmacy_adapter_merge(self) -> None:
        adapter = JsonPharmacyAdapter(self.antibodies_dir)
        ab = MinedAntibody(
            antibody_id="ab_test_defect",
            failure_class="test:defect",
            target_pattern="test:defect",
            constraint_type="Reject",
            operatorizability="repairable",
            action="refuse",
            severity="P0",
            description="Test antibody description",
            negative_fixture="bad",
            positive_fixture="good",
            source_file="test.py",
            evidence_sha256="12345",
        )

        # First merge
        count = adapter.merge_antibodies([ab])
        self.assertEqual(count, 1)

        catalog = adapter.load_catalog()
        self.assertIn("ab_test_defect", catalog["antibodies"])
        self.assertEqual(catalog["antibodies"]["ab_test_defect"]["times_seen"], 1)

        # Second merge (increments times_seen)
        adapter.merge_antibodies([ab])
        catalog2 = adapter.load_catalog()
        self.assertEqual(catalog2["antibodies"]["ab_test_defect"]["times_seen"], 2)

    def test_skills_adapter_append(self) -> None:
        adapter = MarkdownSkillsAdapter(self.register_path)
        existing = adapter.load_proposed_skills()
        self.assertIn("existing-skill", existing)

        proposal = MinedSkillProposal(
            skill_id="new-mined-skill",
            title="New Mined Skill",
            lead_council="L3_logos_techne",
            scope="Testing mined skill append.",
            origin_agent_role="challenger",
            confidence="HIGH",
            source_artifacts=["challenger/test.py"],
            suggested_checks=["check_something"],
        )

        appended = adapter.append_skill_proposals([proposal])
        self.assertEqual(appended, 1)

        updated = adapter.load_proposed_skills()
        self.assertIn("new-mined-skill", updated)

        # Idempotent (does not re-append)
        appended_again = adapter.append_skill_proposals([proposal])
        self.assertEqual(appended_again, 0)

    def test_autopoietic_harvester_full_pipeline(self) -> None:
        # Create mock teamwork directory structure
        challenger_dir = self.teamwork_dir / "challenger_1"
        challenger_dir.mkdir(parents=True)
        (challenger_dir / "verify_refusal_bypass.py").write_text(
            "# refusal bypass test\n", encoding="utf-8"
        )
        (challenger_dir / "BRIEFING.md").write_text("# Mission Briefing\n", encoding="utf-8")

        # Create mock antibody directory
        ab_sample = {
            "antibody_id": "ab_existing_one",
            "failure_class": "defect:zero",
            "target_pattern": "defect:zero",
            "severity": "P1",
        }
        (self.antibodies_dir / "ab_existing_one.json").write_text(
            json.dumps(ab_sample), encoding="utf-8"
        )

        vault = FileHarvestVault(self.vault_dir)
        pharmacy = JsonPharmacyAdapter(self.antibodies_dir)
        skills = MarkdownSkillsAdapter(self.register_path)
        harvester = AutopoieticHarvester(vault, pharmacy, skills, source=FilesystemHarvestSource())

        receipt = harvester.harvest_all(self.teamwork_dir, self.antibodies_dir)

        self.assertGreater(receipt.teamwork_files_preserved, 0)
        self.assertGreater(receipt.antibodies_cataloged, 0)
        self.assertGreater(receipt.skills_mined, 0)
        self.assertGreater(receipt.antibodies_mined, 0)
        self.assertEqual(receipt.authority_effect, "None")

    def test_cli_invocation(self) -> None:
        # Create mock file in teamwork
        (self.teamwork_dir / "test.txt").write_text("data", encoding="utf-8")
        (self.antibodies_dir / "ab.json").write_text("{}", encoding="utf-8")

        # 1. Ingest
        exit_code = run_harvest_cli(
            [
                "ingest-all",
                "--teamwork-dir",
                str(self.teamwork_dir),
                "--antibodies-dir",
                str(self.antibodies_dir),
                "--vault-dir",
                str(self.vault_dir),
                "--skills-register",
                str(self.register_path),
            ]
        )
        self.assertEqual(exit_code, 0)

        # 2. Status
        exit_code_status = run_harvest_cli(
            [
                "status",
                "--vault-dir",
                str(self.vault_dir),
            ]
        )
        self.assertEqual(exit_code_status, 0)

        # 3. Verify
        exit_code_verify = run_harvest_cli(
            [
                "verify-vault",
                "--vault-dir",
                str(self.vault_dir),
            ]
        )
        self.assertEqual(exit_code_verify, 0)

    def test_pre_clean_teamwork_verification_and_safe_clear(self) -> None:
        agent_dir = self.teamwork_dir / "worker_m1"
        agent_dir.mkdir(parents=True)
        (agent_dir / "handoff.md").write_bytes(b"# Handoff\nImportant work.")

        vault = FileHarvestVault(self.vault_dir)
        pharmacy = JsonPharmacyAdapter(self.antibodies_dir)
        skills = MarkdownSkillsAdapter(self.register_path)
        harvester = AutopoieticHarvester(vault, pharmacy, skills, source=FilesystemHarvestSource())

        # Pre-clean with clear_after=True
        receipt, cleared = harvester.pre_clean_teamwork(
            self.teamwork_dir, self.antibodies_dir, clear_after=True
        )
        self.assertGreater(receipt.teamwork_files_preserved, 0)
        self.assertEqual(cleared, 1)

        # Teamwork dir should only contain .gitkeep
        remaining = list(self.teamwork_dir.iterdir())
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].name, ".gitkeep")

        # But in CAS, the handoff.md must be fully recoverable!
        hand_hash = hashlib.sha256(b"# Handoff\nImportant work.").hexdigest()
        recovered = vault.get_file(hand_hash)
        self.assertEqual(recovered, b"# Handoff\nImportant work.")

    def test_cli_pre_clean_invocation(self) -> None:
        agent_dir = self.teamwork_dir / "auditor_1"
        agent_dir.mkdir(parents=True)
        (agent_dir / "BRIEFING.md").write_text("# Briefing\nData.", encoding="utf-8")

        exit_code = run_harvest_cli(
            [
                "pre-clean-teamwork",
                "--teamwork-dir",
                str(self.teamwork_dir),
                "--antibodies-dir",
                str(self.antibodies_dir),
                "--vault-dir",
                str(self.vault_dir),
                "--skills-register",
                str(self.register_path),
                "--clear-after",
            ]
        )
        self.assertEqual(exit_code, 0)

        remaining = list(self.teamwork_dir.iterdir())
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].name, ".gitkeep")

    def test_live_multi_agent_teamwork_concluding_run_clear_after(self) -> None:
        """Simulates a live multi-agent teamwork session concluding with pre-clean-teamwork --clear-after."""
        # 1. Active Run Setup: Multiple agent workspaces
        orchestrator_dir = self.teamwork_dir / "lead_orchestrator"
        worker_dir = self.teamwork_dir / "worker_builder"
        challenger_dir = self.teamwork_dir / "challenger_prosecutor"
        auditor_dir = self.teamwork_dir / "verifier_auditor"

        for d in (orchestrator_dir, worker_dir, challenger_dir, auditor_dir):
            d.mkdir(parents=True)

        payloads = {
            orchestrator_dir
            / "BRIEFING.md": b"# Briefing\nDecompose task into builder, challenger, auditor.",
            orchestrator_dir / "DISPATCH.md": b"# Dispatch\nAllocating roles to subagents.",
            worker_dir
            / "candidate_solution.py": b"def solve():\n    return {'status': 'success'}\n",
            worker_dir / "handoff.md": b"# Handoff\nCandidate solution implemented and tested.",
            challenger_dir
            / "verify_refusal_bypass.py": b"# Adversarial Refusal Test\nassert refusal_check() == 'REFUSE'\n",
            challenger_dir / "counterexample.json": b'{"case": "bypass_attempt", "blocked": true}',
            auditor_dir
            / "check_facades_ast.py": b"# AST Checker\nimport ast\n# Verifies zero facades\n",
            auditor_dir / "VERIFICATION_REPORT.md": b"# Verification Report\nAll 8 checks passed.",
            auditor_dir / "receipt.json": b'{"verdict": "AUTHORIZED", "audit_complete": true}',
        }

        for path, content in payloads.items():
            path.write_bytes(content)

        # 2. Conclude active run by invoking harvest_cli pre-clean-teamwork --clear-after
        exit_code = run_harvest_cli(
            [
                "pre-clean-teamwork",
                "--teamwork-dir",
                str(self.teamwork_dir),
                "--antibodies-dir",
                str(self.antibodies_dir),
                "--vault-dir",
                str(self.vault_dir),
                "--skills-register",
                str(self.register_path),
                "--clear-after",
            ]
        )
        self.assertEqual(exit_code, 0)

        # 3. Invariant: Teamwork directory is cleanly cleared down to .gitkeep
        remaining_items = list(self.teamwork_dir.iterdir())
        self.assertEqual(len(remaining_items), 1)
        self.assertEqual(remaining_items[0].name, ".gitkeep")

        # 4. Invariant: 100% of multi-agent files are bit-for-bit recoverable from CAS
        vault = FileHarvestVault(self.vault_dir)
        for path, original_bytes in payloads.items():
            digest = hashlib.sha256(original_bytes).hexdigest()
            recovered = vault.get_file(digest)
            self.assertIsNotNone(recovered, f"File {path.name} was not saved in CAS!")
            self.assertEqual(recovered, original_bytes, f"Content mismatch for {path.name}")

        # 5. Invariant: Skills & antibodies mined from live multi-agent artifacts
        reg_content = self.register_path.read_text(encoding="utf-8")
        self.assertIn("techne-adversarial-refusal-bypass-auditor", reg_content)
        self.assertIn("techne-ast-anti-mock-and-facade-auditor", reg_content)

        pharmacy_content = (self.antibodies_dir / "pharmacy_catalog.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("ab_adversarial_refusal_bypass_leakage", pharmacy_content)

    def test_pre_clean_refusal_when_cas_verification_fails(self) -> None:
        """Simulates corrupted CAS storage: pre-clean MUST refuse to clear if CAS verification fails."""
        agent_dir = self.teamwork_dir / "critical_agent"
        agent_dir.mkdir(parents=True)
        target_file = agent_dir / "unrecoverable_work.py"
        target_file.write_bytes(b"# Critical Agent Work That Must Not Be Lost")

        # Mock a broken vault that fails get_file
        class CorruptedVault(FileHarvestVault):
            def get_file(self, sha256_digest: str) -> bytes | None:
                return None  # Pretend CAS retrieval failed

        broken_vault = CorruptedVault(self.vault_dir)
        pharmacy = JsonPharmacyAdapter(self.antibodies_dir)
        skills = MarkdownSkillsAdapter(self.register_path)
        harvester = AutopoieticHarvester(
            broken_vault, pharmacy, skills, source=FilesystemHarvestSource()
        )

        with self.assertRaises(RuntimeError) as ctx:
            harvester.pre_clean_teamwork(self.teamwork_dir, self.antibodies_dir, clear_after=True)

        self.assertIn("PRE_CLEAN_REFUSAL", str(ctx.exception))
        # Files MUST still be on disk! Zero data loss guaranteed!
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_bytes(), b"# Critical Agent Work That Must Not Be Lost")

    def test_cas_rejects_wrong_digest_and_corrupted_existing_object(self) -> None:
        vault = FileHarvestVault(self.vault_dir)
        digest = hashlib.sha256(b"original").hexdigest()
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            vault.put_file(b"wrong", digest)
        vault.put_file(b"original", digest)
        (vault.vault_dir / digest[:2] / digest).write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            vault.get_file(digest)
        with self.assertRaisesRegex(ValueError, "existing content differs"):
            vault.put_file(b"original", digest)

    def test_corruption_preserves_source_during_pre_clean(self) -> None:
        source = self.teamwork_dir / "critical.txt"
        source.write_bytes(b"original")
        digest = hashlib.sha256(b"original").hexdigest()
        vault = FileHarvestVault(self.vault_dir)
        vault.put_file(b"original", digest)
        (vault.vault_dir / digest[:2] / digest).write_bytes(b"corrupt")
        harvester = AutopoieticHarvester(
            vault,
            JsonPharmacyAdapter(self.antibodies_dir),
            MarkdownSkillsAdapter(self.register_path),
            source=FilesystemHarvestSource(),
        )
        with self.assertRaises(ValueError):
            harvester.pre_clean_teamwork(self.teamwork_dir, self.antibodies_dir, clear_after=True)
        self.assertEqual(source.read_bytes(), b"original")

    def test_digest_and_snapshot_ids_cannot_escape_vault(self) -> None:
        vault = FileHarvestVault(self.vault_dir)
        with self.assertRaises(ValueError):
            vault.get_file("../outside")
        with self.assertRaises(ValueError):
            vault.get_snapshot("../outside")

    def test_snapshots_are_immutable_and_tampering_is_rejected(self) -> None:
        vault = FileHarvestVault(self.vault_dir)
        a = HarvestSnapshot.create("fixed", "a", [], "fixed-time")
        b = HarvestSnapshot.create("fixed", "b", [], "fixed-time")
        path = vault.save_snapshot(a)
        with self.assertRaisesRegex(ValueError, "existing content differs"):
            vault.save_snapshot(b)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["merkle_root"] = "0" * 64
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot binding mismatch"):
            vault.get_snapshot("fixed")

    def test_pre_clean_archives_previously_skipped_cache_files(self) -> None:
        cache = self.teamwork_dir / "__pycache__"
        cache.mkdir()
        (cache / "valuable.pyc").write_bytes(b"also preserve this")
        vault = FileHarvestVault(self.vault_dir)
        harvester = AutopoieticHarvester(
            vault,
            JsonPharmacyAdapter(self.antibodies_dir),
            MarkdownSkillsAdapter(self.register_path),
            source=FilesystemHarvestSource(),
        )
        harvester.pre_clean_teamwork(self.teamwork_dir, self.antibodies_dir, clear_after=True)
        self.assertEqual(
            vault.get_file(hashlib.sha256(b"also preserve this").hexdigest()), b"also preserve this"
        )

    def test_same_byte_symlink_is_refused(self) -> None:
        vault = FileHarvestVault(self.vault_dir)
        payload = self.root / "payload"
        payload.write_bytes(b"same bytes")
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        obj = vault.vault_dir / digest[:2] / digest
        obj.parent.mkdir()
        obj.symlink_to(payload)
        with self.assertRaisesRegex(ValueError, "non-regular"):
            vault.get_file(digest)
        source_link = self.teamwork_dir / "link"
        source_link.symlink_to(payload)
        harvester = AutopoieticHarvester(
            vault,
            JsonPharmacyAdapter(self.antibodies_dir),
            MarkdownSkillsAdapter(self.register_path),
            source=FilesystemHarvestSource(),
        )
        with self.assertRaisesRegex(RuntimeError, "linked source"):
            harvester.pre_clean_teamwork(self.teamwork_dir, self.antibodies_dir, clear_after=True)
        self.assertTrue(payload.exists())

    def test_new_file_after_cas_verification_prevents_cleanup(self) -> None:
        source = self.teamwork_dir / "critical.txt"
        source.write_bytes(b"original")
        new_source = self.teamwork_dir / "arrived-late.txt"

        class MutatingVault(FileHarvestVault):
            def get_file(self, digest: str) -> bytes | None:
                result = super().get_file(digest)
                new_source.write_bytes(b"not in the snapshot")
                return result

        harvester = AutopoieticHarvester(
            MutatingVault(self.vault_dir),
            JsonPharmacyAdapter(self.antibodies_dir),
            MarkdownSkillsAdapter(self.register_path),
            source=FilesystemHarvestSource(),
        )
        with self.assertRaisesRegex(RuntimeError, "source changed"):
            harvester.pre_clean_teamwork(self.teamwork_dir, self.antibodies_dir, clear_after=True)
        self.assertTrue(source.exists())
        self.assertTrue(new_source.exists())


if __name__ == "__main__":
    unittest.main()
