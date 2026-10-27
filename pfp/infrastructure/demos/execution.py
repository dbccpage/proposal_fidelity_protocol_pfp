"""Compose package scenarios with isolated custody and the traced gateway."""

from __future__ import annotations

import os
import base64
import tempfile
import urllib.error
from pathlib import Path
from uuid import uuid4

from pfp.domain.demos import DemoRefusal
from pfp.infrastructure.adapters.mssn_research import loader
from pfp.use_cases.mssn_demo import evaluate_cases

from .canonical import canonical, digest, load
from .catalog import implementation_digest, lookup, scenario_fixture_bytes
from .named import run_named

SCHEMA = "core.symbol-game.demo-receipt.v1"
FIXTURE_KEY = b"mssn-demo-public-fixture-custody-key-v1"


def fresh_output(path: Path) -> Path:
    output = path.expanduser().resolve()
    if "research" in {part.casefold() for part in output.parts}:
        raise DemoRefusal("RESEARCH_EVIDENCE_WRITE_REFUSED")
    if output.exists():
        raise DemoRefusal("OUTPUT_DIRECTORY_OCCUPIED", str(output))
    output.mkdir(parents=True, exist_ok=False)
    return output


def artifact_store(output: Path, live: bool):
    from operating_system.adapters.security.key_protectors import (
        FixtureOnlyAeadProtector,
        WindowsDpapiKeyProtector,
    )
    from operating_system.infrastructure.encrypted_artifact_cas import (
        EncryptedArtifactCas,
    )

    protector = WindowsDpapiKeyProtector() if live else FixtureOnlyAeadProtector(FIXTURE_KEY)
    return EncryptedArtifactCas(output / "encrypted-artifacts", protector)


class Proposals:
    def __init__(self, gateway, *, live=False, model=None, max_output_tokens=None,
            max_provider_calls=None, run_id=None, trace=None, secrets=()):
        self.gateway = gateway
        self.transcript = []
        self.live, self.model = live, model
        self.max_output_tokens, self.max_provider_calls = max_output_tokens, max_provider_calls
        self.run_id, self.trace = run_id or uuid4().hex, trace
        self._secrets = tuple(secrets)
        self.last_turn = None
        self.turns = []
        self.stopped_reason = None

    def propose(self, prompt, scripted_reply):
        from adversary.domain.providers.types import CandidateRequest

        if self.live:
            from pfp.infrastructure.pilot_matrix import complete_pilot_turn
            from adversary.domain.providers.types import DecodingParamsV1, Provider
            if self.stopped_reason:
                raise DemoRefusal(self.stopped_reason)
            if len(self.turns) >= self.max_provider_calls:
                self.stopped_reason = "CALL_ALLOWANCE_EXHAUSTED"
                if self.trace is not None:
                    from pfp.infrastructure.trace.provider_dispatch import record_preflight_refusal
                    record_preflight_refusal(self.trace, provider=Provider.OPENROUTER, model=self.model,
                        exc=DemoRefusal(self.stopped_reason))
                raise DemoRefusal(self.stopped_reason)
            attempt_id = f"demo:{self.run_id}:{len(self.turns)}"
            turn = complete_pilot_turn(self.gateway, CandidateRequest(
                system="MSS-N bounded candidate proposal. AuthorityEffect: None.", user=prompt,
                decoding=DecodingParamsV1()), model=self.model,
                task_id=f"demo:{self.run_id}", attempt_id=attempt_id, max_tokens=self.max_output_tokens)
            claim = None
            try:
                claim = self.gateway.action(attempt_id)
            except KeyError:
                pass
            turn["attempted"] = bool(turn["provider_wire"] or
                claim is not None and claim["state"] != "refused_before_dispatch")
            self.last_turn = turn
            self.turns.append(turn)
            checked = turn["pfp"]
            response = turn["content"] or ""
            if not response and checked and checked.get("raw_reply_base64"):
                response = base64.b64decode(checked["raw_reply_base64"]).decode("utf-8", errors="replace")
            error = turn["error"]
            if isinstance(error, str):
                error = _scrub(error, *self._secrets)
            self.transcript.append({"prompt": _scrub(prompt, *self._secrets), "response": _scrub(response, *self._secrets),
                "provider": "openrouter", "model": self.model, "error": error,
                "attempt_state": turn["attempt_state"], "usage": turn["usage"],
                "pfp": {key: checked[key] for key in ("schema_valid", "failure_class", "evidence_grade")}
                    if checked else None,
                "provider_wire_sha256": turn["provider_wire"]["raw_reply_sha256"] if turn["provider_wire"] else None})
            if not turn["ok"] or turn["stop"]:
                self.stopped_reason = error or "PFP_TURN_REFUSED"
                if not turn["attempted"] and self.trace is not None:
                    from pfp.infrastructure.trace.provider_dispatch import record_preflight_refusal
                    record_preflight_refusal(self.trace, provider=Provider.OPENROUTER, model=self.model,
                        exc=DemoRefusal(self.stopped_reason))
                raise DemoRefusal(self.stopped_reason)
            return turn["content"]
        response, budget = self.gateway.complete(
            CandidateRequest(
                system="MSS-N bounded candidate proposal. AuthorityEffect: None.", user=prompt
            )
        )
        self.transcript.append(
            {
                "prompt": _scrub(prompt, *self._secrets),
                "response": response.content,
                "provider": response.provider,
                "model": response.model,
            }
        )
        return response.content


