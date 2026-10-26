"""Documented constants, output formats and edge behaviour that the mutation campaigns showed were unpinned.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:pins:v1

Each expected value here comes from the documented contract (README, module
docstrings, the JSON-RPC and CLI tables) or from a hand count, not from the
code under test.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from pfp_lab.cli import rpc
from pfp_lab.cli.main import Exit, main
from pfp_lab.core.admission import AdmissionError, BudgetExceededError
from pfp_lab.core.contracts import (
    MAX_JSON_BYTES,
    MAX_MOVES,
    MAX_TEXT,
    PackSummary,
    ScenarioIn,
    VerdictOut,
    admit_json,
    get_pack,
)
from pfp_lab.core.graph import ConstraintGraph, Edge
from pfp_lab.core.obstruction import DEFAULT_SEARCH_BUDGET, SearchBudget, check_claims, obstruction
from pfp_lab.core.session import ReceiptOut, build_receipt, canonical_json, receipt_digest, run_scenario
from pfp_lab.web import app as web

F = Fraction
TRIANGLE = ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))
ONES = {("a", "b"): F(1), ("b", "c"): F(1), ("c", "a"): F(1)}
# The receipt of the Paper 005 worked session, recorded when the receipt format was fixed.
GOLDEN_DIGEST = "de07ba58d796700acb8d13d904f814cc218b0b862510d16f6244ab141b463541"


def test_documented_contract_limits() -> None:
    assert (MAX_MOVES, MAX_JSON_BYTES, MAX_TEXT, DEFAULT_SEARCH_BUDGET) == (256, 262_144, 200, 1_000_000)


def test_documented_exit_codes() -> None:
    assert {code.name: code.value for code in Exit} == {
        "OK": 0,
        "USAGE": 2,
        "ADMISSION": 3,
        "BUDGET": 4,
        "NOT_VERIFIED": 5,
        "IO": 6,
        "UNKNOWN_PACK": 7,
    }
    assert (web.DEFAULT_PORT, web.REFUSED) == (8765, 2)


def test_golden_receipt_digest() -> None:
    receipt = build_receipt(run_scenario(get_pack("paper-005-worked-session")))
    assert receipt.digest == GOLDEN_DIGEST
    body = receipt.model_dump(mode="json", by_alias=True, exclude={"digest"})
    assert "schema" in body and "schema_id" not in body
    assert hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest() == receipt_digest(receipt)


def test_receipt_field_limits() -> None:
    body = json.loads(build_receipt(run_scenario(get_pack("two-islands"))).model_dump_json(by_alias=True))
    for key, value in (("core_version", "x" * 33), ("digest", "a" * 65), ("digest", "A" * 64)):
        with pytest.raises(ValidationError):
            admit_json(ReceiptOut, json.dumps({**body, key: value}))
    assert admit_json(ReceiptOut, json.dumps({**body, "core_version": "x" * 32})).core_version == "x" * 32


def test_output_models_are_frozen_and_scenarios_strict() -> None:
    verdict = run_scenario(get_pack("two-islands")).verdicts[0]
    assert isinstance(verdict, VerdictOut)
    with pytest.raises(ValidationError):
        verdict.details = "changed"  # type: ignore[misc]
    python_lists = {"schema": "pfp-lab.scenario.v1", "vertices": ["a"], "edges": [], "moves": []}
    with pytest.raises(ValidationError):
        ScenarioIn.model_validate(python_lists)
    by_name = ScenarioIn(schema_id="pfp-lab.scenario.v1", vertices=("a",), edges=(), moves=())
    assert by_name.vertices == ("a",)
    single = admit_json(ScenarioIn, json.dumps(python_lists))
    assert run_scenario(single).final.obstruction == "0"
    assert PackSummary(pack_id="p", title="", moves=0).moves == 0


def test_search_budget_counts_exactly() -> None:
    # The triangle has 11 enumeration steps (hand count of the include/exclude tree).
    assert SearchBudget(1).remaining == 1
    assert obstruction(TRIANGLE, ONES, budget=11)[0] == 3
    with pytest.raises(BudgetExceededError):
        obstruction(TRIANGLE, ONES, budget=10)


def test_claim_refusal_messages_name_the_edge() -> None:
    with pytest.raises(AdmissionError, match="claim on undeclared edge b -> a"):
        check_claims(TRIANGLE, {("b", "a"): F(1)})
    with pytest.raises(AdmissionError, match="claim on a -> b must be an exact Fraction"):
        check_claims(TRIANGLE, {("a", "b"): 1})  # type: ignore[dict-item]


def call(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    return main(list(argv), out, io.StringIO()), out.getvalue()


def test_json_outputs_use_two_space_indent(tmp_path: Path) -> None:
    receipt_file = tmp_path / "r.json"
    code, out = call("run", "--pack", "two-islands", "--json", "--receipt", str(receipt_file))
    assert code == 0
    assert out.startswith('{\n  "schema": "pfp-lab.receipt.v1"')
    assert receipt_file.read_text(encoding="utf-8").startswith('{\n  "schema"')
    assert call("verify", str(receipt_file), "--json")[1].startswith('{\n  "valid": true')
    assert call("packs", "two-islands")[1].startswith('{\n  "schema"')


def test_schema_creates_nested_directories(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b"
    assert call("schema", str(target))[0] == 0
    assert (target / "scenario.v1.schema.json").is_file()


def test_a_command_is_required() -> None:
    with pytest.raises(SystemExit) as caught:
        call()
    assert caught.value.code == 2


def test_rpc_keeps_non_ascii_as_utf8() -> None:
    line = rpc.handle_line(json.dumps({"jsonrpc": "2.0", "id": "é", "method": "lab.version"}))
    assert '"id":"é"' in line


def test_web_admission_error_status_and_bind_check() -> None:
    client = TestClient(web.create_app())
    response = client.post("/api/run", content=json.dumps({"x": 1}))
    assert (response.status_code, response.json()["code"]) == (422, "ADMISSION")
    refused = web.check_bind(web.build_parser().parse_args(["--host", "10.0.0.1"]), io.StringIO())
    assert refused is False
    allowed = web.check_bind(web.build_parser().parse_args(["--host", "::1"]), io.StringIO())
    assert allowed is True


def test_web_core_admission_error_is_422(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_: object) -> object:
        raise AdmissionError("refused for the test")

    monkeypatch.setattr(web, "run_scenario", refuse)
    response = TestClient(web.create_app()).post(
        "/api/run", content=get_pack("two-islands").model_dump_json(by_alias=True)
    )
    assert response.status_code == 422


def test_entry_points_read_sys_argv(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["pfp-lab", "packs"])
    with pytest.raises(SystemExit) as caught:
        from pfp_lab.cli.main import entry

        entry()
    assert caught.value.code == 0
    assert "paper-005-worked-session" in capsys.readouterr().out


def test_rpc_names_a_non_object_request() -> None:
    response = json.loads(rpc.handle_line("[1, 2]"))
    assert response["error"]["message"] == "a request must be a JSON object"
