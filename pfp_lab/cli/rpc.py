"""JSON-RPC 2.0 over stdio: one request per line in, one response per line out.

AuthorityEffect: None.
Contract: urn:pfp-lab:cli:rpc:v1

This is the contract the C# app speaks. Methods:

=================  ==============================  ==========================
method             params                          result
=================  ==============================  ==========================
``lab.version``    none                            ``{version, authority_effect}``
``packs.list``     none                            ``{packs: [PackSummary]}``
``packs.get``      ``{pack_id}``                   ``{scenario: Scenario}``
``scenario.run``   ``{scenario}``                  ``{receipt: Receipt}``
``receipt.verify`` ``{receipt}``                   ``VerifyReport``
=================  ==============================  ==========================

Failures translate to JSON-RPC errors with a stable ``data.code``:
-32700 parse error, -32600 invalid request, -32601 unknown method,
-32602 refused params (``ADMISSION``), -32001 ``BUDGET_EXCEEDED`` and
-32002 ``UNKNOWN_PACK``. Only these expected failures are caught; anything
else ends the process, which the client reports as a crashed core.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import IO, Literal

from pydantic import BaseModel, JsonValue, ValidationError

from pfp_lab.core.admission import AdmissionError, BudgetExceededError, ErrorCode, UnknownPackError
from pfp_lab.core.contracts import CORE_VERSION, MAX_JSON_BYTES, ScenarioIn, Strict, admit_json, get_pack, list_packs
from pfp_lab.core.session import ReceiptOut, build_receipt, run_scenario, verify_receipt

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
BUDGET_EXCEEDED = -32001
UNKNOWN_PACK = -32002


class RequestIn(Strict):
    jsonrpc: Literal["2.0"]
    id: int | str
    method: str
    params: JsonValue = None


class PackIdIn(Strict):
    pack_id: str


class ScenarioParams(Strict):
    scenario: ScenarioIn


class ReceiptParams(Strict):
    receipt: ReceiptOut


class RpcError(Exception):
    """An expected failure with its JSON-RPC code and stable data code."""

    def __init__(self, code: int, message: str, data_code: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data_code = data_code


def _params[ModelT: BaseModel](model: type[ModelT], params: JsonValue) -> ModelT:
    return admit_json(model, json.dumps(params))


def _version(_: JsonValue) -> JsonValue:
    return {"version": CORE_VERSION, "authority_effect": "None"}


def _packs_list(_: JsonValue) -> JsonValue:
    return {"packs": [item.model_dump(mode="json") for item in list_packs()]}


def _packs_get(params: JsonValue) -> JsonValue:
    pack = get_pack(_params(PackIdIn, params).pack_id)
    return {"scenario": pack.model_dump(mode="json", by_alias=True)}


def _scenario_run(params: JsonValue) -> JsonValue:
    scenario = _params(ScenarioParams, params).scenario
    receipt = build_receipt(run_scenario(scenario))
    return {"receipt": receipt.model_dump(mode="json", by_alias=True)}


def _receipt_verify(params: JsonValue) -> JsonValue:
    report = verify_receipt(_params(ReceiptParams, params).receipt)
    return report.model_dump(mode="json")


METHODS: dict[str, Callable[[JsonValue], JsonValue]] = {
    "lab.version": _version,
    "packs.list": _packs_list,
    "packs.get": _packs_get,
    "scenario.run": _scenario_run,
    "receipt.verify": _receipt_verify,
}


def _error(request_id: int | str | None, failure: RpcError) -> dict[str, JsonValue]:
    error: dict[str, JsonValue] = {
        "code": failure.code,
        "message": failure.message,
        "data": {"code": failure.data_code},
    }
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _parse(line: str) -> RequestIn:
    if len(line.encode("utf-8")) > MAX_JSON_BYTES:
        raise RpcError(INVALID_REQUEST, "request exceeds the size limit", ErrorCode.ADMISSION)
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as error:
        raise RpcError(PARSE_ERROR, f"not JSON: {error.msg}", ErrorCode.ADMISSION) from error
    if not isinstance(raw, dict):
        raise RpcError(INVALID_REQUEST, "a request must be a JSON object", ErrorCode.ADMISSION)
    try:
        return RequestIn.model_validate_json(line)
    except ValidationError as error:
        raise RpcError(INVALID_REQUEST, _first_error(error), ErrorCode.ADMISSION) from error


def _dispatch(request: RequestIn) -> JsonValue:
    method = METHODS.get(request.method)
    if method is None:
        raise RpcError(METHOD_NOT_FOUND, f"unknown method {request.method!r}", ErrorCode.ADMISSION)
    try:
        return method(request.params)
    except ValidationError as error:
        raise RpcError(INVALID_PARAMS, _first_error(error), ErrorCode.ADMISSION) from error
    except AdmissionError as error:
        raise RpcError(INVALID_PARAMS, error.message, error.code) from error
    except BudgetExceededError as error:
        raise RpcError(BUDGET_EXCEEDED, error.message, error.code) from error
    except UnknownPackError as error:
        raise RpcError(UNKNOWN_PACK, error.message, error.code) from error


def handle_line(line: str) -> str:
    """Answer one request line with one response line (without the newline)."""
    request_id: int | str | None = None
    try:
        request = _parse(line)
        request_id = request.id
        response: dict[str, JsonValue] = {"jsonrpc": "2.0", "id": request_id, "result": _dispatch(request)}
    except RpcError as failure:
        response = _error(request_id, failure)
    return json.dumps(response, ensure_ascii=False, separators=(",", ":"))


def serve(reader: IO[str], writer: IO[str]) -> int:
    """Answer requests until end of input; blank lines are skipped."""
    for line in reader:
        if line.strip():
            writer.write(handle_line(line) + "\n")
            writer.flush()
    return 0


def _first_error(error: ValidationError) -> str:
    first = error.errors()[0]
    where = ".".join(str(part) for part in first["loc"])
    return f"{where}: {first['msg']}" if where else str(first["msg"])


__all__ = ["METHODS", "handle_line", "serve"]
