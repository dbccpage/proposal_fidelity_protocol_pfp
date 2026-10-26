"""Composition Root for OEWAS V3.

The sole module allowed to import and instantiate both controllers and adapters.
"""

from __future__ import annotations

import pathlib
from typing import Any, Optional
from uuid import uuid4

from ..application.commands.compile_catalog import CompileCatalogHandler
from ..application.commands.compile_licensed_term import CompileLicensedTermHandler
from ..application.commands.compile_projection import CompileProjectionHandler
from ..application.commands.verify_catalog import VerifyCatalogHandler
from ..application.queries.get_catalog import GetCatalogHandler
from ..application.queries.validate_workflows import ValidateWorkflowsHandler
from ..controllers.python_facade import OeopApiV3
from .fs.fs_estate_source_adapter import FsEstateSourceAdapter
from .fs.legacy_catalog_reader_adapter import LegacyCatalogReaderAdapter
from .operad.higher_operad_adapter import HigherOperadAdapter
from .parser.markdown_parser_adapter import LosslessMarkdownParserAdapter
from .providers.projection_manifest_adapter import ProjectionManifestAdapter
from .providers.system_clock import SystemClock
from .providers.uuid_id_generator import UuidIdGenerator
from .storage.anchored_ledger_subscriber import AnchoredLedgerSubscriber, validate_database_paths
from .storage.outbox_dispatcher import OutboxMessageDispatcher
from .storage.sqlite_unit_of_work import SqliteUnitOfWork


class OeopContainer:
    def __init__(self, workspace_root: Optional[pathlib.Path] = None, db_path: str = ":memory:") -> None:
        self.workspace_root = workspace_root or pathlib.Path(__file__).resolve().parents[2]
        self.db_path = db_path
        validate_database_paths(db_path)

        # 1. Infrastructure Adapters
        self.clock = SystemClock()
        self.id_gen = UuidIdGenerator()
        self.uow = SqliteUnitOfWork(db_path=db_path)
        self.parser = LosslessMarkdownParserAdapter()
        self.estate_source = FsEstateSourceAdapter(self.workspace_root)
        self.legacy_reader = LegacyCatalogReaderAdapter(self.workspace_root)
        self.operad_adapter = HigherOperadAdapter()
        self.projection_adapter = ProjectionManifestAdapter()

        # 2. Application Handlers
        self.compile_catalog_handler = CompileCatalogHandler(
            estate_source=self.estate_source,
            parser=self.parser,
            legacy_reader=self.legacy_reader,
            uow=self.uow,
            clock=self.clock,
            id_gen=self.id_gen,
        )
        self.verify_catalog_handler = VerifyCatalogHandler(
            uow=self.uow,
            operad_port=self.operad_adapter,
        )
        self.compile_projection_handler = CompileProjectionHandler(
            uow=self.uow,
            projection_port=self.projection_adapter,
            id_gen=self.id_gen,
        )
        self.compile_licensed_term_handler = CompileLicensedTermHandler(
            operad_port=self.operad_adapter,
        )
        self.get_catalog_handler = GetCatalogHandler(
            uow=self.uow,
        )
        self.validate_workflows_handler = ValidateWorkflowsHandler()

        # 3. Controllers
        self.api = OeopApiV3(
            compile_catalog_handler=self.compile_catalog_handler,
            verify_catalog_handler=self.verify_catalog_handler,
            compile_projection_handler=self.compile_projection_handler,
            compile_licensed_term_handler=self.compile_licensed_term_handler,
            validate_workflows_handler=self.validate_workflows_handler,
            get_catalog_handler=self.get_catalog_handler,
        )
        self._router: Any | None = None
        self.dispatcher: OutboxMessageDispatcher | None = None
        self.receipt_subscriber: AnchoredLedgerSubscriber | None = None

    def configure_receipt_delivery(
        self, *, tip_path: pathlib.Path, key: bytes, ledger_id: str,
        worker_id: str | None = None,
    ) -> OutboxMessageDispatcher:
        """Opt into persistent, leased delivery to the actual receipt ledger.

        A deployment supplies an independently custodied tip and key. The
        default ephemeral catalog API deliberately cannot imply durable delivery.
        """
        if self.dispatcher is not None:
            raise ValueError("Receipt delivery is already configured")
        subscriber = AnchoredLedgerSubscriber(self.db_path, tip_path, key, ledger_id)
        dispatcher = OutboxMessageDispatcher(self.uow, worker_id=worker_id or uuid4().hex)
        dispatcher.subscribe("events.oewas.v3", subscriber)
        self.receipt_subscriber, self.dispatcher = subscriber, dispatcher
        return dispatcher

    def close(self) -> None:
        if self.receipt_subscriber is not None:
            self.receipt_subscriber.close()
        self.uow.close()

    @property
    def router(self) -> Any:
        """Construct the optional FastAPI adapter only when HTTP is requested."""
        if self._router is None:
            from ..controllers.router import create_oeop_router

            self._router = create_oeop_router(self.api)
        return self._router


def create_oeop_container(workspace_root: Optional[pathlib.Path] = None, db_path: str = ":memory:") -> OeopContainer:
    return OeopContainer(workspace_root=workspace_root, db_path=db_path)
