"""Thin Woland CLI for original C006 sessions using canonical PFP/accounting.

No local-model mechanism or matched-arm efficacy is asserted. One exchange file
and the existing Providers ledger retain actual attempts, including failures.
"""

from __future__ import annotations

import argparse
import base64
import json
from decimal import Decimal
from pathlib import Path

from omega_engine_woland.tests.pilots.challenge_suite.catalog import ROOT, canonical, digest
from omega_engine_operations.domain.rop.result import Err
from omega_engine_pfp.ffi import RustSymbolGameHost, find_omega_symbol_game_binary
from omega_engine_pfp.infrastructure import mechanism_sessions as sessions
from omega_engine_pfp.infrastructure.adapters.rust_cohomology_adapter import (
    RustCohomologySolverAdapter,
)
from omega_engine_pfp.infrastructure.estimated_gateway import create_accounted_openrouter_gateway
from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1, Provider
from omega_engine_woland.use_cases.teamwork import POST_RUN_LEARNING_INSTRUCTIONS

PROTOCOL = "omega_engine_pfp/tests/demo_004/a_mechanism/c006_host_scratch_space_vs_cot.md"
PROTOCOL_SHA256 = "e1cf2e0fd816ad060c534f3aad8facc16e7c6d5d8cf5c7bd9bffa2ffd33635fb"
SOURCES = (PROTOCOL, "omega_engine_pfp/infrastructure/mechanism_sessions.py",
    "omega_engine_pfp/infrastructure/mechanism_scratch_space.py",
    "omega_engine_pfp/infrastructure/task_turn.py",
    "omega_engine_pfp/infrastructure/adapters/rust_cohomology_adapter.py",
    "omega_engine_pfp/domain/cohomology/certificate_checker.py",
    "omega_engine_pfp/domain/cohomology/validation.py",
    "omega_engine_pfp/domain/cohomology/solver.py",
    "omega_engine_pfp/domain/solvers/simplicial_cochain.py",
    "omega_engine_pfp/domain/shared_kernel/canonical.py",
    "omega_engine_pfp/domain/pfp_ingress.py",
    "omega_engine_pfp/domain/contracts/pfp_runtime.py",
    "omega_engine_pfp/use_cases/pfp_prompt.py",
    "omega_engine_pfp/use_cases/pfp_proposal.py",
    "omega_engine_pfp/ffi.py",
    "omega_engine_operating_system/adapters/rust_host/ffi.py",
    "omega_engine_pfp/infrastructure/estimated_gateway.py",
    "omega_engine_woland/infrastructure/mechanism_play.py")


def source_bindings():
    sources = {name: digest((ROOT / name).read_bytes()) for name in SOURCES}
    if sources[PROTOCOL] != PROTOCOL_SHA256:
        raise ValueError("C006_PROTOCOL_SOURCE_MISMATCH")
    return sources


def _native(binding):
    path = Path(binding["path"])
    if digest(path.read_bytes()) != binding["sha256"]:
        raise ValueError("C006_NATIVE_SOURCE_DRIFT")
    return RustCohomologySolverAdapter(RustSymbolGameHost(path))


def _native_binding(native_host=None, native_host_sha256=None):
    path = Path(native_host).resolve() if native_host else find_omega_symbol_game_binary().resolve()
    actual = digest(path.read_bytes())
    if native_host_sha256 is not None and actual != native_host_sha256:
        raise ValueError("C006_NATIVE_SOURCE_DRIFT")
    return dict(path=str(path), sha256=actual)


