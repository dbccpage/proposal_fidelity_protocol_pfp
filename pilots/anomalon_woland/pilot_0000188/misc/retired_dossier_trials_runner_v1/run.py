"""Bounded sequential trials through the shared provider transport, then offline replay.

python -m omega_engine_education.pilots.dossier_trials.run --replay
Live dispatch additionally requires --live --model ID --budget-usd CAP.
No retries, provider fallback, cached completions, or default paid budget.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import importlib.metadata
import json
import platform
import time
import urllib.request

import yaml

from omega_engine_providers.domain.types import CandidateRequest, DecodingParamsV1
from omega_engine_providers.infrastructure.budget_ledger import SqliteBudgetLedger
from omega_engine_providers.infrastructure.openai_compat import build_openai_compat_body
from omega_engine_providers.infrastructure.openrouter_transport import openrouter_transport
from omega_engine_providers.infrastructure.wire import decode_reply

from .cases import PILOTS, canonical, sha
from .checking import evaluate
from .prepare import CAMPAIGN, ROOT, prepare, write_once

MAX_OUTPUT = 900
DEPENDENCIES = (
    "omega_engine_education/pilots/dossier_trials/checking.py",
    "omega_engine_education/pilots/dossier_trials/cases.py",
    "omega_engine_education/pilots/dossier_trials/run.py",
    "omega_engine_education/pfp/domain/pilots/checker_registry.py",
    "omega_engine_providers/infrastructure/wire.py",
    "omega_engine_providers/infrastructure/openai_compat.py",
    "omega_engine_providers/infrastructure/openrouter_transport.py",
    "omega_engine_providers/domain/types.py",
)


def environment():
    return dict(python=platform.python_version(), packages={name: importlib.metadata.version(name)
                for name in ("jsonschema", "PyYAML")}, sources={p: sha((ROOT / p).read_bytes()) for p in DEPENDENCIES})


def load_case(row):
    folder = PILOTS / row["capsule"]
    data = (folder / "input.yaml").read_bytes()
    if sha(data) != row["input_sha256"]:
        raise ValueError("INPUT_DIGEST_MISMATCH")
    return folder, yaml.safe_load(data)


def request_for(case):
    prompt = case["prompt"]
    return CandidateRequest(prompt["system_prompt"], prompt["user_prompt"],
        decoding=DecodingParamsV1(temperature=0.0, allow_fallbacks=False,
                                 require_parameters=True, thinking="disabled"))


def request_wire(case, model):
    body = build_openai_compat_body(request_for(case), model=model, max_tokens=MAX_OUTPUT)
    body["usage"] = {"include": True}
    return body


def microusd(value):
    if type(value) not in (str, int, float, Decimal) or not Decimal(str(value)).is_finite() or Decimal(str(value)) < 0:
        raise ValueError("UNRECONCILED_COST")
    return int((Decimal(str(value))*1_000_000).to_integral_value(rounding=ROUND_CEILING))


def pricing(model):
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as reply:
        raw = reply.read()
    catalog = decode_reply(raw)
    row = next((r for r in catalog["data"] if r["id"] == model), None)
    if row is None:
        raise ValueError("MODEL_NOT_LISTED")
    rates = row["pricing"]
    for key, value in rates.items():
        if key not in ("prompt", "completion", "input_cache_read", "input_cache_write") and Decimal(value) != 0:
            raise ValueError("UNSUPPORTED_SURCHARGE")
    if not {"max_tokens", "temperature", "reasoning"}.issubset(row["supported_parameters"]):
        raise ValueError("REQUIRED_DECODING_UNSUPPORTED")
    if any(not Decimal(rates[k]).is_finite() or Decimal(rates[k]) < 0 for k in ("prompt", "completion")):
        raise ValueError("INVALID_PRICING")
    return dict(observed_at=datetime.now(timezone.utc).isoformat(), catalog_sha256=sha(raw), row=row)


def reservation(case, price):
    request = request_for(case)
    # One token per UTF-8 byte plus a framing allowance: deliberately conservative.
    upper_input_tokens = request.estimated_payload_bytes() + 256
    rates = price["row"]["pricing"]
    return microusd(Decimal(rates["prompt"])*upper_input_tokens + Decimal(rates["completion"])*MAX_OUTPUT)


def grade(case, raw, model):
    reply = decode_reply(raw)
    if reply.get("model") != model:
        raise ValueError("REPLY_MODEL_MISMATCH")
    if not isinstance(reply.get("id"), str) or not reply["id"]:
        raise ValueError("MISSING_GENERATION_ID")
    usage = reply.get("usage", {})
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if type(usage.get(name)) is not int or usage[name] < 0:
            raise ValueError("MISSING_USAGE")
    cost = microusd(usage.get("cost"))
    choices = reply.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("MISSING_COMPLETION")
    text = choices[0].get("message", {}).get("content")
    if not isinstance(text, str):
        raise ValueError("MISSING_COMPLETION")
    result = evaluate(case["task"], text, yaml.safe_load(case["prompt"]["response_schema"]))
    return dict(**result, model_id=model, generation_id=reply["id"], usage=usage,
                cost_microusd=cost, finish_reason=choices[0].get("finish_reason"))


def live(plan, model, budget, limit, per_call_budget=50000, session="primary"):
    root = PILOTS / "matrix" / CAMPAIGN / session
    root.mkdir(parents=True, exist_ok=True)
    config = dict(model=model, budget_microusd=budget, per_call_budget_microusd=per_call_budget,
                  max_output_tokens=MAX_OUTPUT, environment=environment())
    write_once(root / "authorization.yaml", config)
    ledger = SqliteBudgetLedger(root / "budget.sqlite3", budget_id=CAMPAIGN + session)
    price = pricing(model)
    price_path = root / ("pricing_" + sha(canonical(price))[:16] + ".yaml")
    write_once(price_path, price)
    transport = openrouter_transport(timeout=55.0)
    if not transport.is_ok:
        raise ValueError("PROVIDER_CREDENTIAL_UNAVAILABLE")
    send = transport.unwrap()
    for row in plan["cases"][:limit]:
        folder, case = load_case(row)
        if (folder / "response.yaml").exists():
            replay_one(row, config)
            continue
        reserve = reservation(case, price)
        if reserve > per_call_budget:
            raise ValueError("PER_CALL_CAP_EXCEEDED")
        attempt = row["capsule"]
        with ledger.transaction(budget) as state:
            if any(a["state"] != "settled" for a in state["attempts"].values()):
                raise ValueError("UNRECONCILED_ATTEMPT")
            if attempt in state["attempts"]:
                raise ValueError("ATTEMPT_ALREADY_RECORDED")
            if state["spent"] + reserve > budget:
                raise ValueError("CAMPAIGN_BUDGET_EXCEEDED")
            state["spent"] += reserve
            state["attempts"][attempt] = dict(state="reserved", reserved=reserve, input_sha256=row["input_sha256"])
        body = request_wire(case, model)
        write_once(folder / "request.json", canonical(body))
        write_once(folder / "reservation.yaml", dict(reserved_microusd=reserve, model_id=model,
            pricing=price_path.relative_to(PILOTS).as_posix(), request_sha256=sha(canonical(body))))
        start = time.monotonic()
        # Reservation persists through any crash or ambiguous HTTP failure; no automatic retry.
        raw = send(model, request_for(case), MAX_OUTPUT)
        elapsed = time.monotonic() - start
        write_once(folder / "provider_response.json", raw)
        result = grade(case, raw, model)
        if result["cost_microusd"] > reserve:
            raise ValueError("BILL_EXCEEDS_RESERVATION")
        with ledger.transaction(budget) as state:
            if any(a.get("generation_id") == result["generation_id"] for a in state["attempts"].values()):
                raise ValueError("DUPLICATE_PROVIDER_GENERATION")
        receipt = dict(schema="pfp.dossier-response.v1", authority_effect="None", **result,
            latency_seconds=elapsed, input_sha256=row["input_sha256"], request_sha256=sha(canonical(body)),
            provider_response_sha256=sha(raw), environment=config["environment"])
        write_once(folder / "response.yaml", receipt)
        with ledger.transaction(budget) as state:
            state["spent"] += result["cost_microusd"] - reserve
            state["attempts"][attempt].update(state="settled", generation_id=result["generation_id"], actual=result["cost_microusd"])
        print(json.dumps(dict(capsule=attempt, status=result["status"], cost_microusd=result["cost_microusd"])), flush=True)


def replay_one(row, config):
    folder, case = load_case(row)
    receipt = yaml.safe_load((folder / "response.yaml").read_text(encoding="utf-8"))
    raw = (folder / "provider_response.json").read_bytes()
    expected = request_wire(case, config["model"])
    wire = (folder / "request.json").read_bytes()
    if (receipt["environment"] != environment() or receipt["environment"] != config["environment"]
            or receipt["input_sha256"] != row["input_sha256"] or sha(raw) != receipt["provider_response_sha256"]
            or wire != canonical(expected) or sha(wire) != receipt["request_sha256"]):
        raise ValueError("REPLAY_BINDING_MISMATCH")
    checked = grade(case, raw, config["model"])
    if any(receipt[k] != v for k, v in checked.items()):
        raise ValueError("REPLAY_RESULT_MISMATCH")
    return dict(capsule=row["capsule"], pilot_id=case["pilot_id"], rung=case["rung"],
                representation=case["representation"], response_sha256=sha(raw), **checked)


def replay(plan, session="primary"):
    root = PILOTS / "matrix" / CAMPAIGN / session
    config_path = root / "authorization.yaml"
    config = yaml.safe_load(config_path.read_text()) if config_path.exists() else None
    rows = []
    for row in plan["cases"]:
        folder, _ = load_case(row)
        rows.append(replay_one(row, config) if (folder / "response.yaml").exists() else dict(capsule=row["capsule"], status="PLANNED"))
    return dict(campaign=CAMPAIGN, planned=250, statuses=dict(Counter(r["status"] for r in rows)),
                cost_microusd=sum(r.get("cost_microusd", 0) for r in rows), rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--session", choices=["primary", "free_followup"], default="primary")
    parser.add_argument("--budget-usd")
    parser.add_argument("--per-call-budget-usd", default="0.05")
    parser.add_argument("--limit", type=int, default=250)
    args = parser.parse_args()
    plan = prepare()
    if args.session == "free_followup":
        plan = yaml.safe_load((PILOTS / "matrix" / f"{CAMPAIGN}_free.yaml").read_text())
    if args.live:
        if not args.model or args.budget_usd is None:
            parser.error("live requires an explicit model and budget")
        live(plan, args.model, microusd(args.budget_usd), args.limit, microusd(args.per_call_budget_usd), args.session)
    report = replay(plan, args.session)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    if all(r["status"] != "PLANNED" for r in report["rows"]):
        write_once(PILOTS / "matrix" / CAMPAIGN / args.session / "replay.json", canonical(report) + b"\n")


if __name__ == "__main__":
    main()
