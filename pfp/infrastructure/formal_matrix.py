"""Shared support for the e_formal_math model-matrix runners (C041 to C050).

The runners are exploratory scripts, not challenge-protocol (SG-CP v1) evaluations. This
module holds what they must all do the same way:

- Live proposals require the shared PFP adapter and an explicitly accounted gateway.
  Injected gateways own credentials; standalone runs require explicit bounded policy.
- Prompts never carry the judge's case ID or answer-bearing fields. Each case is sent under
  an opaque per-run token; the reply is mapped back to the real case ID afterwards.
- Provider and transport failures are recorded as ``INFRA_ERROR``, never as wrong answers.
- The raw response body and the full reply text are kept, not an excerpt.
- Run records go to a new folder under the intelligence root resolved by
  ``omega_engine_operating_system.adapters.intelligence_custody.intelligence_root``; historical result files are never
  overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import time
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Compatibility label only: this module never sends directly to this endpoint.
API_KEY_ENV = "OPENROUTER_API_KEY"
PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
INFRA_ERROR = "INFRA_ERROR"
PARSE_FAILURE = "PARSE_FAILURE"

# Keys that name or grade the answer and are never shown to a model.
ALWAYS_WITHHELD = frozenset({"case_id", "id", "category", "expected", "answer", "label", "verdict"})

SPACE_BUNNY_NOTE = (
    "stealth/space-bunny-alpha is a free stealth model on OpenRouter (as of 2026-09-28); the "
    "provider does not disclose its identity, size or training. Results with it are exploratory, "
    "outside the challenge protocol SG-CP v1 section 2, and may not be reproducible after the "
    "stealth period."
)


class RunnerConfigError(RuntimeError):
    """Typed refusal: the runner is not configured to call a provider."""

    code = PROVIDER_NOT_CONFIGURED


def require_api_key(environ: Mapping[str, str] | None = None) -> str:
    """The provider key from the process environment only; raises RunnerConfigError if absent."""
    env = os.environ if environ is None else environ
    key = env.get(API_KEY_ENV, "").strip()
    if not key:
        raise RunnerConfigError(
            f"{PROVIDER_NOT_CONFIGURED}: set {API_KEY_ENV} in the environment of this process; "
            "no .env file is read"
        )
    return key


def new_run_nonce() -> str:
    return secrets.token_hex(8)


def opaque_token(run_nonce: str, index: int) -> str:
    """A per-run token that reveals nothing about the case."""
    return "q" + hashlib.sha256(f"{run_nonce}:{index}".encode("utf-8")).hexdigest()[:12]


def participant_view(
    case: Mapping[str, Any], token: str, withheld: Iterable[str] = ()
) -> dict[str, Any]:
    """The case as a model may see it: the token instead of the ID, answer-bearing keys removed."""
    hidden = set(ALWAYS_WITHHELD) | set(withheld)
    view: dict[str, Any] = {"case_id": token}
    for key, value in case.items():
        if key in hidden or key.startswith("expected"):
            continue
        view[key] = value
    return view


def build_user_prompt(case: Mapping[str, Any], token: str, withheld: Iterable[str] = ()) -> str:
    view = participant_view(case, token, withheld)
    return f"Case ID: {token}\nTask JSON:\n{json.dumps(view, indent=2, ensure_ascii=False)}"


def map_back(answer: Any, token: str, case_id: str) -> Any:
    """Restores the real case ID on a reply that echoed the token (or omitted the ID)."""
    if not isinstance(answer, dict):
        return answer
    if answer.get("case_id") in (token, None):
        restored = dict(answer)
        restored["case_id"] = case_id
        return restored
    return answer


def call_openrouter(
    api_key: str,
    model_id: str,
    messages: list[dict[str, str]],
    *,
    max_tokens: int | None = None,
    temperature: float = 0.0,
    extra: Mapping[str, Any] | None = None,
    title: str = "Symbol Game matrix runner",
    timeout: float = 60.0,
    gateway: Any = None,
    task_id: str | None = None,
    attempt_id: str | None = None,
) -> dict[str, Any]:
    """Compatibility facade; only the accounted PFP adapter may dispatch.

    ``api_key``, ``title`` and ``timeout`` remain positional/keyword compatibility
    inputs. The supplied gateway owns credentials, transport and output budget.
    Unsupported controls refuse rather than overwrite a bound prompt or model.
    """
    def refused(error: str) -> dict[str, Any]:
        return dict(ok=False, outcome=INFRA_ERROR, error=error, stop=True,
                    content=None, reasoning=None, usage={}, elapsed=0.0,
                    raw_body=None, pfp=None, provider_wire=None, attempt_state=None,
                    request=None)

    if gateway is None:
        return refused("PFP_ACCOUNTED_GATEWAY_REQUIRED")
    if any(type(value) is not str or not value.strip() for value in (task_id, attempt_id)):
        return refused("PFP_TASK_BINDING_REQUIRED")
    from omega_engine_pfp.infrastructure.pilot_matrix import (
        complete_pilot_turn,
        validate_pilot_gateways,
    )
    from omega_engine_woland.domain.providers.types import (
        CandidateRequest,
        ChatMessage,
        DecodingParamsV1,
    )

    try:
        controls = dict(extra or {})
        if set(controls) - {"seed", "top_p", "logit_bias", "grammar", "thinking", "provider"}:
            return refused("UNSUPPORTED_MATRIX_DECODING_CONTROLS")
        provider = controls.pop("provider", {})
        if (not isinstance(provider, Mapping)
                or set(provider) - {"allow_fallbacks", "require_parameters"}
                or provider.get("allow_fallbacks", False) is not False
                or provider.get("require_parameters", True) is not True):
            return refused("UNSUPPORTED_MATRIX_PROVIDER_CONTROLS")
        if (type(messages) is not list or not messages
                or any(not isinstance(message, Mapping) or set(message) != {"role", "content"}
                       for message in messages)):
            return refused("UNSUPPORTED_MATRIX_MESSAGES")
        request = CandidateRequest(messages=tuple(ChatMessage(**message) for message in messages),
            decoding=DecodingParamsV1(temperature=temperature, allow_fallbacks=False,
                                      require_parameters=True, **controls))
        validate_pilot_gateways({model_id: gateway}, [model_id], max_tokens=max_tokens)
    except (TypeError, ValueError) as exc:
        return refused(str(exc))
    result = complete_pilot_turn(gateway, request, model=model_id, task_id=task_id,
                                attempt_id=attempt_id, max_tokens=max_tokens)
    if not result["ok"]:
        result["outcome"] = INFRA_ERROR
    return result


def extract_json_object(text: str) -> dict[str, Any] | None:
    """The first top-level JSON object in the reply, or None. Never invents an answer."""
    if not isinstance(text, str):
        return None
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    start = s.find("{")
    end = s.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(s[start : end + 1])
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def run_folder(challenge_id: str, run_nonce: str) -> Path:
    """A new folder under <intelligence root>/_ic/darpa/symbol_game/matrix_runs/."""
    from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
        resolve_intelligence_repo_root,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = (
        resolve_intelligence_repo_root()
        / "_ic/darpa/symbol_game"
        / "matrix_runs"
        / challenge_id
        / f"{stamp}_{run_nonce}"
    )
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def write_json(path: Path, obj: Any) -> None:
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def model_label(model_id: str) -> str | None:
    """The exploratory-status note for models outside the protocol, else None."""
    return SPACE_BUNNY_NOTE if "space-bunny" in model_id else None


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Counts by outcome; infrastructure errors are excluded from the answered denominator."""
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec["outcome"]] = counts.get(rec["outcome"], 0) + 1
    answered = len(records) - counts.get(INFRA_ERROR, 0)
    verified = counts.get("VERIFIED", 0)
    return {
        "cases": len(records),
        "answered": answered,
        "verified": verified,
        "verified_rate_of_answered": (verified / answered) if answered else None,
        "outcomes": counts,
    }


