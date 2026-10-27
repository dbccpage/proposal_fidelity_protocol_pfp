"""Checked realization of the existing native normal form, not a second wire.

The model preserves provenance as well as the colour/schema typing projection.
It binds an actual native response to its inventory and ordered request before
host effects. The Lean decoder formalizes this JSON model; neither this check
nor its hashes constitute a proof of the Rust compiler or a remote signature.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json

PROFILE = "core.oewas.native-model.v1"
PLANAR = "core.oewas.operation-term.normal.v1"
REINDEXED = "core.oewas.operation-term.reindexed.v1"


class ModelBindingError(ValueError):
    """The actual native structure does not realize this exact request."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def canonical_id(domain, value):
    # Same named compact ASCII profile as kernel/canonical.rs, not RFC 8785.
    encoded = canonical({"domain": domain, "payload": value})
    if not encoded.isascii():
        raise ModelBindingError("native canonical profile requires ASCII")
    return "sha256:" + hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _equal(actual, expected, name):
    # JSON equality also distinguishes booleans from integer input coordinates.
    if canonical(actual) != canonical(expected):
        raise ModelBindingError(f"native {name} differs from the checked request")


def _port(slot, colour):
    return {"port_id": f"slot{slot}", "colour_id": colour, "schema_ref": f"inventory:{colour}:v1"}


def _operation(spec):
    return {"operation_id": spec["op_id"], "version": "v3",
        "input_ports": [_port(i, colour) for i, colour in enumerate(spec["inputs"])],
        "output_port": _port(0, spec["output"]), "executor_ref": "inventory-binding",
        "executor_digest": "sha256:" + sha(spec["binding"]), "tool_refs": [], "effects": [],
        "invocation_grade": "discipline", "authority_effect": "None", "authority_ceiling": "None"}


def _request_model(inventory, wire, input_order):
    """Realize the inventory boundary only; never execute a Python interpreter."""
    raw = inventory.model_dump(mode="json")
    specs = [op for skill in raw["skills"] for op in skill["ops"]]
    guards = [g for skill in raw["skills"] for g in skill["anti_ops"]]
    ids = [s["op_id"] for s in specs] + [g["op_id"] for g in guards]
    if len(set(ids)) != len(ids):
        raise ModelBindingError("duplicate inventory operation/guard")
    ops = {spec["op_id"]: spec for spec in specs}
    for g in guards:
        op = ops.get(g["guards"])
        if (op is None or type(g["slot"]) is not int or not 0 <= g["slot"] < len(op["inputs"])
                or op["inputs"][g["slot"]] != g["inspects"]):
            raise ModelBindingError("invalid guard slot")
    selected_guards = lambda op: [{key: g[key] for key in ("op_id", "guards", "slot", "inspects", "refusal")}
        for g in guards if g["guards"] == op]
    leaves, used, plan, occurrences = [], [], [], []

    def walk(node, path, parent_port=None):
        if len(path) > 32 or len(used) > 128 or len(leaves) > 128:
            raise ModelBindingError("native model resource bound exceeded")
        if type(node) is str:
            leaves.append(node)
            port = parent_port if parent_port is not None else _port(0, node)
            if port["colour_id"] != node:
                raise ModelBindingError("leaf colour differs from its ordered slot")
            return {"identity" if parent_port is None else "input": port}, [port], port, {"input": len(leaves) - 1}
        if type(node) is not dict or set(node) != {"op", "args"} or type(node["args"]) is not list:
            raise ModelBindingError("wire must be an exact operation/arguments object")
        spec = ops.get(node["op"])
        if spec is None or len(node["args"]) != len(spec["inputs"]):
            raise ModelBindingError("unknown operation or wrong arity")
        used.append(spec["op_id"])
        operation = _operation(spec)
        children, inputs, refs = [], [], []
        for slot, child in enumerate(node["args"]):
            tree, child_inputs, output, ref = walk(child, (*path, slot), operation["input_ports"][slot])
            expected = operation["input_ports"][slot]
            # Port names carry provenance; only colour and schema determine type.
            if any(output[key] != expected[key] for key in ("colour_id", "schema_ref")):
                raise ModelBindingError("child output type differs from parent input")
            children.append(tree)
            inputs.extend(child_inputs)
            refs.append(ref)
        ordinal = len(plan)
        plan.append({"op_id": spec["op_id"], "args": refs, "guards": selected_guards(spec["op_id"])})
        occurrences.append({"ordinal": ordinal, "path": list(path), "op_id": spec["op_id"],
            "operation_id": canonical_id("core.oewas.operation-spec.v1", operation),
            "operation": spec, "arg_refs": refs})
        return {"operation": operation, "children": children}, inputs, operation["output_port"], {"step": ordinal}

    tree, inputs, output, output_ref = walk(wire, ())
    if len(used) > 128 or len(leaves) > 128:
        raise ModelBindingError("native model occurrence bound exceeded")
    planar = {"tree": tree, "boundary": {"inputs": inputs, "output": output}}
    if input_order is None:
        order = list(range(len(inputs)))
        normal = planar
        term_profile = PLANAR
    else:
        if (type(input_order) not in (tuple, list) or any(type(i) is not int for i in input_order)
                or sorted(input_order) != list(range(len(inputs)))):
            raise ModelBindingError("input order must be an exact bijection")
        order = list(input_order)
        normal = {"schema_version": REINDEXED, "planar": planar, "external_to_planar": order,
            "boundary": {"inputs": [inputs[i] for i in order], "output": output}}
        term_profile = REINDEXED
    inverse = [0] * len(order)
    for external, index in enumerate(order): inverse[index] = external
    def route(ref):
        if "input" in ref: ref["input"] = inverse[ref["input"]]
    for step in plan:
        for ref in step["args"]: route(ref)
    route(output_ref)
    # Occurrence refs intentionally share the routed plan refs above.
    return raw, normal, canonical_id(term_profile, normal), plan, output_ref, occurrences, used, [leaves[i] for i in order], order, inverse


