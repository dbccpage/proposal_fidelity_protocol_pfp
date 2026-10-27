"""OEWAS resolver: compose a typed op tree from inputs to a goal port, and run it.

``compose`` searches the versioned op inventory (``skill_operad/yaml/op_inventory.yaml``) for the
smallest planar tree of ops whose leaves are drawn from the given input ports and whose root is
the goal port. Every candidate is type-checked with ``planar.formal_compose``. It returns a
``Composition`` or a typed ``Refusal`` (``UNKNOWN_PORT``, ``NO_ADMISSIBLE_PATH``).

``run`` executes a wiring (a composition, or a skill's own wiring) through executors and
detectors that host code registers by op id. A binding in the inventory says which code
implements a step; it is not a call signature, so nothing is called through it. ``run`` checks
everything before it executes anything: the wiring types (``TYPE_MISMATCH``), an executor for
every op and a detector for every anti-op that guards one (``NOT_EXECUTABLE``), and a value for
every leaf (``MISSING_INPUT``). While running, each anti-op inspects its slot before the op it
guards; if it fires, the run stops with the anti-op's refusal code.

Usage::

    python -m operads.skill_operad.resolver.resolver compose --inputs Paper,Code --goal Audit
    python -m operads.skill_operad.resolver.resolver run \\
        --skill techne-silent-failure-hunter --input 'Code=["path/to/file.py"]'

AuthorityEffect: None. A receipt records what ran; it grants nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from operads.skill_operad.domain.planar import (
    ArityMismatch,
    ColorMismatch,
)
from operads.skill_operad.resolver import subcolour_schema
from operads.skill_operad.skill_compiler.op_inventory import (
    INVENTORY_PATH,
    AntiOpSpec,
    OpInventory,
    OpSpec,
    Wire,
    load_inventory,
    wire_term,
)

RECEIPT_SCHEMA = "core.oewas.run_receipt.v2"
INTERPRETER_VERSION = "core.oewas.python-oracle.v2"
DEFAULT_MAX_OPS = 4

Executor = Callable[..., object]
Detector = Callable[[Any], bool]


@dataclass(frozen=True)
class Refusal:
    code: str
    message: str

    def to_json(self) -> dict[str, str]:
        return {"status": "REFUSED", "code": self.code, "message": self.message}


@dataclass(frozen=True)
class Composition:
    wire: Wire | str
    goal: str
    ops: tuple[str, ...]
    leaves: tuple[str, ...]
    unused_inputs: tuple[str, ...]
    anti_ops: tuple[str, ...]
    alternatives: int

    def to_json(self) -> dict[str, object]:
        return {
            "status": "COMPOSED",
            "goal": self.goal,
            "wire": wire_json(self.wire),
            "ops": list(self.ops),
            "leaves": list(self.leaves),
            "unused_inputs": list(self.unused_inputs),
            "anti_ops": list(self.anti_ops),
            "alternatives": self.alternatives,
        }


@dataclass(frozen=True)
class ExecutionResult:
    value: object
    model: str | None = None
    usage: dict | None = None
    cost_micro_usd: int | None = None
    verdict: str = "UNVERIFIED"
    context: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.cost_micro_usd is not None and (type(self.cost_micro_usd) is not int or self.cost_micro_usd < 0):
            raise ValueError("cost must be nonnegative exact micro-USD or unknown")
        if self.usage is not None and type(self.usage) is not dict:
            raise TypeError("usage must be an object or unknown")
        if type(self.context) is not dict or type(self.verdict) is not str or not self.verdict:
            raise TypeError("execution context and verdict are required")


@dataclass(frozen=True)
class Step:
    op_id: str
    output_port: str
    output_digest: str
    input_digest: str = ""
    operation_digest: str = ""
    execution: dict = field(default_factory=dict)


@dataclass(frozen=True)
class InvocationSnapshot:
    """Complete immutable JSON observation of an actually executed occurrence.

    Native validation covers the structural term. These args, result and input
    digest are measured by the invoking host; they are not native evaluation of
    external/PFP effects. Digests use this module's named compact JSON profile.
    """

    ordinal: int
    op_id: str
    args_json: str
    output_json: str
    operation_json: str
    execution_json: str
    inventory_digest: str
    wire_digest: str
    input_digest: str
    root_inputs: tuple[str, ...]
    root_output: str
    input_order: tuple[int, ...] | None = None
    native_term_id: str | None = None

    def __post_init__(self):
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise TypeError("occurrence ordinal must be a nonnegative integer")
        _require_text(self.op_id)
        _require_profile(self.root_inputs, self.root_output)
        for value in (self.inventory_digest, self.wire_digest, self.input_digest):
            _require_digest(value)
        args = _require_canonical_json(self.args_json, list)
        _require_canonical_json(self.output_json)
        operation = _require_canonical_json(self.operation_json, dict)
        _require_canonical_json(self.execution_json, dict)
        if operation.get("op_id") != self.op_id or len(args) != len(operation.get("inputs", ())):
            raise ValueError("snapshot operation/argument binding differs")
        if self.input_order is not None and (
            type(self.input_order) is not tuple
            or any(type(index) is not int for index in self.input_order)
            or sorted(self.input_order) != list(range(len(self.root_inputs)))
        ):
            raise TypeError("snapshot input order must be an exact bijection")
        if self.native_term_id is not None:
            _require_text(self.native_term_id)

    def to_json(self) -> dict:
        self.__post_init__()
        return {"schema": "core.oewas.invocation-snapshot.v1", **asdict(self)}

    def digest(self) -> str:
        return digest(self.to_json())


@dataclass(frozen=True)
class CheckedOccurrenceRejection:
    """Host callback decision; data alone never selects or executes a checker."""

    invocation_digest: str
    gate_id: str
    finding_code: str
    evidence_digest: str
    scope_json: str

    def __post_init__(self):
        _require_digest(self.invocation_digest)
        _require_digest(self.evidence_digest)
        _require_text(self.gate_id)
        _require_text(self.finding_code)
        _require_canonical_json(self.scope_json, dict)


@dataclass(frozen=True)
class NullTree:
    """Stopped root profile with retained checked occurrence evidence, not proof."""

    root_inputs: tuple[str, ...]
    root_output: str
    invocations: tuple[InvocationSnapshot, ...]
    rejected_occurrences: tuple[CheckedOccurrenceRejection, ...]

    def __post_init__(self):
        _require_profile(self.root_inputs, self.root_output)
        if (type(self.invocations) is not tuple or type(self.rejected_occurrences) is not tuple
                or not self.invocations or len(self.invocations) != len(self.rejected_occurrences)):
            raise TypeError("bottom requires paired actual snapshots and checked decisions")
        if len({item.ordinal for item in self.invocations if type(item) is InvocationSnapshot}) != len(self.invocations):
            raise ValueError("bottom occurrence ordinals must be unique")
        for snapshot, rejection in zip(self.invocations, self.rejected_occurrences):
            if type(snapshot) is not InvocationSnapshot or type(rejection) is not CheckedOccurrenceRejection:
                raise TypeError("bottom requires the checked immutable contracts")
            rejection.__post_init__()
            if (snapshot.root_inputs != self.root_inputs or snapshot.root_output != self.root_output
                    or rejection.invocation_digest != snapshot.digest()):
                raise ValueError("bottom occurrence/profile binding differs")

    def to_json(self) -> dict:
        self.__post_init__()
        return {"schema": "core.oewas.null-tree.v1", "root_inputs": list(self.root_inputs),
            "root_output": self.root_output, "invocations": [item.to_json() for item in self.invocations],
            "rejected_occurrences": [asdict(item) for item in self.rejected_occurrences]}


@dataclass(frozen=True)
class RunReceipt:
    wire: Wire | str
    steps: tuple[Step, ...]
    output: object = None
    refusal: Refusal | None = None
    anti_ops_cleared: tuple[str, ...] = field(default=())

    input_digest: str = ""
    inventory_digest: str = ""
    interpreter_version: str = INTERPRETER_VERSION
    native_term_id: str | None = None
    native_plan_digest: str | None = None
    guard_events: tuple[dict, ...] = ()
    input_order: tuple[int, ...] | None = None
    null_tree: NullTree | None = None
    model_binding_json: str | None = None

    def __post_init__(self):
        if self.model_binding_json is not None:
            from operads.contracts.operad_realization_v1 import NativeModelBinding
            NativeModelBinding(self.model_binding_json).verify_receipt(self)
        if self.null_tree is not None:
            if (type(self.null_tree) is not NullTree or self.refusal is None
                    or self.refusal.code != "CHECKED_OCCURRENCE_REJECTED" or self.output is not None):
                raise ValueError("checked bottom requires a stopped receipt with no returned value")
            self.null_tree.__post_init__()
            for snapshot in self.null_tree.invocations:
                if (snapshot.inventory_digest != self.inventory_digest or snapshot.input_digest != self.input_digest
                        or snapshot.input_order != self.input_order or snapshot.native_term_id != self.native_term_id
                        or snapshot.wire_digest != digest({"wire": wire_json(self.wire), "input_order": self.input_order})
                        or snapshot.ordinal >= len(self.steps)):
                    raise ValueError("bottom must bind this exact run and recorded occurrence")
                step = self.steps[snapshot.ordinal]
                if (step.op_id != snapshot.op_id or step.input_digest != digest(json.loads(snapshot.args_json))
                        or step.output_digest != digest(json.loads(snapshot.output_json))
                        or step.operation_digest != digest(json.loads(snapshot.operation_json))
                        or _canonical_json(step.execution) != snapshot.execution_json):
                    raise ValueError("bottom must retain the exact executed step")

    @property
    def completed(self) -> bool:
        return self.refusal is None

    def to_json(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema": "core.oewas.run_receipt.v5" if self.model_binding_json is not None else (
                "core.oewas.run_receipt.v4" if self.null_tree is not None else (
                    RECEIPT_SCHEMA if self.input_order is None else "core.oewas.run_receipt.v3")),
            **({} if self.model_binding_json is None else {"native_model": json.loads(self.model_binding_json)}),
            **({} if self.null_tree is None else {"null_tree": self.null_tree.to_json()}),
            **({} if self.input_order is None else {"input_order": list(self.input_order)}),
            "guard_events": list(self.guard_events),
            "authority_effect": "None",
            "status": "COMPLETED" if self.completed else "REFUSED",
            "wire": wire_json(self.wire),
            "steps": [dict(asdict(s), op=s.op_id) for s in self.steps],
            "input_digest": self.input_digest,
            "inventory_digest": self.inventory_digest,
            "interpreter_version": self.interpreter_version,
            "native_term_id": self.native_term_id,
            "native_plan_digest": self.native_plan_digest,
            "anti_ops_cleared": list(self.anti_ops_cleared),
            "refusal": self.refusal.to_json() if self.refusal else None,
            "output": self.output if self.completed else None,
        }


def wire_json(node: Wire | str) -> object:
    if isinstance(node, str):
        return node
    return {"op": node.op, "args": [wire_json(arg) for arg in node.args]}


def all_ops(inventory: OpInventory) -> dict[str, OpSpec]:
    return {op.op_id: op for skill in inventory.skills for op in skill.ops}


def all_anti_ops(inventory: OpInventory) -> tuple[AntiOpSpec, ...]:
    return tuple(anti for skill in inventory.skills for anti in skill.anti_ops)


def declared_ports(inventory: OpInventory) -> set[str]:
    ports = {p for op in all_ops(inventory).values() for p in (*op.inputs, op.output)}
    ports |= {f"{colour}.{sub}" for colour, subs in inventory.subcolours.items() for sub in subs}
    return ports


def _wire_ops(node: Wire | str) -> list[str]:
    if isinstance(node, str):
        return []
    return [node.op] + [op for arg in node.args for op in _wire_ops(arg)]


def _wire_leaves(node: Wire | str) -> list[str]:
    if isinstance(node, str):
        return [node]
    return [leaf for arg in node.args for leaf in _wire_leaves(arg)]


def _candidates(
    port: str, avail: Counter[str], budget: int, by_output: Mapping[str, tuple[OpSpec, ...]]
) -> Iterator[tuple[Wire | str, Counter[str], int]]:
    """Yield (tree, inputs used, ops used) for every tree yielding ``port`` within the budget."""
    if avail[port] > 0:
        yield port, Counter({port: 1}), 0
    if budget <= 0:
        return
    for op in by_output.get(port, ()):
        for args, used, count in _fill(op.inputs, avail, budget - 1, by_output):
            yield Wire(op=op.op_id, args=args), used, count + 1


def _fill(
    slots: tuple[str, ...],
    avail: Counter[str],
    budget: int,
    by_output: Mapping[str, tuple[OpSpec, ...]],
) -> Iterator[tuple[tuple[Wire | str, ...], Counter[str], int]]:
    if not slots:
        yield (), Counter(), 0
        return
    for head, used, count in _candidates(slots[0], avail, budget, by_output):
        for rest, rest_used, rest_count in _fill(slots[1:], avail - used, budget - count, by_output):
            yield (head, *rest), used + rest_used, count + rest_count


def compose(
    inventory: OpInventory,
    inputs: list[str],
    goal: str,
    *,
    max_ops: int = DEFAULT_MAX_OPS,
    bound_only: bool = False,
) -> Composition | Refusal:
    """Return the smallest typed tree from ``inputs`` to ``goal``, or a typed refusal.

    Smallest means fewest ops; ties go to the tree whose JSON sorts first, so the answer does
    not depend on dictionary order. A tree uses each input at most once and needs at least one op.
    """
    ports = declared_ports(inventory)
    unknown = sorted({p for p in (*inputs, goal) if p not in ports})
    if unknown:
        return Refusal("UNKNOWN_PORT", f"no op takes or yields {', '.join(unknown)}")
    ops = {
        op_id: op for op_id, op in all_ops(inventory).items() if op.binding or not bound_only
    }
    by_output: dict[str, list[OpSpec]] = {}
    for op in sorted(ops.values(), key=lambda o: o.op_id):
        by_output.setdefault(op.output, []).append(op)
    frozen = {port: tuple(group) for port, group in by_output.items()}

    if type(max_ops) is not int or not 0 <= max_ops <= 4 or len(inputs) > 128:
        return Refusal("COMPOSITION_LIMIT", "max_ops must be0..4; at most128 ordered inputs")
    found: list[tuple[int, str, Wire | str]] = []
    for tree, _used, count in _candidates(goal, Counter(inputs), max_ops, frozen):
        remaining=iter(inputs)
        if not all(any(available==leaf for available in remaining) for leaf in _wire_leaves(tree)):
            continue
        wire_term(tree, ops)
        found.append((count, json.dumps(wire_json(tree), sort_keys=True), tree))
    if not found:
        scope = "bound ops" if bound_only else "ops"
        return Refusal(
            "NO_ADMISSIBLE_PATH",
            f"no tree of at most {max_ops} {scope} takes {inputs} to {goal}",
        )
    _count, _key, best = min(found, key=lambda item: item[:2])
    leaves = _wire_leaves(best)
    used_counts=Counter(leaves)
    unused=[]
    for port in inputs:
        if used_counts[port]: used_counts[port]-=1
        else: unused.append(port)
    used_ops = set(_wire_ops(best))
    anti = sorted(a.op_id for a in all_anti_ops(inventory) if a.guards in used_ops)
    return Composition(
        wire=best,
        goal=goal,
        ops=tuple(_wire_ops(best)),
        leaves=tuple(leaves),
        unused_inputs=tuple(unused),
        anti_ops=tuple(anti),
        alternatives=len(found) - 1,
    )


def digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_text(value):
    if type(value) is not str or not value.strip():
        raise TypeError("nonempty literal text required")


def _require_digest(value):
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise TypeError("lowercase SHA256 hex required")


def _require_profile(inputs, output):
    if type(inputs) is not tuple:
        raise TypeError("ordered profile must be an immutable tuple")
    for port in (*inputs, output):
        _require_text(port)


def _canonical_json(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    text.encode("utf-8")
    return text


def _require_canonical_json(text, expected=None):
    if type(text) is not str:
        raise TypeError("canonical JSON text required")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    value = json.loads(text, object_pairs_hook=unique)
    if (expected is not None and type(value) is not expected) or _canonical_json(value) != text:
        raise ValueError("canonical JSON value differs")
    return value


def _occurrence_binding(inventory_digest, input_digest, wire, input_order, root_inputs, root_output, native_term_id=None):
    return {"inventory_digest": inventory_digest, "input_digest": input_digest,
        "wire_digest": digest({"wire": wire_json(wire), "input_order": input_order}),
        "input_order": input_order, "root_inputs": tuple(root_inputs), "root_output": root_output,
        "native_term_id": native_term_id}


def _preflight(
    inventory: OpInventory,
    wire: Wire,
    values: Mapping[str, object] | Sequence[object],
    executors: Mapping[str, Executor],
    detectors: Mapping[str, Detector],
) -> Refusal | None:
    specs=[op for skill in inventory.skills for op in (*skill.ops,*skill.anti_ops)]
    if len({s.op_id for s in specs}) != len(specs):
        return Refusal("DUPLICATE_OPERATION", "operation and guard identifiers must be unique")
    ops = all_ops(inventory)
    try:
        wire_term(wire, ops)
    except (KeyError, ArityMismatch, ColorMismatch) as exc:
        return Refusal("TYPE_MISMATCH", str(exc).strip("'\""))
    used_ops = set(_wire_ops(wire))
    missing = sorted(op for op in used_ops if op not in executors)
    guards = [a for a in all_anti_ops(inventory) if a.guards in used_ops]
    for anti in guards:
        op = ops[anti.guards]
        if anti.slot >= len(op.inputs) or op.inputs[anti.slot] != anti.inspects:
            return Refusal("GUARD_SLOT_INVALID", f"invalid guard {anti.op_id}")
    missing += sorted(a.op_id for a in guards if a.op_id not in detectors)
    if missing:
        return Refusal("NOT_EXECUTABLE", f"no host executor or detector for {', '.join(missing)}")
    for anti in guards:
        if anti.typed_contract_id is not None and getattr(detectors[anti.op_id], "spec_id", None) != anti.typed_contract_id:
            return Refusal("ANTI_OP_UNBOUND", f"{anti.op_id} requires admitted typed detector wrapper")
    leaves = _wire_leaves(wire)
    if not isinstance(values, Mapping):
        if not isinstance(values, (list, tuple)) or len(values) != len(leaves):
            return Refusal("MISSING_INPUT", "ordered input count differs from leaf occurrences")
        return None
    if len(set(leaves)) != len(leaves):
        return Refusal("AMBIGUOUS_INPUT", "repeated colours require ordered input occurrences")
    absent = sorted({leaf for leaf in leaves if leaf not in values})
    if absent:
        return Refusal("MISSING_INPUT", f"no value for input port {', '.join(absent)}")
    return None


class _Stop(Exception):
    def __init__(self, refusal: Refusal, null_tree: NullTree | None = None) -> None:
        super().__init__(refusal.message)
        self.refusal = refusal
        self.null_tree = null_tree



def execute_step(op_id, op, args, guards, executors, detectors, steps, cleared, guard_events,
                 *, occurrence_checker=None, occurrence_binding=None, model_occurrence=None):
    if occurrence_checker is not None and (not callable(occurrence_checker) or type(occurrence_binding) is not dict):
        raise _Stop(Refusal("OCCURRENCE_CHECK_INVALID", "host callback and invocation binding required"))
    for anti in guards:
        try:
            fired = detectors[anti.op_id](args[anti.slot])
            if type(fired) is not bool:
                raise TypeError("detector must return bool")
        except Exception as exc:
            state=getattr(exc,"code",type(exc).__name__)
            guard_events.append({"guard":anti.op_id,"state":state,"subject_digest":digest(args[anti.slot])})
            code="DETECTOR_UNAVAILABLE" if state in {"NOT_EXTERNALLY_ADMITTED","HOST_HEALTH_UNAVAILABLE","HOST_HEALTH_UNHEALTHY","HOST_HEALTH_UNVERIFIED"} else "DETECTOR_FAILED"
            raise _Stop(Refusal(code, f"{anti.op_id}: {state}")) from exc
        activation=getattr(detectors[anti.op_id],"last_activation",None)
        event={"guard":anti.op_id,"state":"FIRED" if fired else "CLEAR","subject_digest":digest(args[anti.slot])}
        if activation is not None:
            event["activation"]=asdict(activation) if hasattr(activation,"__dataclass_fields__") else activation
            if isinstance(activation,dict) and "state" in activation:
                event["state"]=activation["state"]
        guard_events.append(event)
        if fired:
            raise _Stop(Refusal(
                anti.refusal, f"{anti.op_id} fired on slot {anti.slot} of {op_id}"
            ))
        if event["state"] == "CLEAR":
            cleared.append(anti.op_id)
    if occurrence_checker is not None:
        try:
            invocation_args_json = _canonical_json(args)
            invocation_operation_json = _canonical_json(op.model_dump(mode="json"))
            _require_canonical_json(invocation_args_json, list)
            _require_canonical_json(invocation_operation_json, dict)
        except (TypeError, ValueError) as exc:
            raise _Stop(Refusal("OCCURRENCE_CHECK_INVALID", f"invalid invocation input: {type(exc).__name__}")) from exc
    try:
        output = executors[op_id](*args)
    except Exception as exc:
        raise _Stop(Refusal("EXECUTOR_FAILED", f"{op_id}: {type(exc).__name__}")) from exc
    callback=executors[op_id]
    try:
        source=inspect.getsource(callback).encode("utf8")
    except (TypeError,OSError):
        try:
            source=inspect.getsource(type(callback)).encode("utf8")
        except (TypeError,OSError):
            source=repr(type(callback)).encode("utf8")
    execution = {"executor_source_digest":hashlib.sha256(source).hexdigest(),"cost_micro_usd":None}
    if isinstance(output, ExecutionResult):
        details = asdict(output)
        output = details.pop("value")
        execution.update(details)
    if model_occurrence is not None:
        # Host-created coordinates are recorded after untrusted executor metadata.
        execution["native_model_occurrence"] = model_occurrence
    try:
        output_digest = digest(output)
    except (TypeError, ValueError) as exc:
        raise _Stop(Refusal("OUTPUT_NOT_JSON", f"{op_id} returned {exc}")) from exc
    if (shape := subcolour_schema.output_problem(op.output, output)) is not None:
        raise _Stop(Refusal("OUTPUT_SCHEMA_REFUSED", f"{op_id} -> {op.output}: {shape}"))
    steps.append(Step(op_id, op.output, output_digest,
        hashlib.sha256(invocation_args_json.encode("utf-8")).hexdigest() if occurrence_checker is not None else digest(args),
        hashlib.sha256(invocation_operation_json.encode("utf-8")).hexdigest() if occurrence_checker is not None else digest(op.model_dump(mode="json")), execution))
    if occurrence_checker is not None:
        try:
            snapshot = InvocationSnapshot(ordinal=len(steps) - 1, op_id=op_id,
                args_json=invocation_args_json, output_json=_canonical_json(output),
                operation_json=invocation_operation_json,
                execution_json=_canonical_json(execution), **occurrence_binding)
            before_digest = snapshot.digest()
        except (TypeError, ValueError) as exc:
            raise _Stop(Refusal("OCCURRENCE_CHECK_INVALID", f"invalid invocation observation: {type(exc).__name__}")) from exc
        try:
            decision = occurrence_checker(snapshot)
        except Exception as exc:
            raise _Stop(Refusal("OCCURRENCE_CHECK_UNAVAILABLE", f"host occurrence check: {type(exc).__name__}")) from exc
        try:
            if snapshot.digest() != before_digest:
                raise ValueError("checker mutated the invocation observation")
            if decision is not None:
                if type(decision) is not CheckedOccurrenceRejection:
                    raise TypeError("host checker must return a typed decision or None")
                decision.__post_init__()
                if decision.invocation_digest != before_digest:
                    raise ValueError("checker decision is for another occurrence")
                bottom = NullTree(snapshot.root_inputs, snapshot.root_output, (snapshot,), (decision,))
        except (TypeError, ValueError) as exc:
            raise _Stop(Refusal("OCCURRENCE_CHECK_INVALID", f"invalid host decision: {type(exc).__name__}")) from exc
        if decision is not None:
            raise _Stop(Refusal("CHECKED_OCCURRENCE_REJECTED", f"{decision.gate_id}: {decision.finding_code}"), bottom)
    return output

def run(
    inventory: OpInventory,
    wire: Wire,
    values: Mapping[str, object] | Sequence[object],
    executors: Mapping[str, Executor],
    detectors: Mapping[str, Detector],
    *,
    input_order: Sequence[int] | None = None,
    occurrence_checker: Callable[[InvocationSnapshot], CheckedOccurrenceRejection | None] | None = None,
) -> RunReceipt:
    """Run bottom-up with pre-execution guards and an optional host occurrence check.

    A checker observes each completed Step before its value reaches a parent.
    Only its exact typed, bound rejection creates the profile-preserving v4
    NullTree. Model-shaped JSON does not select this host port. Enabled checks
    use an explicit input order; leaving the port unused retains v2/v3 bytes.
    """
    inventory_digest = digest(inventory.model_dump(mode="json"))
    try:
        input_digest = digest(values)
    except (TypeError, ValueError):
        return RunReceipt(wire, (), refusal=Refusal("INPUT_NOT_JSON", "inputs must be finite JSON"), inventory_digest=inventory_digest)
    binding = dict(input_digest=input_digest, inventory_digest=inventory_digest)
    if occurrence_checker is not None:
        if not callable(occurrence_checker):
            return RunReceipt(wire, (), refusal=Refusal("OCCURRENCE_CHECK_INVALID", "host checker must be callable"), **binding)
        if input_order is None:
            input_order = tuple(range(len(_wire_leaves(wire))))
    if input_order is not None:
        leaves = _wire_leaves(wire)
        if (not isinstance(input_order, (list, tuple))
                or any(type(i) is not int for i in input_order)
                or sorted(input_order) != list(range(len(leaves)))):
            return RunReceipt(wire, (), refusal=Refusal("INVALID_INPUT_PERMUTATION", "expected external-to-planar bijection"), **binding)
        binding.update(input_order=tuple(input_order), interpreter_version="core.oewas.python-oracle.reindexed.v1")
    refusal = _preflight(inventory, wire, values, executors, detectors)
    if refusal:
        return RunReceipt(wire=wire, steps=(), refusal=refusal, **binding)
    ops = all_ops(inventory)
    anti_by_op: dict[str, list[AntiOpSpec]] = {}
    for anti in all_anti_ops(inventory):
        anti_by_op.setdefault(anti.guards, []).append(anti)
    steps: list[Step] = []
    cleared: list[str] = []
    guard_events: list[dict] = []
    leaves = _wire_leaves(wire)
    external_leaves = leaves if input_order is None else [leaves[i] for i in input_order]
    ordered = list(values) if not isinstance(values, Mapping) else [values[p] for p in external_leaves]
    if input_order is not None:
        planar = [None] * len(ordered)
        for external, target in enumerate(input_order):
            planar[target] = ordered[external]
        ordered = planar
    occurrences = iter(ordered)
    occurrence_binding = _occurrence_binding(inventory_digest, input_digest, wire,
        tuple(input_order) if input_order is not None else None, external_leaves,
        wire if isinstance(wire, str) else ops[wire.op].output) if occurrence_checker is not None else None

    def evaluate(node: Wire | str) -> object:
        if isinstance(node, str):
            return next(occurrences)
        args = [evaluate(arg) for arg in node.args]
        return execute_step(node.op, ops[node.op], args, anti_by_op.get(node.op, ()), executors, detectors, steps, cleared, guard_events,
            occurrence_checker=occurrence_checker, occurrence_binding=occurrence_binding)

    try:
        output = evaluate(wire)
    except _Stop as stop:
        return RunReceipt(wire, tuple(steps), refusal=stop.refusal, null_tree=stop.null_tree,
            anti_ops_cleared=tuple(cleared), guard_events=tuple(guard_events), **binding)
    return RunReceipt(wire, tuple(steps), output=output, anti_ops_cleared=tuple(cleared), guard_events=tuple(guard_events), **binding)


def _parse_input(text: str) -> tuple[str, object]:
    port, sep, payload = text.partition("=")
    if not sep:
        raise argparse.ArgumentTypeError(f"{text!r} is not PORT=JSON")
    return port, json.loads(payload)


def main(argv: list[str] | None = None) -> int:
    from .executors import HOST_DETECTORS, HOST_EXECUTORS

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    comp = sub.add_parser("compose", help="find the smallest typed tree from inputs to a goal")
    comp.add_argument("--inputs", required=True, help="comma-separated input ports")
    comp.add_argument("--goal", required=True)
    comp.add_argument("--max-ops", type=int, default=DEFAULT_MAX_OPS)
    comp.add_argument("--bound-only", action="store_true", help="use only ops bound to code")
    go = sub.add_parser("run", help="run a skill's wiring through the host executors")
    go.add_argument("--skill", required=True)
    go.add_argument("--input", action="append", type=_parse_input, default=[])
    args = parser.parse_args(argv)

    inventory = load_inventory(args.repo_root / INVENTORY_PATH)
    if args.command == "compose":
        result = compose(
            inventory,
            [p for p in args.inputs.split(",") if p],
            args.goal,
            max_ops=args.max_ops,
            bound_only=args.bound_only,
        )
        print(json.dumps(result.to_json(), indent=2, sort_keys=True))
        return 0 if isinstance(result, Composition) else 1
    skill = next((s for s in inventory.skills if s.skill_id == args.skill), None)
    if skill is None:
        print(json.dumps(Refusal("UNKNOWN_SKILL", args.skill).to_json(), indent=2))
        return 1
    from .native_runtime import run_native
    receipt = run_native(inventory, skill.wiring, dict(args.input), HOST_EXECUTORS, HOST_DETECTORS)
    print(json.dumps(receipt.to_json(), indent=2, sort_keys=True, default=str))
    return 0 if receipt.completed else 1


if __name__ == "__main__":
    sys.exit(main())
