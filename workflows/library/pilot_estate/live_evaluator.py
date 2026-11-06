"""Strict pilot evaluation with immutable observations. AuthorityEffect: None.

Historical response.yaml files are never a live cache or an overwrite target.
P0 evaluations are ineligible for efficacy claims. Fresh model dispatch moved
to bounded ``pfp run-seed`` execution; this module retains offline regrading.
"""
from __future__ import annotations
from omega_engine_pfp.infrastructure.model_loading import load_yaml_model

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = next((p for p in _HERE.parents if (p / ".git").exists()), _HERE.parents[1])
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from omega_engine_pfp.domain.types import EvaluationStatus
from omega_engine_pfp.domain.types import PilotSpec
from omega_engine_pfp.domain.types import PStarPrompt
from omega_engine_pfp.domain.types import SeedPrompt
from omega_engine_pfp.domain.pilots.checker_registry import (  # noqa: E402
    MAX_REPLY_BYTES,
    checker_definition,
    evaluate_candidate,
    strict_json,
)
from omega_engine_pfp.infrastructure.pilot_evidence import (  # noqa: E402
    canonical_bytes,
    digest,
    input_binding,
    record_evaluation,
)

DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning:free"


class LegacyLiveMigrationRefusal(ValueError):
    """The legacy directory evaluator has no bounded dispatch contract."""

    code = "LEGACY_LIVE_REQUIRES_CANONICAL_PFP"
    migration_command = (
        "pfp run-seed <SEED_ID> --model <MODEL> --output <NEW_DIRECTORY> "
        "--max-provider-calls <1-8> --max-output-tokens <1-3000> "
        "--max-estimated-cost-microusd <1-50000>"
    )

    def __init__(self):
        super().__init__(
            f"{self.code}: fresh pilot-directory dispatch is retired; "
            f"use {self.migration_command}. Existing observations can still be regraded offline."
        )


def sanitize_raw_reply(raw: str | None) -> tuple[bool, bool, int, Any]:
    if not isinstance(raw, str):
        return False, False, 0, None
    if not raw or len(raw) > MAX_REPLY_BYTES:
        return False, False, len(raw or ""), None
    cleaned = raw.strip()
    fenced = cleaned.startswith("```")
    if fenced:
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        parsed = strict_json(cleaned)
    except (ValueError, RecursionError):
        return fenced, False, len(raw), None
    if not isinstance(parsed, (dict, list)):
        return fenced, False, len(raw), None
    return fenced, True, len(raw) - len(cleaned), parsed


def extract_and_evaluate(
    checker_id: str, expected_answer: Any, raw_reply: str, parsed_json: Any,
) -> tuple[Any, EvaluationStatus]:
    _, valid, _, payload = sanitize_raw_reply(raw_reply)
    if not valid or parsed_json is None:
        return None, EvaluationStatus.MALFORMED
    result = evaluate_candidate(checker_id, expected_answer, payload)
    return result.extracted_answer, result.status


def build_live_request(model: str, system_prompt: str, user_prompt: str, checker_id: str) -> dict:
    schema = checker_definition(checker_id).response_schema
    for text in (system_prompt, user_prompt):
        if re.search(r'"(?:expected_answer|expected_outcome|output)"\s*:', text):
            raise ValueError("ANSWER_BEARING_PUBLIC_PROMPT")
    hint = "Return JSON matching this response schema: " + json.dumps(schema, sort_keys=True)
    return {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": f"{user_prompt}\n\n{hint}"}],
        "temperature": 0.0,
    }


def dispatch_live_prompt(
    api_key: str, model: str, system_prompt: str, user_prompt: str,
    checker_id: str, timeout_sec: int = 60,
) -> dict[str, Any]:
    """Preserve the public signature, refusing the retired unbudgeted transport."""
    build_live_request(model, system_prompt, user_prompt, checker_id)
    raise LegacyLiveMigrationRefusal()


