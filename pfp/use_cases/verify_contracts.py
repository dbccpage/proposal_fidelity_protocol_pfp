"""Verify PFP Contracts, Schemas, and Normal Forms Use Case.

Accepts and returns typed PilotAggregate and ValueObject instances directly.
Zero infrastructure imports; depends strictly on domain ports and entities.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import List, Union

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.contracts.contracts import ContractAuditReceipt
from ..domain.kernel.ports import PfpStoragePort
from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.normal_forms import NormalFormVerificationReceipt
from ..domain.value_objects.identifiers import NormalFormId, PilotId


def _unavailable(subject: str) -> DomainError:
    return DomainError(
        code=RefusalCode.HOST_VERIFIER_UNAVAILABLE,
        message=(
            f"{subject}: no candidate execution and semantic checker are bound to this API. "
            "Contract declarations do not establish compliance, confluence, normal-form "
            "membership, or pilot success; these obligations remain unverified."
        ),
    )


class VerifyPfpContractsUseCase:
    """Preserve verification obligations until candidate-bound checking is available."""

    def __init__(self, storage: PfpStoragePort) -> None:
        self.storage = storage

    def verify_all_normal_forms(self) -> Result[List[NormalFormVerificationReceipt], DomainError]:
        try:
            contracts = self.storage.list_normal_form_contracts()
            if not contracts:
                return Result.err(
                    DomainError(
                        code=RefusalCode.CATALOG_UNAVAILABLE,
                        message="No normal-form contracts were found",
                    )
                )
            return Result.err(_unavailable(f"{len(contracts)} normal-form declarations loaded"))
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message=f"Normal form verification failed: {str(exc)}",
                )
            )

    def verify_all(self) -> Result[List[ContractAuditReceipt], DomainError]:
        try:
            contracts = self.storage.list_normal_form_contracts()
            if not contracts:
                return Result.err(
                    DomainError(
                        code=RefusalCode.CATALOG_UNAVAILABLE,
                        message="No normal-form contracts were found",
                    )
                )
            return Result.err(_unavailable(f"{len(contracts)} contract declarations loaded"))
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message=f"Contract verification failed: {str(exc)}",
                )
            )

    def verify_contract(
        self, contract_id: Union[str, NormalFormId, PilotId]
    ) -> Result[ContractAuditReceipt, DomainError]:
        """Verify an individual contract by string or typed ValueObject."""
        raw_id = (
            contract_id.value
            if isinstance(contract_id, (NormalFormId, PilotId))
            else contract_id
        )
        try:
            c = self.storage.load_contract_spec(raw_id)
            return Result.err(_unavailable(f"Contract '{c.contract_id}'"))
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message=f"Contract verification failed: {str(exc)}",
                )
            )

    def verify_normal_form(
        self, nf_id: Union[str, NormalFormId]
    ) -> Result[NormalFormVerificationReceipt, DomainError]:
        """Verify a single normal form by string or NormalFormId value object."""
        raw_id = nf_id.value if isinstance(nf_id, NormalFormId) else nf_id
        try:
            contracts = self.storage.list_normal_form_contracts()
            matching = [c for c in contracts if c.identity.id == raw_id]
            if not matching:
                return Result.err(
                    DomainError(
                        code=RefusalCode.SCHEMA_VIOLATION,
                        message=f"Normal form '{raw_id}' not found",
                    )
                )
            return Result.err(_unavailable(f"Normal form '{raw_id}'"))
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message=f"Normal form verification failed for '{raw_id}': {str(exc)}",
                )
            )

    def verify_pilot(self, pilot: PilotAggregate) -> Result[PilotAggregate, DomainError]:
        """Refuse unsupported verification without replacing the pilot's state or evidence."""
        try:
            if pilot.expected_outcome not in ("PASS", "FAIL"):
                return Result.err(
                    DomainError(
                        code=RefusalCode.SCHEMA_VIOLATION,
                        message=f"Pilot '{pilot.pilot_id.value}' violates contract: invalid expected outcome",
                    )
                )
            return Result.err(_unavailable(f"Pilot '{pilot.pilot_id.value}'"))
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message=f"Pilot verification failed for '{pilot.pilot_id.value}': {str(exc)}",
                )
            )

    def execute(
        self, target: Union[PilotAggregate, NormalFormId, PilotId, str]
    ) -> Result[Union[PilotAggregate, ContractAuditReceipt, NormalFormVerificationReceipt], DomainError]:
        """Polymorphic execute entry point accepting PilotAggregate, ValueObjects, or string."""
        if isinstance(target, PilotAggregate):
            return self.verify_pilot(target)
        if isinstance(target, NormalFormId):
            return self.verify_normal_form(target)
        return self.verify_contract(target)


__all__ = ["VerifyPfpContractsUseCase"]
