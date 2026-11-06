"""Live seed calls for pilots 0000001 through 0000025.

AuthorityEffect: None.

Each spec's models list is that pilot's existing free model, then
deepseek/deepseek-v4.1-flash. No other model is added. target_spend_usd
stays 0.0010. The session ceiling stays 0.0010 USD until the priced
DeepSeek calls cannot fit, and then it is 0.01 USD. A chat completion is
a candidate for the seed text. It does not execute a mode substrate.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.request
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any

import yaml

from omega_engine_education.pilots.mode_trials.execute import NoAliasDumper, _write
from omega_engine_providers.domain.types import CandidateRequest, DecodingParamsV1
from omega_engine_providers.infrastructure.credential_source import resolve_credential
from omega_engine_providers.infrastructure.openrouter_transport import openrouter_transport

PILOTS = Path(__file__).resolve().parents[1]
PAID_MODEL = "deepseek/deepseek-v4.1-flash"
PREFERRED_USD = Decimal("0.0010")
LARGER_USD = Decimal("0.01")
PREFERRED_MICROUSD = 1_000
LARGER_MICROUSD = 10_000
MAX_OUTPUT_TOKENS = 160
MARKER = "\n# Folder pointers. PilotSpec ignores unknown keys.\n"
LEAK = re.compile(r'"(?:expected_answer|expected_outcome|output)"\s*:')
SYSTEM = (
    "Reply with one JSON object and no markdown. "
    "Use only the facts in the task."
)


def models_for(model_id: str) -> list[str]:
    if type(model_id) is not str or not model_id.endswith(":free"):
        raise ValueError("models list accepts only a :free id plus DeepSeek V4.1 Flash")
    if model_id == PAID_MODEL:
        raise ValueError("the free slot cannot be the metered model")
    return [model_id, PAID_MODEL]


def session_cap_microusd(estimates: list[int]) -> int:
    """0.0010 USD when the priced calls fit. 0.01 USD when they need more room."""
    if any(type(item) is not int or item < 0 for item in estimates):
        raise ValueError("estimates must be non-negative ints")
    if any(item > LARGER_MICROUSD for item in estimates):
        raise ValueError("one call exceeds 0.01 USD")
    if sum(estimates) <= PREFERRED_MICROUSD:
        return PREFERRED_MICROUSD
    return LARGER_MICROUSD


def public_messages(seed_prompt: str, answer: object) -> tuple[str, str]:
    if type(seed_prompt) is not str or not seed_prompt.strip():
        raise ValueError("seed prompt is empty")
    user = seed_prompt.strip()
    blob = SYSTEM + "\n" + user
    if LEAK.search(blob):
        raise ValueError("ANSWER_BEARING_PUBLIC_PROMPT")
    encoded = json.dumps(answer, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if type(answer) in (dict, list) and encoded in blob:
        raise ValueError("ANSWER_BEARING_PUBLIC_PROMPT")
    return SYSTEM, user


def estimate_microusd(
    prompt_per_token: Decimal,
    completion_per_token: Decimal,
    input_tokens: int,
    output_tokens: int,
) -> int:
    if input_tokens < 0 or output_tokens < 1:
        raise ValueError("token counts")
    cost = prompt_per_token * input_tokens + completion_per_token * output_tokens
    return int((cost * Decimal(1_000_000)).to_integral_value(rounding=ROUND_CEILING))


def input_token_estimate(system: str, user: str) -> int:
    size = len(system.encode("utf-8")) + len(user.encode("utf-8"))
    return max(1, (size + 1) // 2) + 16


def retarget_specs(root: Path | None = None) -> list[str]:
    base = root or PILOTS
    changed: list[str] = []
    for index in range(1, 26):
        pilot_id = f"pilot_{index:07d}"
        path = base / pilot_id / "spec.yaml"
        text = path.read_text(encoding="utf-8")
        if "\r" in text or MARKER not in text:
            raise RuntimeError(f"{pilot_id} spec is not a mode-trial spec")
        raw = yaml.safe_load(text)
        models = models_for(raw["coordinates"]["model_id"])
        text = text.replace("\n  target_spend_usd: 0.0\n", "\n  target_spend_usd: 0.0010\n", 1)
        block = "models:\n" + "".join(f"  - {model_id}\n" for model_id in models)
        if "\nmodels:\n" in text:
            start = text.index("\nmodels:\n")
            end = text.index(MARKER)
            text = text[:start] + "\n" + block + text[end:]
        else:
            text = text.replace(MARKER, "\n" + block + MARKER, 1)
        if not text.endswith("\n"):
            text += "\n"
        _write(path, text)
        changed.append(pilot_id)
    return changed


def _dump(payload: dict) -> str:
    text = yaml.dump(payload, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True, width=100)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _slug(model_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", model_id)


def host_answer_matches(parsed: object, answer: object) -> bool:
    """Match a bare oracle or the one-key envelope the seed asks the model to return."""
    if _exact(parsed, answer):
        return True
    if type(parsed) is dict and "answer" in parsed:
        return _exact(parsed["answer"], answer)
    return False


def _exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_exact(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(_exact(a, b) for a, b in zip(left, right))
    if type(left) is float:
        return False
    return left == right


def _parse_reply(raw: str) -> tuple[bool, object]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        return True, json.loads(cleaned)
    except (json.JSONDecodeError, RecursionError):
        return False, None


def _price_row(payload: dict) -> dict[str, str]:
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("PRICE_CATALOG_UNREADABLE")
    for row in rows:
        if isinstance(row, dict) and row.get("id") == PAID_MODEL and isinstance(row.get("pricing"), dict):
            pricing = row["pricing"]
            prompt = pricing.get("prompt")
            completion = pricing.get("completion")
            if isinstance(prompt, str) and isinstance(completion, str):
                return {"prompt": prompt, "completion": completion}
    raise ValueError("PRICE_NOT_LISTED")


def fetch_paid_pricing(api_key: str) -> tuple[Decimal, Decimal, dict[str, str]]:
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    quoted = _price_row(payload)
    return Decimal(quoted["prompt"]), Decimal(quoted["completion"]), quoted


def _microusd(cost: float) -> int:
    return int((Decimal(str(cost)) * Decimal(1_000_000)).to_integral_value(rounding=ROUND_CEILING))


def _call_dir(folder: Path, model_id: str, suffix: str = "") -> tuple[Path, Path]:
    live = folder / "results" / "live"
    slug = _slug(model_id) + suffix
    return live / f"{slug}.reservation.yaml", live / f"{slug}.yaml"


def _retryable(path: Path) -> bool:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return False
    if loaded.get("transport_code") == "PROVIDER_HTTP_429":
        return True
    return loaded.get("status") == "RECORDED" and loaded.get("raw_reply") == ""


def _open_slot(folder: Path, model_id: str, billing: str) -> tuple[Path | None, Path | None]:
    previous: Path | None = None
    for index, suffix in enumerate(("", ".attempt2", ".attempt3")):
        reservation, call = _call_dir(folder, model_id, suffix)
        if not call.exists():
            if reservation.exists() or index == 0:
                return reservation, call
            if billing == "metered" and previous is not None and _retryable(previous):
                if index == 2:
                    loaded = yaml.safe_load(previous.read_text(encoding="utf-8"))
                    if not isinstance(loaded, dict) or loaded.get("transport_code") != "PROVIDER_HTTP_429":
                        return None, None
                return reservation, call
            return None, None
        previous = call
    return None, None


def _spent_already(base: Path) -> int:
    total = 0
    paths = []
    for index in range(1, 26):
        live = base / f"pilot_{index:07d}" / "results" / "live"
        if live.is_dir():
            paths.extend(live.glob("*.yaml"))
    for path in paths:
        if path.name.endswith(".reservation.yaml"):
            continue
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or loaded.get("billing") != "metered":
            continue
        if loaded.get("status") not in {"RECORDED", "SESSION_CAP_EXCEEDED"}:
            continue
        cost = loaded.get("reported_cost_usd")
        if type(cost) in (int, float) and math.isfinite(float(cost)) and float(cost) >= 0:
            total += _microusd(float(cost))
    return total


def dispatch_pilots(root: Path | None = None) -> dict[str, Any]:
    base = root or PILOTS
    retarget_specs(base)
    found = resolve_credential(["OPENROUTER_API_KEY"], start=base)
    if not found.is_ok:
        raise RuntimeError("MISSING_OPENROUTER_API_KEY")
    api_key = found.unwrap().value
    prompt_price, completion_price, quoted = fetch_paid_pricing(api_key)
    transport = openrouter_transport(timeout=90.0)
    if not transport.is_ok:
        raise RuntimeError("OPENROUTER_TRANSPORT_REFUSED")
    send = transport.unwrap()
    plans: list[dict[str, Any]] = []
    for index in range(1, 26):
        folder = base / f"pilot_{index:07d}"
        spec = yaml.safe_load((folder / "spec.yaml").read_text(encoding="utf-8"))
        seed = yaml.safe_load((folder / "seed.yaml").read_text(encoding="utf-8"))
        models = spec.get("models")
        if models != models_for(spec["coordinates"]["model_id"]):
            raise RuntimeError(f"{folder.name} models list drifted")
        try:
            system, user = public_messages(seed["seed_prompt"], seed["expected_outcome"]["answer"])
        except ValueError as error:
            plans.append({"folder": folder, "skip": str(error), "model_id": None, "billing": None})
            continue
        tokens = input_token_estimate(system, user)
        request = CandidateRequest(
            system, user,
            decoding=DecodingParamsV1(
                temperature=0.0, allow_fallbacks=False, require_parameters=False, thinking="disabled",
            ),
        )
        output_tokens = MAX_OUTPUT_TOKENS
        estimate = estimate_microusd(prompt_price, completion_price, tokens, output_tokens)
        while estimate > LARGER_MICROUSD and output_tokens > 32:
            output_tokens //= 2
            estimate = estimate_microusd(prompt_price, completion_price, tokens, output_tokens)
        for model_id in models:
            billing = "free" if model_id.endswith(":free") else "metered"
            if billing == "metered" and estimate > LARGER_MICROUSD:
                plans.append({
                    "folder": folder, "pilot_id": folder.name, "model_id": model_id,
                    "skip": "OVER_PER_CALL_CAP", "billing": billing,
                })
                continue
            plans.append({
                "folder": folder,
                "pilot_id": folder.name,
                "model_id": model_id,
                "billing": billing,
                "system": system,
                "user": user,
                "request": request,
                "answer": seed["expected_outcome"]["answer"],
                "estimate": 0 if billing == "free" else estimate,
                "output_tokens": output_tokens,
                "skip": None,
            })
    priced = [
        plan["estimate"] for plan in plans
        if plan.get("billing") == "metered" and not plan.get("skip")
    ]
    cap = session_cap_microusd(priced)
    spent = _spent_already(base)
    stopped = False
    stop_reason = ""
    results: list[dict[str, Any]] = []
    for plan in plans:
        if plan.get("skip"):
            results.append({"pilot_id": plan["folder"].name, "status": plan["skip"]})
            continue
        if stopped and plan["billing"] == "metered":
            results.append({"pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": stop_reason})
            continue
        reservation_path, call_path = _open_slot(plan["folder"], plan["model_id"], plan["billing"])
        if reservation_path is None:
            results.append({"pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": "ALREADY_RECORDED"})
            continue
        if reservation_path.exists():
            stopped = True
            stop_reason = "UNSETTLED_RESERVATION"
            results.append({"pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": stop_reason})
            continue
        if plan["billing"] == "metered" and (plan["estimate"] > cap or spent + plan["estimate"] > cap):
            results.append({
                "pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": "OVER_SESSION_CAP",
            })
            continue
        _write(reservation_path, _dump({
            "schema": "pfp.mode-trial-live-reservation.v1",
            "authority_effect": "None",
            "pilot_id": plan["pilot_id"],
            "model_id": plan["model_id"],
            "billing": plan["billing"],
            "reserved_microusd": plan["estimate"] if plan["billing"] == "metered" else 0,
            "session_cap_microusd": cap,
            "status": "reserved",
        }))
        try:
            raw_bytes = send(plan["model_id"], plan["request"], plan["output_tokens"])
        except Exception as error:
            code = str(getattr(error, "code", None) or type(error).__name__)
            _write(call_path, _dump({
                "schema": "pfp.mode-trial-live-response.v1",
                "authority_effect": "None",
                "pilot_id": plan["pilot_id"],
                "model_id": plan["model_id"],
                "billing": plan["billing"],
                "status": "TRANSPORT_FAILURE",
                "transport_code": code,
                "provider_calls": 1,
                "live_call_is_mode_winning_condition": False,
            }))
            results.append({"pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": code})
            continuable = {"PROVIDER_HTTP_400", "PROVIDER_HTTP_404", "PROVIDER_HTTP_408", "PROVIDER_HTTP_429"}
            if code not in continuable:
                stopped = True
                stop_reason = code
            continue
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError, RecursionError):
            _write(call_path, _dump({
                "schema": "pfp.mode-trial-live-response.v1",
                "authority_effect": "None",
                "pilot_id": plan["pilot_id"],
                "model_id": plan["model_id"],
                "status": "UNRECONCILED_COST",
                "provider_calls": 1,
                "live_call_is_mode_winning_condition": False,
            }))
            stopped = True
            stop_reason = "UNRECONCILED_COST"
            results.append({"pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": stop_reason})
            continue
        usage = payload.get("usage") if isinstance(payload, dict) else None
        cost = usage.get("cost") if isinstance(usage, dict) else None
        if isinstance(cost, str):
            try:
                cost = float(cost)
            except ValueError:
                cost = None
        if not isinstance(usage, dict) or type(cost) not in (int, float) or not math.isfinite(float(cost)) or float(cost) < 0:
            _write(call_path, _dump({
                "schema": "pfp.mode-trial-live-response.v1",
                "authority_effect": "None",
                "pilot_id": plan["pilot_id"],
                "model_id": plan["model_id"],
                "status": "UNRECONCILED_COST",
                "provider_calls": 1,
                "live_call_is_mode_winning_condition": False,
            }))
            stopped = True
            stop_reason = "UNRECONCILED_COST"
            results.append({"pilot_id": plan["pilot_id"], "model_id": plan["model_id"], "status": stop_reason})
            continue
        reported = float(cost)
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        token_total = 0
        if type(prompt_tokens) is int:
            token_total += prompt_tokens
        if type(completion_tokens) is int:
            token_total += completion_tokens
        if plan["billing"] == "free" and reported > 0:
            status = "UNEXPECTED_FREE_MODEL_CHARGE"
            stopped = True
            stop_reason = status
        elif plan["billing"] == "metered" and reported == 0 and token_total > 0:
            status = "UNRECONCILED_ZERO_COST"
            stopped = True
            stop_reason = status
        else:
            status = "RECORDED"
        content = ""
        reasoning = ""
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                if type(message.get("content")) is str:
                    content = message["content"]
                if type(message.get("reasoning")) is str:
                    reasoning = message["reasoning"]
        parsed_ok, parsed = _parse_reply(content)
        matched = parsed_ok and host_answer_matches(parsed, plan["answer"])
        billed = _microusd(reported)
        if status == "RECORDED":
            spent += billed
            if spent > cap:
                status = "SESSION_CAP_EXCEEDED"
                stopped = True
                stop_reason = status
        echoed = payload.get("model") if isinstance(payload, dict) else None
        _write(call_path, _dump({
            "schema": "pfp.mode-trial-live-response.v1",
            "authority_effect": "None",
            "pilot_id": plan["pilot_id"],
            "model_id": plan["model_id"],
            "echoed_model": echoed,
            "billing": plan["billing"],
            "status": status,
            "provider_calls": 1,
            "request_sha256": hashlib.sha256(json.dumps(
                {"model": plan["model_id"], "system": plan["system"], "user": plan["user"]},
                sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ).encode("utf-8")).hexdigest(),
            "raw_reply": content,
            "reasoning_text": reasoning,
            "parsed_json": parsed_ok,
            "host_exact_match": matched,
            "reported_cost_usd": reported,
            "reported_usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost": reported,
            },
            "reserved_microusd": plan["estimate"] if plan["billing"] == "metered" else 0,
            "session_cap_microusd": cap,
            "price_quote_usd_per_token": quoted,
            "live_call_is_mode_winning_condition": False,
        }))
        results.append({
            "pilot_id": plan["pilot_id"],
            "model_id": plan["model_id"],
            "status": status,
            "reported_cost_usd": reported,
            "host_exact_match": matched,
        })
    ledger = {
        "schema": "pfp.mode-trial-live-session.v1",
        "authority_effect": "None",
        "paid_model": PAID_MODEL,
        "target_spend_usd": "0.0010",
        "session_cap_usd": "0.0010" if cap == PREFERRED_MICROUSD else "0.01",
        "session_cap_microusd": cap,
        "spent_microusd": spent,
        "price_quote_usd_per_token": quoted,
        "calls": results,
    }
    _write(base / "mode_trials" / "live_session.yaml", _dump(ledger))
    return ledger


def main() -> None:
    ledger = dispatch_pilots()
    print(json.dumps({
        "session_cap_usd": ledger["session_cap_usd"],
        "spent_microusd": ledger["spent_microusd"],
        "calls": len(ledger["calls"]),
    }))


if __name__ == "__main__":
    main()
