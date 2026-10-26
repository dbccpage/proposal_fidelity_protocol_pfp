"""``woland research``: drive a WF_RESEARCH_PFP run from the shell or an IDE agent.

Every command prints one JSON object. Exit codes: ``0`` the command was applied, ``2`` a
typed refusal (also printed as JSON), argparse's own ``2`` for unusable arguments.

IDE mode: an agent writes each stage response to a file and calls ``submit``.
The old Anthropic Messages ``dispatch`` command is retained as an explicit refusal.
Use ``submit`` with the current IDE session, or the shared Woland teamwork
OpenRouter route; this shell never substitutes one provider for another.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    try_resolve_intelligence_repo_root,
)
from omega_engine_operations.domain.rop.result import Err, Refusal, Result
from omega_engine_woland.domain.researcher.models import LoopSnapshotV1, SubmissionV1
from omega_engine_woland.infrastructure.researcher.native_research_host import (
    NativeResearchLoopHost,
)
from omega_engine_woland.infrastructure.researcher.run_custody_store import FileRunCustody
from omega_engine_woland.runtime import build_woland_swarm
from omega_engine_woland.use_cases.base_swarm.specializations import WORKLOAD_PROFILES_V01
from omega_engine_woland.use_cases.base_swarm.woland_swarm import OmegaEngineWolandSwarm
from omega_engine_woland.use_cases.researcher.researcher_swarm import ResearchLoopUseCase

_LOCUS = "omega_engine_woland.entrypoints.researcher_cli"


class ResearchExecutorRetired(ValueError):
    code = "RESEARCH_EXECUTOR_RETIRED"


def _load(path: str) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    return yaml.safe_load(text) if path.endswith((".yaml", ".yml")) else json.loads(text)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _refused(refusal: Refusal) -> int:
    _emit({"status": "REFUSED", "error": {"code": refusal.code, "message": refusal.message}})
    return 2


def _snapshot(snapshot: LoopSnapshotV1) -> dict[str, Any]:
    return {
        "status": "OK",
        "run_id": snapshot.run_id,
        "state_sha256": snapshot.state_sha256,
        "next_action": dict(snapshot.next_action),
        "spent": dict(snapshot.spent),
        "terminal": snapshot.terminal,
        "output": dict(snapshot.output),
    }


def _report(result: Result[Any, Refusal]) -> int:
    if isinstance(result, Err):
        return _refused(result.error)
    value = result.value
    if isinstance(value, SubmissionV1):
        payload = _snapshot(value.snapshot)
        payload.update(
            occurrence_id=value.occurrence_id,
            raw_path=value.raw_path,
            accepted=value.accepted,
            violations=list(value.violations),
        )
        _emit(payload)
    elif isinstance(value, LoopSnapshotV1):
        _emit(_snapshot(value))
    else:
        _emit({"status": "OK", "result": value})
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="woland research", description=__doc__.split("\n")[0])
    parser.add_argument("--repo-root", help="checkout whose _intelligence/ holds the run folders")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="admit a mission and open its run folder")
    start.add_argument("--mission", required=True, help="mission YAML or JSON")
    commands.add_parser("check-pack", help="check the workflow folder against the controller")
    for name in ("status", "begin-round", "submit", "evaluate", "route", "halt", "dispatch"):
        sub = commands.add_parser(name)
        sub.add_argument("--run-id", required=True)
        if name == "begin-round":
            sub.add_argument("--source-sha256", required=True)
        if name in {"submit", "dispatch"}:
            sub.add_argument("--stage", type=int, required=True)
            sub.add_argument("--attempt", type=int, default=1)
        if name == "submit":
            sub.add_argument("--response-file", required=True)
        if name == "evaluate":
            sub.add_argument("--checks-file", required=True, help="host check records (JSON list)")
            sub.add_argument("--checker-policy-sha256", required=True)
        if name == "route":
            sub.add_argument("--observation-file", required=True)
        if name == "halt":
            sub.add_argument("--disposition", required=True)
            sub.add_argument("--reason", required=True)
        if name == "dispatch":
            sub.add_argument("--request-file", required=True, help="rendered Messages request")
            sub.add_argument("--ceiling-microusd", type=int, required=True)
            sub.add_argument("--token-bound", type=int, required=True)
            sub.add_argument("--prices-file", required=True, help="dated price observations")
            sub.add_argument("--at-utc", required=True)
            sub.add_argument("--advisor-pairings-file")
    return parser


def _swarm(root: Path, args: argparse.Namespace) -> ResearchLoopUseCase:
    if args.command == "dispatch":
        raise ResearchExecutorRetired(
            "The Anthropic Messages dispatch route is retired. Use `woland research submit` "
            "with a current-IDE response file, or `woland teamwork run --executor openrouter` "
            "for the shared PFP OpenRouter workflow. No fallback or provider substitution was attempted."
        )
    return ResearchLoopUseCase(
        woland=build_woland_swarm(
            OmegaEngineWolandSwarm,
            specialization=WORKLOAD_PROFILES_V01["researcher"],
            repo_root=root,
        ),
        host=NativeResearchLoopHost(),
        custody=FileRunCustody(root),
        dispatcher=None,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "check-pack":
        try:
            return _report(NativeResearchLoopHost().check_pack())
        except (OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
            return _refused(Refusal("RESEARCH_CLI_INPUT_INVALID", str(exc), _LOCUS))
    if args.repo_root:
        root = Path(args.repo_root).resolve()
    else:
        resolved = try_resolve_intelligence_repo_root()
        if isinstance(resolved, Err):
            return _refused(resolved.error)
        root = resolved.value
    try:
        swarm = _swarm(root, args)
        match args.command:
            case "start":
                return _report(swarm.start(_load(args.mission)))
            case "status":
                return _report(swarm.status(args.run_id))
            case "begin-round":
                return _report(swarm.begin_round(args.run_id, args.source_sha256))
            case "submit":
                raw = Path(args.response_file).read_bytes()
                return _report(swarm.submit(args.run_id, stage=args.stage, attempt=args.attempt, raw=raw))
            case "evaluate":
                checks = _load(args.checks_file)
                return _report(swarm.evaluate(args.run_id, checks, args.checker_policy_sha256))
            case "route":
                return _report(swarm.route(args.run_id, _load(args.observation_file)))
            case "halt":
                return _report(swarm.halt(args.run_id, args.disposition, args.reason))
            case "dispatch":
                return _report(
                    swarm.dispatch(
                        args.run_id,
                        stage=args.stage,
                        attempt=args.attempt,
                        request=_load(args.request_file),
                        ceiling_microusd=args.ceiling_microusd,
                        token_bound=args.token_bound,
                    )
                )
    except (
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        yaml.YAMLError,
    ) as exc:
        code = getattr(exc, "code", "RESEARCH_CLI_INPUT_INVALID")
        return _refused(Refusal(str(code), str(exc), _LOCUS))
    return _refused(Refusal("RESEARCH_CLI_COMMAND_UNKNOWN", args.command, _LOCUS))


if __name__ == "__main__":
    sys.exit(main())