def _scrub(text: str, *secrets: str) -> str:
    redacted = text
    for secret in (os.environ.get("OPENROUTER_API_KEY") or "", *secrets):
        if secret and secret in redacted:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def _file_sourced_secrets(env_file: Path | str | None) -> tuple[str, ...]:
    """Resolve a file key for this call only. Nothing is written to ``os.environ``."""
    from operations.domain.rop.result import Ok
    from adversary.infrastructure.providers.openrouter_transport import resolve_openrouter_key

    found = resolve_openrouter_key(env_file)
    if isinstance(found, Ok) and found.value:
        return (found.value,)
    return ()


def _annotate_live_result(
    result: dict, *, scenario_id: str, model: str | None, transcript: list,
    secrets: tuple[str, ...] = (),
) -> dict:
    """Record the live provider outcome inside result. The receipt key set stays closed."""
    responses = []
    for item in transcript:
        if isinstance(item, dict):
            responses.append(_scrub(str(item.get("response") or ""), *secrets))
    body = "\n".join(responses)
    annotated = dict(result)
    annotated["scenario_id"] = scenario_id
    annotated["provider"] = "openrouter"
    annotated["model"] = model or ""
    annotated["provider_response"] = body
    for key in ("code", "detail"):
        value = annotated.get(key)
        if isinstance(value, str):
            annotated[key] = _scrub(value, *secrets)
    if annotated.get("status") == "CHECKED" and not body:
        annotated["status"] = "TYPED_REFUSAL"
        annotated["code"] = "EMPTY_PROVIDER_RESPONSE"
        annotated["detail"] = "live transport returned no provider bytes"
    return annotated


def _live_bounds_ok(
    model, max_output_tokens, max_provider_calls, max_estimated_cost_microusd, max_cost_microusd,
) -> bool:
    """One explicit model, output cap, call cap and exactly one financial policy."""
    estimated = max_estimated_cost_microusd is not None
    hard = max_cost_microusd is not None
    cap = max_estimated_cost_microusd if estimated else max_cost_microusd
    call_ceiling = 64 if estimated else 32
    return (
        type(model) is str and bool(model.strip())
        and type(max_output_tokens) is int and 0 < max_output_tokens <= 3000
        and type(max_provider_calls) is int and 0 < max_provider_calls <= call_ceiling
        and estimated != hard
        and type(cap) is int and 0 < cap <= 50000
    )


