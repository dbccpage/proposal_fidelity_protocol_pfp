"""QDDC domain port through the canonical Rust process seam. AuthorityEffect: None."""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import ValidationError

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operating_system.adapters.rust_host.majorana_math import (
    NativeMathRefusal,
    call_native,
)
from omega_engine_pfp.domain.homology.qddc import (
    Contract,
    DeformationRequest,
    DeformationResult,
    DensityRequest,
    DensityResult,
    HodgeResult,
    LindbladRequest,
    LindbladResult,
    ProbeRequest,
    ProbeResult,
    QddcState,
    RepairProjectorResult,
    RetractionRequest,
    RetractionResult,
)

ResultContract = TypeVar("ResultContract", bound=Contract)


class NativeQddc:
    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host or RustSymbolGameHost()

    def _invoke(
        self, action: str, request: Contract, result_type: type[ResultContract]
    ) -> ResultContract:
        result = call_native(action, request.model_dump(mode="json"), host=self._host)
        # JSON validation admits wire arrays as immutable tuples, while retaining
        # strict scalar types. Native refusals retain their complete host outcome.
        try:
            return result_type.model_validate_json(json.dumps(result))
        except ValidationError as error:
            raise NativeMathRefusal(
                "QDDC_OUTPUT_SCHEMA",
                f"{action} returned an invalid {result_type.__name__}",
                outcome=result.outcome,
            ) from error

    def hodge(self, state: QddcState) -> HodgeResult:
        return self._invoke("qddc_hodge", state, HodgeResult)

    def repair_projector(self, state: QddcState) -> RepairProjectorResult:
        return self._invoke("qddc_repair_projector", state, RepairProjectorResult)

    def lindblad(self, request: LindbladRequest) -> LindbladResult:
        return self._invoke("qddc_lindblad", request, LindbladResult)

    def retract(self, request: RetractionRequest) -> RetractionResult:
        return self._invoke("qddc_retract", request, RetractionResult)

    def probe(self, request: ProbeRequest) -> ProbeResult:
        return self._invoke("qddc_probe", request, ProbeResult)

    def deform(self, request: DeformationRequest) -> DeformationResult:
        return self._invoke("qddc_deform", request, DeformationResult)

    def density(self, request: DensityRequest) -> DensityResult:
        return self._invoke("qddc_density", request, DensityResult)
