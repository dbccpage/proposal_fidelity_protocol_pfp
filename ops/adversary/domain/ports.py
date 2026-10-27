"""Domain ports for Adversary's carrier measurement and candidate checking.

Both ports have null implementations, and both nulls are honest: they return
``NOT_MEASURED``, which the terminal gate can never turn into an
authorization. A null object stands in for a missing measurement; it never
stands in for a passing one.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from operations.domain.rop.result import Ok, Refusal, Result

from .evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    ObstructionMeasurementV1,
    PrimeDescentReceiptV1,
    sha256_ref,
)
from .instruction_ingress import InstructionIngressReceiptV1
from .models import AdversaryBoutOutcomeV1, AdversaryBoutRequestV1
from .network import Network


class LearningCompletionPort(Protocol):
    """Observe persisted terminal runs without changing their verdicts."""

    def completed(self, run_directory: str, *, outcome: str, origin: str = "session") -> None: ...

    def prepare(self, objective: str, run_id: str) -> str: ...


@runtime_checkable
class InstructionIngressPort(Protocol):
    """Check an independently admitted instruction plan before any bout work.

    A candidate OEWAS plan or text body alone cannot implement this port as an
    admission. The composition root must bind an external admission verifier.
    """

    def pre_dispatch(self, request: AdversaryBoutRequestV1) -> Result[InstructionIngressReceiptV1, Refusal]: ...


@runtime_checkable
class CochainScoringPort(Protocol):
    """Exact carrier measurement: Phi1, Gamma2 and the certificate behind them."""

    def identify_obstructions(
        self,
        carrier_network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any],
        *,
        ablation_flags: Mapping[str, bool] | None = None,
    ) -> Result[ObstructionMeasurementV1, Refusal]:
        """Measure the carrier, or return ``NOT_MEASURED`` with the reason."""
        ...


class NullCochainScoringAdapter:
    """No scorer is bound. Every carrier is ``NOT_MEASURED``.

    This adapter used to report the raw l1 mass as if it were Phi1 and a
    Gamma2 of zero, so a zero cochain read as an exact repair.
    """

    def identify_obstructions(
        self,
        carrier_network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any],
        *,
        ablation_flags: Mapping[str, bool] | None = None,
    ) -> Result[ObstructionMeasurementV1, Refusal]:
        del carrier_network, initial_cochain, ablation_flags
        return Ok(
            ObstructionMeasurementV1.not_measured(
                "No cochain scorer is bound to this bout.", backend="null_scorer"
            )
        )


@runtime_checkable
class CandidateCheckerPort(Protocol):
    """The challenge's exact checker, applied to one candidate's exact bytes."""

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        """Return the checker's typed verdict bound to the checker receipt digest."""
        ...


class NullCandidateCheckerAdapter:
    """No checker is bound. Every candidate is ``NOT_MEASURED``."""

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        del run_key, objective, carrier_context
        return Ok(
            CandidateCheckV1(
                verdict=CheckerVerdict.NOT_MEASURED,
                candidate_id=candidate_id,
                candidate_content_sha256=sha256_ref(candidate_bytes),
                checker_id="null_checker",
                reason="No challenge checker is bound to this bout.",
            )
        )


@runtime_checkable
class PrimeDescentPort(Protocol):
    """Port for prime descent coordination across carriers."""

    def execute_descent(
        self,
        *,
        run_id: str,
        carrier_network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any] | Sequence[int],
        max_steps: int = 64,
        grant: Mapping[str, Any] | None = None,
    ) -> Result[PrimeDescentReceiptV1, Refusal]:
        """Execute prime descent and return the certified descent receipt."""
        ...


class NullPrimeDescentAdapter:
    """No descent coordinator is bound. Every descent is NOT_MEASURED."""

    def execute_descent(
        self,
        *,
        run_id: str,
        carrier_network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any] | Sequence[int],
        max_steps: int = 64,
        grant: Mapping[str, Any] | None = None,
    ) -> Result[PrimeDescentReceiptV1, Refusal]:
        del carrier_network, initial_cochain, max_steps, grant
        return Ok(
            PrimeDescentReceiptV1.not_measured(
                "No prime descent coordinator is bound to this bout.",
                backend="null_descent_coordinator",
                run_id=run_id,
            )
        )


__all__ = [
    "CandidateCheckerPort",
    "CochainScoringPort",
    "NullCandidateCheckerAdapter",
    "NullCochainScoringAdapter",
    "NullPrimeDescentAdapter",
    "PrimeDescentPort",
]


class NativeBoutExecutionPort(Protocol):
    """Port for the native bout composition; collaborators remain injectable."""

    def execute_bout(
        self, request: "AdversaryBoutRequestV1", *, repo_root: "Path", learning_guidance: str,
        instruction_plan: Mapping[str, object] | None = None,
    ) -> Result["AdversaryBoutOutcomeV1", Refusal]: ...
