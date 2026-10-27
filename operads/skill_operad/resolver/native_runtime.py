"""Use the existing workflow action and Rust operad kernel before effects.

Python run is the differential/reference interpreter. Runtime callers use
run_native; external host and PFP functions are explicitly injected.
"""
from __future__ import annotations

import json
from collections.abc import Mapping

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err
from .resolver import (
    Refusal, RunReceipt, digest, wire_json, all_ops, execute_step, _Stop,
    _wire_leaves, _occurrence_binding,
)
from ..skill_compiler.op_inventory import AntiOpSpec
from operads.contracts.operad_realization_v1 import (
    ModelBindingError, realize_native_result,
)


class NativeOperadRefusal(ValueError):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


_NATIVE_VALIDATE_CACHE: dict[str, str] = {}


def native_validate(inventory, wire, *, host=None, values=None, input_order=None):
    inventory_json = json.dumps(inventory.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload = {"command":"operad", "inventory_json":inventory_json, "wire":wire_json(wire)}
    if values is not None:
        payload["values"] = list(values)
    if input_order is not None:
        if not isinstance(input_order, (list, tuple)) or any(type(i) is not int for i in input_order):
            raise NativeOperadRefusal("INVALID_INPUT_PERMUTATION", "expected explicit integer input occurrences")
        payload["input_order"] = list(input_order)
    cache_key = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) if host is None else None
    if cache_key is not None and cache_key in _NATIVE_VALIDATE_CACHE:
        return json.loads(_NATIVE_VALIDATE_CACHE[cache_key])
    native = host or RustSymbolGameHost()
    response = native.invoke_runtime("workflow_graph", payload)
    if isinstance(response, Err):
        raise NativeOperadRefusal(response.error.code, response.error.message)
    envelope = response.value
    if not envelope.get("success"):
        error = envelope.get("error") or {}
        if not isinstance(error,dict):
            raise NativeOperadRefusal("NATIVE_OPERAD_FAILED",str(error))
        raise NativeOperadRefusal(error.get("code", "NATIVE_OPERAD_FAILED"), str(error.get("message", error)))
    result = envelope["result"]
    if result.get("refusal"):
        error=result["refusal"]
        raise NativeOperadRefusal(error["code"],error["message"])
    result = result.get("outcome",result)
    if result.get("status") != "VALID" or result.get("inventory_sha256") != digest(inventory.model_dump(mode="json")):
        raise NativeOperadRefusal("NATIVE_OPERAD_BINDING", "native term is not bound to this inventory")
    if result.get("input_order") != (None if input_order is None else list(input_order)):
        raise NativeOperadRefusal("NATIVE_OPERAD_BINDING", "native term is not bound to this input order")
    if input_order is not None:
        requested = {"wire": payload["wire"], "input_order": payload["input_order"], "values": payload.get("values")}
        if digest(result.get("request_binding")) != digest(requested):
            raise NativeOperadRefusal("NATIVE_OPERAD_BINDING", "native term is not bound to this wire and values")
    try:
        realize_native_result(inventory, wire, result, input_order=input_order, values=payload.get("values"))
    except ModelBindingError as exc:
        raise NativeOperadRefusal("NATIVE_MODEL_BINDING", str(exc)) from exc
    if cache_key is not None:
        _NATIVE_VALIDATE_CACHE[cache_key] = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return result