def classify(verified: bool, answer: Mapping[str, Any]) -> str:
    """VERIFIED only when the checkers pass; an UNKNOWN is an abstention, never a pass."""
    if verified:
        return "VERIFIED"
    if answer.get("status") == "UNKNOWN":
        return "ABSTAINED"
    return "REJECTED"


def run_model_matrix(
    *,
    challenge_id: str,
    models: list[Mapping[str, Any]],
    cases: list[Mapping[str, Any]],
    system_prompt: str,
    evaluate: Any,
    prompt_builder: Any = None,
    withheld: Iterable[str] = (),
    title: str = "Symbol Game matrix runner",
    max_tokens: int | None = None,
    pause_sec: float = 1.0,
    gateways: Mapping[str, Any] | None = None,
    max_estimated_cost_microusd: int | None = None,
    max_provider_calls: int | None = None,
    env_file: Path | str | None = None,
    configuration_metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Runs every model on every case and writes one run record; returns the run folder.

    ``evaluate(case, answer)`` returns ``(ok, message)``. ``prompt_builder(case, token)``
    returns the user prompt (default: ``build_user_prompt`` with ``withheld``).
    """
    from omega_engine_pfp.infrastructure.pilot_matrix import (
        make_pilot_gateways,
        validate_pilot_gateways,
    )

    nonce = new_run_nonce()
    folder = run_folder(challenge_id, nonce)
    model_ids = [model["id"] for model in models]
    objective_sha256 = hashlib.sha256(json.dumps(dict(challenge=challenge_id, models=models,
        cases=cases, system_prompt=system_prompt, configuration=configuration_metadata),
        sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    if gateways is None:
        if (max_estimated_cost_microusd is None or max_provider_calls is None
                or type(max_tokens) is not int):
            raise RunnerConfigError("PFP_ACCOUNTED_GATEWAY_REQUIRED: supply gateways or explicit bounded policy")
        if any(model.get("max_tokens", max_tokens) != max_tokens for model in models):
            raise RunnerConfigError("MATRIX_OUTPUT_BUDGET_MISMATCH: standalone models require the explicit output cap")
        gateways = make_pilot_gateways(model_ids, max_output_tokens=max_tokens,
            max_estimated_cost_microusd=max_estimated_cost_microusd,
            max_calls=max_provider_calls, accounting_path=folder / "budget.sqlite3", env_file=env_file,
            run_id=f"formal-matrix:{challenge_id}:{nonce}", objective_sha256=objective_sha256)
    validate_pilot_gateways(gateways, model_ids, max_tokens=max_tokens)
    for model in models:
        validate_pilot_gateways({model["id"]: gateways[model["id"]]}, [model["id"]],
                               max_tokens=model.get("max_tokens", max_tokens))
    withheld = tuple(withheld)
    build = prompt_builder or (lambda case, token: build_user_prompt(case, token, withheld))
    record: dict[str, Any] = {
        "challenge": challenge_id,
        "run_nonce": nonce,
        "objective_sha256": objective_sha256,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "status": "exploratory model matrix; not an SG-CP v1 evaluation",
        "system_prompt": system_prompt,
        "withheld_case_fields": sorted(set(ALWAYS_WITHHELD) | set(withheld)),
        "models": {},
    }
    if configuration_metadata is not None:
        record["configuration"] = dict(configuration_metadata)
    stopped = False
    for model in models:
        model_id = model["id"]
        records: list[dict[str, Any]] = []
        for idx, case in enumerate(cases):
            token = opaque_token(nonce, idx)
            prompt = build(case, token)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            res = call_openrouter(
                "",
                model_id,
                messages,
                max_tokens=model.get("max_tokens", max_tokens),
                temperature=model.get("temperature", 0.0),
                extra=model.get("extra_params"),
                title=title,
                gateway=gateways[model_id], task_id=f"formal-matrix:{nonce}:{token}",
                attempt_id=f"{hashlib.sha256(model_id.encode()).hexdigest()[:16]}:{idx}",
            )
            rec: dict[str, Any] = {
                "case_id": case["case_id"],
                "token": token,
                "prompt": prompt,
                "raw_body": res["raw_body"],
                "elapsed": res["elapsed"],
                "usage": res["usage"],
                "pfp": res.get("pfp"), "provider_wire": res.get("provider_wire"),
                "attempt_state": res.get("attempt_state"), "request": res.get("request"),
                "stop": res.get("stop", False),
            }
            if not res["ok"]:
                rec.update(outcome=INFRA_ERROR, error=res["error"])
                records.append(rec)
                if res.get("stop"):
                    stopped = True
                    record["stop_reason"] = res["error"]
                    break
                continue
            rec.update(content=res["content"], reasoning=res["reasoning"])
            answer = extract_json_object(res["content"])
            if answer is None:
                rec["outcome"] = PARSE_FAILURE
                records.append(rec)
                continue
            answer = map_back(answer, token, case["case_id"])
            ok, message = evaluate(case, answer)
            rec.update(
                answer=answer,
                verified=bool(ok),
                message=message,
                outcome=classify(bool(ok), answer),
            )
            records.append(rec)
            print(
                f"[{rec['outcome']}] {model_id} {case['case_id']}: {str(message)[:80]}", flush=True
            )
            time.sleep(pause_sec)
        record["models"][model_id] = {
            "name": model.get("name", model_id),
            "label": model_label(model_id),
            "summary": summarize(records),
            "records": records,
        }
        write_json(folder / "run_record.json", record)
        if stopped:
            break
    return folder


def run_model_matrix_cli(*, argv: Sequence[str] | None = None, **matrix_options: Any) -> Path:
    """Select an explicitly bounded exploratory run without changing its catalog."""
    parser = argparse.ArgumentParser(description="Exploratory formal-math model matrix")
    parser.add_argument("--model", action="append", dest="models", required=True)
    parser.add_argument("--max-estimated-cost-microusd", type=int, required=True)
    parser.add_argument("--max-provider-calls", type=int, required=True)
    parser.add_argument("--max-output-tokens", type=int, required=True)
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    if not 0 < args.max_estimated_cost_microusd <= 50000:
        parser.error("estimated cost allowance must be from 1 to 50000 microusd")
    if not 0 < args.max_provider_calls <= 64:
        parser.error("provider call allowance must be from 1 to 64")
    if not 0 < args.max_output_tokens <= 3000:
        parser.error("estimated mode requires from 1 to 3000 output tokens")
    if args.case_limit is not None and args.case_limit < 1:
        parser.error("case limit must be positive")
    declared = {model["id"]: model for model in matrix_options.get("models", [])}
    if set(args.models) - declared.keys():
        parser.error("every selected model must be declared by this runner")
    if len(set(args.models)) != len(args.models):
        parser.error("select each model only once")
    selected = [deepcopy(dict(declared[model])) for model in args.models]
    for model in selected:
        model["max_tokens"] = args.max_output_tokens
    cases = matrix_options["cases"]
    if not cases:
        parser.error("at least one case is required for an exploratory run")
    gateways = matrix_options.get("gateways")
    if gateways is not None:
        from omega_engine_pfp.infrastructure.pilot_matrix import _scope, validate_pilot_gateways

        try:
            validate_pilot_gateways(gateways, args.models, max_tokens=args.max_output_tokens)
            scope = _scope(gateways[args.models[0]], args.models[0], args.max_output_tokens)
            if scope[2] > args.max_estimated_cost_microusd or scope[3] > args.max_provider_calls:
                parser.error("injected gateway allowance exceeds the explicit CLI limits")
        except ValueError as exc:
            parser.error(str(exc))
    options = dict(matrix_options)
    options.update(
        models=selected,
        cases=deepcopy(cases[: args.case_limit]),
        max_tokens=args.max_output_tokens,
        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
        max_provider_calls=args.max_provider_calls,
        env_file=args.env_file,
        configuration_metadata={
            "original_case_count": len(cases),
            "selected_case_count": len(cases[: args.case_limit]),
            "original_max_tokens": matrix_options.get("max_tokens"),
            "original_model_max_tokens": {
                name: model.get("max_tokens", matrix_options.get("max_tokens"))
                for name, model in declared.items()
            },
            "selected_models": args.models,
            "max_output_tokens": args.max_output_tokens,
            "max_estimated_cost_microusd": args.max_estimated_cost_microusd,
            "max_provider_calls": args.max_provider_calls,
        },
    )
    return run_model_matrix(**options)


class ArmAntibodyStore:
    """Antibodies minted in one run for one arm (model x method).

    Earlier harnesses loaded every antibody ever written for a case, so rejections from other
    runs, models and methods leaked into later prompts. This store only returns antibodies
    minted by the same run and arm, and each round records the IDs it injected.
    """

    def __init__(self, arm: str, folder: Path | None = None) -> None:
        self.arm = arm
        self.folder = folder
        self._by_case: dict[str, list[dict[str, Any]]] = {}

    def mint(self, case_id: str, failed: Any, diagnostic: str) -> dict[str, Any]:
        items = self._by_case.setdefault(case_id, [])
        antibody = {
            "antibody_id": f"ab_{self.arm}_{case_id}_{len(items) + 1}",
            "arm": self.arm,
            "case_id": case_id,
            "failed": failed if isinstance(failed, str) else json.dumps(failed, ensure_ascii=False),
            "diagnostic": diagnostic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        items.append(antibody)
        if self.folder is not None:
            target = self.folder / "antibodies" / self.arm
            target.mkdir(parents=True, exist_ok=True)
            write_json(target / f"{antibody['antibody_id']}.json", antibody)
        return antibody

    def active(self, case_id: str) -> list[dict[str, Any]]:
        return list(self._by_case.get(case_id, []))
