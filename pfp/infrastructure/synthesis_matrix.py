"""Original synthesis cases/judges with PFP-bound, accounted model turns.

Private answer fields stay host-side. Raw provider bytes and checked completion
bytes are retained separately. Malformed replies are infrastructure failures;
unknown accounting stops the sweep. No raw HTTP fallback is available.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import traceback
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from pfp.infrastructure.pilot_matrix import (
    complete_pilot_turn,
    make_pilot_gateways,
    validate_pilot_gateways,
)
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1

API_KEY_ENV = "OPENROUTER_API_KEY"
OUTCOME_ACCEPTED = "ACCEPTED"
OUTCOME_REJECTED = "REJECTED"
OUTCOME_INFRA_ERROR = "INFRA_ERROR"
OUTCOME_CHECKER_DEFECT = "CHECKER_DEFECT"
OUTCOME_WARRANTED_REFUSAL = "WARRANTED_REFUSAL"
OUTCOME_UNWARRANTED_REFUSAL = "UNWARRANTED_REFUSAL"
OUTCOMES = (
    OUTCOME_ACCEPTED,
    OUTCOME_WARRANTED_REFUSAL,
    OUTCOME_UNWARRANTED_REFUSAL,
    OUTCOME_REJECTED,
    OUTCOME_INFRA_ERROR,
    OUTCOME_CHECKER_DEFECT,
)
REFUSAL_STATUSES = frozenset({"UNKNOWN", "OUT_OF_SCOPE", "REFUSED"})

ANSWER_BEARING_KEYS = frozenset(
    {"case_id", "type", "answer", "label", "verdict", "class", "classification", "solution"}
)
ANSWER_BEARING_PREFIXES = ("expected",)

Checker = Callable[[Any, Any], Any]
Transport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], tuple[int, str]]


class RunnerRefusal(Exception):
    """Typed refusal raised before any provider call is made."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def require_api_key(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    key = env.get(API_KEY_ENV, "")
    if not isinstance(key, str) or not key.strip():
        raise RunnerRefusal(
            "CONFIGURATION_MISSING",
            f"{API_KEY_ENV} must be set by the launching process; .env files are not read",
        )
    return key


def opaque_token(index: int) -> str:
    if type(index) is not int or index < 1:
        raise ValueError("index must be a positive int")
    return f"case_{index:02d}"


def is_answer_bearing_key(key: str) -> bool:
    return key in ANSWER_BEARING_KEYS or key.startswith(ANSWER_BEARING_PREFIXES)


