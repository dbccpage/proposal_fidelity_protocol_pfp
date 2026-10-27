"""OpenRouter seat gateway: leg fallback, budget refusal, ledger. No live calls."""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction

import pytest

from operations.domain.rop.result import Ok
from pfp.domain.value_objects.seat_turn import SeatTurnRequestV1
from pfp.infrastructure.openrouter_seat_gateway import (
    CallLedger,
    RoutedSeatExecutor,
    SeatTurnRefused,
    parse_machine_block,
)
from pfp.infrastructure.seat_transport.routing import (
    BudgetPolicy,
    RouteLeg,
    RoutingTable,
    SeatRoute,
)

GOOD_BLOCK = "Critique.\n```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Open\nDISPOSITION=CHALLENGE\nDDC_LETTER=R\n```\n"


def _raw(content: str, cost: str | None = "0.000123", model: str = "m") -> bytes:
    """OpenRouter-shaped reply bytes; ``cost`` is emitted as a JSON number literal."""
    usage = '{"prompt_tokens": 100, "completion_tokens": 50' + (f', "cost": {cost}' if cost else "") + "}"
    choices = json.dumps([{"message": {"content": content}}])
    return f'{{"id": "g1", "model": {json.dumps(model)}, "choices": {choices}, "usage": {usage}}}'.encode()


def _leg(router: str, model: str, price_in: str = "1", price_out: str = "1") -> RouteLeg:
    return RouteLeg(router, model, Fraction(price_in), Fraction(price_out))


def _table(per_bout: int = 1_000_000, per_day: int = 10_000_000) -> RoutingTable:
    legs = (_leg("openrouter", "a/x"), _leg("openrouter", "b/y"), _leg("openrouter", "c/z"), _leg("openrouter", "d/w"))
    return RoutingTable(
        version="t",
        primary_router="openrouter",
        cheap_share_min=Fraction(1, 2),
        budget=BudgetPolicy(per_bout, per_day),
        seats=(
            SeatRoute("Defect Hunter", "strong", legs),
            SeatRoute("Gauge Breaker", "cheap", legs),
            SeatRoute("Syntax Prefilter", "deterministic"),
        ),
    )


def _request(seat: str = "Defect Hunter") -> SeatTurnRequestV1:
    return SeatTurnRequestV1(scene_id="s1", seat_id=seat, prompt_text="judge this", candidate_id="c1")


def _executor(tmp_path, transports, table=None):
    return RoutedSeatExecutor(
        table=table or _table(),
        config_digest="sha256:test",
        transports=transports,
        ledger=CallLedger(tmp_path / "calls.jsonl"),
        bout_id="bout-1",
        today=lambda: "2026-10-04",
    )


def _ledger(tmp_path) -> list[dict]:
    return [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()]


# ---- executor -------------------------------------------------------------


def test_happy_path_debits_receipt_cost_and_writes_ledger(tmp_path):
    ex = _executor(tmp_path, {"openrouter": lambda model, req, mt: _raw(GOOD_BLOCK, model=model)})
    result = ex._execute_legacy_fixture(_request())
    assert isinstance(result, Ok)
    reply = result.value
    assert reply.machine_fields["DISPOSITION"] == "CHALLENGE"
    assert reply.parameters["cost_source"] == "provider_receipt"
    assert reply.parameters["cost_microusd"] == 123
    assert ex.spent_bout == 123
    (rec,) = _ledger(tmp_path)
    assert rec["outcome"] == "OK" and rec["model"] == "a/x" and rec["cost_microusd"] == 123
    assert rec["config_digest"] == "sha256:test" and rec["authority_effect"] == "None"



@pytest.mark.parametrize("cost_field", ["cost", "total_cost"])
def test_numeric_receipt_retains_exact_rounding_and_original_reply_bytes(tmp_path, cost_field):
    # Binary float rounds this to one micro-USD; the original exact receipt exceeds one.
    raw = _raw(GOOD_BLOCK, cost="0.000001000000000000000001")
    if cost_field == "total_cost":
        raw = raw.replace(b'"cost":', b'"total_cost":')
    ex = _executor(tmp_path, {"openrouter": lambda model, req, mt: raw})
    result = ex._execute_legacy_fixture(_request())
    assert isinstance(result, Ok)
    assert result.value.raw_bytes == raw
    assert result.value.parameters["cost_microusd"] == 2
    assert result.value.parameters["cost_source"] == "provider_receipt"
    assert ex.spent_bout == 2
    (record,) = _ledger(tmp_path)
    assert record["outcome"] == "OK" and record["cost_microusd"] == 2