@dataclass(frozen=True)
class NativeModelBinding:
    """Immutable complete static model; executed prefixes remain in RunReceipt."""
    payload_json: str

    def __post_init__(self):
        value = json.loads(self.payload_json)
        if canonical(value) != self.payload_json or value.get("schema_version") != PROFILE:
            raise ModelBindingError("noncanonical native model binding")

    def to_json(self):
        self.__post_init__()
        return json.loads(self.payload_json)

    def digest(self):
        return hashlib.sha256(self.payload_json.encode("utf-8")).hexdigest()

    def with_input_digest(self, input_digest):
        if type(input_digest) is not str or len(input_digest) != 64 or any(c not in "0123456789abcdef" for c in input_digest):
            raise ModelBindingError("invalid input digest")
        value = self.to_json()
        value["input_digest"] = input_digest
        return replace(self, payload_json=canonical(value))

    def verify_invocation(self, snapshot):
        value = self.to_json()
        rows = value["occurrences"]
        if type(snapshot.ordinal) is not int or not 0 <= snapshot.ordinal < len(rows):
            raise ModelBindingError("invocation has no structural operation occurrence")
        row = rows[snapshot.ordinal]
        _equal(json.loads(snapshot.execution_json).get("native_model_occurrence"),
            self.occurrence_context(snapshot.ordinal), "execution coordinate")
        for actual, expected, label in (
            (snapshot.op_id, row["op_id"], "occurrence operation"),
            (json.loads(snapshot.operation_json), row["operation"], "operation provenance"),
            (snapshot.native_term_id, value["native_term_id"], "term"),
            (snapshot.inventory_digest, value["inventory_digest"], "inventory"),
            (snapshot.wire_digest, value["wire_digest"], "wire"),
            (snapshot.input_order, value["input_order"], "input order"),
            (snapshot.root_inputs, value["root_inputs"], "root inputs"),
            (snapshot.root_output, value["root_output"], "root output"),
        ): _equal(actual, expected, label)
        if "input_digest" in value:
            _equal(snapshot.input_digest, value["input_digest"], "actual inputs")

    def occurrence_context(self, ordinal):
        row = self.to_json()["occurrences"][ordinal]
        return {"model_digest": self.digest(), "ordinal": ordinal, "path": row["path"],
            "operation_id": row["operation_id"], "arg_refs": row["arg_refs"], "output_ref": {"step": ordinal}}

    def verify_receipt(self, receipt):
        from operads.skill_operad.resolver.resolver import wire_json
        value = self.to_json()
        for actual, expected, label in (
            (wire_json(receipt.wire), value["wire"], "receipt wire"),
            (receipt.input_order, value["input_order"], "receipt input order"),
            (sha({"wire": wire_json(receipt.wire), "input_order": receipt.input_order}), value["wire_digest"], "receipt request"),
            (receipt.native_term_id, value["native_term_id"], "receipt term"),
            (receipt.inventory_digest, value["inventory_digest"], "receipt inventory"),
            (receipt.native_plan_digest, sha({"steps": value["plan"], "output_ref": value["output_ref"]}), "receipt plan"),
            (receipt.input_digest, value.get("input_digest"), "receipt inputs"),
            (receipt.interpreter_version, value["interpreter_version"], "receipt interpreter"),
        ): _equal(actual, expected, label)
        if len(receipt.steps) > len(value["occurrences"]):
            raise ModelBindingError("executed prefix exceeds structural model")
        for ordinal, (step, row) in enumerate(zip(receipt.steps, value["occurrences"])):
            _equal(step.op_id, row["op_id"], "executed prefix operation")
            _equal(step.operation_digest, sha(row["operation"]), "executed operation provenance")
            _equal(step.execution.get("native_model_occurrence"), self.occurrence_context(ordinal), "executed coordinate")
        if receipt.completed and len(receipt.steps) != len(value["occurrences"]):
            raise ModelBindingError("completed receipt omits an operation occurrence")
        if receipt.completed and "step" in value["output_ref"]:
            _equal(sha(receipt.output), receipt.steps[value["output_ref"]["step"]].output_digest,
                "returned operation output")


