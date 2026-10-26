"""Adversarial and property tests for the OpenRouter seat gateway. No network.

These pin budget and failure-mode invariants of the current behaviour. They do
not show anything about model quality or about untested inputs.
"""

from __future__ import annotations

import json
from fractions import Fraction

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_pfp.domain.value_objects.seat_turn import SeatTurnRequestV1
from omega_engine_pfp.infrastructure.openrouter_seat_gateway import (
    CallLedger,
    RoutedSeatExecutor,
    parse_machine_block,
)
from omega_engine_pfp.infrastructure.seat_transport.routing import (
    BudgetPolicy,
    RouteLeg,
    RoutingTable,
    SeatRoute,
    canonical_seat_key,
)

GOOD = "x\n```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Open\nDISPOSITION=CHALLENGE\nDDC_LETTER=R\n```\n"
FAST = settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
REQUIRED = {"authority_effect", "bout_id", "day", "outcome", "cost_microusd", "seat_id", "tier", "config_digest"}


def _legs() -> tuple[RouteLeg, ...]:
    return tuple(RouteLeg("openrouter", m, Fraction(1), Fraction(2)) for m in ("a/x", "b/y", "c/z"))


def _table(budget: BudgetPolicy) -> RoutingTable:
    return RoutingTable(
        "t", "openrouter", Fraction(1, 2), budget,
        (SeatRoute("Koroviev", "strong", _legs()), SeatRoute("Begemot", "cheap", _legs())),
    )


def _req(seat: str, text: str = "judge") -> SeatTurnRequestV1:
    return SeatTurnRequestV1(scene_id="s", seat_id=seat, prompt_text=text, candidate_id="c")


def _body(content=GOOD, prompt=10, completion=5, cost=None) -> bytes:
    usage = {"prompt_tokens": prompt, "completion_tokens": completion}
    if cost is not None:
        usage["cost"] = cost
    return json.dumps({"id": "g", "model": "m", "choices": [{"message": {"content": content}}], "usage": usage}).encode()


def _executor(tmp_path, transport, budget, max_tokens=64):
    return RoutedSeatExecutor(
        table=_table(budget),
        config_digest="sha256:t",
        transports={"openrouter": transport},
        ledger=CallLedger(tmp_path / "calls.jsonl"),
        bout_id="b",
        max_output_tokens=max_tokens,
        today=lambda: "2026-10-04",
    )


def _rows(tmp_path):
    path = tmp_path / "calls.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


@FAST
@given(
    seats=st.lists(st.sampled_from(["Koroviev", "Begemot"]), min_size=1, max_size=25),
    cap=st.integers(min_value=200, max_value=5000),
    in_tok=st.integers(0, 40),
    out_tok=st.integers(0, 64),
)
def test_strict_mode_never_passes_the_bout_cap(tmp_path_factory, seats, cap, in_tok, out_tok):
    tmp = tmp_path_factory.mktemp("strict")
    ex = _executor(tmp, lambda m, r, mt: _body(prompt=in_tok, completion=out_tok), BudgetPolicy(cap, cap * 10))
    for seat in seats:
        ex._execute_legacy_fixture(_req(seat))
        assert ex.spent_bout <= cap
    assert sum(r["cost_microusd"] for r in _rows(tmp)) == ex.spent_bout


@FAST
@given(
    costs=st.lists(st.integers(0, 3000), min_size=1, max_size=20),
    cap=st.integers(500, 4000),
)
def test_reserve_mode_overshoot_is_bounded_to_one_call_and_then_refuses(tmp_path_factory, costs, cap):
    tmp = tmp_path_factory.mktemp("reserve")
    it = iter(costs)
    state = {"last": 0}

    def transport(m, r, mt):
        state["last"] = next(it)
        return _body(cost=f"{state['last'] / 1_000_000:.6f}")

    budget = BudgetPolicy(cap, cap * 10, admission_reserve_output_tokens=8)
    ex = _executor(tmp, transport, budget, max_tokens=65536)
    biggest = 0
    for _ in costs:
        before = ex.spent_bout
        result = ex._execute_legacy_fixture(_req("Koroviev"))
        if isinstance(result, Err):
            assert result.error.code == "BUDGET_BOUT_EXCEEDED"
            assert ex.spent_bout == before
            break
        biggest = max(biggest, state["last"])
        assert ex.spent_bout <= cap + biggest
    over = max(0, ex.spent_bout - cap)
    assert over <= biggest
    if ex.spent_bout > cap:
        assert ex._execute_legacy_fixture(_req("Koroviev")).error.code == "BUDGET_BOUT_EXCEEDED"


