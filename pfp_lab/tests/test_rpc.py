"""JSON-RPC contract: methods, error codes and line framing.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:rpc:v1
"""

from __future__ import annotations

import io
import json
from typing import Any

import pytest

from pfp_lab.cli import rpc
from pfp_lab.core.contracts import CORE_VERSION, MAX_JSON_BYTES, get_pack


def ask(method: str, params: Any = None, request_id: int | str = 1) -> dict[str, Any]:
    request: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    result: dict[str, Any] = json.loads(rpc.handle_line(json.dumps(request)))
    return result


def error_of(response: dict[str, Any]) -> tuple[int, str]:
    return response["error"]["code"], response["error"]["data"]["code"]


def test_version_and_packs() -> None:
    assert ask("lab.version") == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"version": CORE_VERSION, "authority_effect": "None"},
    }
    packs = ask("packs.list", request_id="x")
    assert packs["id"] == "x"
    assert [item["pack_id"] for item in packs["result"]["packs"]][0] == "paper-005-worked-session"
    scenario = ask("packs.get", {"pack_id": "two-islands"})["result"]["scenario"]
    assert scenario["schema"] == "pfp-lab.scenario.v1"


def test_run_then_verify_round_trip() -> None:
    scenario = get_pack("paper-005-worked-session").model_dump(mode="json", by_alias=True)
    receipt = ask("scenario.run", {"scenario": scenario})["result"]["receipt"]
    assert receipt["final"]["obstruction"] == "3"
    report = ask("receipt.verify", {"receipt": receipt})["result"]
    assert report == {"valid": True, "digest": receipt["digest"], "problems": []}
    receipt["verdicts"][0]["status"] = "Refused"
    assert ask("receipt.verify", {"receipt": receipt})["result"]["valid"] is False


@pytest.mark.parametrize(
    ("method", "params", "expected"),
    [
        ("nope", None, (-32601, "ADMISSION")),
        ("packs.get", None, (-32602, "ADMISSION")),
        ("packs.get", {"pack_id": "zzz"}, (-32002, "UNKNOWN_PACK")),
        ("scenario.run", {"scenario": {"schema": "x"}}, (-32602, "ADMISSION")),
        ("scenario.run", {"scenario": None, "extra": 1}, (-32602, "ADMISSION")),
        ("receipt.verify", {"receipt": {}}, (-32602, "ADMISSION")),
    ],
)
def test_error_codes(method: str, params: Any, expected: tuple[int, str]) -> None:
    response = ask(method, params)
    assert response["id"] == 1
    assert error_of(response) == expected
    assert response["error"]["message"]


def test_admission_error_from_a_method(monkeypatch: pytest.MonkeyPatch) -> None:
    from pfp_lab.core.admission import AdmissionError

    def refuse(_: object) -> None:
        raise AdmissionError("refused for the test")

    monkeypatch.setitem(rpc.METHODS, "lab.version", refuse)
    response = ask("lab.version")
    assert error_of(response) == (-32602, "ADMISSION")
    assert response["error"]["message"] == "refused for the test"


def test_budget_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import pfp_lab.core.session as session

    monkeypatch.setattr(session.run_scenario, "__kwdefaults__", {"budget": 2})
    scenario = get_pack("paper-005-worked-session").model_dump(mode="json", by_alias=True)
    assert error_of(ask("scenario.run", {"scenario": scenario})) == (-32001, "BUDGET_EXCEEDED")


@pytest.mark.parametrize(
    ("line", "code"),
    [
        ("{not json", -32700),
        ("[1, 2]", -32600),
        ('{"jsonrpc": "1.0", "id": 1, "method": "lab.version"}', -32600),
        ('{"jsonrpc": "2.0", "method": "lab.version"}', -32600),
        ('{"jsonrpc": "2.0", "id": true, "method": "lab.version"}', -32600),
        ('{"jsonrpc": "2.0", "id": 1, "method": "lab.version", "x": 1}', -32600),
        (" " * (MAX_JSON_BYTES + 1), -32600),
    ],
    ids=["not-json", "array", "wrong-version", "no-id", "bool-id", "extra-field", "oversize"],
)
def test_malformed_requests(line: str, code: int) -> None:
    response = json.loads(rpc.handle_line(line))
    assert (response["id"], response["error"]["code"]) == (None, code)


def test_serve_frames_one_response_per_line() -> None:
    lines = "\n".join(
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "lab.version"}),
            "",
            "   ",
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "packs.list"}),
        ]
    )
    reader, writer = io.StringIO(lines + "\n"), io.StringIO()
    assert rpc.serve(reader, writer) == 0
    responses = [json.loads(line) for line in writer.getvalue().splitlines()]
    assert [item["id"] for item in responses] == [1, 2]
    assert writer.getvalue().endswith("\n")
