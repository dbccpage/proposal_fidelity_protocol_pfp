"""Verify declared legacy mappings against their current successor mirrors."""

import hashlib
import json
import pathlib
import tempfile
import unittest
from omega_engine_operads.domain.value_objects import SkillId
from omega_engine_operads.migration.skill_migrator import SkillMigratorV3

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


class GooMigrationManifestParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.migrator = SkillMigratorV3()

    def test_manifest_contains_41_entries(self) -> None:
        self.assertEqual(len(self.migrator.manifest["entries"]), 41)

    def test_all_41_manifest_hashes_match_disk(self) -> None:
        res = self.migrator.verify_manifest_hashes(REPO_ROOT)
        self.assertTrue(res.is_ok, f"Hash verification failed: {res}")
        self.assertEqual(res.unwrap(), 41)

    def test_manifest_rejects_drift_in_any_required_mirror(self) -> None:
        canonical_bytes = b"# Mirror-safe skill\n"
        entry = {
            "legacy_skill_id": "example-skill",
            "successor_skill_id": "example-successor",
            "operation_id": "example-successor:run",
            "blob_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
            "byte_count": len(canonical_bytes),
            "hosts": {
                ".agents": True,
                ".claude": True,
                ".codex": True,
                ".grok": True,
            },
            "all_4_hosts_agree": True,
            "residual_status": "unknown",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            for host in (".agents", ".claude", ".codex", ".grok"):
                target = root / host / "skills" / "example-successor" / "SKILL.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(
                    b"# Tampered mirror\n" if host == ".grok" else canonical_bytes
                )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "total_entries": 1,
                        "entries": [entry],
                        "artifact_binding": "SUCCESSOR_SKILL_BYTES",
                        "mapping_status": "DECLARED_UNADMITTED",
                    }
                ),
                encoding="utf-8",
            )

            result = SkillMigratorV3(manifest_path).verify_manifest_hashes(root)

        self.assertTrue(result.is_err)
        self.assertIn(".grok/example-successor", result.unwrap_err().message)

    def test_compile_migrated_capability_slices_produces_valid_v3_slices(self) -> None:
        res = self.migrator.compile_migrated_capability_slices(REPO_ROOT)
        self.assertTrue(res.is_ok)
        slices = res.unwrap()
        self.assertGreater(len(slices), 0)

        # Verify blackrod slice contains operations
        self.assertIn(SkillId("blackrod"), slices)
        blackrod_slice = slices[SkillId("blackrod")]
        self.assertGreater(len(blackrod_slice.operation_ids), 0)

        # Verify rip-python slice contains operations
        self.assertIn(SkillId("rip-python"), slices)
        py_slice = slices[SkillId("rip-python")]
        self.assertGreater(len(py_slice.operation_ids), 0)

    def test_generated_migration_block_is_explicitly_unadmitted(self) -> None:
        rendered = self.migrator.migrate_document_to_v3(
            b"# Legacy source\n",
            "legacy-skill",
            "successor-skill",
            "successor-skill:declared-operation",
        ).decode("utf-8")
        self.assertIn('schema_binding: "Unbound"', rendered)
        self.assertIn('executor_binding: "Unbound"', rendered)
        self.assertIn('validation: "Unchecked"', rendered)
        self.assertIn('admission: "Unadmitted"', rendered)
        self.assertIn('residual_status: "unknown"', rendered)
        self.assertNotIn('admission: "Admitted"', rendered)