@FAST
@given(
    payload=st.one_of(
        st.binary(max_size=200),
        st.just(b""),
        st.just(b"null"),
        st.just(b"[]"),
        st.just(b'{"choices": []}'),
        st.just(b'{"choices": [{"message": {"content": null}}]}'),
        st.just(b'{"choices": [{"message": {"content": "hi"}}], "usage": {"cost": "abc"}}'),
        st.just(b'{"choices": [{"message": {"content": "hi"}}], "usage": {"cost": true, "prompt_tokens": 1, "completion_tokens": 1}}'),
        st.just(b'{"choices": [{"message": {"content": "hi"}}], "usage": {"cost": -5, "prompt_tokens": 1, "completion_tokens": 1}}'),
        st.just(b'{"choices": [{"message": {"content": "hi"}}], "usage": {"prompt_tokens": -1, "completion_tokens": 1e999}}'),
        st.text(max_size=80).map(lambda s: _body(content=s)),
    )
)
def test_hostile_replies_never_raise_and_always_leave_a_typed_ledger_row(tmp_path_factory, payload):
    tmp = tmp_path_factory.mktemp("hostile")
    ex = _executor(tmp, lambda m, r, mt: payload, BudgetPolicy(10**9, 10**10))
    result = ex._execute_legacy_fixture(_req("Koroviev"))
    assert isinstance(result, (Ok, Err))
    rows = _rows(tmp)
    assert rows, "every attempt must be recorded"
    for row in rows:
        assert REQUIRED <= set(row)
        assert row["authority_effect"] == "None"
        assert type(row["cost_microusd"]) is int and row["cost_microusd"] >= 0
    if isinstance(result, Ok):
        assert result.value.machine_fields == {} or result.value.machine_fields["AUTHORITY_EFFECT"] == "None"


@FAST
@given(
    fail_mask=st.lists(st.booleans(), min_size=3, max_size=3),
    exc=st.sampled_from([TimeoutError, ConnectionError, ValueError, OSError, KeyError]),
)
def test_every_leg_is_attempted_in_order_and_failures_are_recorded(tmp_path_factory, fail_mask, exc):
    tmp = tmp_path_factory.mktemp("legs")
    calls = []

    def transport(model, req, mt):
        idx = ["a/x", "b/y", "c/z"].index(model)
        calls.append(model)
        if fail_mask[idx]:
            raise exc("boom")
        return _body()

    ex = _executor(tmp, transport, BudgetPolicy(10**9, 10**10))
    result = ex._execute_legacy_fixture(_req("Koroviev"))
    rows = _rows(tmp)
    first_ok = next((i for i, failed in enumerate(fail_mask) if not failed), None)
    if first_ok is None:
        assert isinstance(result, Err) and result.error.code == "ALL_LEGS_FAILED"
        assert [r["outcome"] for r in rows] == ["TRANSPORT_ERROR"] * 3
    else:
        assert isinstance(result, Ok)
        assert calls == ["a/x", "b/y", "c/z"][: first_ok + 1]
        assert [r["outcome"] for r in rows] == ["TRANSPORT_ERROR"] * first_ok + ["OK"]


@FAST
@given(text=st.text(max_size=300))
def test_parse_machine_block_never_raises_and_ok_means_required_keys(text):
    result = parse_machine_block(text)
    if isinstance(result, Ok):
        assert {"AUTHORITY_EFFECT", "RESIDUAL_COLOUR", "DISPOSITION", "DDC_LETTER"} <= set(result.value)
        assert result.value["RESIDUAL_COLOUR"] in ("Open", "Closed", "Exact")


@FAST
@given(effect=st.text(alphabet=st.characters(blacklist_characters="\n\r`=", blacklist_categories=("Cs",)), max_size=12))
def test_any_non_none_authority_effect_is_refused_without_a_reply(tmp_path_factory, effect):
    tmp = tmp_path_factory.mktemp("authority")
    block = f"```machine\nAUTHORITY_EFFECT={effect}\nRESIDUAL_COLOUR=Open\nDISPOSITION=PASS_TO_MASTER\nDDC_LETTER=E\n```\n"
    ex = _executor(tmp, lambda m, r, mt: _body(content=block), BudgetPolicy(10**9, 10**10))
    result = ex._execute_legacy_fixture(_req("Koroviev"))
    if effect.strip() == "None":
        assert isinstance(result, Ok)
    else:
        assert isinstance(result, Err) and result.error.code == "AUTHORITY_MINT_REFUSED"


