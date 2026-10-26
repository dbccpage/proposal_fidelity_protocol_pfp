"""One resumable intelligence-metabolism tick. AuthorityEffect: None."""

import json
from dataclasses import dataclass

from omega_engine_prompt_civilization.domain.prompt_ecology.protocols import (
    DefectVerifier,
    MetabolismStore,
    TelemetrySource,
)


@dataclass(frozen=True)
class MetabolismReceiptV1:
    processed: int
    refused: int
    candidate_ids: tuple[str, ...]
    authority_effect: str = "None"


def ingest_batch(
    source: TelemetrySource, store: MetabolismStore, verifier: DefectVerifier,
    *, max_records: int, required_support: int = 3,
) -> MetabolismReceiptV1:
    """Repeated calls resume durable cursors; the caller controls cadence/budget.

    Only the injected host checker may name an independently replayed defect.
    Recurrence produces a candidate proposal and never activates a detector.
    """
    if type(max_records) is not int or max_records <= 0:
        raise ValueError("INGESTION_BUDGET_REQUIRED")
    if type(required_support) is not int or required_support < 3:
        raise ValueError("INDEPENDENT_SUPPORT_REQUIRED")
    processed = 0
    refused = 0
    candidates = []
    for row in source.read_batch(store.checkpoints(), max_records):
        if processed >= max_records:
            raise ValueError("INGESTION_SOURCE_EXCEEDED_BUDGET")
        residual = None
        witness = None
        try:
            record = json.loads(row.raw)
        except (ValueError, UnicodeDecodeError):
            residual = "MALFORMED_TELEMETRY"
        else:
            if not isinstance(record, dict):
                residual = "TELEMETRY_OBJECT_REQUIRED"
            else:
                witness = verifier.verify(record, row)
                if witness is None:
                    residual = "EXACT_DEFECT_NOT_REPRODUCED"
                elif not all((
                    witness.defect_id, witness.observation_id,
                    witness.checker_digest, witness.witness_digest,
                )):
                    raise ValueError("INCOMPLETE_HOST_WITNESS")
        candidate = store.record(row, witness, required_support, residual)
        processed += 1
        refused += residual is not None
        if candidate is not None:
            candidates.append(candidate)
    return MetabolismReceiptV1(processed, refused, tuple(candidates))

PromptEcologyIngestUseCase = ingest_batch
EcologyBatchReceiptV1 = MetabolismReceiptV1
