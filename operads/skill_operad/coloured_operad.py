"""coloured_operad.py
==================

Clean Architecture Colored Operad Registry & Multicategory Model.

Responsibilities:
-----------------
1. Symbolic Registry & Verification:
   - ColouredOperad: Central registry tracking colours, declared operations,
     partial compositions o_i, identity units, and symmetric group orbits.
   - Capability Slices (AgentSlice): Functorial capability boundaries restricting
     an agent to its licensed sub-operad with typed ROP Result returns.

2. Executable constructors & Interoperability:
   - Owns the skill constructors formerly in colored_operad.py and imports
     planar morphisms, terms, residuals, witnesses and antibodies directly
     from their domain owners. There is no alternate-spelling module.

Result / DomainError come from domain.errors (single ROP kernel).
AuthorityEffect: None. Finite residual structure only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import permutations
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

# ---------------------------------------------------------------------------
# Single ROP kernel (domain is source of truth)
# ---------------------------------------------------------------------------

try:
    from .domain.errors import (
        DomainError,
        Err,
        Failure,
        Ok,
        Result,
        Success,
    )
except (ImportError, ValueError):
    from domain.errors import (
        DomainError,
        Err,
        Failure,
        Ok,
        Result,
        Success,
    )

# ---------------------------------------------------------------------------
# Re-exported Executable Planar Operad Core
# ---------------------------------------------------------------------------

try:
    from .domain.planar import (
        ArgumentCountError,
        ArityMismatch,
        ColorMismatch,
        ColoredOp,
        OperadError,
        _is_pure_identity,
        formal_compose,
        identity,
        nullary,
        receipt_to_residual,
        Term,
    )
    from .domain.evidence import EMPTY, Residual, Witness
    from .domain.antibodies import AntiMorphism
except (ImportError, ValueError):
    from domain.planar import (
        ArgumentCountError,
        ArityMismatch,
        ColorMismatch,
        ColoredOp,
        OperadError,
        _is_pure_identity,
        formal_compose,
        identity,
        nullary,
        receipt_to_residual,
        Term,
    )
    from domain.evidence import EMPTY, Residual, Witness
    from domain.antibodies import AntiMorphism

Color = str


# ---------------------------------------------------------------------------
# Typed Refusals & Exceptions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IllTypedCompositionRefusal:
    """Record of a failed composition attempt violating sort/colour agreement."""
    outer: str
    slot: int
    inner: str
    target_colour: str
    source_colour: str
    message: str


class MissingColourRefusal(ValueError):
    """Raised when an unregistered colour is referenced."""


class NonMonotoneResidualRefusal(ValueError):
    """Raised when an operation claims contractivity without a monotonic reduction trace."""


# ---------------------------------------------------------------------------
# Symbolic Operad Entities: Colour, Operation, CompositionKey
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Colour:
    """Object / sort / colour of the symbolic operad."""
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("colour name must be a non-empty string")

    def __str__(self) -> str:
        return self.name


@dataclass
class Operation:
    """
    Multi-ary morphism K : (T1, ..., Tn) -> Tout in the symbolic registry.
    Corresponds to one registered skill.
    """
    id: str
    name: str
    source: List[Colour]
    target: Colour
    equivariant: bool = False
    residual_effect: str = "unknown"  # "contractive" | "unknown" | "exact"
    impl: Optional[Callable[..., Any]] = None

    @property
    def arity(self) -> int:
        return len(self.source)


@dataclass(frozen=True)
class CompositionKey:
    """Addresses a partial composition slot: (outer, slot, inner)."""
    outer: str
    slot: int
    inner: str

    def __hash__(self) -> int:
        return hash((self.outer, self.slot, self.inner))


# ---------------------------------------------------------------------------
# Aggregate Root: ColouredOperad Registry
# ---------------------------------------------------------------------------

class ColouredOperad:
    """
    Finite coloured (non-symmetric) multicategory registry.

    Maintains:
      - Canonical sort colours
      - Declared operations (skills)
      - Partial composition lookup table (o_i)
      - Identity unit operations per colour
      - Optional symmetric group permutations (unused by current skills)
      - Refusal audit log

    Naming note: this is a coloured planar multicategory / non-symmetric operad
    fragment. No skill is currently equivariant; "symmetric operad" language in
    older docstrings is aspirational.
    """

    def __init__(self, name: str = "SkillOperad") -> None:
        self.name = name
        self.colours: Dict[str, Colour] = {}
        self.operations: Dict[str, Operation] = {}
        self.composition: Dict[CompositionKey, str] = {}
        self.identities: Dict[str, str] = {}
        self.sym: Dict[str, Dict[Tuple[int, ...], str]] = {}
        self.refusals: List[IllTypedCompositionRefusal] = []

    # ----- Colours & Units -------------------------------------------------

    def add_colour(self, name: str) -> Colour:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("colour name must be a non-empty string")
        if name not in self.colours:
            c = Colour(name)
            self.colours[name] = c
            # Instantiate automatic identity operation for this colour
            id_name = f"id_{name}"
            self.operations[id_name] = Operation(
                id=id_name,
                name=f"Identity/{name}",
                source=[c],
                target=c,
                equivariant=True,
                residual_effect="exact",
            )
            self.identities[name] = id_name
        return self.colours[name]

    # ----- Operations (Skills) ---------------------------------------------

    def add_operation(
        self,
        op_id: str,
        name: str,
        source_colours: List[str],
        target_colour: str,
        equivariant: bool = False,
        residual_effect: str = "unknown",
        impl: Optional[Callable[..., Any]] = None,
    ) -> Operation:
        """Adds or verifies an operation in the registry with strict idempotency."""
        if not isinstance(op_id, str) or not op_id.strip():
            raise ValueError("operation id must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("operation name must be a non-empty string")

        for c in source_colours + [target_colour]:
            self.add_colour(c)

        src = [self.colours[c] for c in source_colours]
        tgt = self.colours[target_colour]
        existing = self.operations.get(op_id)

        if existing is not None:
            same_signature = (
                existing.name == name
                and existing.source == src
                and existing.target == tgt
                and existing.equivariant == equivariant
                and existing.residual_effect == residual_effect
                and existing.impl is impl
            )
            if same_signature:
                return existing
            raise ValueError(f"operation id {op_id!r} already has a different declaration")

        op = Operation(
            id=op_id,
            name=name,
            source=src,
            target=tgt,
            equivariant=equivariant,
            residual_effect=residual_effect,
            impl=impl,
        )
        self.operations[op_id] = op
        return op

    # ----- Partial Composition (o_i) ---------------------------------------

    def add_composition(
        self, outer: str, slot: int, inner: str, result: str
    ) -> Result[None, DomainError]:
        """
        Registers partial composition outer o_slot inner = result.
        Performs strict sort type-checking on insertion and returns an ROP Result.
        """
        if outer not in self.operations or inner not in self.operations:
            err = DomainError(
                "UNKNOWN_OPERATION",
                f"Unknown operation: outer='{outer}' or inner='{inner}'",
            )
            return Failure(err)

        o = self.operations[outer]
        i = self.operations[inner]

        if slot < 0 or slot >= o.arity:
            err = DomainError(
                "SLOT_OUT_OF_RANGE",
                f"slot {slot} out of range for arity {o.arity} of '{outer}'",
            )
            return Failure(err)

        if i.target != o.source[slot]:
            refusal = IllTypedCompositionRefusal(
                outer=outer,
                slot=slot,
                inner=inner,
                target_colour=i.target.name,
                source_colour=o.source[slot].name,
                message=f"IllTypedComposition: {i.target.name} != {o.source[slot].name} at slot {slot}",
            )
            self.refusals.append(refusal)
            err = DomainError("ILL_TYPED_COMPOSITION", refusal.message)
            return Failure(err)

        expected_source = o.source[:slot] + i.source + o.source[slot + 1 :]
        if result not in self.operations:
            # Synthesise composite shell if missing
            self.add_operation(
                result,
                name=f"({outer}∘{slot}{inner})",
                source_colours=[c.name for c in expected_source],
                target_colour=o.target.name,
                residual_effect="unknown",
            )
        else:
            declared_result = self.operations[result]
            if declared_result.source != expected_source or declared_result.target != o.target:
                return Failure(
                    DomainError(
                        "RESULT_SIGNATURE_MISMATCH",
                        f"result {result!r} does not have the composite signature",
                    )
                )

        key = CompositionKey(outer, slot, inner)
        prior = self.composition.get(key)
        if prior is not None and prior != result:
            return Failure(
                DomainError(
                    "COMPOSITION_DRIFT",
                    f"composition {key} is already bound to {prior!r}",
                )
            )

        self.composition[key] = result
        return Success(None)

    def compose(self, outer: str, slot: int, inner: str) -> Optional[str]:
        return self.composition.get(CompositionKey(outer, slot, inner))

    # ----- Unit Laws -------------------------------------------------------

    def left_unit(self, op_id: str) -> bool:
        """id_T o_0 K = K"""
        op = self.operations[op_id]
        id_t = self.identities[op.target.name]
        return self.compose(id_t, 0, op_id) == op_id

    def right_unit(self, op_id: str, slot: int) -> bool:
        """K o_slot id_Ti = K"""
        op = self.operations[op_id]
        id_s = self.identities[op.source[slot].name]
        return self.compose(op_id, slot, id_s) == op_id

    def ensure_units(self) -> None:
        """Registers canonical left and right unit compositions across all operations."""
        for op in list(self.operations.values()):
            # Right units
            for i, c in enumerate(op.source):
                id_c = self.identities[c.name]
                key = CompositionKey(op.id, i, id_c)
                if key not in self.composition:
                    self.composition[key] = op.id
            # Left unit
            id_t = self.identities[op.target.name]
            key = CompositionKey(id_t, 0, op.id)
            if key not in self.composition:
                self.composition[key] = op.id

    # ----- Symmetric Group Equivariance ------------------------------------

    def permute(self, op_id: str, perm: Tuple[int, ...]) -> Optional[str]:
        op = self.operations.get(op_id)
        if op is None or sorted(perm) != list(range(op.arity)):
            return None
        if perm == tuple(range(op.arity)):
            return op_id
        if not op.equivariant:
            return None
        memo = self.sym.setdefault(op_id, {})
        if perm in memo:
            return memo[perm]
        new_src = [op.source[i] for i in perm]
        new_id = f"{op_id}_p{''.join(map(str, perm))}"
        if new_id not in self.operations:
            self.add_operation(
                new_id,
                name=f"{op.name}[perm]",
                source_colours=[c.name for c in new_src],
                target_colour=op.target.name,
                equivariant=True,
                residual_effect=op.residual_effect,
                impl=op.impl,
            )
        memo[perm] = new_id
        return new_id

    def ensure_symmetric_closure(self) -> None:
        for op_id, op in list(self.operations.items()):
            if op.equivariant and op.arity > 1:
                for p in permutations(range(op.arity)):
                    self.permute(op_id, p)

    # ----- Structural Validation -------------------------------------------

    def validate_types(self) -> List[str]:
        errs = []
        for key, res_id in self.composition.items():
            o = self.operations.get(key.outer)
            i = self.operations.get(key.inner)
            r = self.operations.get(res_id)
            if not o or not i or not r:
                errs.append(f"Missing op in {key}")
                continue
            if key.slot >= o.arity:
                errs.append(f"Bad slot {key}")
                continue
            if i.target != o.source[key.slot]:
                errs.append(f"Type mismatch {key}")
            expected_src = o.source[: key.slot] + i.source + o.source[key.slot + 1 :]
            if r.source != expected_src or r.target != o.target:
                errs.append(f"Signature mismatch for result {res_id}")
        return errs

    def validate_units(self) -> List[str]:
        """Check stored unit-table entries without creating or repairing them.

        This is declaration consistency, not evidence about executor values.
        See unit_law_evidence for the explicit evidence ceiling.
        """
        errs = []
        for op in self.operations.values():
            for i in range(op.arity):
                if not self.right_unit(op.id, i):
                    errs.append(f"Right unit fail {op.id} slot {i}")
            if not self.left_unit(op.id):
                errs.append(f"Left unit fail {op.id}")
        return errs

    def unit_law_evidence(self) -> dict:
        """No symbolic lookup table certifies the implementations it names."""
        return {
            "status": "UNAVAILABLE",
            "reason": "Symbolic table entries do not bind evaluated input/output witnesses",
            "scope": "declaration-table consistency only",
            "authority_effect": "None",
        }

    def validate_all(self) -> List[str]:
        return self.validate_types() + self.validate_units()

    # ----- Capability Slices -----------------------------------------------

    def slice(self, name: str, allowed_ops: List[str]) -> AgentSlice:
        for op_id in allowed_ops:
            if op_id not in self.operations:
                raise KeyError(f"Unknown skill {op_id} in agent slice {name}")
        return AgentSlice(name, self, set(allowed_ops))

    # ----- Serialization DTOs ----------------------------------------------

    def to_signature_dict(self) -> dict:
        return {
            "name": self.name,
            "colours": list(self.colours.keys()),
            "operations": [
                {
                    "skill_id": op.id,
                    "name": op.name,
                    "arity": op.arity,
                    "source_colours": [c.name for c in op.source],
                    "target_colour": op.target.name,
                    "equivariant": op.equivariant,
                    "residual_effect": op.residual_effect,
                }
                for op in self.operations.values()
                if not op.id.startswith("id_")
            ],
            "identities": self.identities,
            "compositions": [
                {
                    "outer": k.outer,
                    "slot": k.slot,
                    "inner": k.inner,
                    "result": v,
                }
                for k, v in self.composition.items()
            ],
            "refusals": [
                {
                    "outer": r.outer,
                    "slot": r.slot,
                    "inner": r.inner,
                    "target_colour": r.target_colour,
                    "source_colour": r.source_colour,
                    "message": r.message,
                }
                for r in self.refusals
            ],
        }

    def dump_signature(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_signature_dict(), f, indent=2)


# ---------------------------------------------------------------------------
# Capability-Gated Agent Slice (Sub-Operad Adapter)
# ---------------------------------------------------------------------------

class AgentSlice:
    """Sub-operad: an agent may invoke only its licensed operations using ROP Result returns."""

    def __init__(self, name: str, operad: ColouredOperad, allowed: Set[str]) -> None:
        self.name = name
        self.operad = operad
        self.allowed = allowed

    def can_invoke(self, op_id: str) -> bool:
        return op_id in self.allowed

    def invoke(self, op_id: str, *args: Any) -> Result[Any, DomainError]:
        """Invokes licensed operation returning Success(value) or Failure(DomainError)."""
        if not self.can_invoke(op_id):
            return Failure(
                DomainError(
                    "PERMISSION_DENIED",
                    f"Agent '{self.name}' not licensed for skill '{op_id}'",
                )
            )
        if op_id not in self.operad.operations:
            return Failure(
                DomainError(
                    "UNKNOWN_OPERATION",
                    f"Operation '{op_id}' not found in operad",
                )
            )
        op = self.operad.operations[op_id]
        if len(args) != op.arity:
            return Failure(
                DomainError(
                    "ARITY_MISMATCH",
                    f"Operation '{op_id}' requires {op.arity} inputs, got {len(args)}",
                )
            )
        if op.impl is None:
            return Failure(
                DomainError(
                    "NOT_IMPLEMENTED",
                    f"No implementation attached for skill '{op_id}'",
                )
            )
        try:
            res = op.impl(*args)
            return Success(res)
        except Exception as exc:
            return Failure(
                DomainError(
                    "EXECUTION_FAILED",
                    f"Skill '{op_id}' execution failed: {exc}",
                )
            )

    def to_dict(self) -> dict:
        return {
            "agent": self.name,
            "licensed_skills": sorted(self.allowed),
            "colours": sorted(
                {
                    c.name
                    for op_id in self.allowed
                    for c in self.operad.operations[op_id].source
                    + [self.operad.operations[op_id].target]
                }
            ),
        }


def make_principal_developer(residual: Residual = EMPTY) -> ColoredOp:
    """1-ary Code → Code skill (illustration)."""

    def body(code: object) -> Tuple[object, Residual]:
        return code, Residual(obligations=("needs_antibody_check",), risk=0.3)

    return ColoredOp(
        name="principal_developer",
        source_colors=("Code",),
        target_color="Code",
        residual=residual,
        body=body,
    )


def make_type_strengthen() -> ColoredOp:
    """1-ary Code → Code that strengthens types."""

    def body(code: object) -> Tuple[object, Residual]:
        return code, Residual(obligations=("types_strengthened",), risk=0.1)

    return ColoredOp(
        name="type_strengthen",
        source_colors=("Code",),
        target_color="Code",
        residual=EMPTY,
        body=body,
    )


def make_tester() -> ColoredOp:
    """Code → Evidence."""

    def body(code: object) -> Tuple[object, Residual]:
        return {"tested": True, "id": id(code)}, Residual(
            obligations=("tests_passed",), risk=0.0
        )

    return ColoredOp(
        name="tester",
        source_colors=("Code",),
        target_color="Evidence",
        residual=EMPTY,
        body=body,
    )


def make_apply_contract() -> ColoredOp:
    """2-ary (Code, Contract) → Code."""

    def body(code: object, contract: object) -> Tuple[object, Residual]:
        return code, Residual(obligations=("contract_applied",), risk=0.2)

    return ColoredOp(
        name="apply_contract",
        source_colors=("Code", "Contract"),
        target_color="Code",
        residual=EMPTY,
        body=body,
    )


def make_binary_merge(out_color: Color = "Code") -> ColoredOp:
    """Simple 2-ary (Code, Code) → out_color."""

    def body(left: object, right: object) -> Tuple[object, Residual]:
        return (left, right), EMPTY

    return ColoredOp(
        name="merge",
        source_colors=("Code", "Code"),
        target_color=out_color,
        residual=EMPTY,
        body=body,
    )


# ---------------------------------------------------------------------------
# Self-verifying smoke tests (historical)
# ---------------------------------------------------------------------------


def _assert_raises(exc_type: type[Exception], fn: Callable[[], object]) -> bool:
    caught = False
    try:
        fn()
    except exc_type:
        caught = True
    if not caught:
        raise AssertionError(f"Expected {exc_type.__name__} was not raised")
    return True


def _run_tests() -> None:
    f = make_principal_developer()
    _assert_raises(ArityMismatch, lambda: f.compose())
    _assert_raises(ArityMismatch, lambda: f.compose(identity("Code"), identity("Code")))
    _assert_raises(ColorMismatch, lambda: f.compose(identity("Evidence")))

    f_clean = ColoredOp(
        name=f.name,
        source_colors=f.source_colors,
        target_color=f.target_color,
        residual=EMPTY,
        body=f.body,
    )
    g = f_clean.compose(identity("Code"))
    assert g is f_clean, "right unit did not return the same object"

    idc = identity("Code")
    left = idc.compose(f_clean)
    probe = {"code": "x"}
    r1, res1 = f_clean(probe)
    r2, res2 = left(probe)
    assert r1 == r2
    assert res1 == res2

    def body_a(args: Tuple[object, ...]) -> Tuple[object, Residual]:
        return args[0], Residual(obligations=("from_A",), risk=0.2)

    def body_b(args: Tuple[object, ...]) -> Tuple[object, Residual]:
        return args[0], Residual(obligations=("from_B",), risk=0.4)

    a = ColoredOp("A", ("Code",), "Code", body_a, EMPTY)
    b = ColoredOp("B", ("Code",), "Code", body_b, EMPTY)
    composed = a.compose(b)
    result, resid = composed("payload")
    assert "from_A" in resid.obligations
    assert "from_B" in resid.obligations
    assert resid.risk == 0.4

    merge = make_binary_merge()
    code_op = nullary("Code", "pure_code", name="const_code")
    other_op = nullary("Code", "other_code", name="const_other")
    bundled = merge.compose(code_op, other_op)
    assert bundled.arity == 0
    val, r = bundled()
    assert val == ("pure_code", "other_code")

    apply = make_apply_contract()
    contract = nullary("Contract", {"inv": "x > 0"})
    pd = make_principal_developer()
    applied = apply.compose(pd, contract)
    assert applied.source_colors == ("Code",)
    assert applied.target_color == "Code"

    t = formal_compose(
        merge,
        Term(op=nullary("Code", 1)),
        Term(op=nullary("Code", 2)),
    )
    val, _ = t.evaluate()
    assert val == (1, 2)


if __name__ == "__main__":
    _run_tests()
    print("All coloured_operad constructor self-tests passed.")
