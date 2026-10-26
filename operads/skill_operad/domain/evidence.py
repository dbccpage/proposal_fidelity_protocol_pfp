"""Evidence, Residuals, and Diagnostic Observations for Coloured Operads.

Single Residual monoid for the package. Accepts both the obligations/risk API
and the legacy claims/unverified/risk_score API so facades need no translation.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional, Sequence, Tuple


class Witness:
    """Protocol / base class for any kill or falsifying witness."""

    def kills(self, candidate: object) -> bool:
        return True

    def describe(self) -> str:
        return "Witness"


@dataclass(frozen=True)
class ConcreteWitness(Witness):
    kind: str
    description: str
    location: Optional[str] = None
    context: Optional[str] = None

    def describe(self) -> str:
        loc = f" at {self.location}" if self.location else ""
        return f"[{self.kind}]{loc}: {self.description}"


@dataclass(frozen=True)
class HallucinationWitness(Witness):
    claimed_source: str
    claimed_target: str
    antibody_name: str
    inner_witness: Witness

    def describe(self) -> str:
        return (
            f"Hallucination detected by {self.antibody_name}: "
            f"claimed Path({self.claimed_source} == {self.claimed_target}) falsified: "
            f"{self.inner_witness.describe()}"
        )


@dataclass(frozen=True)
class PathObstructionWitness(Witness):
    path_source: str
    path_target: str
    fibration_name: str
    detail: str

    def describe(self) -> str:
        return (
            f"Path obstruction in fibration '{self.fibration_name}' "
            f"along Path({self.path_source} -> {self.path_target}): {self.detail}"
        )


@dataclass(frozen=True, init=False)
class Residual:
    """Monoid of open obligations and accumulated execution risk.

    absorb is associative; the unit is EMPTY. risk uses the tropical (max)
    convention. Legacy field names claims/unverified/risk_score are aliases.
    """

    _claims: Tuple[str, ...] = ()
    _unverified: Tuple[str, ...] = ()
    _risk: float = 0.0

    def __init__(
        self,
        claims: Sequence[str] = (),
        unverified: Sequence[str] = (),
        obligations: Sequence[str] = (),
        risk: float = 0.0,
        risk_score: float | None = None,
    ) -> None:
        merged_unv = tuple(unverified) if unverified else tuple(obligations)
        merged_claims = tuple(claims)
        if not merged_unv and obligations:
            merged_unv = tuple(obligations)
        effective_risk = float(risk_score if risk_score is not None else risk)
        object.__setattr__(self, "_claims", merged_claims)
        object.__setattr__(self, "_unverified", merged_unv)
        object.__setattr__(self, "_risk", effective_risk)

    @property
    def claims(self) -> Tuple[str, ...]:
        return self._claims

    @property
    def unverified(self) -> Tuple[str, ...]:
        return self._unverified

    @property
    def obligations(self) -> Tuple[str, ...]:
        return self._unverified

    @property
    def risk(self) -> float:
        return self._risk

    @property
    def risk_score(self) -> float:
        return self._risk

    @property
    def is_empty(self) -> bool:
        return not self._claims and not self._unverified and self._risk == 0.0

    def is_clean(self) -> bool:
        return self.is_empty

    def absorb(self, other: Residual) -> Residual:
        if other.is_empty:
            return self
        if self.is_empty:
            return other
        return Residual(
            claims=self._claims + other._claims,
            unverified=self._unverified + other._unverified,
            risk_score=max(self._risk, other._risk),
        )

    def __add__(self, other: Residual) -> Residual:
        return self.absorb(other)

    def discharge(self, obligation: str, evidence: str) -> Residual:
        new_unverified = tuple(o for o in self.obligations if o != obligation)
        if len(new_unverified) == len(self.obligations):
            return self
        return Residual(
            unverified=new_unverified,
            claims=self._claims + (f"discharged:{obligation}:{evidence}",),
            risk_score=0.0 if not new_unverified else self._risk,
        )


EMPTY: Residual = Residual()


@dataclass(frozen=True)
class CommandRecord:
    """Immutable record of an executed command during verification."""

    cmd: Tuple[str, ...]
    cwd: str
    exit_code: int
    stdout_sha256: str
    stderr_sha256: str
    duration_s: float

    @classmethod
    def from_execution(
        cls,
        cmd: Sequence[str],
        cwd: str,
        exit_code: int,
        stdout: str | bytes = "",
        stderr: str | bytes = "",
        duration_s: float = 0.0,
    ) -> CommandRecord:
        stdout_bytes = stdout.encode("utf-8") if isinstance(stdout, str) else stdout
        stderr_bytes = stderr.encode("utf-8") if isinstance(stderr, str) else stderr
        return cls(
            cmd=tuple(cmd),
            cwd=str(cwd),
            exit_code=exit_code,
            stdout_sha256=hashlib.sha256(stdout_bytes).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr_bytes).hexdigest(),
            duration_s=round(float(duration_s), 4),
        )


@dataclass(frozen=True)
class EvidenceReceipt:
    """Structured evidence-bearing receipt produced by operadic executions."""

    sys_executable: str
    python_version: str
    platform: str
    packaging_root: str
    layout: str
    git_head: Optional[str]
    git_status_dirty: bool
    changed_paths: Tuple[str, ...]
    change_sha256: str
    commands: Tuple[CommandRecord, ...]
    test_counts: Dict[str, int]
    coverage_delta: Optional[Dict[str, Any]] = None
    mutation_score: Optional[float] = None
    contract_discovery: str = "docstring_and_types"
    invariants: Tuple[str, ...] = ()
    counterexample_level: str = "concrete"
    antibodies_applied: Tuple[str, ...] = ()
    witnesses_found: Tuple[str, ...] = ()
    residual: Tuple[str, ...] = ()
    unverified_claims: Tuple[str, ...] = ()
    authority_effect: str = "None"

    def is_clean(self) -> bool:
        return (
            len(self.residual) == 0
            and len(self.witnesses_found) == 0
            and self.test_counts.get("failed", 0) == 0
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass(frozen=True)
class DiagnosticObservation:
    """Observation row recorded in evidence traces without authority promotion."""

    skill_id: str
    run_id: str
    phi_before: float
    phi_after: float
    delta_phi: float
    authority_effect: str = "None"
