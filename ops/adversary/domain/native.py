"""Adversary native wire decoding through a supplied domain port. AuthorityEffect: None."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from fractions import Fraction
from typing import Any, Mapping, Protocol

from operations.domain.rop.result import Err, Ok, Refusal, Result


class NativeOperationPort(Protocol):
    """A supplied support transport; domain code never acquires a host."""

    def invoke_runtime_with_file(
        self, action: str, payload: Any, *, file_action: str
    ) -> Result[Mapping[str, Any], Refusal]: ...


def invoke(native_port: NativeOperationPort, /, operation: str, **payload: Any) -> Result[Any, Refusal]:
    response = native_port.invoke_runtime_with_file(
        "adversary_support", {"operation": operation, **payload}, file_action="adversary_support_file"
    )
    if isinstance(response, Err):
        return response
    envelope = response.value
    if not envelope["success"]:
        return Err(Refusal("ADVERSARY_NATIVE_DISPATCH_FAILED", str(envelope["error"]), __name__))
    reply = envelope["result"]
    if reply["refusal"] is not None:
        error = reply["refusal"]
        return Err(Refusal(error["code"], error["message"], error.get("locus", __name__)))
    return Ok(reply["outcome"])


def value(native_port: NativeOperationPort, /, operation: str, **payload: Any) -> Any:
    result = invoke(native_port, operation, **payload)
    if isinstance(result, Err):
        error = result.error
        if error.code == "ADVERSARY_EVIDENCE_TYPE_ERROR":
            raise TypeError(error.message)
        raise ValueError(error.message)
    return result.value


def wire_json(value: Any) -> str:
    def wire(item):
        if isinstance(item, Fraction):
            return str(item)
        if is_dataclass(item):
            return wire(asdict(item))
        if isinstance(item, dict):
            return {key: wire(v) for key, v in item.items()}
        if isinstance(item, (tuple, list)):
            return [wire(v) for v in item]
        return item

    return json.dumps(wire(value), ensure_ascii=False)
