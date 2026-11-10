"""Bounded fresh trials through the canonical provider port; no retries.

Every two-stage run reserves at most USD 0.05 total. Ambiguous attempts retain
their hold and stop dependent work. AuthorityEffect: None.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import json
from pathlib import Path
import time
import urllib.request

from omega_engine_providers.domain.types import CandidateRequest, DecodingParamsV1
from omega_engine_providers.infrastructure.budget_ledger import SqliteBudgetLedger
from omega_engine_providers.infrastructure.openai_compat import build_openai_compat_body
from omega_engine_providers.infrastructure.openrouter_transport import openrouter_transport
from omega_engine_providers.infrastructure.wire import decode_reply
from omega_engine_symbol_game.use_cases.pfp_proposal import ProposalCheck
from omega_engine_symbol_game.use_cases.pfp_stages import PfpStagePolicy

from .catalog import ROOT, canonical, digest, load_plan, prompt_for
from .execution import isolated, source_bindings

MAX_OUTPUT = 3000
CAP = 50000


def write_new(path, data):
    if not isinstance(data, bytes):
        data = canonical(data)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        import os
        os.fsync(stream.fileno())


def micro(value):
    if type(value) not in (str, int, float, Decimal):
        raise ValueError("MISSING_COST")
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("INVALID_COST")
    return int((amount * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


def snapshot_pricing(model):
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
        raw = response.read()
    catalog = json.loads(raw)
    row = next((r for r in catalog["data"] if r["id"] == model), None)
    if row is None:
        raise ValueError("MODEL_NOT_LISTED")
    pricing = row["pricing"]
    for key, value in pricing.items():
        if not Decimal(value).is_finite() or Decimal(value) < 0:
            raise ValueError("INVALID_PRICING")
        if key not in ("prompt", "completion", "input_cache_read", "input_cache_write") and Decimal(value) != 0:
            raise ValueError("UNSUPPORTED_SURCHARGE")
    if not {"max_tokens", "temperature", "reasoning"}.issubset(row["supported_parameters"]):
        raise ValueError("DECODING_UNSUPPORTED")
    return dict(observed_at=datetime.now(timezone.utc).isoformat(), catalog_sha256=digest(raw), row=row)


def request(prompt):
    return CandidateRequest(prompt["system"], prompt["user"], decoding=DecodingParamsV1(
        temperature=0.0, allow_fallbacks=False, require_parameters=True, thinking="disabled"))


def grade(row, raw, model):
    reply = decode_reply(raw)
    if reply.get("model") != model or type(reply.get("id")) is not str or not reply["id"]:
        raise ValueError("PROVIDER_IDENTITY_MISMATCH")
    usage = reply.get("usage", {})
    if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ("prompt_tokens", "completion_tokens", "total_tokens")):
        raise ValueError("MISSING_USAGE")
    cost = micro(usage.get("cost"))
    text = reply["choices"][0]["message"]["content"]
    if type(text) is not str:
        raise ValueError("MISSING_COMPLETION")
    result = isolated(dict(kind="LLM", row=row, raw_reply=text), timeout=30)
    return dict(result=result, generation_id=reply["id"], model=model, usage=usage,
                cost_microusd=cost, finish_reason=reply["choices"][0].get("finish_reason"))


def choose_case(challenge_id, split, ordinal):
    matches = [row for f in load_plan()["families"] for c in f["challenges"]
               if c["challenge"] == challenge_id for row in c["cases"] if row["split"] == split]
    return matches[ordinal]


RUNTIME_SOURCES = (
    "omega_engine_symbol_game/domain/pfp_ingress.py",
    "omega_engine_symbol_game/use_cases/pfp_proposal.py",
    "omega_engine_symbol_game/use_cases/pfp_stages.py",
    "omega_engine_education/pfp/infrastructure/challenge_campaign/catalog.py",
    "omega_engine_education/pfp/infrastructure/challenge_campaign/execution.py",
    "omega_engine_education/pfp/infrastructure/challenge_campaign/live.py",
)


def live_run(row, output: Path, model, arm, price=None, transfer_from=None):
    if output.exists():
        raise ValueError("RUN_ALREADY_EXISTS")
    output.mkdir(parents=True)
    price = price or snapshot_pricing(model)
    if price["row"]["id"] != model:
        raise ValueError("PRICING_MODEL_MISMATCH")
    write_new(output / "pricing.json", price)
    initial_feedback = None
    lineage = None
    if arm == "transfer":
        if transfer_from is None or row["split"] != "held_out":
            raise ValueError("TRANSFER_REQUIRES_HELD_OUT_AND_DEVELOPMENT_EVIDENCE")
        replay_live(transfer_from)
        previous = json.loads((transfer_from / "config.json").read_bytes())["row"]
        if previous["split"] != "development" or previous["challenge"] != row["challenge"] or previous["source"] == row["source"]:
            raise ValueError("TRANSFER_SPLIT_OR_FAMILY_VIOLATION")
        first = json.loads((transfer_from / "stage_1/receipt.json").read_bytes())
        initial_feedback = first["result"].get("feedback")
        if initial_feedback is None:
            raise ValueError("NO_REUSABLE_FAILURE_RULE")
        lineage = dict(source_run=str(transfer_from), source_receipt_sha256=digest((transfer_from / "stage_1/receipt.json").read_bytes()),
                       admission_status="CANDIDATE_ONLY")
    source = ROOT / row["source"]
    challenge = next(p for p in source.parents if p.name[:4] == row["challenge"].lower())
    sources = source_bindings(challenge)
    sources.update({p: digest((ROOT / p).read_bytes()) for p in RUNTIME_SOURCES})
    write_new(output / "config.json", dict(row=row, model=model, arm=arm, max_stages=2, sources=sources,
              initial_feedback=initial_feedback, lineage=lineage, cap_microusd=CAP, max_output_tokens=MAX_OUTPUT,
              authorization="User approved OpenRouter; USD 0.05 per run"))
    ledger = SqliteBudgetLedger(output / "budget.sqlite3", budget_id="pfp-learning")
    transport = openrouter_transport(timeout=55.0)
    if transport.is_err:
        raise ValueError("PROVIDER_CREDENTIAL_UNAVAILABLE")
    send = transport.unwrap()
    policy = PfpStagePolicy()
    feedback = initial_feedback
    records = []
    for stage in range(1, policy.max_stages + 1):
        prompt = prompt_for(row, arm, feedback)
        candidate_request = request(prompt)
        candidate_request.check_payload_ceiling()
        rates = price["row"]["pricing"]
        reserve = micro(Decimal(rates["prompt"]) * (candidate_request.estimated_payload_bytes() + 256)
                        + Decimal(rates["completion"]) * MAX_OUTPUT)
        with ledger.transaction(CAP) as state:
            if any(a["state"] != "settled" for a in state["attempts"].values()):
                raise ValueError("UNRECONCILED_ATTEMPT")
            if state["spent"] + reserve > CAP:
                raise ValueError("RUN_CAP_EXCEEDED")
            state["spent"] += reserve
            state["attempts"][str(stage)] = dict(state="reserved", reserved=reserve)
        stage_dir = output / f"stage_{stage}"
        stage_dir.mkdir()
        body = build_openai_compat_body(candidate_request, model=model, max_tokens=MAX_OUTPUT)
        body["usage"] = {"include": True}
        write_new(stage_dir / "request.json", body)
        write_new(stage_dir / "reservation.json", dict(reserved_microusd=reserve, request_sha256=digest(canonical(body))))
        start = time.monotonic()
        try:
            raw = send(model, candidate_request, MAX_OUTPUT)
        except Exception as exc:
            # Preserve the hold: HTTP failure is not a zero-cost completion.
            failure = dict(status="INFRASTRUCTURE_ERROR", failure_class="TRANSPORT",
                           error=type(exc).__name__, reason=str(exc), reserved_microusd=reserve,
                           cost_microusd=None, reconciliation="REQUIRED", completed_stages=len(records))
            write_new(stage_dir / "transport_failure.json", failure)
            write_new(output / "summary.json", failure)
            print(json.dumps(failure), flush=True)
            return records
        elapsed = time.monotonic() - start
        write_new(stage_dir / "provider_response.json", raw)
        receipt = grade(row, raw, model)
        if receipt["cost_microusd"] > reserve:
            raise ValueError("BILL_EXCEEDS_RESERVATION")
        receipt.update(latency_seconds=elapsed, raw_sha256=digest(raw), request_sha256=digest(canonical(body)))
        write_new(stage_dir / "receipt.json", receipt)
        with ledger.transaction(CAP) as state:
            if receipt["generation_id"] in [a.get("generation_id") for a in state["attempts"].values()]:
                raise ValueError("DUPLICATE_GENERATION")
            state["spent"] += receipt["cost_microusd"] - reserve
            state["attempts"][str(stage)].update(state="settled", actual=receipt["cost_microusd"], generation_id=receipt["generation_id"])
        records.append(receipt)
        result = receipt["result"]
        feedback = policy.feedback_after(stage, ProposalCheck(result["status"], result["failure_class"]))
        print(json.dumps(dict(challenge=row["challenge"], stage=stage, arm=arm, status=result["status"], cost_microusd=receipt["cost_microusd"])), flush=True)
        if feedback is None:
            break
    write_new(output / "summary.json", dict(status=records[-1]["result"]["status"], stages=len(records),
              cost_microusd=sum(r["cost_microusd"] for r in records), transfer_benefit="UNMEASURED"))
    return records


def replay_live(output):
    config = json.loads((output / "config.json").read_bytes())
    for path, expected in config["sources"].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError("RUNTIME_SOURCE_DRIFT")
    feedback = config["initial_feedback"]
    stages = sorted(output.glob("stage_*"))
    for stage in stages:
        receipt = json.loads((stage / "receipt.json").read_bytes())
        raw = (stage / "provider_response.json").read_bytes()
        wire = (stage / "request.json").read_bytes()
        expected = build_openai_compat_body(request(prompt_for(config["row"], config["arm"], feedback)), model=config["model"], max_tokens=MAX_OUTPUT)
        expected["usage"] = {"include": True}
        if digest(raw) != receipt["raw_sha256"] or digest(wire) != receipt["request_sha256"] or wire != canonical(expected):
            raise ValueError("REPLAY_BINDING_MISMATCH")
        checked = grade(config["row"], raw, config["model"])
        for key, value in checked.items():
            if canonical(value) != canonical(receipt[key]):
                raise ValueError("REPLAY_RESULT_MISMATCH")
        result = checked["result"]
        feedback = result.get("feedback")
    return len(stages)