def run_native(inventory, wire, values, executors, detectors, *, host=None, input_order=None,
               occurrence_checker=None):
    """Dispatch the native ordered plan, never reconstruct a Python term.

    The optional host occurrence checker selects an explicit identity order when
    none was given, so native plan readback binds the exact wire/order/inventory.
    Native values stay absent: external/PFP executors run here, and their actual
    ordered arguments/results and input digest bind the immutable host snapshot.
    Unused legacy paths and their receipt projections remain unchanged.
    """
    steps=[]; cleared=[]; guard_events=[]
    binding={"inventory_digest":digest(inventory.model_dump(mode="json")),"interpreter_version":"core.oewas.native-plan-host.v1"}
    try:
        binding["input_digest"]=digest(values)
        if occurrence_checker is not None:
            if not callable(occurrence_checker):
                raise NativeOperadRefusal("OCCURRENCE_CHECK_INVALID", "host checker must be callable")
            if input_order is None:
                input_order = tuple(range(len(_wire_leaves(wire))))
        checked=native_validate(inventory, wire, host=host, input_order=input_order)
        if input_order is not None:
            binding.update(input_order=tuple(checked["input_order"]), interpreter_version="core.oewas.native-plan-host.reindexed.v1")
        plan=checked["execution_plan"]
        binding.update(native_term_id=checked["term_id"],native_plan_digest=digest({"steps":plan,"output_ref":checked["output_ref"]}))
        model = None
        bind_model = getattr(occurrence_checker, "bind_native_model", None)
        if bind_model is not None:
            if not callable(bind_model):
                raise NativeOperadRefusal("OCCURRENCE_CHECK_INVALID", "native model binder must be callable")
            model = realize_native_result(inventory, wire, checked, input_order=input_order).with_input_digest(binding["input_digest"])
            try:
                bind_model(model)
            except Exception as exc:
                raise NativeOperadRefusal("OCCURRENCE_CHECK_UNAVAILABLE", f"native model binding: {type(exc).__name__}") from exc
            binding["model_binding_json"] = model.payload_json
        leaves=checked["leaves"]
        if isinstance(values,Mapping):
            if len(set(leaves))!=len(leaves):
                raise NativeOperadRefusal("AMBIGUOUS_INPUT","repeated colours require ordered values")
            if any(name not in values for name in leaves):
                raise NativeOperadRefusal("MISSING_INPUT","native input occurrence missing")
            ordered=[values[name] for name in leaves]
        elif isinstance(values,(list,tuple)) and len(values)==len(leaves):
            ordered=list(values)
        else:
            raise NativeOperadRefusal("MISSING_INPUT","native input occurrence count differs")
        ops=all_ops(inventory)
        for step in plan:
            if step["op_id"] not in executors:
                raise NativeOperadRefusal("NOT_EXECUTABLE",step["op_id"])
            for guard in step["guards"]:
                if guard["op_id"] not in detectors:
                    raise NativeOperadRefusal("NOT_EXECUTABLE",guard["op_id"])
        for skill in inventory.skills:
            for guard in skill.anti_ops:
                if guard.guards in checked["operation_ids"] and guard.typed_contract_id is not None and getattr(detectors[guard.op_id],"spec_id",None)!=guard.typed_contract_id:
                    raise NativeOperadRefusal("ANTI_OP_UNBOUND",guard.op_id)
        outputs=[]
        occurrence_binding = _occurrence_binding(binding["inventory_digest"], binding["input_digest"],
            wire, tuple(input_order) if input_order is not None else None, leaves,
            wire if isinstance(wire, str) else ops[wire.op].output, checked["term_id"]) if occurrence_checker is not None else None
        def resolve(ref):
            if set(ref)=={"input"}: return ordered[ref["input"]]
            if set(ref)=={"step"}: return outputs[ref["step"]]
            raise NativeOperadRefusal("NATIVE_PLAN_INVALID","unknown result reference")
        def check_occurrence(snapshot):
            if model is not None:
                model.verify_invocation(snapshot)
            return occurrence_checker(snapshot)
        for ordinal, step in enumerate(plan):
            op_id=step["op_id"]
            guards=[AntiOpSpec(summary="native checked guard",**g) for g in step["guards"]]
            outputs.append(execute_step(op_id,ops[op_id],[resolve(r) for r in step["args"]],guards,executors,detectors,steps,cleared,guard_events,
                occurrence_checker=check_occurrence if occurrence_checker is not None else None,
                occurrence_binding=occurrence_binding,
                model_occurrence=model.occurrence_context(ordinal) if model is not None else None))
        output=resolve(checked["output_ref"])
    except _Stop as exc:
        return RunReceipt(wire,tuple(steps),refusal=exc.refusal,null_tree=exc.null_tree,
            anti_ops_cleared=tuple(cleared),guard_events=tuple(guard_events),**binding)
    except NativeOperadRefusal as exc:
        return RunReceipt(wire,tuple(steps),refusal=Refusal(exc.code,exc.message),anti_ops_cleared=tuple(cleared),guard_events=tuple(guard_events),**binding)
    except (TypeError,ValueError,KeyError,IndexError) as exc:
        return RunReceipt(wire,tuple(steps),refusal=Refusal("NATIVE_PLAN_INVALID",str(exc)),anti_ops_cleared=tuple(cleared),guard_events=tuple(guard_events),**binding)
    return RunReceipt(wire,tuple(steps),output=output,anti_ops_cleared=tuple(cleared),guard_events=tuple(guard_events),**binding)
