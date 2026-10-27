from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from pfp.domain.documentation_integrity.models import (
    DocumentationCommand,
    ExecutionReceipt,
    IntegrityRequest,
)
from pfp.domain.documentation_integrity.policies import (
    extension_kind,
    is_document_relative_path,
)
from pfp.domain.kernel.result import Result
from pfp.use_cases.documentation_integrity import DocumentationIntegrityService


class FakeClock:
    def now(self) -> str:
        return "2026-10-16T00:00:00Z"


class FakeGateway:
    def __init__(self) -> None:
        self.request: IntegrityRequest | None = None

    def execute(self, request: IntegrityRequest, started_at: str):
        self.request = request
        return Result.ok(ExecutionReceipt(request.command, started_at, 0))


def test_service_uses_injected_clock_and_gateway() -> None:
    gateway = FakeGateway()
    service = DocumentationIntegrityService(gateway, FakeClock())
    request = IntegrityRequest(DocumentationCommand.VALIDATE, Path("repo"), Namespace())

    result = service.execute(request)

    assert result.is_ok
    assert result.unwrap().started_at == "2026-10-16T00:00:00Z"
    assert gateway.request is request


def test_pure_path_policies_cover_known_types_and_confinement() -> None:
    assert extension_kind("guide.md") == "markdown"
    assert extension_kind("gate.yaml") == "structured_data"
    assert extension_kind("payload.bin") == "other"
    assert is_document_relative_path("reference/page.md")
    assert not is_document_relative_path("../outside.md")
    assert not is_document_relative_path("C:\\outside.md")