def test_missing_machine_block_is_malformed_not_fabricated(tmp_path):
    ex = _executor(tmp_path, {"openrouter": lambda model, req, mt: _raw("no block here")})
    reply = ex._execute_legacy_fixture(_request()).value
    assert reply.machine_fields == {}
    assert reply.parameters["machine_block"] == "MALFORMED"
    assert _ledger(tmp_path)[0]["outcome"] == "MALFORMED"


def test_authority_mint_is_refused(tmp_path):
    bad = GOOD_BLOCK.replace("AUTHORITY_EFFECT=None", "AUTHORITY_EFFECT=Sovereign")
    ex = _executor(tmp_path, {"openrouter": lambda model, req, mt: _raw(bad)})
    assert ex._execute_legacy_fixture(_request()).error.code == "AUTHORITY_MINT_REFUSED"


def test_transport_failure_falls_through_to_next_leg(tmp_path):
    seen = []

    def flaky_then_ok(model, req, mt):
        seen.append(model)
        if model != "d/w":
            raise TimeoutError("down")
        return _raw(GOOD_BLOCK, cost=None, model=model)

    ex = _executor(tmp_path, {"openrouter": flaky_then_ok})
    reply = ex._execute_legacy_fixture(_request()).value
    assert seen == ["a/x", "b/y", "c/z", "d/w"] and reply.provider == "openrouter"
    assert reply.parameters["cost_source"] == "price_table"
    assert reply.parameters["cost_microusd"] == 150  # 100*1 + 50*1
    outcomes = [r["outcome"] for r in _ledger(tmp_path)]
    assert outcomes == ["TRANSPORT_ERROR"] * 3 + ["OK"]


def test_unconfigured_router_is_recorded_then_all_legs_fail(tmp_path):
    ex = _executor(tmp_path, {})
    result = ex._execute_legacy_fixture(_request())
    assert result.error.code == "ALL_LEGS_FAILED"
    assert {r["outcome"] for r in _ledger(tmp_path)} == {"ROUTER_UNCONFIGURED"}
    with pytest.raises(SeatTurnRefused):
        ex(_request())


def test_budget_refuses_before_sending(tmp_path):
    calls = []
    ex = _executor(tmp_path, {"openrouter": lambda *a: calls.append(a) or _raw(GOOD_BLOCK)}, table=_table(per_bout=10, per_day=10))
    assert ex._execute_legacy_fixture(_request()).error.code == "BUDGET_BOUT_EXCEEDED"
    assert calls == []


def test_day_budget_counts_prior_ledger_spend(tmp_path):
    CallLedger(tmp_path / "calls.jsonl").append({"day": "2026-10-04", "cost_microusd": 9_999_000})
    ex = _executor(tmp_path, {"openrouter": lambda *a: _raw(GOOD_BLOCK)})
    assert ex._execute_legacy_fixture(_request()).error.code == "BUDGET_DAY_EXCEEDED"


def test_non_model_and_unknown_seats_refuse(tmp_path):
    ex = _executor(tmp_path, {"openrouter": lambda *a: _raw(GOOD_BLOCK)})
    assert ex._execute_legacy_fixture(_request("Syntax Prefilter")).error.code == "SEAT_NOT_MODEL_BACKED"
    assert ex._execute_legacy_fixture(_request("Nobody")).error.code == "SEAT_ROUTE_MISSING"


def test_missing_cost_falls_back_to_price_table(tmp_path):
    ex = _executor(tmp_path, {"openrouter": lambda *a: _raw(GOOD_BLOCK, cost=None)})
    reply = ex._execute_legacy_fixture(_request()).value
    assert reply.parameters["cost_source"] == "price_table"
    assert reply.parameters["cost_microusd"] == 150  # 100*1 + 50*1


@pytest.mark.parametrize(
    "text, ok",
    [
        (GOOD_BLOCK, True),
        (GOOD_BLOCK + GOOD_BLOCK, False),
        (GOOD_BLOCK.replace("DDC_LETTER=R\n", ""), False),
        (GOOD_BLOCK.replace("Open", "Purple"), False),
    ],
)
def test_parse_machine_block(text, ok):
    assert isinstance(parse_machine_block(text), Ok) is ok