def realize_native_result(inventory, wire, result, *, input_order=None, values=None):
    """Validate the complete actual response before any external executor runs."""
    from operads.skill_operad.resolver.resolver import wire_json
    raw_wire = wire_json(wire)
    try:
        raw, normal, term_id, plan, output_ref, occurrences, used, leaves, order, inverse = _request_model(inventory, raw_wire, input_order)
        expected = {"status": "VALID", "normal_form": normal, "term_id": term_id,
            "inventory_sha256": sha(raw), "execution_plan": plan, "output_ref": output_ref,
            "operation_ids": used, "leaves": leaves, "authority_effect": "None",
            "guards": [g for skill in raw["skills"] for guard in skill["anti_ops"]
                if guard["guards"] in used for g in [{key: guard[key] for key in ("op_id", "guards", "slot", "inspects", "refusal")}]]}
        if type(result) is not dict:
            raise ModelBindingError("native result must be an object")
        for key, value in expected.items(): _equal(result.get(key), value, key)
        if input_order is not None:
            _equal(result.get("input_order"), list(input_order), "input order")
            _equal(result.get("request_binding"), {"wire": raw_wire, "input_order": list(input_order), "values": values}, "request binding")
        elif "input_order" in result or "request_binding" in result:
            raise ModelBindingError("unsolicited reindexing")
        payload = {"schema_version": PROFILE, "normal_form": normal, "native_term_id": term_id,
            "interpreter_version": "core.oewas.native-plan-host.v1" if input_order is None
                else "core.oewas.native-plan-host.reindexed.v1",
            "inventory_digest": sha(raw), "wire": raw_wire,
            "wire_digest": sha({"wire": raw_wire, "input_order": input_order}),
            "input_order": input_order, "external_to_planar": order, "planar_to_external": inverse,
            "plan": plan, "output_ref": output_ref, "occurrences": occurrences,
            "root_inputs": leaves, "root_output": normal["boundary"]["output"]["colour_id"]}
        return NativeModelBinding(canonical(payload))
    except (KeyError, IndexError, TypeError, ValueError, RecursionError) as exc:
        if isinstance(exc, ModelBindingError): raise
        raise ModelBindingError(f"invalid native realization: {type(exc).__name__}") from exc