def _validate(state):
    if state.get("schema") != "woland.c006-session.v1":
        raise ValueError("UNSUPPORTED_MECHANISM_STATE")
    if source_bindings() != state["sources"]:
        raise ValueError("C006_RUNTIME_SOURCE_DRIFT")
    if state["session"]["protocol_sha256"] != PROTOCOL_SHA256:
        raise ValueError("C006_PROTOCOL_SOURCE_MISMATCH")
    captured = [row for row in state["transport"]["observations"] if "raw_reply_base64" in row]
    for row in captured:
        for name in ("raw_reply", "raw_wire"):
            try:
                raw = base64.b64decode(row[name + "_base64"], validate=True)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("C006_TRANSPORT_RAW_MISMATCH") from exc
            if digest(raw) != row.get(name + "_sha256"):
                raise ValueError("C006_TRANSPORT_RAW_MISMATCH")
    if state["executor"] == "openrouter":
        transcript = state["session"]["transcript"]
        if not len(transcript) <= len(captured) <= len(transcript) + 1:
            raise ValueError("C006_TRANSPORT_SESSION_MISMATCH")
        for row, admitted in zip(captured, transcript):
            checked = admitted["pfp"]
            if (row["attempt_state"] != "CompletedSettled"
                    or row["pfp_binding"] != checked["binding"]
                    or row["raw_reply_base64"] != checked["raw_reply_base64"]
                    or row["raw_reply_sha256"] != checked["raw_reply_sha256"]):
                raise ValueError("C006_TRANSPORT_SESSION_MISMATCH")
        if len(captured) > len(transcript):
            if state["session"]["terminal"] is not None or (
                    captured[-1]["pfp_binding"] != sessions.prepare_session_turn(state["session"]).binding):
                raise ValueError("C006_TRANSPORT_SESSION_MISMATCH")
    return _native(state["native"])


def start(board, *, run_id, executor="ide", arm="ledger", detector_firing_share="1/3",
          native_host=None, native_host_sha256=None):
    sources = source_bindings()
    binding = _native_binding(native_host, native_host_sha256)
    native = _native(binding)
    session = sessions.start_session(board, run_id=run_id, protocol_sha256=PROTOCOL_SHA256,
        arm=arm, detector_firing_share=detector_firing_share, native=native)
    return dict(schema="woland.c006-session.v1", executor=executor, sources=sources,
        native=binding, session=session, transport=dict(status="READY", config=None, observations=[]))


def report(state):
    session, transport = state["session"], state["transport"]
    turn = sessions.prepare_session_turn(session) if session["terminal"] is None else None
    observations = transport["observations"]
    paid = [row for row in observations if row.get("provider") == "openrouter"]
    known = [row["cost_usd"] for row in paid if row.get("cost_usd") is not None]
    return dict(challenge="C006", run_id=session["run_id"], executor=state["executor"],
        terminal=session["terminal"], transport_status=transport["status"],
        transport_reason=transport.get("reason"), turns=len(session["transcript"]),
        fuel=session["fuel"], phi1=session["measurement"]["phi1"],
        result=sessions.session_result(session) if session["terminal"] is not None else None,
        pfp_turn={**turn.prompt.to_dict(), "binding": turn.binding} if turn else None,
        provider_replies=len(paid), unknown_cost_replies=len(paid) - len(known),
        known_cost_usd=str(sum((Decimal(str(cost)) for cost in known), Decimal(0))) if paid else None,
        authority_effect="None", scope="Bounded C006 session; matched-arm scientific experiment remains open.",
        post_run_learning={"status": "HOST_ACTION_REQUIRED", "instructions": POST_RUN_LEARNING_INSTRUCTIONS})


