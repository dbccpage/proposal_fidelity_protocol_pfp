"""ROP application service for documentation-integrity commands."""

from __future__ import annotations

from omega_engine_pfp.domain.documentation_integrity.models import (
    ExecutionReceipt,
    IntegrityRefusal,
    IntegrityRequest,
)
from omega_engine_pfp.domain.documentation_integrity.ports import (
    ClockPort,
    DocumentationIntegrityGatewayPort,
)
from omega_engine_pfp.domain.kernel.result import Result


class DocumentationIntegrityService:
    def __init__(self, gateway: DocumentationIntegrityGatewayPort, clock: ClockPort) -> None:
        self._gateway = gateway
        self._clock = clock

    def execute(self, request: IntegrityRequest) -> Result[ExecutionReceipt, IntegrityRefusal]:
        return self._gateway.execute(request, self._clock.now())
