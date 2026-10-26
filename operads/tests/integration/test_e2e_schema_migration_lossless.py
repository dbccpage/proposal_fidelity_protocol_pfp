"""End-to-end multi-document schema migration test verifying lossless v1/v2 to v3 upgrade."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from omega_engine_operads.application.commands.compile_catalog import (
    CompileCatalogCommand,
)
from omega_engine_operads.domain.value_objects.identifier import SkillId
from omega_engine_operads.infrastructure.bootstrap import OeopContainer
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)
from omega_engine_operads.migration.skill_migrator import SkillMigratorV3


class TestE2ESchemaMigrationLossless(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "migrated_estate.db")
        self.migrator = SkillMigratorV3()
        self.parser = LosslessMarkdownParserAdapter()
        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )
        self.handler = self.container.compile_catalog_handler
        self.uow = self.container.uow

    def tearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    def test_multi_document_v1_v2_migration_and_catalog_compilation(self) -> None:
        # 1. Define 3 legacy documents (v1 YAML frontmatter, v2 prose + tables, v1 directive)
        legacy_docs = {
            "legacy-skill-audit": b"""---
name: legacy-skill-audit
description: Audits code receipts and returns proof status
version: 1.0.0
---
# Legacy Skill Audit
This is the original v1 prose body describing the audit procedure.

| Step | Action | Expected |
|---|---|---|
| 1 | Read Code | AST |
| 2 | Check Invariant | Receipt |
""",
            "legacy-skill-transform": b"""# Legacy Skill Transform (v2)
Transforms raw python AST to typed domain models.

## Directives
- Strict types
- No shims
""",
            "legacy-skill-publish": b"""---
title: Legacy Publish
tags: [release, deployment]
---
# Deployment Script
Publishes build artifacts to target directories.
""",
        }

        # 2. Migrate each document to v3 format and assert lossless preservation
        skills_dir = self.workspace_root / ".agents" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        for legacy_id, raw_bytes in legacy_docs.items():
            succ_id = f"consolidated-{legacy_id.replace('legacy-skill-', '')}"
            op_id = f"{succ_id}:execute"

            migrated_bytes = self.migrator.migrate_document_to_v3(
                legacy_content=raw_bytes,
                skill_id=legacy_id,
                successor_skill_id=succ_id,
                op_id=op_id,
                description=f"Migrated from {legacy_id}",
            )

            # Assert original raw bytes are completely preserved in the beginning of migrated bytes
            self.assertTrue(migrated_bytes.startswith(raw_bytes.rstrip()))

            # Parse with v3 parser and assert lossless AST reconstruction
            parse_res = self.parser.parse_document(SkillId(succ_id), f"skills/{succ_id}/SKILL.md", migrated_bytes)
            self.assertTrue(parse_res.is_ok, f"Failed to parse migrated document: {parse_res}")
            doc = parse_res.unwrap()

            # Ensure operation was extracted
            self.assertEqual(len(doc.operations), 1)
            self.assertEqual(str(doc.operations[0].operation_id), op_id)

            # Ensure 100% byte-slice roundtrip from AST leaf nodes
            reconstructed = b"".join(migrated_bytes[n.span.start_byte:n.span.end_byte] for n in doc.leaf_nodes)
            self.assertEqual(reconstructed, migrated_bytes)

            # Write to disk in workspace fixture for catalog compile
            sdir = skills_dir / succ_id
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_bytes(migrated_bytes)

        # 3. Compile the migrated estate catalog
        cmd = CompileCatalogCommand(
            estate_ref="canonical",
            correlation_id="corr-migration-test-01",
            causation_id="cause-migration-test",
            idempotency_key="idem-migration-01",
        )
        res = self.handler.handle(cmd)
        self.assertTrue(res.is_ok, f"Catalog compilation failed: {res}")
        dto = res.unwrap()

        # 4. Verify catalog properties
        self.assertEqual(dto.total_skills, 3)
        self.assertEqual(dto.total_operations, 3)
        self.assertEqual(dto.epoch, 1)

        # 5. Read back from SQLite WAL persistence engine
        catalog_opt = self.uow.get_latest_catalog()
        self.assertTrue(catalog_opt.is_ok)
        catalog = catalog_opt.unwrap()
        self.assertEqual(len(catalog.skills), 3)
        self.assertEqual(len(catalog.operations), 3)

        # 6. Verify idempotency on second run
        res2 = self.handler.handle(cmd)
        self.assertTrue(res2.is_ok)
        dto2 = res2.unwrap()
        self.assertEqual(dto.catalog_id, dto2.catalog_id)
        self.assertEqual(dto.catalog_digest, dto2.catalog_digest)


if __name__ == "__main__":
    unittest.main()