def run_bound(state, gateway, model, *, max_calls, checkpoint):
    """One existing accounted gateway throughout; unsettled replies cannot be admitted."""
    if state["executor"] != "openrouter" or state["transport"]["status"] != "READY":
        raise ValueError("MECHANISM_EXECUTOR_NOT_READY")
    native = _validate(state)
    for _ in range(max_calls):
        if state["session"]["terminal"] is not None:
            break
        # Detect source/native drift before the next paid dispatch as well.
        native = _validate(state)
        turn = sessions.prepare_session_turn(state["session"])
        request = CandidateRequest(system=turn.prompt.system, user=turn.prompt.user,
            decoding=DecodingParamsV1(thinking=None, allow_fallbacks=False))
        try:
            result = gateway.for_action(turn.binding["attempt_id"]).complete_result(
                request, provider=Provider.OPENROUTER, model=model)
        except Exception as exc:
            state["transport"].update(status="BLOCKED", reason="PROVIDER_EXECUTION_UNAVAILABLE")
            state["transport"]["observations"].append(dict(failure_code="PROVIDER_EXECUTION_UNAVAILABLE",
                error_type=type(exc).__name__, settlement="UNKNOWN; existing reservation retained"))
            checkpoint(state)
            break
        if isinstance(result, Err):
            failure = result.error
            state["transport"]["observations"].append(dict(failure_code=failure.code,
                attempt_id=failure.attempt_id,
                **(failure.response_metadata() if hasattr(failure, "response_metadata") else {})))
            state["transport"].update(status="BLOCKED", reason=failure.code)
            checkpoint(state)
            break
        outcome, candidate = result.value, result.value.candidate
        admitted = outcome.admitted
        encoding = "utf-8"
        try:
            raw = candidate.content.encode("utf-8")
        except UnicodeEncodeError:
            # Retain the exact string's surrogate code points; strict PFP UTF-8
            # decoding rejects it after paid custody, without inventing a reply.
            raw, encoding = candidate.content.encode("utf-8", errors="surrogatepass"), "utf-8-surrogatepass-invalid"
        observation = dict(provider=candidate.provider, model=candidate.model,
            transport=candidate.transport, cost_usd=candidate.cost_usd,
            input_tokens=candidate.input_tokens, output_tokens=candidate.output_tokens,
            generation_id=candidate.generation_id, attempt_id=admitted.attempt_id,
            request_digest=admitted.request_digest, reservation_id=admitted.reservation_id,
            estimated_microusd=admitted.estimated_microusd, attempt_state=outcome.state,
            raw_wire_base64=base64.b64encode(outcome.reply_bytes).decode("ascii"),
            raw_wire_sha256=digest(outcome.reply_bytes),
            raw_reply_base64=base64.b64encode(raw).decode("ascii"), raw_reply_sha256=digest(raw),
            raw_reply_encoding=encoding,
            pfp_binding=turn.binding,
            budget_receipt=admitted.receipt.to_dict() if admitted.receipt is not None else None)
        state["transport"]["observations"].append(observation)
        mismatch = candidate.provider != "openrouter" or candidate.model != model or candidate.transport == "fixture"
        if mismatch or outcome.state != "CompletedSettled" or candidate.cost_usd is None:
            state["transport"].update(status="BLOCKED",
                reason="PROVIDER_MODE_MISMATCH" if mismatch else (
                    "CompletedCostUnknown" if candidate.cost_usd is None else outcome.state))
            checkpoint(state)
            break
        # Retain paid evidence before native admission, so native failure cannot erase it.
        checkpoint(state)
        native = _validate(state)
        state["session"] = sessions.submit_session_turn(state["session"], raw, native=native)
        checkpoint(state)
    if state["session"]["terminal"] is None and state["transport"]["status"] == "READY":
        state["transport"].update(status="BLOCKED", reason="CALL_ALLOWANCE_EXHAUSTED")
        checkpoint(state)
    return state


