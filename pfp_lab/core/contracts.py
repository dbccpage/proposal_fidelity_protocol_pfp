"""Wire contracts: the Pydantic v2 models every front end admits and emits.

AuthorityEffect: None.
Contract: urn:pfp-lab:core:contracts:v1

RULE_PY_001: every external input (scenario files, HTTP bodies, JSON-RPC
params, receipts) is validated by these models before the core sees it. Models
are strict, frozen and refuse unknown fields. Rationals are canonical strings,
integers refuse booleans, and names follow ``admission.NAME_PATTERN``. The
conversion to governor values happens in ``to_graph`` and ``to_move`` only.

Inputs are admitted from JSON text with ``admit_json``: strict mode accepts a
JSON array for a tuple field, so the frozen models hold no mutable lists
(RULE_PY_005). ``AdmissionError`` is a ``ValueError``, so a refusal raised
inside a validator surfaces as a single ``pydantic.ValidationError``.

The built-in scenario packs are JSON files in ``pfp_lab/core/packs`` and are
admitted through the same models as user input; a malformed pack fails the
first lookup instead of reaching the governor.
"""

from __future__ import annotations

from fractions import Fraction
from functools import cache
from importlib.resources import files
from typing import Annotated, Final, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from pfp_lab.core.admission import (
    AdmissionError,
    UnknownPackError,
    admit_int,
    admit_name,
    format_rational,
    parse_rational,
)
from pfp_lab.core.governor import (
    AssertMove,
    CutMove,
    Move,
    MoveKind,
    RetractMove,
    Status,
    Verdict,
    VerifyMove,
)
from pfp_lab.core.graph import MAX_EDGES, MAX_VERTICES, MAX_WEIGHT, ConstraintGraph, Edge, EdgeKey

CORE_VERSION: Final = "0.1.0"
MAX_MOVES = 256
MAX_TEXT = 200
SCENARIO_SCHEMA = "pfp-lab.scenario.v1"


def _name(value: object) -> str:
    return admit_name(value, field="name")


def _rational(value: object) -> str:
    # Admitted spellings are canonical, so formatting the parsed value returns the input.
    return format_rational(parse_rational(value, field="rational"))


def _weight(value: object) -> int:
    return admit_int(value, minimum=1, maximum=MAX_WEIGHT, field="weight")


Name = Annotated[str, BeforeValidator(_name)]
Rational = Annotated[str, BeforeValidator(_rational)]
Weight = Annotated[int, BeforeValidator(_weight)]
Text = Annotated[str, Field(max_length=MAX_TEXT)]


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")


class EdgeIn(Strict):
    source: Name
    target: Name
    weight: Weight = 1


class ClaimIn(Strict):
    source: Name
    target: Name
    value: Rational


class AssertIn(Strict):
    move: Literal["ASSERT"]
    source: Name
    target: Name
    value: Rational
    step_id: Name | None = None
    provisional: bool = False
    enforce_monotonicity: bool = False


class CutIn(Strict):
    move: Literal["CUT"]
    section: dict[Name, Rational] | None = Field(default=None, max_length=MAX_VERTICES)
    claims: tuple[ClaimIn, ...] | None = Field(default=None, max_length=MAX_EDGES)
    step_id: Name | None = None

    @model_validator(mode="after")
    def _distinct_claims(self) -> CutIn:
        if self.claims is not None:
            keys = [(claim.source, claim.target) for claim in self.claims]
            if len(set(keys)) != len(keys):
                raise ValueError("a claim set names the same directed edge twice")
        return self


class VerifyIn(Strict):
    move: Literal["VERIFY"]
    obligation: Text
    step_id: Name | None = None


class RetractIn(Strict):
    move: Literal["RETRACT"]
    target_step_id: Name
    reason: Text = ""
    step_id: Name | None = None


MoveIn = Annotated[AssertIn | CutIn | VerifyIn | RetractIn, Field(discriminator="move")]


class ScenarioIn(Strict):
    """A declared graph and the proposals to run against it, in order."""

    schema_id: Literal["pfp-lab.scenario.v1"] = Field(alias="schema")
    title: Text = ""
    vertices: tuple[Name, ...] = Field(min_length=1, max_length=MAX_VERTICES)
    edges: tuple[EdgeIn, ...] = Field(max_length=MAX_EDGES)
    moves: tuple[MoveIn, ...] = Field(max_length=MAX_MOVES)

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _graph_is_valid(self) -> ScenarioIn:
        to_graph(self)  # raises AdmissionError, which Pydantic does not catch
        return self


