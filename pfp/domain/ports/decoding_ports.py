"""Domain ports (protocols) for constrained decoding, polygraph confluence, and antimorphism.

Clean Architecture: Pure abstract interfaces with zero outer infrastructure dependencies.
AuthorityEffect: None.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Protocol, Sequence, runtime_checkable

from pfp.domain.decoding.antimorphism import (
    AntimorphismTransitionModel,
)
from pfp.domain.decoding.cohomology import (
    InformationCohomologyBarcode,
    QuarantinedShadowPacket,
)
from pfp.domain.decoding.errors import DecodingError
from pfp.domain.decoding.polygraph import (
    Confluence2Cell,
    TarskiPolygraph,
)
from pfp.domain.decoding.token_frontier import TokenFrontier
from pfp.domain.decoding.vocabulary import WireVocabulary
from pfp.domain.shared_kernel.result import Result


@runtime_checkable
class ITokenFrontierEvaluator(Protocol):
    """Port for computing dynamic logit masks and exact Bayes probability conditioning."""

    def evaluate(
        self,
        vocabulary: WireVocabulary,
        base_weights: Sequence[int | Fraction],
        admitted_indices: Sequence[int],
    ) -> Result[TokenFrontier, DecodingError]:
        """Evaluate a decoding step with exact Bayes conditioning."""
        ...


@runtime_checkable
class ILogitsProvider(Protocol):
    """Port for retrieving raw discrete probability vectors or unnormalized integer weights."""

    def get_discrete_logits(
        self,
        prompt: str,
        vocabulary: WireVocabulary,
    ) -> Sequence[int | Fraction]:
        """Fetch discrete unnormalized logit weights from model or mock generator."""
        ...


@runtime_checkable
class IPolygraphConfluenceEngine(Protocol):
    """Port for identifying critical pairs and evaluating 2-cell confluence joins under Newman's lemma."""

    def evaluate_confluence(
        self,
        polygraph: TarskiPolygraph,
        cell: Confluence2Cell,
    ) -> Result[bool, DecodingError]:
        """Validate confluent join of critical peaks."""
        ...


@runtime_checkable
class IAntimorphismService(Protocol):
    """Port for executing contravariant path reversal and verifying involution invariants."""

    def invert_path(
        self,
        model: AntimorphismTransitionModel,
        path: Sequence[str],
    ) -> Result[tuple[str, ...], DecodingError]:
        """Invert execution path contravariantly: (e1 . e2)^dag = e2^dag . e1^dag."""
        ...

    def verify_involution(self, model: AntimorphismTransitionModel) -> bool:
        """Verify involution law ((e)^dag)^dag = e across all reversible edges."""
        ...


@runtime_checkable
class ICohomologyBarcodeAnalyzer(Protocol):
    """Port for computing persistence barcodes and verifying gauge relabeling invariance."""

    def compute_barcode(
        self,
        barcode_id: str,
        filtration_steps: Sequence[Any],
    ) -> InformationCohomologyBarcode:
        """Compute diagnostic persistence barcode from multi-scale filtration."""
        ...


@runtime_checkable
class IQuarantineLedgerPort(Protocol):
    """Port for appending obstructed derivations to append-only quarantine storage."""

    def append_quarantined_packet(self, packet: QuarantinedShadowPacket) -> None:
        """Append shadow packet to persistent quarantine ledger."""
        ...

    def load_ledger(self) -> Sequence[QuarantinedShadowPacket]:
        """Load all committed quarantine records."""
        ...


__all__ = [
    "IAntimorphismService",
    "ICohomologyBarcodeAnalyzer",
    "ILogitsProvider",
    "IPolygraphConfluenceEngine",
    "IQuarantineLedgerPort",
    "ITokenFrontierEvaluator",
]