def _load_observation(path: Path, binding: dict[str, str]) -> dict:
    observation = strict_json(path.read_text(encoding="utf-8"))
    if (not isinstance(observation, dict)
            or observation.get("schema") != "pfp.pilot-observation.v2"
            or not isinstance(observation.get("input_binding"), dict)
            or not isinstance(observation.get("request"), dict)
            or not isinstance(observation.get("provider_response"), dict)):
        raise ValueError("OBSERVATION_SCHEMA_MISMATCH")
    if observation["input_binding"].get("request_sha256") != binding["request_sha256"]:
        raise ValueError("OBSERVATION_BINDING_MISMATCH")
    if observation.get("provider_response_sha256") != digest(canonical_bytes(observation["provider_response"])):
        raise ValueError("OBSERVATION_DIGEST_MISMATCH")
    if digest(canonical_bytes(observation["request"])) != binding["request_sha256"]:
        raise ValueError("REQUEST_DIGEST_MISMATCH")
    return observation


def _raw_reply(response: dict) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        return ""
    return message["content"]


def _observe(pilot_dir: Path, model: str, skip_completed: bool) -> tuple[dict, dict, Path]:
    spec = load_yaml_model(PilotSpec, pilot_dir / "spec.yaml")
    p_star_path = pilot_dir / "tests" / "test_11" / "p_star.yaml"
    if not p_star_path.exists():
        p_star_path = pilot_dir / "p_star.yaml"
    prompt = load_yaml_model(PStarPrompt, p_star_path)
    checker_id = str(spec.host_gate.checker_id)
    request = build_live_request(model, prompt.system_prompt, prompt.user_prompt, checker_id)
    binding = input_binding(pilot_dir, request)
    request_id = binding["request_sha256"]
    path = pilot_dir / "observations" / f"{request_id}.json"
    if path.exists():
        if not skip_completed:
            raise ValueError("IMMUTABLE_REQUEST_ALREADY_OBSERVED")
        return _load_observation(path, binding), binding, path
    if (pilot_dir / "response.yaml").exists():
        raise ValueError("UNBOUND_HISTORICAL_OBSERVATION: regrade offline; dispatch needs a new clean experiment")
    # This old route has no reservation or settlement port. Refuse before
    # credentials, attempt markers or transport; retain historical markers intact.
    raise LegacyLiveMigrationRefusal()


def run_live_evaluator(
    results_dir: Path | None = None, model: str = DEFAULT_MODEL,
    pilot_limit: int | None = None, pilot_pattern: str | None = None,
    skip_completed: bool = True,
) -> list[dict[str, Any]]:
    base = results_dir or (_HERE / "results")
    if not base.is_dir():
        raise FileNotFoundError(base)
    directories = sorted(p for p in base.iterdir() if p.is_dir() and p.name.startswith("pilot_"))
    if pilot_pattern:
        directories = [p for p in directories if re.search(pilot_pattern, p.name)]
    reports = []
    for pilot_dir in directories[:pilot_limit]:
        spec = load_yaml_model(PilotSpec, pilot_dir / "spec.yaml")
        seed = load_yaml_model(SeedPrompt, pilot_dir / "seed.yaml")
        observation, binding, path = _observe(pilot_dir, model, skip_completed)
        response = observation["provider_response"]
        raw = _raw_reply(response)
        _, _, _, parsed = sanitize_raw_reply(raw)
        received, status = extract_and_evaluate(str(spec.host_gate.checker_id), seed.expected_outcome.answer, raw, parsed)
        evaluation = record_evaluation(
            pilot_dir, path.read_bytes(), seed.expected_outcome.answer,
            str(spec.host_gate.checker_id), received, status.value,
            observation_mode="live_gateway_dispatch", binding=binding,
        )
        reports.append({"pilot_id": spec.pilot_id, "status": status.value,
                        "received": received, "evaluation": str(evaluation),
                        "cost_usd": (response["usage"].get("cost")
                                     if isinstance(response.get("usage"), dict) else None),
                        "efficacy_eligible": False})
    return reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=_HERE / "results")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pattern")
    parser.add_argument("--force", action="store_true", help="Refuse reuse of an existing immutable observation")
    args = parser.parse_args(argv)
    try:
        reports = run_live_evaluator(args.results_dir, args.model, args.limit, args.pattern, not args.force)
        print(json.dumps(reports, indent=2))
        return 0
    except LegacyLiveMigrationRefusal as error:
        print(json.dumps(dict(status="REFUSED", code=error.code,
                              migration_command=error.migration_command)), file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