class VerdictOut(Strict):
    step_id: str
    move: MoveKind
    admitted: bool
    status: Status
    defect_before: str
    defect_after: str
    details: str


class StateOut(Strict):
    section: dict[str, str]
    claims: tuple[ClaimIn, ...]
    defect: str
    obstruction: str


MAX_JSON_BYTES = 262_144


def admit_json[ModelT: BaseModel](model: type[ModelT], data: str | bytes) -> ModelT:
    """Validate JSON text against ``model``; refuse oversized input before parsing.

    Raises ``AdmissionError`` for oversized input and ``pydantic.ValidationError``
    for everything the model refuses.
    """
    size = len(data.encode("utf-8")) if isinstance(data, str) else len(data)
    if size > MAX_JSON_BYTES:
        raise AdmissionError(f"input is {size} bytes; the limit is {MAX_JSON_BYTES}")
    return model.model_validate_json(data)


def to_graph(scenario: ScenarioIn) -> ConstraintGraph:
    """Build the immutable graph; ``AdmissionError`` if it is not a valid carrier."""
    edges = tuple(Edge(item.source, item.target, item.weight) for item in scenario.edges)
    return ConstraintGraph(vertices=tuple(scenario.vertices), edges=edges)


def to_move(item: AssertIn | CutIn | VerifyIn | RetractIn) -> Move:
    """Convert an admitted wire move into a governor move with exact values."""
    if isinstance(item, AssertIn):
        return AssertMove(
            source=item.source,
            target=item.target,
            value=parse_rational(item.value, field="value"),
            step_id=item.step_id,
            provisional=item.provisional,
            enforce_monotonicity=item.enforce_monotonicity,
        )
    if isinstance(item, CutIn):
        return CutMove(section=_section(item), claims=_claims(item), step_id=item.step_id)
    if isinstance(item, VerifyIn):
        return VerifyMove(obligation=item.obligation, step_id=item.step_id)
    return RetractMove(target_step_id=item.target_step_id, reason=item.reason, step_id=item.step_id)


def _section(item: CutIn) -> tuple[tuple[str, Fraction], ...] | None:
    if item.section is None:
        return None
    return tuple((name, parse_rational(text, field="section")) for name, text in item.section.items())


def _claims(item: CutIn) -> tuple[tuple[EdgeKey, Fraction], ...] | None:
    if item.claims is None:
        return None
    return tuple(((claim.source, claim.target), parse_rational(claim.value, field="claim")) for claim in item.claims)


def verdict_out(verdict: Verdict) -> VerdictOut:
    return VerdictOut(
        step_id=verdict.step_id,
        move=verdict.move,
        admitted=verdict.admitted,
        status=verdict.status,
        defect_before=format_rational(verdict.defect_before),
        defect_after=format_rational(verdict.defect_after),
        details=verdict.details,
    )


class PackSummary(Strict):
    pack_id: str
    title: str
    moves: int = Field(ge=0)


# Catalog order: the Paper 005 session first, then one pack per protocol idea.
PACK_IDS: Final = ("paper-005-worked-session", "section-repair", "refusal-gallery", "two-islands")


@cache
def _load_pack(pack_id: str) -> ScenarioIn:
    data = files("pfp_lab.core").joinpath("packs", f"{pack_id}.json").read_bytes()
    return admit_json(ScenarioIn, data)


def get_pack(pack_id: str) -> ScenarioIn:
    """The admitted scenario for ``pack_id``; ``UnknownPackError`` if there is none."""
    if pack_id not in PACK_IDS:
        raise UnknownPackError(f"no pack named {pack_id!r}")
    return _load_pack(pack_id)


def list_packs() -> tuple[PackSummary, ...]:
    """Every built-in pack, in catalog order."""
    return tuple(
        PackSummary(pack_id=pack_id, title=get_pack(pack_id).title, moves=len(get_pack(pack_id).moves))
        for pack_id in PACK_IDS
    )


__all__ = [
    "CORE_VERSION",
    "MAX_JSON_BYTES",
    "PACK_IDS",
    "PackSummary",
    "get_pack",
    "list_packs",
    "MAX_MOVES",
    "SCENARIO_SCHEMA",
    "admit_json",
    "AssertIn",
    "ClaimIn",
    "CutIn",
    "EdgeIn",
    "MoveIn",
    "RetractIn",
    "ScenarioIn",
    "StateOut",
    "VerdictOut",
    "VerifyIn",
    "to_graph",
    "to_move",
    "verdict_out",
]
