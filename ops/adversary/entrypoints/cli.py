"""Turn-stepper CLI for the Adversary Swarm (the evaluation single point of entry).

Exit codes: ``0`` completed or persisted, ``2`` typed refusal (message on
stderr), argparse's own ``2`` for unusable arguments.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from operating_system.adapters.intelligence_custody.ic_routing import (
    IcMigrationRefusal,
    intelligence_path,
)
from operating_system.adapters.intelligence_custody.intelligence_root import (
    try_resolve_intelligence_repo_root,
)
from operations.domain.rop.result import Refusal
from adversary.infrastructure.native import DefaultNativeOperationPort

from ..controllers.adversary_controller import AdversarySwarmController
from ..domain.specialization import SwarmTypeV1
from ..runtime import build_adversary_service
from ..use_cases.skill_run_persistence import (
    TERMINAL_VERDICTS,
    WORK_STATUSES,
    parse_ddc_actions,
    persist_skill_run,
)


def generate_task_key(objective: str, explicit_key: str | None = None) -> str:
    """Generate a collision-free task key for a Adversary bout.

    If an explicit key is supplied, validates and returns it.
    Otherwise, generates a unique key with an objective slug, UTC timestamp, and hex nonce.
    """
    if explicit_key is not None and explicit_key.strip():
        return explicit_key.strip()

    # ASCII only: the key must be a canonical identifier, and str.isalnum()
    # admits letters such as "É" that the identifier grammar refuses.
    slug = "".join(c if c.isascii() and c.isalnum() else "_" for c in objective[:24]).strip("_")
    if not slug:
        slug = "run"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    nonce = uuid.uuid4().hex[:12]
    return f"task_{slug}_{timestamp}_{nonce}"


def _print_refusal(refusal: Refusal) -> int:
    print(f"[AdversarySwarm] REFUSED {refusal.code}: {refusal.message}", file=sys.stderr)
    return 2


BOUT_ALIASES: dict[str, str] = {
    "software-dev": "Software development bout (Techne Council)",
    "research-paper": "Research paper loop bout (Episteme Council)",
    "product-mgmt": "Product planning & sprint bout (Product Planning Office)",
    "governing-councils": "Governing councils deliberation bout (Councils)",
    "thanatos": "Defensive security & threat bout (Thanatos Council)",
}


def _add_bout_arguments(p: argparse.ArgumentParser, default_swarm_type: str = "open-topic") -> None:
    p.add_argument(
        "--objective", required=False, help="Task objective or prepared live request value"
    )
    p.add_argument(
        "--task-key",
        default=None,
        help="Explicit task key for the bout (default: auto-generated unique key)",
    )
    p.add_argument(
        "--swarm-type",
        choices=[st.value for st in SwarmTypeV1],
        default=default_swarm_type,
        help=f"Adversary swarm specialization type (default: {default_swarm_type})",
    )
    p.add_argument(
        "--max-rounds",
        type=int,
        choices=range(1, 11),
        default=4,
        metavar="1..10",
        help="Maximum number of critique rounds",
    )
    p.add_argument(
        "--request-admission",
        action="store_true",
        help="Mark the candidate as proposed for separate external admission; never promotes",
    )
    p.add_argument("--fixture", action="store_true", help="Run with fixture replies for CI/test")
    p.add_argument(
        "--live",
        action="store_true",
        help="Run with live LLM turn completions via OpenRouter instead of fixtures",
    )
    p.add_argument(
        "--provider",
        choices=["openrouter"],
        default="openrouter",
        help="Model provider for live execution (default: openrouter)",
    )
    p.add_argument(
        "--model",
        default=None,
        help="Model identifier override for live provider (e.g. openai/gpt-4o-mini)",
    )
    p.add_argument("--live-config", type=Path, default=None)
    p.add_argument("--repo-root", type=Path, default=None)
    p.add_argument("--native-host", type=Path, default=None)
    p.add_argument("--native-host-sha256", default=None)
    p.add_argument("--routing-config", type=Path, default=None)
    p.add_argument("--env-file", type=Path, default=None)
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--max-cost-microusd", type=int, default=None)
    p.add_argument("--max-output-tokens", type=int, default=None)
    p.add_argument("--compute-budget", type=int, default=100)
    p.add_argument(
        "--roles",
        "--characters",
        dest="selected_characters",
        default=None,
        help="Comma-separated runtime seat names; fixed checker stages remain",
    )
    p.add_argument(
        "--panel",
        dest="panel_mode",
        choices=["core", "full"],
        default="core",
        help="core: five seats (default); full: the larger cast",
    )
    p.add_argument("--case", type=Path, default=None, help="Exact finite C011 challenge JSON")
    p.add_argument("--checker", choices=["c011", "symbol_game.c011.exact.v1"], default=None)
    p.add_argument(
        "--learning-config",
        type=Path,
        default=None,
        help="Explicit fixed learning evaluations and GitHub destination",
    )
    p.add_argument(
        "--digest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Execute intelligence digestion and archive runs at end of execution (default: True)",
    )


def _add_run_live_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--template",
        type=Path,
        required=True,
        help="Existing live_config.json; operator settings only",
    )
    parser.add_argument("--objective", required=True)
    parser.add_argument("--task-key", required=True, help="Fresh explicit task identifier")
    parser.add_argument(
        "--max-cost-microusd", type=int, required=True, help="Explicit fresh paid allowance"
    )
    parser.add_argument(
        "--native-host-sha256", required=True, help="Independently reviewed native binary pin"
    )
    parser.add_argument(
        "--signing-key", type=Path, required=True, help="Existing external operator key"
    )
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--native-host", type=Path, default=None)
    parser.add_argument("--deployment-root", type=Path, default=None)
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument(
        "--panel", dest="panel_mode", choices=["core", "full"], default=None
    )
    parser.add_argument("--max-rounds", type=int, choices=range(1, 11), default=None)
    parser.add_argument("--compute-budget", type=int, default=None)
    parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Replace old scene bindings with fresh catalog refs",
    )
    parser.add_argument(
        "--prepare-only", action="store_true", help="Sign the fresh task without provider dispatch"
    )


def _digest_and_archive_post_run(repo_root: Path, *, task_key: str | None = None) -> bool:
    """Gut run outputs for knowledge (antibodies, anti-skills) and transition to cold archive."""
    from ..use_cases.intelligence_digestion.digestion_service import digest_and_archive_intelligence

    try:
        receipt = digest_and_archive_intelligence(repo_root, native_support=DefaultNativeOperationPort())
        print(
            f"[AdversarySwarm] Intelligence Digestion: Examined={receipt.total_runs_examined}, "
            f"Archived={receipt.total_runs_archived}, Blocked={len(receipt.blocked)}"
        )
        for record in receipt.records:
            print(f"  ✔ [{record.source_id}] {record.digestion_state} -> {record.archive_path}")
            if record.defects_extracted:
                print(
                    f"    Transmuted {record.defects_count} defect(s) into candidate antibodies/transfers."
                )
        for blocked in receipt.blocked:
            print(
                f"  ! [{blocked.run_id}] {blocked.state}: {'; '.join(blocked.residuals)}",
                file=sys.stderr,
            )
        if receipt.errors:
            for err in receipt.errors:
                print(f"  ! Error: {err}", file=sys.stderr)
            return False
        return True
    except Exception as exc:
        print(f"[AdversarySwarm] Intelligence digestion failed: {exc}", file=sys.stderr)
        return False


def main(args: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if args is None else args)
    if argv[:1] == ["empirical"]:
        from pfp.entrypoints.empirical_gates import main as empirical_main

        return empirical_main(argv[1:])
    if argv[:1] == ["report-operation"]:
        from .report_operation_cli import main as report_operation_main

        return report_operation_main(argv[1:])
    if argv[:1] == ["teamwork"]:
        from .teamwork_cli import main as teamwork_main

        return teamwork_main(argv[1:])
    if argv[:1] == ["pilot035"]:
        if argv[1:2] == ["resume"]:
            from adversary.infrastructure.pilot035_continuation import (
                main as continuation_main,
            )

            try:
                return continuation_main(argv[1:])
            except sqlite3.Error as exc:
                print(json.dumps({"status": "REFUSED", "reason": "EPISODE_LEDGER_UNAVAILABLE: " + str(exc),
                                  "authority_effect": "None"}))
                return 2
        if argv[1:2] == ["replay"]:
            from adversary.infrastructure.pilot035_replay import (
                main as pilot035_replay_main,
            )

            return pilot035_replay_main(argv[2:])
        from adversary.infrastructure.pilot035_play import main as pilot035_main

        return pilot035_main(argv[1:])
    if argv[:1] == ["challenge"]:
        from adversary.infrastructure.challenge_play import main as challenge_main

        return challenge_main(argv[1:])
    if argv[:1] == ["mechanism"]:
        from adversary.infrastructure.mechanism_play import main as mechanism_main

        return mechanism_main(argv[1:])
    if argv[:1] == ["research"]:
        from .researcher_cli import main as research_main

        return research_main(argv[1:])
    parser = argparse.ArgumentParser(description="Adversary Swarm 7-Act Turn-Stepper & Runner CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "empirical", add_help=False, help="Collect existing bounded PFP empirical gates (see `empirical --help`)"
    )
    subparsers.add_parser(
        "teamwork", add_help=False, help="Shared IDE/OpenRouter workflow (see `teamwork --help`)"
    )
    subparsers.add_parser(
        "challenge", add_help=False, help="PFP proposals and original demo judges (see `challenge --help`)"
    )
    subparsers.add_parser(
        "mechanism", add_help=False, help="Bounded C006 sessions through PFP (see `mechanism --help`)"
    )
    subparsers.add_parser(
        "research", add_help=False, help="WF_RESEARCH_PFP research loop (see `research --help`)"
    )
    subparsers.add_parser(
        "pilot035", add_help=False, help="Admitted immune fences and finite Tao checking through the IDE (see `pilot035 --help`)"
    )

    run_parser = subparsers.add_parser("run-bout", help="Run full 7-Act Adversary Swarm bout")
    _add_bout_arguments(run_parser, default_swarm_type="open-topic")

    for alias_cmd, desc in BOUT_ALIASES.items():
        alias_parser = subparsers.add_parser(alias_cmd, help=desc)
        _add_bout_arguments(alias_parser, default_swarm_type=alias_cmd)

    prepare_parser = subparsers.add_parser(
        "prepare-live", help="Prepare an exact signed typed task"
    )
    _add_bout_arguments(prepare_parser)
    prepare_parser.add_argument("--config-dir", required=True, type=Path)
    prepare_parser.add_argument("--reviewer", required=True)
    prepare_parser.add_argument("--allowed-signers", required=True, type=Path)
    prepare_parser.add_argument(
        "--signing-key",
        type=Path,
        default=None,
        help="Existing external key; omitted means unsigned draft",
    )
    prepare_parser.add_argument("--ssh-keygen", default="ssh-keygen")
    prepare_parser.add_argument(
        "--carrier-context",
        type=Path,
        default=None,
        help="Bounded JSON carrier and phase intergate declarations",
    )
    prepare_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Bounded canonical scene fallback graph with typed skill gate references",
    )
    fresh_parser = subparsers.add_parser(
        "run-live",
        help="Sign a fresh explicit task from operator settings and run the live circuit",
    )
    _add_run_live_arguments(fresh_parser)
    schemas_parser = subparsers.add_parser(
        "gate-schemas", help="Describe actual native primary and empirical witness contracts"
    )
    schemas_parser.add_argument("--native-host", type=Path, required=True)
    schemas_parser.add_argument("--native-host-sha256", required=True)
    for name in ("journal-inspect", "journal-reconcile"):
        journal_parser = subparsers.add_parser(name)
        journal_parser.add_argument("--repo-root", type=Path, default=None)

    persist_parser = subparsers.add_parser(
        "persist-run",
        help="Persist a novella and results authored by the /adversary skill or agent",
    )
    persist_parser.add_argument(
        "--objective", required=True, help="Task objective the run addressed"
    )
    persist_parser.add_argument(
        "--task-key",
        default=None,
        help="Explicit task key (default: auto-generated unique key)",
    )
    persist_parser.add_argument(
        "--novella", required=True, type=Path, help="Path to the novella markdown"
    )
    persist_parser.add_argument(
        "--ddc-actions",
        "--dda-actions",
        dest="ddc_actions",
        type=Path,
        default=None,
        help="Optional JSONL of DDC actions; any 'letter' must be a DDC letter",
    )
    persist_parser.add_argument(
        "--summary", type=Path, default=None, help="Optional JSON object of results"
    )
    persist_parser.add_argument(
        "--work-status",
        choices=WORK_STATUSES,
        default=None,
        help="Reported task progress, separate from checker evidence and authority",
    )
    persist_parser.add_argument(
        "--verdict",
        default="OPEN_RESIDUAL",
        choices=TERMINAL_VERDICTS,
        help=(
            "Evidence verdict (default: OPEN_RESIDUAL); PASS_TO_MASTER requires "
            "--checker-receipt stating ACCEPTED (REFUSE with a receipt needs REJECTED). "
            "REFERENCE_SELF_CONSISTENT and REFERENCE_SELF_INCONSISTENT label a "
            "reference scored by its own checker and need no receipt"
        ),
    )
    persist_parser.add_argument(
        "--checker-receipt",
        type=Path,
        default=None,
        help=(
            "Challenge checker receipt file: a JSON object with verdict, "
            "candidate_content_sha256 and checker_id; its SHA-256 binds the verdict"
        ),
    )
    persist_parser.add_argument(
        "--source", default="adversary_skill", help="Producer of the run (default: adversary_skill)"
    )
    persist_parser.add_argument(
        "--learning-runtime-factory",
        default=None,
        help="Explicit module:function returning a parent-bound learning completion adapter",
    )
    persist_parser.add_argument(
        "--digest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Execute intelligence digestion and archive runs at end of execution (default: True)",
    )
    persist_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional destination directory for the run bundle (e.g. _ic/adversary)",
    )

    descent_parser = subparsers.add_parser(
        "run-descent", help="Run the core_wdp::prime_algos descent coordinator on carrier"
    )
    descent_parser.add_argument(
        "--run-id", default=None, help="Run ID for the descent execution (default: auto-generated)"
    )
    descent_parser.add_argument(
        "--carrier-json",
        type=Path,
        default=None,
        help="Path to JSON file specifying carrier topology",
    )
    descent_parser.add_argument(
        "--triangle",
        action="store_true",
        help="Use standard 3-cycle triangle carrier with 2-cell face",
    )
    descent_parser.add_argument(
        "--omega",
        default="-2,1,1",
        help="Comma-separated integer cochain values on edges (default: -2,1,1)",
    )
    descent_parser.add_argument(
        "--max-steps", type=int, default=64, help="Maximum descent steps (default: 64)"
    )
    descent_parser.add_argument(
        "--output-receipt",
        type=Path,
        default=None,
        help="Optional output path to write JSON descent receipt",
    )

    graph_parser = subparsers.add_parser(
        "run-graph", help="Diagnose or search a declared rational graph repair catalog"
    )
    graph_parser.add_argument(
        "--task", required=True, type=Path, help="GraphTaskV1 JSON declaration"
    )
    graph_parser.add_argument("--mode", required=True, choices=["diagnose", "repair"])
    graph_parser.add_argument(
        "--output-dir", required=True, type=Path, help="Adversary output root; writes runs/<task_id>/"
    )
    graph_parser.add_argument(
        "--native-host", type=Path, default=None, help="Explicit existing native host binary"
    )
    graph_generation = graph_parser.add_mutually_exclusive_group()
    graph_generation.add_argument(
        "--fixture", action="store_true", help="Explicit offline proposal and critic fixtures"
    )
    graph_generation.add_argument(
        "--gateway-factory",
        default=None,
        help="module:function returning an existing configured provider gateway",
    )
    graph_parser.add_argument(
        "--instruction-ingress-factory", default=None,
        help="module:function returning the operator-configured InstructionIngressPort",
    )
    graph_parser.add_argument(
        "--anti-skill-gate-factory", default=None,
        help="module:function returning the existing active AntiSkillGatePort",
    )
    graph_parser.add_argument(
        "--provider", default=None, help="Explicit provider for the configured gateway"
    )
    graph_parser.add_argument(
        "--model", default=None, help="Explicit model for the configured gateway"
    )
    replay_parser = subparsers.add_parser(
        "replay-graph", help="Replay native evidence and mining from an externally pinned graph run"
    )
    replay_parser.add_argument("--run-dir", required=True, type=Path)
    replay_parser.add_argument(
        "--receipt-ref",
        required=True,
        help="sha256:<hex> returned by run-graph, retained outside the run folder",
    )
    replay_parser.add_argument("--native-host", type=Path, default=None)

    intake_parser = subparsers.add_parser(
        "intake-omc-dags",
        help="Intake OMC DAG receipts and farm obstructions for DDC, OEWAS, OEEIS, OEPRMPTCIV",
    )
    intake_parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing OMC DAG .jsonl files (default: _intelligence/omc_dags)",
    )
    intake_parser.add_argument(
        "--domain",
        choices=["ALL", "DDC", "OEWAS", "OEEIS", "OEPRMPTCIV"],
        default="ALL",
        help="Filter findings by canonical domain (default: ALL)",
    )
    intake_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write full harvest JSON report",
    )
    intake_parser.add_argument(
        "--persist-adversary-run",
        action="store_true",
        help="Persist a canonical Adversary five-file run bundle under _intelligence/_adversary/runs/",
    )
    intake_parser.add_argument(
        "--task-key",
        default=None,
        help="Explicit task key for the persisted Adversary run bundle",
    )
    intake_parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional root repository path (defaults to auto-detection)",
    )
    intake_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed obstruction and skill breakdowns to stdout",
    )
    intake_parser.add_argument(
        "--digest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Execute intelligence digestion and archive runs at end of execution (default: True)",
    )

    parsed = parser.parse_args(argv)
    parsed.provided_options = frozenset(
        item.split("=", 1)[0] for item in argv if item.startswith("--")
    )
    if parsed.command == "gate-schemas":
        return _run_gate_schemas(parsed)
    if parsed.command == "run-live":
        return _run_fresh_live(parsed)
    if parsed.command == "prepare-live":
        return _prepare_live(parsed)
    if parsed.command in ("journal-inspect", "journal-reconcile"):
        return _run_journal(parsed)
    if parsed.command == "run-graph":
        return _run_graph(parsed)
    if parsed.command == "replay-graph":
        return _replay_graph(parsed)
    if parsed.command == "persist-run":
        return _persist_run(parsed)
    if parsed.command == "run-bout" or parsed.command in BOUT_ALIASES:
        return _run_bout(parsed)
    if parsed.command == "run-descent":
        return _run_descent(parsed)
    if parsed.command == "intake-omc-dags":
        return _run_intake_omc_dags(parsed)
    return 2


def _run_intake_omc_dags(parsed: argparse.Namespace) -> int:
    from .intake_omc_dags import main as intake_main

    args: list[str] = []
    if parsed.input_dir:
        args.extend(["--input-dir", str(parsed.input_dir)])
    if parsed.domain:
        args.extend(["--domain", parsed.domain])
    if parsed.out:
        args.extend(["--out", str(parsed.out)])
    if parsed.persist_adversary_run:
        args.append("--persist-adversary-run")
    if parsed.task_key:
        args.extend(["--task-key", parsed.task_key])
    if getattr(parsed, "repo_root", None):
        args.extend(["--repo-root", str(parsed.repo_root)])
    if parsed.verbose:
        args.append("--verbose")
    ret = intake_main(args)
    if parsed.persist_adversary_run and getattr(parsed, "digest", True) and ret == 0:
        root = try_resolve_intelligence_repo_root()
        if not root.is_err:
            _digest_and_archive_post_run(root.unwrap(), task_key=parsed.task_key)
    return ret


def _run_bout(parsed: argparse.Namespace) -> int:
    if parsed.live and parsed.fixture:
        print(
            "[AdversarySwarm] REFUSED ARGUMENTS_INCOMPATIBLE: --live and --fixture cannot be used together",
            file=sys.stderr,
        )
        return 2

    task_key = generate_task_key(parsed.objective or "live", parsed.task_key)
    fixture_mode = bool(parsed.fixture)
    provider = parsed.provider if parsed.live else None
    swarm_type = getattr(parsed, "swarm_type", "open-topic")

    if parsed.live:
        return _run_live_bout(parsed)
    if not fixture_mode:
        return _print_refusal(
            Refusal(
                "INSTRUCTION_INGRESS_UNBOUND",
                "use --live with a prepared --live-config",
                "adversary.cli",
            )
        )
    if not parsed.objective:
        return _print_refusal(
            Refusal("OBJECTIVE_REQUIRED", "--objective is required in fixture mode", "adversary.cli")
        )

    print(
        f"[AdversarySwarm] Executing 7-Act bout for objective: '{parsed.objective}' "
        f"(task_key={task_key}, swarm_type={swarm_type}, fixture_mode={fixture_mode}, provider={provider})"
    )
    root = try_resolve_intelligence_repo_root() if parsed.repo_root is None else None
    if parsed.repo_root is not None:
        from operations.domain.rop.result import Ok

        root = Ok(parsed.repo_root.absolute())
    if root.is_err:
        return _print_refusal(root.unwrap_err())
    from ..infrastructure.live_configuration import _case

    try:
        case = _case(parsed.case, parsed.checker)
    except (OSError, ValueError, TypeError) as exc:
        return _print_refusal(Refusal("CASE_INVALID", str(exc), "adversary.cli"))
    controller = AdversarySwarmController(
        service=build_adversary_service(
            repo_root=root.unwrap(),
            provider=provider,
            model=parsed.model,
            learning_config=parsed.learning_config,
            output_dir=parsed.output_dir,
            symbol_game_request=case,
            panel_mode=parsed.panel_mode,
        )
    )
    result = controller.run_bout(
        task_key=task_key,
        objective=parsed.objective,
        max_rounds=parsed.max_rounds,
        fixture_mode=fixture_mode,
        request_external_admission=parsed.request_admission,
        swarm_type=swarm_type,
    )
    learning = getattr(controller.service.learning_completion, "last_receipt", None)
    if learning:
        print(
            f"[AutoP] {learning['overall_status']}: {learning.get('reason', learning.get('pr_url', ''))}"
        )
    if controller.service.learning_error:
        print(f"[AutoP] FAILED: {controller.service.learning_error}", file=sys.stderr)
    if result.is_err:
        return _print_refusal(result.unwrap_err())
    outcome = result.unwrap()
    print(
        f"[AdversarySwarm] Bout finished: status={outcome.status}, authorized={outcome.is_authorized}, "
        f"verdict={outcome.terminal_verdict} (receipt={outcome.receipt_id})"
    )
    if not _report_bout_files(outcome):
        return 2
    if getattr(parsed, "digest", True):
        _digest_and_archive_post_run(root.unwrap(), task_key=task_key)
    return 0


def _prepare_live(parsed: argparse.Namespace) -> int:
    from ..infrastructure.live_configuration import prepare_cli_configuration

    try:
        path = prepare_cli_configuration(
            parsed, task_key=generate_task_key(parsed.objective or "live", parsed.task_key)
        )
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        return _print_refusal(Refusal("LIVE_CONFIGURATION_INVALID", str(exc), "adversary.cli"))
    print(f"[AdversarySwarm] Prepared exact task at {path}")
    if parsed.signing_key is None:
        print("[AdversarySwarm] Unsigned draft: review and sign instruction_manifest.json")
    print(
        f'python -m adversary.entrypoints.cli run-bout --live --live-config "{path}" --no-digest'
    )
    return 0


def _run_fresh_live(parsed: argparse.Namespace) -> int:
    from ..infrastructure.live_configuration import prepare_template_configuration

    try:
        path = prepare_template_configuration(parsed)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        return _print_refusal(Refusal("LIVE_CONFIGURATION_INVALID", str(exc), "adversary.cli"))
    print(f"[AdversarySwarm] Signed fresh exact task at {path}", flush=True)
    print(
        f'python -m adversary.entrypoints.cli run-bout --live --live-config "{path}" --no-digest',
        flush=True,
    )
    if parsed.prepare_only:
        return 0
    return main(["run-bout", "--live", "--live-config", str(path), "--no-digest"])


def _report_bout_files(outcome) -> bool:
    if outcome.receipt_path is not None:
        print(f"[AdversarySwarm] Run outputs written to {Path(outcome.receipt_path).parent}")
        return True
    print(f"[AdversarySwarm] Reporting: {outcome.reporting_status} "
          f"({outcome.reporting_failure_code}); task outcome retained; "
          f"working state: {outcome.working_state_path}", file=sys.stderr)
    return False


def _run_live_bout(parsed: argparse.Namespace) -> int:
    from ..infrastructure.live_configuration import execute_cli_configuration

    try:
        config, request, result = execute_cli_configuration(parsed)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        return _print_refusal(Refusal("LIVE_EXECUTION_UNAVAILABLE", str(exc), "adversary.cli"))
    if result.is_err:
        return _print_refusal(result.unwrap_err())
    sealed = result.unwrap()
    outcome = sealed.outcome
    print(
        f"[AdversarySwarm] Live bout: status={outcome.status}, routing={sealed.routing_terminal}, verdict={outcome.terminal_verdict}, receipt={outcome.receipt_id}"
    )
    published = _report_bout_files(outcome)
    for residual in sealed.estate_residuals:
        print(f"[AdversarySwarm] Residual {residual.code}: {residual.message}", file=sys.stderr)
    if parsed.digest and published:
        _digest_and_archive_post_run(Path(config["repo_root"]), task_key=request.task_key)
    return 2 if not published or outcome.status == "REFUSED" or sealed.routing_terminal == "Refused" else 0


def _run_gate_schemas(parsed: argparse.Namespace) -> int:
    import hashlib
    import re

    from pfp.ffi import RustSymbolGameHost

    try:
        path = parsed.native_host
        expected = parsed.native_host_sha256
        if (
            path.is_symlink()
            or not path.is_file()
            or re.fullmatch(r"[0-9a-f]{64}", expected) is None
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("native host differs from the explicit expected binary SHA256")
        result = RustSymbolGameHost(path).invoke("adversary_support", {"operation": "gate_schemas"})
        if result.is_err:
            return _print_refusal(result.unwrap_err())
        envelope = result.unwrap()
        if envelope["success"] is not True:
            raise ValueError(str(envelope["error"]))
        reply = envelope["result"]
        if reply["refusal"] is not None:
            failure = reply["refusal"]
            return _print_refusal(Refusal(failure["code"], failure["message"], "adversary.cli"))
        print(json.dumps(reply["outcome"], sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _print_refusal(Refusal("GATE_SCHEMA_UNAVAILABLE", str(exc), "adversary.cli"))


def _run_journal(parsed: argparse.Namespace) -> int:
    from dataclasses import asdict

    from ..infrastructure.bout_journal import JsonlBoutJournal

    try:
        root = (
            parsed.repo_root.absolute()
            if parsed.repo_root
            else try_resolve_intelligence_repo_root().unwrap()
        )
        journal = JsonlBoutJournal.for_repository(root)
        result = journal.inspect() if parsed.command == "journal-inspect" else journal.reconcile()
        if result.is_err:
            return _print_refusal(result.unwrap_err())
        value = result.unwrap()
        report = (
            value.to_dict()
            if parsed.command == "journal-inspect"
            else [asdict(item) for item in value]
        )
        print(json.dumps(report, sort_keys=True, indent=2, default=str))
        return 0
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return _print_refusal(Refusal("JOURNAL_UNAVAILABLE", str(exc), "adversary.cli"))


def _persist_run(parsed: argparse.Namespace) -> int:
    """Persist a skill-authored run; exit 2 on a typed refusal."""
    try:
        novella_md = parsed.novella.read_text(encoding="utf-8")
        ddc_actions_path = parsed.ddc_actions
        ddc_text = (
            ddc_actions_path.read_text(encoding="utf-8") if ddc_actions_path is not None else ""
        )
        summary = (
            json.loads(parsed.summary.read_text(encoding="utf-8"))
            if parsed.summary is not None
            else {}
        )
        checker_receipt_bytes = (
            parsed.checker_receipt.read_bytes() if parsed.checker_receipt is not None else None
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"[AdversarySwarm] REFUSED INPUT_UNREADABLE: {exc}", file=sys.stderr)
        return 2
    if type(summary) is not dict:
        print("[AdversarySwarm] REFUSED SUMMARY_NOT_OBJECT", file=sys.stderr)
        return 2

    steps = parse_ddc_actions(ddc_text, native_support=DefaultNativeOperationPort())
    if steps.is_err:
        return _print_refusal(steps.unwrap_err())

    root = try_resolve_intelligence_repo_root()
    if root.is_err:
        return _print_refusal(root.unwrap_err())
    try:
        output = (
            parsed.output_dir.absolute()
            if getattr(parsed, "output_dir", None) is not None
            else intelligence_path(root.unwrap(), "_intelligence/_adversary")
        )
    except IcMigrationRefusal as exc:
        return _print_refusal(Refusal(exc.code, str(exc), "ic_routing"))
    result = persist_skill_run(
        output,
        task_key=generate_task_key(parsed.objective, parsed.task_key),
        objective=parsed.objective,
        verdict=parsed.verdict,
        source=parsed.source,
        novella_md=novella_md,
        created_utc=datetime.now(timezone.utc).isoformat(),
        dda_steps=steps.unwrap(),
        summary=summary,
        checker_receipt_bytes=checker_receipt_bytes,
        work_status=parsed.work_status,
        native_support=DefaultNativeOperationPort(),
    )
    if result.is_err:
        return _print_refusal(result.unwrap_err())
    print(f"[AdversarySwarm] Run persisted to {result.unwrap()}")
    from ..runtime import notify_persisted_learning

    learning = notify_persisted_learning(
        root.unwrap(),
        result.unwrap(),
        parsed.verdict,
        source=parsed.source,
        runtime_factory=parsed.learning_runtime_factory,
    )
    if learning:
        if (
            learning.get("overall_status") == "BLOCKED"
            and learning.get("reason") == "CALLER_CONFIGURATION_MISSING"
        ):
            print(
                "[AutoP] Optional learning not configured (CALLER_CONFIGURATION_MISSING); "
                "work remains persisted."
            )
        else:
            print(
                f"[AutoP] {learning['overall_status']}: "
                f"{learning.get('reason', learning.get('pr_url', ''))}"
            )
    if getattr(parsed, "digest", True):
        _digest_and_archive_post_run(root.unwrap(), task_key=parsed.task_key)
    return 0


def _run_descent(parsed: argparse.Namespace) -> int:
    from ..domain.network import Network
    from ..runtime import build_prime_descent_adapter

    run_id = parsed.run_id or generate_task_key("prime_descent")

    if parsed.carrier_json is not None:
        try:
            carrier_data = json.loads(parsed.carrier_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"[AdversarySwarm] REFUSED CARRIER_UNREADABLE: {exc}", file=sys.stderr)
            return 2
        nodes = tuple(range(carrier_data.get("num_vertices", 0)))
        raw_edges = carrier_data.get("edges", [])
        edges = tuple(
            (e["tail"], e["head"]) if isinstance(e, dict) else tuple(e) for e in raw_edges
        )
        raw_faces = carrier_data.get("faces", [])
        faces = tuple(tuple(f) for f in raw_faces)
        network = Network(nodes=nodes, edges=edges, faces=faces)
    else:
        # Default canonical triangle carrier with 1 face
        network = Network(
            nodes=(0, 1, 2),
            edges=((0, 1), (1, 2), (2, 0)),
            faces=((0, 1, 2),),
        )

    try:
        omega_parts = [int(p.strip()) for p in parsed.core.split(",") if p.strip()]
    except ValueError as exc:
        print(f"[AdversarySwarm] REFUSED CORE_INVALID: {exc}", file=sys.stderr)
        return 2

    if len(omega_parts) != len(network.edges):
        print(
            f"[AdversarySwarm] REFUSED CORE_DIMENSION_MISMATCH: expected {len(network.edges)} values, got {len(omega_parts)}",
            file=sys.stderr,
        )
        return 2

    adapter = build_prime_descent_adapter()
    result = adapter.execute_descent(
        run_id=run_id,
        carrier_network=network,
        initial_cochain=omega_parts,
        max_steps=parsed.max_steps,
    )
    if result.is_err:
        return _print_refusal(result.unwrap_err())

    receipt = result.unwrap()
    print(
        f"[AdversarySwarm] Prime descent completed: status={receipt.status.value}, "
        f"terminal_status={receipt.terminal_status}, letters={receipt.letters}, "
        f"phi1={receipt.phi1}, gamma2={receipt.gamma2}, laws_passed={receipt.laws_passed}"
    )

    if parsed.output_receipt is not None:
        receipt_dict = {
            "status": receipt.status.value,
            "backend": receipt.backend,
            "run_id": receipt.run_id,
            "letters": receipt.letters,
            "terminal_status": receipt.terminal_status,
            "phi1": str(receipt.phi1) if receipt.phi1 is not None else None,
            "gamma2": str(receipt.gamma2) if receipt.gamma2 is not None else None,
            "b1_over_q": receipt.b1_over_q,
            "laws_passed": receipt.laws_passed,
            "authority_effect": receipt.authority_effect,
            "reason": receipt.reason,
        }
        try:
            parsed.output_receipt.write_text(json.dumps(receipt_dict, indent=2), encoding="utf-8")
            print(f"[AdversarySwarm] Receipt written to {parsed.output_receipt}")
        except OSError as exc:
            print(f"[AdversarySwarm] REFUSED OUTPUT_UNWRITABLE: {exc}", file=sys.stderr)
            return 2

    return 0


def _run_graph(parsed: argparse.Namespace) -> int:
    if parsed.gateway_factory and not (
        parsed.instruction_ingress_factory and parsed.anti_skill_gate_factory
    ):
        return _print_refusal(
            Refusal(
                "GRAPH_INSTRUCTION_INGRESS_UNBOUND",
                "live graph gateway lacks an admitted OEWAS plan and anti-skill binding",
                "adversary.cli",
            )
        )
    from pfp.ffi import RustSymbolGameHost

    from ..domain.graph_task import MAX_TASK_BYTES, GraphTaskV1, read_json
    from ..runtime import build_graph_service

    try:
        if parsed.task.stat().st_size > MAX_TASK_BYTES:
            raise ValueError("graph task byte ceiling exceeded")
        task = GraphTaskV1.from_bytes(parsed.task.read_bytes())
        if not parsed.gateway_factory and (parsed.provider or parsed.model):
            raise ValueError("--provider and --model require --gateway-factory")
        if not parsed.gateway_factory and (
            parsed.instruction_ingress_factory or parsed.anti_skill_gate_factory
        ):
            raise ValueError("instruction and anti-skill factories require --gateway-factory")
        if parsed.gateway_factory and not (parsed.provider and parsed.model):
            raise ValueError("--gateway-factory requires explicit --provider and --model")
        host = RustSymbolGameHost(parsed.native_host) if parsed.native_host else None
        live_options = {}
        if parsed.gateway_factory:
            from importlib import import_module

            def load_factory(reference):
                module, separator, name = reference.partition(":")
                if not separator or not module or not name or ":" in name:
                    raise ValueError("factory must be module:function")
                factory = getattr(import_module(module), name)
                if not callable(factory):
                    raise ValueError("configured factory is not callable")
                return factory()

            live_options = {
                "task": task,
                "mode": parsed.mode,
                "instruction_ingress": load_factory(parsed.instruction_ingress_factory),
                "anti_skill_gate": load_factory(parsed.anti_skill_gate_factory),
                "gateway": load_factory(parsed.gateway_factory),
                "provider": parsed.provider,
                "model": parsed.model,
            }
        controller = AdversarySwarmController(
            build_graph_service(parsed.output_dir, host=host, fixture_mode=parsed.fixture,
                                **live_options)
        )
        outcome = controller.run_graph(task, parsed.mode)
    except (ValueError, TypeError, OSError, ImportError, AttributeError, RuntimeError) as exc:
        return _print_refusal(Refusal("GRAPH_INPUT_REFUSED", str(exc), "adversary.cli"))
    if outcome.is_err:
        return _print_refusal(outcome.unwrap_err())
    run = outcome.unwrap()
    result = run.result
    model_turns = [read_json(raw) for raw in result.model_turns]
    model_turns.extend(
        row.get("turn", row) for row in (read_json(raw) for raw in result.challenges)
    )
    model_incomplete = any(
        row.get("status") == "NOT_MEASURED"
        or row.get("validation_outcome") == "NOT_MEASURED"
        for row in model_turns
    )
    model_status = (
        "NOT_REQUESTED" if not model_turns else
        "INCOMPLETE" if model_incomplete else
        "FIXTURE" if parsed.fixture else "COMPLETED"
    )
    selected = next(
        (row for row in result.evaluations if row.candidate_ref == result.selected_candidate_ref),
        None,
    )
    print(
        json.dumps(
            {
                "run_directory": run.directory,
                "receipt_ref": run.receipt_ref,
                "receipt_id": run.receipt_id,
                "original_diagnosis": result.original.measurement.to_dict()
                if result.original.measurement
                else {"status": "NOT_MEASURED", "reason": result.original.reason},
                "selected_repair": {
                    "candidate_ref": selected.candidate_ref,
                    "measurement": selected.measurement.to_dict(),
                    "edit_cost": str(selected.edit_cost),
                }
                if selected
                else None,
                "search_status": result.search_status,
                "search_complete": result.search_complete,
                "optimality_certified": result.optimality_certified,
                "model_dispatch_status": model_status,
                "authority_effect": "None",
            },
            indent=2,
        )
    )
    return 0 if result.original.native_evidence_bytes and not model_incomplete else 2


def _replay_graph(parsed: argparse.Namespace) -> int:
    from pfp.ffi import RustSymbolGameHost

    from ..runtime import replay_graph_run

    try:
        host = RustSymbolGameHost(parsed.native_host) if parsed.native_host else None
        result = replay_graph_run(parsed.run_dir, parsed.receipt_ref, host=host)
    except (ValueError, OSError, RuntimeError) as exc:
        return _print_refusal(Refusal("GRAPH_REPLAY_REFUSED", str(exc), "adversary.cli"))
    if result.is_err:
        return _print_refusal(result.unwrap_err())
    print(json.dumps(result.unwrap().to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