def main(args=None):
    parser = argparse.ArgumentParser(description="Woland -> PFP -> original C006 bounded session")
    commands = parser.add_subparsers(dest="command", required=True)
    baseline = commands.add_parser("baseline", help="Explicit deterministic arm E; never a model trial")
    baseline.add_argument("--board", required=True, type=Path)
    baseline.add_argument("--native-host", type=Path)
    baseline.add_argument("--native-host-sha256")
    for name in ("start", "next", "submit", "replay", "run"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--state", required=True, type=Path)
        if name in ("start", "run"):
            cmd.add_argument("--board", required=True, type=Path)
            cmd.add_argument("--run-id", required=True)
            cmd.add_argument("--arm", choices=("ledger", "history", "prose"), default="ledger")
            cmd.add_argument("--detector-firing-share", default="1/3")
            cmd.add_argument("--native-host", type=Path)
            cmd.add_argument("--native-host-sha256")
        if name == "submit":
            cmd.add_argument("--raw-reply", required=True, type=Path)
        if name == "run":
            cmd.add_argument("--model", required=True)
            cmd.add_argument("--max-output-tokens", required=True, type=int, choices=range(1, 3001), metavar="1..3000")
            cmd.add_argument("--max-provider-calls", required=True, type=int, help="Explicit positive call allowance; session fuel also bounds execution")
            cmd.add_argument("--max-estimated-cost-microusd", required=True, type=int)
            cmd.add_argument("--env-file", type=Path)
    parsed = parser.parse_args(args)

    def save(value, *, new=False):
        parsed.state.parent.mkdir(parents=True, exist_ok=True)
        with parsed.state.open("x" if new else "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    try:
        if parsed.command == "baseline":
            source_bindings()
            binding = _native_binding(parsed.native_host, parsed.native_host_sha256)
            result = sessions.exact_baseline(json.loads(parsed.board.read_bytes()),
                protocol_sha256=PROTOCOL_SHA256, native=_native(binding))
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if parsed.command in ("start", "run"):
            if parsed.state.exists():
                raise ValueError("MECHANISM_STATE_ALREADY_EXISTS: retain the existing accounting; paid runs require a fresh state")
            if parsed.command == "run" and not 0 < parsed.max_estimated_cost_microusd <= 50000:
                raise ValueError("INVALID_ESTIMATED_BUDGET")
            if parsed.command == "run" and parsed.max_provider_calls < 1:
                raise ValueError("INVALID_CALL_LIMIT")
            if parsed.command == "run" and parsed.state.with_suffix(".budget.sqlite3").exists():
                raise ValueError("MECHANISM_ACCOUNTING_ALREADY_EXISTS: preserve the previous allowance")
            state = start(json.loads(parsed.board.read_bytes()), run_id=parsed.run_id,
                executor="ide" if parsed.command == "start" else "openrouter", arm=parsed.arm,
                detector_firing_share=parsed.detector_firing_share,
                native_host=parsed.native_host, native_host_sha256=parsed.native_host_sha256)
            if parsed.command == "run":
                state["transport"]["config"] = dict(model=parsed.model, max_calls=parsed.max_provider_calls,
                    max_output_tokens=parsed.max_output_tokens,
                    max_estimated_cost_microusd=parsed.max_estimated_cost_microusd,
                    accounting_path=str(parsed.state.with_suffix(".budget.sqlite3").resolve()))
            save(state, new=True)
            if parsed.command == "run":
                gateway = create_accounted_openrouter_gateway(parsed.model, parsed.max_output_tokens,
                    env_file=parsed.env_file, max_estimated_cost_microusd=parsed.max_estimated_cost_microusd,
                    max_calls=parsed.max_provider_calls, accounting_path=parsed.state.with_suffix(".budget.sqlite3"),
                    run_id=state["session"]["run_id"], objective_sha256=digest(canonical(dict(
                        board=state["session"]["board"], sources=state["sources"], native=state["native"],
                        protocol_sha256=state["session"]["protocol_sha256"], arm=state["session"]["arm"]))))
                state = run_bound(state, gateway, parsed.model, max_calls=parsed.max_provider_calls, checkpoint=save)
        else:
            state = json.loads(parsed.state.read_bytes())
            native = _validate(state)
            if parsed.command == "replay":
                print(json.dumps(sessions.replay_session(state["session"], native=native)))
                return 0
            if parsed.command == "submit":
                if state["executor"] != "ide":
                    raise ValueError("EXECUTOR_MISMATCH")
                state["session"] = sessions.submit_session_turn(state["session"], parsed.raw_reply.read_bytes(), native=native)
                save(state)
        print(json.dumps(report(state), ensure_ascii=False))
        return 2 if state["transport"]["status"] == "BLOCKED" or state["session"]["terminal"] in (
            "SURVIVOR_OBSTRUCTION", "EXECUTION_UNAVAILABLE") else 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REFUSED", error=str(exc), authority_effect="None")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
