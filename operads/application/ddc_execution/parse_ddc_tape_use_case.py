"""Parse DDC tape receipts and delegate optional custody to injected ports."""

from omega_engine_operads.domain.ddc_execution.errors import OperadDomainError
from omega_engine_operads.domain.ddc_execution.protocols import (
    DdcReceiptStoragePort,
    DdcTapeParserPort,
)
from omega_engine_operads.domain.ddc_execution.tape import (
    ParseDdcTapeRequest,
    ParseDdcTapeResponse,
)
from omega_engine_operads.domain.operad.errors import Err, Ok, Result


class ParseDdcTapeUseCase:
    def __init__(self, *, parser: DdcTapeParserPort, receipts: DdcReceiptStoragePort) -> None:
        self.parser = parser
        self.receipts = receipts

    def execute(
        self, request: ParseDdcTapeRequest
    ) -> Result[ParseDdcTapeResponse, OperadDomainError]:
        parsed = self.parser.parse(request.source)
        if isinstance(parsed, Err):
            return parsed
        receipt = parsed.value
        saved = None
        if request.persist_evidence:
            try:
                destination = self.receipts.destination(
                    receipt.run_id, request.output_receipt_path, request.evidence_vault_dir
                )
            except OperadDomainError as exc:
                return Err(exc)
            persisted = self.receipts.persist(receipt, destination)
            if isinstance(persisted, Err):
                return persisted
            saved = persisted.value
        return Ok(
            ParseDdcTapeResponse(
                receipt, saved, "SUCCESS" if receipt.ddc_laws_valid else "LAW_VIOLATIONS_DETECTED"
            )
        )
