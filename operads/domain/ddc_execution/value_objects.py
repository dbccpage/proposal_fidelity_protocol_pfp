#!/usr/bin/env python3
"""Domain Value Objects for the operad Bounded Context.

Enforces exact-type equality (RULE_VO_EXACT_TYPE_EQUALITY_001) and immutability.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColourSignature:
    """Immutable signature defining source colours and target colour."""

    source_colours: tuple[str, ...]
    target_colour: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_colours, tuple):
            object.__setattr__(self, "source_colours", tuple(self.source_colours))

    @property
    def arity(self) -> int:
        return len(self.source_colours)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ColourSignature)
        return (
            self.source_colours == other.source_colours
            and self.target_colour == other.target_colour
        )

    def __hash__(self) -> int:
        return hash((type(self), self.source_colours, self.target_colour))


@dataclass(frozen=True)
class OperadOperation:
    """Immutable declaration of an operadic morphism in the colored operad."""

    skill_id: str
    name: str
    signature: ColourSignature
    arity: int
    residual_effect: str = "unknown"
    equivariant: bool = False

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, OperadOperation)
        return (
            self.skill_id == other.skill_id
            and self.name == other.name
            and self.signature == other.signature
            and self.arity == other.arity
            and self.residual_effect == other.residual_effect
            and self.equivariant == other.equivariant
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.skill_id,
                self.name,
                self.signature,
                self.arity,
                self.residual_effect,
                self.equivariant,
            )
        )


@dataclass(frozen=True)
class ArtifactOutput:
    """Immutable reference to an emitted artifact with path and content hash."""

    path: str
    sha256: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ArtifactOutput)
        return self.path == other.path and self.sha256 == other.sha256

    def __hash__(self) -> int:
        return hash((type(self), self.path, self.sha256))


@dataclass(frozen=True)
class ExecutionRunRecord:
    """Immutable single execution run entry for evidence_trace.json."""

    timestamp: str
    skill_name: str
    source_colours: tuple[str, ...]
    target_colour: str
    inputs: tuple[str, ...]
    output: ArtifactOutput
    residual_before: float
    residual_after: float
    residual_delta: float
    contractive: bool
    findings_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_colours, tuple):
            object.__setattr__(self, "source_colours", tuple(self.source_colours))
        if not isinstance(self.inputs, tuple):
            object.__setattr__(self, "inputs", tuple(self.inputs))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExecutionRunRecord)
        return (
            self.timestamp == other.timestamp
            and self.skill_name == other.skill_name
            and self.source_colours == other.source_colours
            and self.target_colour == other.target_colour
            and self.inputs == other.inputs
            and self.output == other.output
            and self.residual_before == other.residual_before
            and self.residual_after == other.residual_after
            and self.residual_delta == other.residual_delta
            and self.contractive == other.contractive
            and self.findings_count == other.findings_count
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.timestamp,
                self.skill_name,
                self.source_colours,
                self.target_colour,
                self.inputs,
                self.output,
                self.residual_before,
                self.residual_after,
                self.residual_delta,
                self.contractive,
                self.findings_count,
            )
        )


@dataclass(frozen=True)
class EvidenceTraceReport:
    """Immutable aggregate evidence trace ledger state."""

    schema: str
    skill_name: str
    signature: str
    total_runs: int
    contractive_runs: int
    required_contractive_runs: int
    residual_evidence_bar_satisfied: bool
    authority_effect: str
    runs: tuple[ExecutionRunRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.runs, tuple):
            object.__setattr__(self, "runs", tuple(self.runs))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EvidenceTraceReport)
        return (
            self.schema == other.schema
            and self.skill_name == other.skill_name
            and self.signature == other.signature
            and self.total_runs == other.total_runs
            and self.contractive_runs == other.contractive_runs
            and self.required_contractive_runs == other.required_contractive_runs
            and self.residual_evidence_bar_satisfied == other.residual_evidence_bar_satisfied
            and self.authority_effect == other.authority_effect
            and self.runs == other.runs
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.schema,
                self.skill_name,
                self.signature,
                self.total_runs,
                self.contractive_runs,
                self.required_contractive_runs,
                self.residual_evidence_bar_satisfied,
                self.authority_effect,
                self.runs,
            )
        )