def run(
    scenario_id: str, output_dir: Path, *, live: bool = False, model: str | None = None,
    max_output_tokens: int | None = None, max_provider_calls: int | None = None,
    max_estimated_cost_microusd: int | None = None, max_cost_microusd: int | None = None,
    env_file: Path | str | None = None,
) -> dict:
    from adversary.domain.providers.types import ProviderError

    row = lookup(scenario_id)
    fixture_bytes = scenario_fixture_bytes(row)
    fixture = load(fixture_bytes)
    if live and fixture.get("kind") not in {
        "immune",
        "protocol",
        "meron-2d",
        "meron-3d",
        "meron-4d",
        "meron-4d-su2",
    }:
        raise DemoRefusal("LIVE_SCENARIO_NOT_SUPPORTED", scenario_id)
    if live and not _live_bounds_ok(
        model, max_output_tokens, max_provider_calls, max_estimated_cost_microusd, max_cost_microusd,
    ):
        raise DemoRefusal(
            "LIVE_BOUNDS_REQUIRED",
            "explicit model, output tokens, provider calls and one hard/estimated cost policy required",
        )
    secrets = _file_sourced_secrets(env_file) if live else ()
    output = fresh_output(Path(output_dir))
    (output / "fixture.json").write_bytes(fixture_bytes)
    from eis.infrastructure.mssn_ports import (
        RunQuarantineSink,
    )
    from pfp.infrastructure.trace.execution_trace import (
        DURABILITY_BUFFERED_REPLAY,
        DURABILITY_FSYNC_LIVE,
        ExecutionTrace,
        RunMode,
    )
    from pfp.infrastructure.trace.gateway_factories import (
        fixture_gateway,
    )
    from pfp.infrastructure.trace.provider_dispatch import (
        scripted_openai_payload,
    )

    store = artifact_store(output, live)
    if live:
        trace = ExecutionTrace(
            output / "trace.jsonl",
            execution_id=scenario_id,
            durability=DURABILITY_FSYNC_LIVE,
            live_transport=True,
            run_mode=RunMode.LIVE,
        )
        gateway = None
    elif fixture.get("replies"):
        fixture_run = fixture_gateway(
            output / "trace.jsonl",
            [scripted_openai_payload(r) for r in fixture.get("replies", [])],
            artifact_store=store,
            execution_id=scenario_id,
            durability=DURABILITY_BUFFERED_REPLAY,
        )
        trace, gateway = fixture_run.trace, fixture_run.gateway
    else:
        trace = ExecutionTrace(
            output / "trace.jsonl",
            execution_id=scenario_id,
            durability=DURABILITY_BUFFERED_REPLAY,
            live_transport=False,
            run_mode=RunMode.DETERMINISTIC_FIXTURE,
        )
        gateway = None
    run_id = uuid4().hex
    proposals = Proposals(gateway, live=live, model=model, max_output_tokens=max_output_tokens,
        max_provider_calls=max_provider_calls, run_id=run_id, trace=trace, secrets=secrets)
    bindings = None
    try:
        if live:
            from pfp.infrastructure.estimated_gateway import create_accounted_openrouter_gateway
            objective = digest(canonical({"scenario": scenario_id,
                "fixture_sha256": row["fixture_sha256"], "model": model,
                "max_output_tokens": max_output_tokens, "max_provider_calls": max_provider_calls}))
            try:
                proposals.gateway = create_accounted_openrouter_gateway(model, max_output_tokens,
                    env_file=env_file, max_cost_microusd=max_cost_microusd,
                    max_estimated_cost_microusd=max_estimated_cost_microusd, max_calls=max_provider_calls,
                    accounting_path=output / "accounting.sqlite3", run_id=run_id,
                    objective_sha256=objective, trace=trace, artifact_store=store)
            except ProviderError:
                raise
            except ValueError as exc:
                raise DemoRefusal("LIVE_CONFIGURATION_REFUSED", str(exc)) from exc
        level = row["scenario"]["level"]
        if level is not None:
            bindings = loader.entry(level)
            outcomes = evaluate_cases(loader.checker(level), fixture["cases"])
            result = {
                "status": "CHECKED"
                if all(c["matches_expectation"] for c in outcomes)
                else "FAILED",
                "cases": outcomes,
                "grade": "RESEARCH_GRADE_PYTHON",
            }
        else:
            result = run_named(
                scenario_id,
                fixture,
                proposals,
                RunQuarantineSink(output / "quarantine"),
                live=live,
            )
    except DemoRefusal as exc:
        result = {"status": "TYPED_REFUSAL", "code": exc.code, "detail": exc.detail}
    except (ProviderError, urllib.error.URLError, TimeoutError) as exc:
        result = {
            "status": "TYPED_REFUSAL",
            "code": type(exc).__name__,
            "detail": str(exc),
        }
    except BaseException:
        trace.abandon()
        raise
    if live:
        result = _annotate_live_result(
            result, scenario_id=scenario_id, model=model, transcript=proposals.transcript,
            secrets=secrets,
        )
        result["pfp"] = {"evidence_grade": "UNVERIFIED", "checked_turns": sum(
            bool(turn["ok"]) for turn in proposals.turns), "provider_calls": sum(
            bool(turn["attempted"]) for turn in proposals.turns),
            "stop_reason": proposals.stopped_reason,
            "total_reported_cost_usd": None if any(turn["attempted"] and turn["usage"].get("cost") is None
                for turn in proposals.turns) else sum(turn["usage"].get("cost") or 0 for turn in proposals.turns),
            "financial_policy": "estimated_not_vendor_liability_cap" if max_estimated_cost_microusd is not None else "hard_maximum_liability",
            "max_provider_calls": max_provider_calls, "max_output_tokens": max_output_tokens}
    terminal_digest = trace.seal(result["status"])
    (output / "transcript.json").write_bytes(canonical(proposals.transcript))
    artifacts = {
        p.relative_to(output).as_posix(): digest(p.read_bytes())
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    receipt = {
        "schema": SCHEMA,
        "AuthorityEffect": "None",
        "scenario": row["scenario"],
        "implementation_sha256": implementation_digest(),
        "checker": bindings,
        "checker_registry_sha256": loader.REGISTRY_SHA256,
        "fixture_sha256": row["fixture_sha256"],
        "transport": "live" if live else "fixture",
        "trace_sha256": digest((output / "trace.jsonl").read_bytes()),
        "trace_terminal_digest": terminal_digest,
        "transcript_sha256": digest((output / "transcript.json").read_bytes()),
        "artifacts_sha256": artifacts,
        "result": result,
        "verification_scope": "integrity_only" if live else "fixture_replay",
        "scope": row["scenario"]["scope"],
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    (output / "receipt.json").write_bytes(canonical(receipt))
    return receipt


def _inside(root: Path, relative: str) -> Path:
    if type(relative) is not str or "\\" in relative or ":" in relative:
        raise DemoRefusal("ARTIFACT_PATH_ESCAPE")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root) or candidate == root:
        raise DemoRefusal("ARTIFACT_PATH_ESCAPE")
    return candidate


def verify(path: Path) -> dict:
    path = Path(path).resolve(strict=True)
    receipt = load(path.read_bytes())
    keys = {
        "schema",
        "AuthorityEffect",
        "scenario",
        "implementation_sha256",
        "checker",
        "checker_registry_sha256",
        "fixture_sha256",
        "transport",
        "trace_sha256",
        "trace_terminal_digest",
        "transcript_sha256",
        "artifacts_sha256",
        "result",
        "verification_scope",
        "scope",
        "receipt_sha256",
    }
    if (
        type(receipt) is not dict
        or set(receipt) != keys
        or receipt["schema"] != SCHEMA
        or receipt["AuthorityEffect"] != "None"
    ):
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA")
    if path.read_bytes() != canonical(receipt):
        raise DemoRefusal("NONCANONICAL_RECEIPT")
    payload = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if digest(canonical(payload)) != receipt["receipt_sha256"]:
        raise DemoRefusal("RECEIPT_DIGEST_MISMATCH")
    row = lookup(receipt["scenario"]["scenario_id"])
    if (
        receipt["scenario"] != row["scenario"]
        or receipt["fixture_sha256"] != row["fixture_sha256"]
        or receipt["scope"] != row["scenario"]["scope"]
    ):
        raise DemoRefusal("SCENARIO_VERSION_MISMATCH")
    if (
        receipt["implementation_sha256"] != implementation_digest()
        or receipt["checker_registry_sha256"] != loader.REGISTRY_SHA256
    ):
        raise DemoRefusal("IMPLEMENTATION_VERSION_MISMATCH")
    expected_checker = (
        loader.entry(row["scenario"]["level"]) if row["scenario"]["level"] is not None else None
    )
    if receipt["checker"] != expected_checker:
        raise DemoRefusal("CHECKER_BINDING_MISMATCH")
    root = path.parent
    observed = {
        p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != path
    }
    if observed != set(receipt["artifacts_sha256"]):
        raise DemoRefusal("ARTIFACT_SET_MISMATCH")
    for relative, expected in receipt["artifacts_sha256"].items():
        if digest(_inside(root, relative).read_bytes()) != expected:
            raise DemoRefusal("ARTIFACT_DIGEST_MISMATCH", relative)
    if digest((root / "fixture.json").read_bytes()) != receipt["fixture_sha256"]:
        raise DemoRefusal("FIXTURE_DIGEST_MISMATCH")
    if (
        digest((root / "trace.jsonl").read_bytes()) != receipt["trace_sha256"]
        or digest((root / "transcript.json").read_bytes()) != receipt["transcript_sha256"]
    ):
        raise DemoRefusal("TRACE_BINDING_MISMATCH")
    live = receipt["transport"] == "live"
    if receipt["transport"] not in ("fixture", "live") or receipt["verification_scope"] != (
        "integrity_only" if live else "fixture_replay"
    ):
        raise DemoRefusal("TRANSPORT_SCOPE_MISMATCH")
    from pfp.infrastructure.trace.execution_trace import verify_trace
    from pfp.infrastructure.trace.provider_dispatch import (
        DISPATCH_COMPLETE,
        derive_dispatch_outcomes,
    )

    scan = verify_trace(
        root / "trace.jsonl", expected_terminal_digest=receipt["trace_terminal_digest"]
    )
    if scan.records[-1].payload["terminal"] != receipt["result"]["status"]:
        raise DemoRefusal("TRACE_RESULT_MISMATCH")
    first = scan.records[0].payload
    if first["live_transport"] != live:
        raise DemoRefusal("TRACE_TRANSPORT_MISMATCH")
    outcomes = tuple(derive_dispatch_outcomes(scan.records, artifact_store=artifact_store(root, live)))
    if live and receipt["result"]["status"] == "CHECKED" and not outcomes:
        raise DemoRefusal("PROVIDER_EVIDENCE_MISSING")
    for outcome in outcomes:
        if outcome.status != DISPATCH_COMPLETE:
            raise DemoRefusal("PROVIDER_EVIDENCE_INCOMPLETE", outcome.status)
    if live:
        return {
            "status": "INTEGRITY_ONLY",
            "reproduced": False,
            "AuthorityEffect": "None",
            "scenario_id": row["scenario"]["scenario_id"],
        }
    with tempfile.TemporaryDirectory(prefix="mssn-replay-") as directory:
        rerun = run(row["scenario"]["scenario_id"], Path(directory) / "run")
    if (
        rerun["result"] != receipt["result"]
        or rerun["transcript_sha256"] != receipt["transcript_sha256"]
    ):
        raise DemoRefusal("FIXTURE_REPLAY_MISMATCH")
    if receipt["result"]["status"] == "FAILED":
        raise DemoRefusal("FIXTURE_EXPECTATION_FAILED")
    return {
        "status": "VERIFIED_FIXTURE",
        "reproduced": True,
        "AuthorityEffect": "None",
        "scenario_id": row["scenario"]["scenario_id"],
        "outcome": receipt["result"]["status"],
    }
