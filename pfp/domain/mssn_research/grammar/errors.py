"""Domain error catalog for the Grammar Bounded Context."""

from __future__ import annotations

from dataclasses import dataclass

from ..packets.value_objects import RefusalCode


@dataclass(frozen=True)
class GrammarDomainError:
    """Base error for grammar domain violations."""
    code: RefusalCode
    message: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, GrammarDomainError)
        return self.code == other.code and self.message == other.message

    def __hash__(self) -> int:
        return hash((type(self), self.code, self.message))


@dataclass(frozen=True)
class AlphabetViolationError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class ZeroRetainedMassError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class AlternationDepthExceededError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class FrontierInconsistencyError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class TensorInvariantError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class OptimalityInvariantError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class DaggerInvolutionError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class QuarantineViolationError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class ScopeBoundaryViolationError(GrammarDomainError):
    pass


@dataclass(frozen=True)
class PolygraphConfluenceError(GrammarDomainError):
    """Raised when rewrite step continuity or peak join confluence fails."""
    pass


@dataclass(frozen=True)
class DDAEventVerificationError(GrammarDomainError):
    """Raised when a DDA event fails host verification, parent digest, or Kleene logic constraints."""
    pass


@dataclass(frozen=True)
class ExpansionCycleError(GrammarDomainError):
    """Raised when a macro expansion cycle or stationary loop is detected without progress."""
    pass


@dataclass(frozen=True)
class BQNFRoutingError(GrammarDomainError):
    """Raised when cochain view repair, invalidation, or routing invariants fail."""
    pass


@dataclass(frozen=True)
class UnboundedQuantifierError(GrammarDomainError):
    """Raised when a quantifier lacks explicit finite bound limits (FW-UNBOUNDED)."""
    pass


@dataclass(frozen=True)
class AlternationBudgetError(GrammarDomainError):
    """Raised when quantifier alternation depth exceeds the budget ceiling (FW-BUDGET)."""
    pass


@dataclass(frozen=True)
class BianchiNilpotenceError(GrammarDomainError):
    """Raised when a chain/cochain complex violates discrete Bianchi nilpotence (d_k ∘ d_{k-1} != 0)."""
    pass


@dataclass(frozen=True)
class DualCavityGapError(GrammarDomainError):
    """Raised when degree-4 cavity primal and dual objectives exhibit a non-zero duality gap."""
    pass


@dataclass(frozen=True)
class AuthorityBoundaryError(GrammarDomainError):
    """Raised when a candidate attempts to self-certify authority or lacks independent verifier digest (Level 15)."""
    pass


@dataclass(frozen=True)
class IndObjectMorphismError(GrammarDomainError):
    """Raised when an ind-object diagram morphism collapses generators or source relations (Level 16)."""
    pass


@dataclass(frozen=True)
class DialectChecksumError(GrammarDomainError):
    """Raised when a dialect container fails checksum verification or round-trip decoding (Level 17)."""
    pass


@dataclass(frozen=True)
class HodgeDecompositionError(GrammarDomainError):
    """Raised when discrete Hodge reconstruction or mutual orthogonality fails over Q (Level 18)."""
    pass


@dataclass(frozen=True)
class ZetaSpectralQuarantineError(GrammarDomainError):
    """Raised when an irrational pole is laundered as rational or spectral fence breached (Level 19)."""
    pass


@dataclass(frozen=True)
class AutopoieticCycleError(GrammarDomainError):
    """Raised when productive recursion is misclassified as an expansion cycle or cycle detection fails (Level 20)."""
    pass


@dataclass(frozen=True)
class ReggeSimplicialError(GrammarDomainError):
    """Raised when a 4D Regge complex has non-positive Gram matrix or substitutes scalar sums for Bianchi closure (Level 21)."""
    pass


@dataclass(frozen=True)
class LedgerSerializationError(GrammarDomainError):
    """Raised when JSON-L serialization or schema parsing fails for an epistemic quarantine ledger."""
    pass


@dataclass(frozen=True)
class LedgerTruncationError(GrammarDomainError):
    """Raised when an append-only ledger fails explicit head count binding or exhibits prefix/tail truncation."""
    pass


@dataclass(frozen=True)
class LedgerIntegrityError(GrammarDomainError):
    """Raised when a hash chain link or record content digest fails cryptographic verification."""
    pass


@dataclass(frozen=True)
class LiftNecessityError(GrammarDomainError):
    """Raised when an unearned stage lift is attempted or certificate validation fails."""
    pass

