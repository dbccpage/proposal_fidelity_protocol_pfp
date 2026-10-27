"""Integration test verifying transactional atomicity and rollback for outbox and events."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from operations.domain.rop.result import Err, Ok
from operads.application.commands.compile_catalog import (
    CompileCatalogCommand,
)
from operads.domain.entities.catalog_v3 import EstateCatalogV3
from operads.domain.events.domain_events import (
    DocumentImportedV3,
    EstateCapturedV3,
)
from operads.domain.errors.domain_errors import DomainInvariantError
from operads.domain.value_objects.content_digest import ContentDigest
from operads.domain.value_objects.identifier import (
    EstateRef,
    IdempotencyKey,
)
from operads.infrastructure.bootstrap import OeopContainer


class TestOutboxTransactionAtomicity(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "atomicity_test.db")
        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )
        self.uow = self.container.uow

    def tearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    def test_mid_stream_exception_rolls_back_outbox_and_events_completely(self) -> None:
        """If an exception occurs mid-transaction, no partial outbox entries or events should leak."""
        now = datetime.now(timezone.utc)

        # Create 3 valid events and 1 faulty object that raises an error during serialization
        event1 = EstateCapturedV3.create(
            event_id="evt_01",
            correlation_id="corr-atom-01",
            causation_id="cause-atom-01",
            estate_ref=EstateRef("canonical"),
        )
        event2 = DocumentImportedV3.create(
            event_id="evt_02",
            correlation_id="corr-atom-01",
            causation_id="cause-atom-01",
        )

        class FaultyEvent:
            @property
            def event_id(self) -> str:
                raise RuntimeError("Simulated serialization crash during outbox emission")

        faulty_event = FaultyEvent()

        catalog = EstateCatalogV3(
            catalog_id="cat_fail_01",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=now,
            skills={},
            operations={},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.empty_sha256(),
        )

        # Attempt to save catalog with faulty event stream
        res = self.uow.save_catalog(
            catalog=catalog,
            events=(event1, event2, faulty_event),  # type: ignore
            idempotency_key=IdempotencyKey("idem-fail-01"),
            request_digest="req_digest_01",
            response_data={"status": "should_never_persist"},
        )

        # Must return an error result
        self.assertTrue(res.is_err, "UoW commit should have failed")
        err = res.unwrap_err()
        self.assertEqual(err.code, "UOW_COMMIT_FAILED")

        # Directly query SQLite database to assert 100% rollback across all tables
        with self.uow._conn:
            cur = self.uow._conn.execute("SELECT count(*) as c FROM catalogs_v3")
            self.assertEqual(cur.fetchone()["c"], 0, "catalogs_v3 must be empty after rollback")

            cur = self.uow._conn.execute("SELECT count(*) as c FROM events_v3")
            self.assertEqual(cur.fetchone()["c"], 0, "events_v3 must be empty after rollback")

            cur = self.uow._conn.execute("SELECT count(*) as c FROM outbox_v3")
            self.assertEqual(cur.fetchone()["c"], 0, "outbox_v3 must be empty after rollback")

            cur = self.uow._conn.execute("SELECT count(*) as c FROM idempotency_v3")
            self.assertEqual(cur.fetchone()["c"], 0, "idempotency_v3 must be empty after rollback")

    def test_handler_failure_leaves_outbox_unmodified(self) -> None:
        """If compilation handler encounters an invalid skill, zero outbox entries are committed."""
        # Create an invalid skill file that fails parsing
        skills_dir = self.workspace_root / ".agents" / "skills" / "bad-skill"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "SKILL.md").write_text(
            """# Bad Skill
```oewas.operation.v3
inputs: [ unclosed
```
""",
            encoding="utf-8",
        )

        cmd = CompileCatalogCommand(
            estate_ref="canonical",
            correlation_id="corr-bad-01",
            causation_id="cause-bad-01",
            idempotency_key="idem-bad-01",
        )

        with patch.object(
            self.container.estate_source,
            "list_skill_paths",
            return_value=Ok((".agents/skills/bad-skill/SKILL.md",)),
        ):
            res = self.container.compile_catalog_handler.handle(cmd)
        self.assertTrue(res.is_err, "Handler should return error on malformed YAML")

        # Assert no outbox entries or catalogs were committed
        with self.uow._conn:
            cur = self.uow._conn.execute("SELECT count(*) as c FROM outbox_v3")
            self.assertEqual(cur.fetchone()["c"], 0)
            cur = self.uow._conn.execute("SELECT count(*) as c FROM catalogs_v3")
            self.assertEqual(cur.fetchone()["c"], 0)

    def test_handler_refuses_an_unreadable_skill_instead_of_skipping_it(self) -> None:
        skills_dir = self.workspace_root / ".agents" / "skills" / "unreadable-skill"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "SKILL.md").write_text("# Unreadable\n", encoding="utf-8")

        with patch.object(
            self.container.estate_source,
            "list_skill_paths",
            return_value=Ok((".agents/skills/unreadable-skill/SKILL.md",)),
        ), patch.object(
            self.container.estate_source,
            "read_skill_bytes",
            return_value=Err(DomainInvariantError("FILE_READ_ERROR", "fixture read failure")),
        ):
            result = self.container.compile_catalog_handler.handle(CompileCatalogCommand(
                estate_ref="canonical",
                correlation_id="corr-read-fail",
                causation_id="cause-read-fail",
            ))

        self.assertTrue(result.is_err)
        self.assertEqual(result.unwrap_err().code, "DOCUMENT_READ_ERROR")
        self.assertEqual(
            self.uow._conn.execute("SELECT COUNT(*) AS c FROM catalogs_v3").fetchone()["c"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