def prompt_view(
    case: Mapping[str, Any], token: str, hidden_keys: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """The case as the model may see it: opaque token, no answer-bearing or judge-only keys."""
    view: dict[str, Any] = {"case_id": token}
    for key, value in case.items():
        if not is_answer_bearing_key(key) and key not in hidden_keys:
            view[key] = value
    return view


def build_user_prompt(
    instruction: str, case: Mapping[str, Any], token: str, hidden_keys: frozenset[str] = frozenset()
) -> str:
    body = json.dumps(prompt_view(case, token, hidden_keys), indent=2, ensure_ascii=False)
    prompt = (
        f"{instruction}\n\n{body}\n\n"
        f'Return one JSON object only, with "case_id": "{token}", and no Markdown fences.'
    )
    problems = prompt_leaks(prompt, case, token)
    if problems:
        raise RunnerRefusal("PROMPT_LEAK", "; ".join(problems))
    return prompt


def prompt_leaks(prompt: str, case: Mapping[str, Any], token: str) -> list[str]:
    problems: list[str] = []
    case_id = case.get("case_id")
    if isinstance(case_id, str) and case_id and case_id != token and case_id in prompt:
        problems.append("case ID appears in the prompt")
    if "RFC 8785" in prompt:
        problems.append("prompt claims RFC 8785")
    return problems


def system_prompt_problems(system_prompt: str) -> list[str]:
    return ["system prompt claims RFC 8785"] if "RFC 8785" in system_prompt else []


@dataclass(frozen=True)
class ProviderExchange:
    ok: bool
    request: dict[str, Any]
    http_status: int | None
    raw_body: str | None
    content: str | None
    reasoning: str | None
    finish_reason: str | None
    usage: dict[str, Any]
    error: str | None
    elapsed_s: float
    pfp: dict | None = None
    provider_wire: dict | None = None
    attempt_state: str | None = None
    stop: bool = False


def urllib_transport(
    url: str, headers: Mapping[str, str], payload: Mapping[str, Any], timeout: float
) -> tuple[int, str]:
    """Retired compatibility entry point: raw pilot sends are no longer supported."""
    raise RunnerRefusal("PFP_ACCOUNTED_GATEWAY_REQUIRED", "use an accounted PFP gateway")


def call_model(
    api_key: str, model_id: str, system_prompt: str, user_prompt: str, *,
    max_tokens: int, title: str, transport: Transport = urllib_transport,
    timeout: float = 120.0, gateway=None, task_id: str = "pilot-synthesis",
    attempt_id: str = "pilot-turn",
) -> ProviderExchange:
    # Legacy positional credentials/title/timeout remain callable; the composed
    # gateway owns transport configuration and credentials.
    if transport is not urllib_transport:
        result = dict(ok=False, request={}, raw_body=None, content=None, reasoning=None,
            usage={}, error="PFP_RAW_TRANSPORT_UNSUPPORTED", elapsed=0, stop=True)
    else:
        result = complete_pilot_turn(gateway,
            CandidateRequest(system_prompt, user_prompt, decoding=DecodingParamsV1(temperature=0.0)),
            model=model_id, task_id=task_id, attempt_id=attempt_id, max_tokens=max_tokens)
    wire = result.get("provider_wire") or {}
    finish_reason = None
    try:
        finish_reason = json.loads(result.get("raw_body") or "{}")["choices"][0]["finish_reason"]
    except (ValueError, KeyError, TypeError, IndexError):
        pass
    return ProviderExchange(ok=result["ok"], request=result["request"],
        http_status=wire.get("http_status"), raw_body=result["raw_body"], content=result["content"],
        reasoning=result["reasoning"], finish_reason=finish_reason, usage=result["usage"],
        error=result["error"], elapsed_s=result["elapsed"], pfp=result.get("pfp"),
        provider_wire=result.get("provider_wire"), attempt_state=result.get("attempt_state"),
        stop=result["stop"])


def parse_answer(text: str) -> tuple[Any, str | None]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    if not stripped:
        return None, "EMPTY_CONTENT"
    try:
        return json.loads(stripped), None
    except json.JSONDecodeError as exc:
        return None, f"JSON_PARSE_ERROR: {exc}"


def rebind_token(answer: Any, token: str, case_id: Any) -> Any:
    """Map the opaque token in a reply back to the judge's case ID."""
    if isinstance(answer, dict) and answer.get("case_id") == token:
        rebound = dict(answer)
        rebound["case_id"] = case_id
        return rebound
    return answer


def run_checkers(
    case: Any, answer: Any, checkers: Sequence[tuple[str, Checker]]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, checker in checkers:
        try:
            verdict = checker(case, answer)
            if not isinstance(verdict, tuple) or len(verdict) != 2 or type(verdict[0]) is not bool:
                raise TypeError(f"checker returned {verdict!r}, expected (bool, message)")
            results.append({"checker": name, "ok": verdict[0], "message": str(verdict[1])})
        except Exception as exc:  # noqa: BLE001 - a crashing checker is a recorded defect
            results.append(
                {
                    "checker": name,
                    "ok": None,
                    "defect": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )
    return results


def score_exchange(
    case: Mapping[str, Any],
    token: str,
    exchange: ProviderExchange,
    checkers: Sequence[tuple[str, Checker]],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "case_id": case.get("case_id"),
        "token": token,
        "request": exchange.request,
        "http_status": exchange.http_status,
        "raw_body": exchange.raw_body,
        "content": exchange.content,
        "reasoning": exchange.reasoning,
        "finish_reason": exchange.finish_reason,
        "truncated": exchange.finish_reason == "length",
        "usage": exchange.usage,
        "elapsed_s": round(exchange.elapsed_s, 3),
        "pfp": exchange.pfp,
        "provider_wire": exchange.provider_wire,
        "attempt_state": exchange.attempt_state,
        "stop": exchange.stop,
    }
    if not exchange.ok:
        record["outcome"] = OUTCOME_INFRA_ERROR
        record["error"] = exchange.error
        return record
    if not checkers:
        record["outcome"] = OUTCOME_CHECKER_DEFECT
        record["error"] = "CHECKER_REQUIRED"
        return record
    answer, parse_error = parse_answer(exchange.content or "")
    if parse_error is not None:
        record["outcome"] = OUTCOME_REJECTED
        record["parse_error"] = parse_error
        return record
    record["answer"] = answer
    results = run_checkers(case, rebind_token(answer, token, case.get("case_id")), checkers)
    record["checkers"] = results
    refusal = isinstance(answer, dict) and answer.get("status") in REFUSAL_STATUSES
    if any(r["ok"] is None for r in results):
        record["outcome"] = OUTCOME_CHECKER_DEFECT
    elif all(r["ok"] for r in results):
        record["outcome"] = OUTCOME_WARRANTED_REFUSAL if refusal else OUTCOME_ACCEPTED
    else:
        record["outcome"] = OUTCOME_UNWARRANTED_REFUSAL if refusal else OUTCOME_REJECTED
    return record


def summarize(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Counts per outcome. ``accepted`` counts constructive solutions only; ``warranted_refusals``
    counts refusals every checker accepted; ``scored`` excludes INFRA_ERROR and CHECKER_DEFECT."""
    counts = {outcome: 0 for outcome in OUTCOMES}
    for record in records:
        counts[record["outcome"]] += 1
    scored = sum(
        counts[o] for o in OUTCOMES if o not in (OUTCOME_INFRA_ERROR, OUTCOME_CHECKER_DEFECT)
    )
    return {
        "counts": counts,
        "scored": scored,
        "accepted": counts[OUTCOME_ACCEPTED],
        "warranted_refusals": counts[OUTCOME_WARRANTED_REFUSAL],
        "total": len(records),
    }


def prepare_output_dir(path: Path) -> Path:
    if path.exists():
        raise RunnerRefusal(
            "OUTPUT_DIR_EXISTS", f"{path} already exists; runs never overwrite results"
        )
    path.mkdir(parents=True)
    return path


def _dump(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


@dataclass(frozen=True)
class MatrixSpec:
    challenge: str
    system_prompt: str
    instruction: str
    cases: Sequence[Mapping[str, Any]]
    checkers: Sequence[tuple[str, Checker]]
    models: Sequence[Mapping[str, str]]
    max_tokens: int = 4096
    hidden_keys: frozenset[str] = frozenset()
    notes: Mapping[str, Any] = field(default_factory=dict)

    def prompts(self) -> list[tuple[Mapping[str, Any], str, str]]:
        problems = system_prompt_problems(self.system_prompt)
        if problems:
            raise RunnerRefusal("PROMPT_LEAK", "; ".join(problems))
        out = []
        for index, case in enumerate(self.cases, start=1):
            token = opaque_token(index)
            out.append(
                (case, token, build_user_prompt(self.instruction, case, token, self.hidden_keys))
            )
        return out


def run_matrix(
    spec: MatrixSpec,
    output_dir: Path,
    api_key: str = "",
    *,
    model_ids: Sequence[str] | None = None,
    transport: Transport = urllib_transport,
    pause_s: float = 1.0,
    gateways: Mapping[str, Any] | None = None,
    max_estimated_cost_microusd: int | None = None,
    max_calls: int = 5,
    env_file: Path | str | None = None,
) -> dict[str, Any]:
    if transport is not urllib_transport:
        raise RunnerRefusal("PFP_RAW_TRANSPORT_UNSUPPORTED", "inject an accounted gateway instead")
    if not spec.checkers:
        raise RunnerRefusal("CHECKER_REQUIRED", "the original judge must be supplied")
    if model_ids is not None and set(model_ids) - {m["id"] for m in spec.models}:
        raise RunnerRefusal("UNKNOWN_MODEL", "every requested model must be declared by this runner")
    prompts = spec.prompts()
    models = [m for m in spec.models if model_ids is None or m["id"] in model_ids]
    if not models:
        raise RunnerRefusal(
            "NO_MODEL_SELECTED", "none of the requested model ids is declared by this runner"
        )
    if gateways is None and max_estimated_cost_microusd is None:
        raise RunnerRefusal("PFP_ACCOUNTED_GATEWAY_REQUIRED", "supply a gateway or explicit estimated policy")
    if gateways is not None:
        try:
            validate_pilot_gateways(gateways, [m["id"] for m in models], max_tokens=spec.max_tokens)
        except ValueError as exc:
            raise RunnerRefusal(str(exc), "PFP gateway preflight failed") from exc
    out = prepare_output_dir(output_dir)
    task_id = f"{spec.challenge}:{uuid4().hex}"
    objective_sha256 = sha256(_dump(dict(challenge=spec.challenge, models=models,
        system_prompt=spec.system_prompt, prompts=[(token, prompt) for _, token, prompt in prompts],
        max_output_tokens=spec.max_tokens, notes=dict(spec.notes))).encode()).hexdigest()
    if gateways is None:
        try:
            gateways = make_pilot_gateways([m["id"] for m in models], max_output_tokens=spec.max_tokens,
                max_estimated_cost_microusd=max_estimated_cost_microusd, max_calls=max_calls,
                accounting_path=out / "accounting.sqlite3", env_file=env_file,
                run_id=task_id, objective_sha256=objective_sha256)
        except ValueError as exc:
            raise RunnerRefusal(getattr(exc, "code", str(exc)), "PFP gateway composition failed") from exc
    (out / "run.json").write_text(
        _dump(
            {
                "challenge": spec.challenge,
                "task_id": task_id,
                "objective_sha256": objective_sha256,
                "max_output_tokens": spec.max_tokens,
                "case_count": len(prompts),
                "financial_policy": "injected_accounted_gateway" if max_estimated_cost_microusd is None
                    else "estimated_vendor_cost",
                "system_prompt": spec.system_prompt,
                "models": list(models),
                "cases": [
                    {"token": token, "case_id": case.get("case_id")} for case, token, _ in prompts
                ],
                "notes": dict(spec.notes),
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    summary: dict[str, Any] = {"challenge": spec.challenge, "models": {},
        "planned": len(models) * len(prompts), "attempted": 0, "stop_reason": None}
    for model_index, model in enumerate(models):
        records: list[dict[str, Any]] = []
        with (out / f"records_{_safe(model['id'])}.jsonl").open(
            "w", encoding="utf-8", newline="\n"
        ) as sink:
            for case, token, user_prompt in prompts:
                exchange = call_model(
                    api_key,
                    model["id"],
                    spec.system_prompt,
                    user_prompt,
                    max_tokens=spec.max_tokens,
                    title=f"Symbol Game {spec.challenge}",
                    gateway=gateways[model["id"]], task_id=task_id,
                    attempt_id=f"{task_id}:model-{model_index}:{token}",
                )
                record = score_exchange(case, token, exchange, spec.checkers)
                record["model_id"] = model["id"]
                records.append(record)
                summary["attempted"] += 1
                sink.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                sink.flush()
                print(f"{model['id']} {token}: {record['outcome']}", flush=True)
                if exchange.stop:
                    summary["stop_reason"] = exchange.error
                    break
                if pause_s:
                    time.sleep(pause_s)
        summary["models"][model["id"]] = summarize(records)
        if summary["stop_reason"]:
            break
    (out / "summary.json").write_text(_dump(summary), encoding="utf-8", newline="\n")
    return summary


def _safe(model_id: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in model_id)


def main(
    spec: MatrixSpec,
    argv: Sequence[str] | None = None,
    transport: Transport = urllib_transport,
) -> int:
    parser = argparse.ArgumentParser(
        description=f"{spec.challenge} model matrix (makes live provider calls)"
    )
    parser.add_argument("--output-dir", required=True, type=Path, help="new directory for this run")
    parser.add_argument(
        "--model", action="append", dest="models", help="model id to run (repeatable)"
    )
    parser.add_argument("--max-estimated-cost-microusd", required=True, type=int,
        help="explicit estimated vendor-cost allowance for the whole sweep (maximum 50000)")
    parser.add_argument("--max-provider-calls", type=int, default=5)
    parser.add_argument("--max-output-tokens", type=int,
        help="explicit output-bound override; estimated mode supports at most 3000")
    parser.add_argument("--case-limit", type=int, help="exploratory prefix selection, not the full protocol")
    parser.add_argument("--env-file", type=Path, help="explicit credential file for the existing gateway")
    args = parser.parse_args(argv)
    try:
        if args.case_limit is not None and args.case_limit < 1:
            raise RunnerRefusal("INVALID_CASE_LIMIT", "case limit must be positive")
        selected = replace(spec, max_tokens=args.max_output_tokens
            if args.max_output_tokens is not None else spec.max_tokens,
            cases=spec.cases[:args.case_limit] if args.case_limit is not None else spec.cases,
            notes={**spec.notes, "original_case_count": len(spec.cases),
                "original_max_output_tokens": spec.max_tokens})
        summary = run_matrix(selected, args.output_dir, model_ids=args.models,
            max_estimated_cost_microusd=args.max_estimated_cost_microusd,
            max_calls=args.max_provider_calls, env_file=args.env_file)
    except RunnerRefusal as refusal:
        print(f"REFUSED {refusal.code}: {refusal.message}")
        return 2
    print(_dump(summary))
    return 2 if summary.get("stop_reason") else 0
