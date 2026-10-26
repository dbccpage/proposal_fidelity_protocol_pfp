"""Domain entities, adapters, and protocols for Symbol Game problems.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from omega_engine_pfp.domain.shared_kernel.canonical import domain_digest, freeze
from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.entities.projection_receipt import (
    DetectorCase,
    ProjectionReceipt,
    SolverManifest,
    SolverProposal,
)


@dataclass(frozen=True, slots=True)
class OperatorResult:
    data: Any


@dataclass(frozen=True, slots=True)
class OperatorFailure:
    failure_reason: str
    failure_details: dict[str, Any]


class OperatorBase:
    def __init__(
        self,
        operator_id: str,
        domain: str,
        codomain: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.operator_id = operator_id
        self.domain = domain
        self.codomain = codomain
        self.config = config or {}


class Projector(OperatorBase):
    contract_id = "os:projector"

    def __init__(
        self,
        projector_id: str,
        domain: str,
        codomain: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(projector_id, domain, codomain, config)
        self.projector_id = projector_id

    @property
    def config_digest(self) -> str:
        return domain_digest("omega.oesos.projector-config.v1", self.config)

    def _apply_once(self, input_data: Any) -> Any | OperatorFailure:
        try:
            return self.project(input_data)
        except Exception as e:
            return OperatorFailure(
                failure_reason="ProjectionError",
                failure_details={"error": str(e)},
            )

    def project(self, state: Any) -> ProjectionReceipt:
        raise NotImplementedError

    def meaning(self, state: Any) -> Any:
        raise NotImplementedError

    def skeleton(self, state: Any) -> Any:
        raise NotImplementedError

    def validate_packet(
        self, envelope: PacketEnvelopeV2, native_initial_state: Any
    ) -> bool:
        raise NotImplementedError

    def verify_retraction(
        self, solver_id: str, before_state: Any, after_state: Any
    ) -> bool:
        raise NotImplementedError


class Retractor(OperatorBase):
    contract_id = "os:retractor"

    def __init__(
        self,
        retractor_id: str,
        domain: str,
        codomain: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(retractor_id, domain, codomain, config)
        self.retractor_id = retractor_id

    @property
    def config_digest(self) -> str:
        return domain_digest("omega.oesos.retractor-config.v1", self.config)

    def _apply_once(self, input_data: Any) -> Any | OperatorFailure:
        try:
            return self.retract(input_data)
        except Exception as e:
            return OperatorFailure(
                failure_reason="RetractionError",
                failure_details={"error": str(e)},
            )

    def retract(self, state: Any) -> Any:
        raise NotImplementedError


@runtime_checkable
class PacketAdapter(Protocol):
    adapter_id: str
    source_carrier_id: str
    target_carrier_id: str
    config_digest: str

    def adapt(self, native_state: Any) -> Any: ...

    def descend(self, packet_state: Any) -> Any: ...

    def native_meaning(self, native_state: Any) -> Any: ...

    def packet_meaning(self, packet_state: Any) -> Any: ...

    def loss_ledger(self, native_state: Any) -> tuple[str, ...]: ...


@runtime_checkable
class CandidateSolver(Protocol):
    manifest: SolverManifest

    def propose(
        self,
        problem: "RuntimeProblem",
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal | None: ...


@dataclass(frozen=True, slots=True)
class IdentityAdapter:
    source_carrier_id: str
    target_carrier_id: str
    adapter_id: str = "identity-adapter-v1"

    @property
    def config_digest(self) -> str:
        return domain_digest(
            "omega.oesos.adapter-config.v1",
            {
                "adapter_id": self.adapter_id,
                "source_carrier_id": self.source_carrier_id,
                "target_carrier_id": self.target_carrier_id,
            },
        )

    def adapt(self, native_state: Any) -> Any:
        return native_state

    def descend(self, packet_state: Any) -> Any:
        return packet_state

    def native_meaning(self, native_state: Any) -> Any:
        return freeze(native_state)

    def packet_meaning(self, packet_state: Any) -> Any:
        return freeze(packet_state)

    def loss_ledger(self, native_state: Any) -> tuple[str, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class RuntimeProblem:
    envelope: PacketEnvelopeV2
    native_initial_state: Any
    projector: Projector
    adapter: PacketAdapter
    detector_cases: tuple[DetectorCase, ...]
    primitive_difference: str
    zero_relation: str
    observer_id: str
    witness_certificate: str
    protected_obstruction_ids: tuple[str, ...] = ()
    cochain_declared: bool = False

    @property
    def runtime_id(self) -> str:
        return domain_digest(
            "omega.oesos.runtime-problem.v1",
            {
                "packet_id": self.envelope.packet_id,
                "projector_id": self.projector.projector_id,
                "projector_config_digest": getattr(self.projector, "config_digest", ""),
                "adapter_id": self.adapter.adapter_id,
                "adapter_config_digest": getattr(self.adapter, "config_digest", ""),
                "native_initial_state": self.native_initial_state,
                "detector_cases": self.detector_cases,
                "primitive_difference": self.primitive_difference,
                "zero_relation": self.zero_relation,
                "observer_id": self.observer_id,
                "witness_certificate": self.witness_certificate,
                "protected_obstruction_ids": self.protected_obstruction_ids,
                "cochain_declared": self.cochain_declared,
            },
        )


__all__ = [
    "CandidateSolver",
    "IdentityAdapter",
    "OperatorBase",
    "OperatorFailure",
    "OperatorResult",
    "PacketAdapter",
    "Projector",
    "Retractor",
    "RuntimeProblem",
]