def test_ledger_skips_blank_lines(tmp_path):
    path = tmp_path / "calls.jsonl"
    path.write_text('{"day": "d", "cost_microusd": 5}\n\n{"day": "d", "cost_microusd": 7}\n', encoding="utf-8")
    assert CallLedger(path).spent_on("d") == 12
    assert CallLedger(tmp_path / "none.jsonl").spent_on("d") == 0


def test_reserve_admits_large_max_tokens_and_records_overshoot(tmp_path):
    # strict worst case at 65536 output tokens would be 65_536 + input > 60_000 cap
    table = _table(per_bout=60_000, per_day=10_000_000)
    table = replace(table, budget=replace(table.budget, admission_reserve_output_tokens=1_000))
    ex = RoutedSeatExecutor(
        table=table,
        config_digest="sha256:test",
        transports={"openrouter": lambda m, r, mt: _raw(GOOD_BLOCK, cost="0.080000")},
        ledger=CallLedger(tmp_path / "calls.jsonl"),
        bout_id="bout-1",
        max_output_tokens=65_536,
        today=lambda: "2026-10-04",
    )
    assert isinstance(ex._execute_legacy_fixture(_request()), Ok)
    (rec,) = _ledger(tmp_path)
    assert rec["max_tokens"] == 65_536 and rec["admission_output_tokens"] == 1_000
    assert rec["overshoot_microusd"] == 20_000  # 80_000 receipt - 60_000 cap
    refused = ex._execute_legacy_fixture(_request())
    assert refused.error.code == "BUDGET_BOUT_EXCEEDED"


def test_strict_admission_when_no_reserve(tmp_path):
    table = _table(per_bout=60_000, per_day=10_000_000)
    ex = RoutedSeatExecutor(
        table=table,
        config_digest="sha256:test",
        transports={"openrouter": lambda m, r, mt: _raw(GOOD_BLOCK)},
        ledger=CallLedger(tmp_path / "calls.jsonl"),
        bout_id="bout-1",
        max_output_tokens=65_536,
        today=lambda: "2026-10-04",
    )
    assert ex._execute_legacy_fixture(_request()).error.code == "BUDGET_BOUT_EXCEEDED"


def test_huge_input_is_refused_before_sending(tmp_path):
    calls = []
    table = _table()
    table = replace(table, budget=replace(table.budget, max_input_bytes_per_call=100))
    ex = RoutedSeatExecutor(
        table=table,
        config_digest="sha256:test",
        transports={"openrouter": lambda *a: calls.append(a) or _raw(GOOD_BLOCK)},
        ledger=CallLedger(tmp_path / "calls.jsonl"),
        bout_id="bout-1",
        today=lambda: "2026-10-04",
    )
    huge = SeatTurnRequestV1(scene_id="s1", seat_id="Defect Hunter", prompt_text="x" * 5000, candidate_id="c1")
    assert ex._execute_legacy_fixture(huge).error.code == "INPUT_TOO_LARGE"
    assert calls == []
    (rec,) = _ledger(tmp_path)
    assert rec["outcome"] == "INPUT_TOO_LARGE" and rec["cost_microusd"] == 0


def test_cheap_tier_cap_applies_within_bout_while_strong_continues(tmp_path):
    table = _table(per_bout=10_000_000)
    table = replace(table, budget=replace(table.budget, tier_per_bout_microusd=(("cheap", 700), ("strong", 5_000_000))))
    ex = RoutedSeatExecutor(
        table=table,
        config_digest="sha256:test",
        transports={"openrouter": lambda m, r, mt: _raw(GOOD_BLOCK, cost="0.000600")},
        ledger=CallLedger(tmp_path / "calls.jsonl"),
        bout_id="bout-1",
        max_output_tokens=64,
        today=lambda: "2026-10-04",
    )
    assert isinstance(ex._execute_legacy_fixture(_request("Gauge Breaker")), Ok)
    assert ex._execute_legacy_fixture(_request("Gauge Breaker")).error.code == "BUDGET_TIER_EXCEEDED"
    assert isinstance(ex._execute_legacy_fixture(_request("Defect Hunter")), Ok)