def test_negative_token_counts_refuse_at_provider_parser_and_record_every_attempt(tmp_path):
    ex = _executor(tmp_path, lambda m, r, mt: _body(prompt=-1, completion=1), BudgetPolicy(10**9, 10**10))
    result = ex._execute_legacy_fixture(_req("Koroviev"))
    # Strict provider usage validation runs before constructing a seat reply.
    assert isinstance(result, Err) and result.error.code == "ALL_LEGS_FAILED"
    rows = _rows(tmp_path)
    assert len(rows) == len(_legs())
    assert [row["leg_index"] for row in rows] == list(range(len(_legs())))
    assert all(row["outcome"] == "TRANSPORT_ERROR" and row["error"] == "ProviderError" for row in rows)
    assert all(row["authority_effect"] == "None" for row in rows)


@pytest.mark.parametrize("bad_day_row", [
    {"day": "2026-10-04", "cost_microusd": True},
    {"day": "2026-10-04", "cost_microusd": 1.5},
    {"day": "2026-10-04", "cost_microusd": "7"},
    {"day": "2026-10-05", "cost_microusd": 99},
    {"cost_microusd": 99},
])
def test_ledger_day_total_ignores_non_integer_and_other_day_costs(tmp_path, bad_day_row):
    ledger = CallLedger(tmp_path / "l.jsonl")
    ledger.append({"day": "2026-10-04", "cost_microusd": 5})
    ledger.append(bad_day_row)
    assert ledger.spent_on("2026-10-04") == 5


# This property includes native process startup; elapsed time is not its oracle.
@settings(deadline=None)
@given(name=st.text(max_size=40))
def test_canonical_seat_key_is_idempotent_and_case_insensitive(name):
    key = canonical_seat_key(name)
    assert canonical_seat_key(key) == key
    assert canonical_seat_key(name.upper()) == canonical_seat_key(name.lower())
    assert canonical_seat_key(name) == canonical_seat_key(name.casefold())


def test_day_cap_is_enforced_across_executors_sharing_a_ledger(tmp_path):
    budget = BudgetPolicy(10**9, 600)
    a = _executor(tmp_path, lambda m, r, mt: _body(prompt=100, completion=10), budget)
    results = [a._execute_legacy_fixture(_req("Koroviev")) for _ in range(5)]
    spent = CallLedger(tmp_path / "calls.jsonl").spent_on("2026-10-04")
    assert spent <= 600 and any(isinstance(r, Err) and r.error.code == "BUDGET_DAY_EXCEEDED" for r in results)
    b = _executor(tmp_path, lambda m, r, mt: _body(), budget)
    assert b._execute_legacy_fixture(_req("Koroviev")).error.code == "BUDGET_DAY_EXCEEDED"


@pytest.mark.parametrize("name", ["", "   ", "\u65e5\u672c", "___", "!!!"])
def test_ids_without_ascii_alphanumerics_never_match_a_seat(name):
    table = _table(BudgetPolicy(10**6, 10**7))
    result = table.seat(name)
    assert isinstance(result, Err) and result.error.code == "SEAT_ID_INVALID"


def test_sharp_s_folds_to_ss_and_is_refused_with_a_typed_code():
    from omega_engine_pfp.infrastructure.seat_transport.routing import canonical_seat_key

    assert canonical_seat_key("\u00df") == canonical_seat_key("SS") == "ss"
    result = _table(BudgetPolicy(10**6, 10**7)).seat("\u00df")
    assert isinstance(result, Err) and result.error.code == "SEAT_ROUTE_MISSING"


def test_validator_refuses_a_seat_whose_key_is_empty():
    from dataclasses import replace

    from omega_engine_pfp.infrastructure.seat_transport.routing import validate_table

    table = _table(BudgetPolicy(10**6, 10**7))
    bad = replace(table, seats=table.seats + (SeatRoute("\u65e5\u672c", "cheap", _legs()),))
    result = validate_table(bad)
    assert isinstance(result, Err) and result.error.code == "ROUTING_SEAT_ID_INVALID"
