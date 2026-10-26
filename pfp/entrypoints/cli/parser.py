"""CLI argument declarations with lazy command dispatch. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from functools import partial
from importlib import import_module
from pathlib import Path

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route


def _dispatch(module, command, args):
    if not module.endswith(".demo_commands"):
        from omega_engine_pfp import _initialize_exact_ports

        _initialize_exact_ports()
    return getattr(import_module(module), command)(args)


def register_source_bound_checker_subparser(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    check = sub.add_parser(
        "code-change-check-source-bound",
        help="Check exact patch bytes with a host-pinned finite native checker (offline)",
    )
    check.add_argument("--packet", type=Path, required=True)
    check.add_argument("--patch-bytes", type=Path, required=True)
    check.add_argument("--source-root", type=Path, required=True)
    check.add_argument("--source-path", action="append", required=True)
    check.add_argument("--checker-binary", type=Path, required=True)
    check.add_argument("--checker-sha256", required=True)
    check.add_argument("--run-id", required=True)
    check.add_argument("--attempt-id", required=True)
    check.add_argument("--max-native-calls", type=int, default=3)
    check.add_argument(
        "--output", type=Path, required=True, help="New JSON output; never overwritten"
    )
    check.add_argument(
        "--replay-check", action="store_true", help="Replay within this host run with zero calls"
    )
    check.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_check_source_bound",
        )
    )


def register_code_change_subparsers(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    register_source_bound_checker_subparser(sub)
    cc_create = sub.add_parser(
        "code-change-create-task", help="Build code-change proposal envelope"
    )
    cc_create.add_argument("--payload", type=Path, required=True)
    cc_create.add_argument("--task-id", required=True)
    cc_create.add_argument("--carrier-id", default="omega-code-change-proposal-v1")
    cc_create.add_argument("--step-budget", type=int, default=None)
    cc_create.add_argument("--artifact-dir", type=Path, default=None)
    cc_create.add_argument("--output", type=Path, default=None)
    cc_create.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_create_task",
        )
    )

    cc_attach = sub.add_parser(
        "code-change-attach-candidate", help="Attach code-change patch candidate"
    )
    cc_attach.add_argument("--packet", type=Path, required=True)
    cc_attach.add_argument("--patch-bytes", type=Path, required=True)
    cc_attach.add_argument("--producer-id", required=True)
    cc_attach.add_argument("--base-source-revision", default=None)
    cc_attach.add_argument("--patch-encoding", default="unified-diff")
    cc_attach.add_argument("--touched-path", action="append", default=[], required=True)
    cc_attach.add_argument("--claimed-summary", default=None)
    cc_attach.add_argument("--claimed-terminal", action="store_true", default=False)
    cc_attach.add_argument("--claimed-valid", choices=["true", "false"], default=None)
    cc_attach.add_argument("--artifact-dir", type=Path, default=None)
    cc_attach.add_argument("--output", type=Path, default=None)
    cc_attach.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_attach_candidate",
        )
    )

    cc_eval = sub.add_parser("code-change-evaluate", help="Evaluate code-change candidate")
    cc_eval.add_argument("--packet", type=Path, required=True)
    cc_eval.add_argument("--candidate", type=Path, required=True)
    cc_eval.add_argument("--patch", type=Path, required=True)
    cc_eval.add_argument("--gate-receipt", type=Path, action="append", default=[])
    cc_eval.add_argument("--prior-candidate-count", type=int, default=0)
    cc_eval.add_argument("--operation-count", type=int, default=1)
    cc_eval.add_argument("--artifact-dir", type=Path, default=None)
    cc_eval.add_argument("--output", type=Path, default=None)
    cc_eval.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_evaluate",
        )
    )

    cc_verify = sub.add_parser("code-change-verify-run-root", help="Verify code-change run root")
    cc_verify.add_argument("--run-root", type=Path, required=True)
    cc_verify.add_argument("--output", type=Path, default=None)
    cc_verify.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_verify_run_root",
        )
    )

    cc_run = sub.add_parser(
        "code-change-run-fixture",
        help="Run the whole code-change path once under a trace (deterministic fixture)",
    )
    cc_run.add_argument("--task-id", required=True)
    cc_run.add_argument("--objective", required=True)
    cc_run.add_argument(
        "--patch",
        type=Path,
        required=True,
        help="Patch the scripted provider returns as its reply",
    )
    cc_run.add_argument("--owned-path", action="append", default=[], required=True)
    cc_run.add_argument("--protected-path", action="append", default=[])
    cc_run.add_argument("--base-revision", default="0" * 40)
    cc_run.add_argument("--producer-id", default="fixture-worker")
    cc_run.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for trace, run root, and fixture-only encrypted artifacts",
    )
    cc_run.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_run_fixture",
        )
    )

    cc_render = sub.add_parser(
        "code-change-render-markdown", help="Render Markdown from code-change run root"
    )
    cc_render.add_argument("--run-root", type=Path, required=True)
    cc_render.add_argument("--output", type=Path, default=None)
    cc_render.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.code_change_commands",
            "cmd_code_change_render_markdown",
        )
    )


def register_gate11_subparsers(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    g_self = sub.add_parser("gate11-self", help="Host-verify frozen K0 fixtures")
    g_self.add_argument("--out-dir", type=Path, default=None)
    g_self.set_defaults(
        func=partial(
            _dispatch, "omega_engine_pfp.entrypoints.cli.gate11_commands", "cmd_gate11_self"
        )
    )

    g_ingest = sub.add_parser("gate11-ingest", help="Parse symbolic proposal + host-verify")
    g_ingest.add_argument("reply", help="Path to reply.md")
    g_ingest.add_argument("--out-dir", type=Path, default=None)
    g_ingest.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.gate11_commands",
            "cmd_gate11_ingest",
        )
    )

    g_project = sub.add_parser("gate11-project", help="CochainProjector phi1/gamma2")
    g_project.add_argument("--output", type=Path, default=None)
    g_project.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.gate11_commands",
            "cmd_gate11_project",
        )
    )


def register_glyph_subparsers(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    verify = sub.add_parser(
        "verify-glyph-reply",
        help="Run the glyph-calculus host check over a packet and emit its receipt",
    )
    verify.add_argument("--packet", required=True, help="Path to the packet JSON")
    verify.add_argument(
        "--presentations",
        help=(
            "Path to the rewrite presentations THIS HOST pins (see "
            "omega_engine_governance/contracts/pinned/"
            "symbol_game_presentations.json). A packet's presentation_ref is "
            "resolved against this file and nothing else; without it, every row "
            "about a presentation is UNCHECKABLE."
        ),
    )
    verify.add_argument(
        "--carrier",
        help=(
            "Path to the carrier THIS HOST pins (see "
            "omega_engine_governance/contracts/pinned/symbol_game_carrier.json). "
            "Without it the packet's own carrier is used and the run tops out "
            "at SELF_CONSISTENT_ONLY."
        ),
    )
    verify.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.glyph_commands",
            "cmd_verify_glyph_reply",
        )
    )


def register_prompt_subparsers(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    compile_p = sub.add_parser(
        "compile-prompt", help="Compile a content-addressed PromptArtifactV1"
    )
    compile_p.add_argument("--regime-bytes", type=Path, required=True)
    compile_p.add_argument(
        "--regime-kind",
        required=True,
        choices=[
            "branch_u_undecidable",
            "branch_o_observational",
            "branch_q_opaque_normalizer",
            "fence_only",
            "code_change",
            "research_claim",
            "custom_bound",
            "coda_l1",
            "coda_regge_mc_4d",
            "symbol_only",
            "finite_library",
        ],
    )
    compile_p.add_argument("--prompt-body-bytes", type=Path, default=None)
    compile_p.add_argument("--objective-json", type=Path, default=None)
    compile_p.add_argument("--objective-kind", default="prompt_turn")
    compile_p.add_argument("--objective-summary", default="structured prompt turn")
    compile_p.add_argument("--target-obstruction-ids", default="")
    compile_p.add_argument("--target-demand-ids", default="")
    compile_p.add_argument("--admitted-constructors", default="")
    compile_p.add_argument("--kill-conditions", default="F-01_inherited_meaning")
    compile_p.add_argument("--required-reply-fields", default="")
    compile_p.add_argument("--obstructions-json", type=Path, default=None)
    compile_p.add_argument("--demands-json", type=Path, default=None)
    compile_p.add_argument("--residual-colour", default="Open", choices=["Open", "Closed", "Exact"])
    compile_p.add_argument("--dual-witness-required", default=None, choices=["true", "false"])
    compile_p.add_argument("--dual-witness-ref", default=None)
    compile_p.add_argument("--parent-packet-id", default=None)
    compile_p.add_argument("--conversation-root-id", default=None)
    compile_p.add_argument("--artifact-dir", type=Path, default=None)
    compile_p.add_argument("--output", type=Path, default=None)
    compile_p.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.prompt_commands",
            "cmd_compile_prompt",
        )
    )

    verify_p = sub.add_parser("verify-prompt", help="Strictly verify a PromptArtifactV1")
    verify_p.add_argument("--artifact", type=Path, required=True)
    verify_p.add_argument("--prompt-body-bytes", type=Path, default=None)
    verify_p.add_argument("--output", type=Path, default=None)
    verify_p.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.prompt_commands",
            "cmd_verify_prompt",
        )
    )

    create_from_p = sub.add_parser(
        "create-task-from-prompt", help="Build envelope bound to PromptArtifactV1"
    )
    create_from_p.add_argument("--artifact", type=Path, required=True)
    create_from_p.add_argument("--task-id", required=True)
    create_from_p.add_argument("--carrier-id", default="omega-llm-turn-v1")
    create_from_p.add_argument(
        "--role", default="user", choices=["user", "assistant", "system", "tool"]
    )
    create_from_p.add_argument(
        "--turn-kind",
        default="prose",
        choices=["prose", "code_change", "claimed_result", "tool_result", "status"],
    )
    create_from_p.add_argument("--candidate-budget", type=int, default=3)
    create_from_p.add_argument("--operation-budget", type=int, default=20)
    create_from_p.add_argument("--step-budget", type=int, default=None)
    create_from_p.add_argument("--artifact-dir", type=Path, default=None)
    create_from_p.add_argument("--output", type=Path, default=None)
    create_from_p.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.prompt_commands",
            "cmd_create_task_from_prompt",
        )
    )


def register_run_subparsers(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    for cmd_name in ("run-turn", "run-bout", "run"):
        run_p = sub.add_parser(cmd_name, help="Execute a Symbol Game turn / bout from prompt")
        run_p.add_argument("--prompt", default="", help="Prompt text for the symbol game turn")
        run_p.add_argument(
            "--prompt-file", type=Path, default=None, help="File containing prompt text"
        )
        run_p.add_argument("--task-id", default=None, help="Task identifier")
        run_p.add_argument("--objective", default=None, help="Objective summary")
        run_p.add_argument(
            "--role", default="user", choices=["user", "assistant", "system", "tool"]
        )
        run_p.add_argument(
            "--producer-id", default="symbol_game_agent_v1", help="Candidate producer ID"
        )
        run_p.add_argument("--candidate-budget", type=int, default=3)
        run_p.add_argument("--operation-budget", type=int, default=20)
        run_p.add_argument("--max-steps", type=int, default=4, help="Max reduction steps")
        run_p.add_argument("--carrier-id", default="omega-symbol-game-v1")
        run_p.add_argument("--output-dir", type=Path, default=Path(canonical_intelligence_route("_intelligence/symbol_game")))
        run_p.add_argument("--output", type=Path, default=None)
        run_p.set_defaults(
            func=partial(
                _dispatch, "omega_engine_pfp.entrypoints.cli.run_commands", "cmd_run_turn"
            )
        )


def register_turn_subparsers(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    create = sub.add_parser("create-task", help="Build a PacketEnvelopeV2 llm-turn packet")
    create.add_argument("--payload", type=Path, default=None)
    create.add_argument("--content-bytes", type=Path, default=None)
    create.add_argument("--objective", default="Complete the bounded task")
    create.add_argument("--role", default="user", choices=["user", "assistant", "system", "tool"])
    create.add_argument(
        "--turn-kind",
        default="prose",
        choices=["prose", "code_change", "claimed_result", "tool_result", "status"],
    )
    create.add_argument("--candidate-budget", type=int, default=3)
    create.add_argument("--operation-budget", type=int, default=20)
    create.add_argument("--parent-packet-id", default=None)
    create.add_argument("--conversation-root-id", default=None)
    create.add_argument("--task-id", required=True)
    create.add_argument("--carrier-id", default="omega-llm-turn-v1")
    create.add_argument("--step-budget", type=int, default=None)
    create.add_argument("--artifact-dir", type=Path, default=None)
    create.add_argument("--output", type=Path, default=None)
    create.set_defaults(
        func=partial(
            _dispatch, "omega_engine_pfp.entrypoints.cli.turn_commands", "cmd_create_task"
        )
    )

    attach = sub.add_parser("attach-candidate", help="Attach a candidate turn reply")
    attach.add_argument("--packet", type=Path, required=True)
    attach.add_argument("--content-bytes", type=Path, required=True)
    attach.add_argument("--producer-id", required=True)
    attach.add_argument("--content-encoding", default="utf-8")
    attach.add_argument("--content-sha256", default=None)
    attach.add_argument("--claimed-summary", default=None)
    attach.add_argument("--claimed-terminal", action="store_true", default=False)
    attach.add_argument("--claimed-valid", choices=["true", "false"], default=None)
    attach.add_argument("--artifact-dir", type=Path, default=None)
    attach.add_argument("--output", type=Path, default=None)
    attach.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.turn_commands",
            "cmd_attach_candidate",
        )
    )

    evaluate = sub.add_parser("evaluate", help="Independently evaluate turn candidate")
    evaluate.add_argument("--packet", type=Path, required=True)
    evaluate.add_argument("--candidate", type=Path, required=True)
    evaluate.add_argument("--content", type=Path, default=None)
    evaluate.add_argument("--content-bytes", type=Path, default=None)
    evaluate.add_argument("--reply-text", type=Path, default=None)
    evaluate.add_argument("--prior-candidate-count", type=int, default=0)
    evaluate.add_argument("--operation-count", type=int, default=1)
    evaluate.add_argument("--artifact-dir", type=Path, default=None)
    evaluate.add_argument("--output", type=Path, default=None)
    evaluate.set_defaults(
        func=partial(
            _dispatch, "omega_engine_pfp.entrypoints.cli.turn_commands", "cmd_evaluate"
        )
    )

    verify = sub.add_parser("verify-run-root", help="Strictly reparse a run root")
    verify.add_argument("--run-root", type=Path, required=True)
    verify.add_argument("--output", type=Path, default=None)
    verify.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.turn_commands",
            "cmd_verify_run_root",
        )
    )

    render = sub.add_parser("render-markdown", help="Render Markdown from a run root")
    render.add_argument("--run-root", type=Path, required=True)
    render.add_argument("--output", type=Path, default=None)
    render.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.turn_commands",
            "cmd_render_markdown",
        )
    )


def register_workbench_subparsers(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    search = sub.add_parser(
        "search-gauge",
        help="Stream exact finite signed-graph gauge candidates as JSONL",
    )
    search.add_argument(
        "--input-file", type=Path, help="Typed YAML input packet; no per-run script"
    )
    search.add_argument("--fixture", default=None)
    search.add_argument("--list-fixtures", action="store_true")
    search.add_argument("--node-budget", type=int, default=None)
    search.add_argument("--pace-ms", type=int, default=None)
    search.add_argument("--output-dir", type=Path)
    search.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.workbench_commands",
            "cmd_search_gauge",
        )
    )

    serve = sub.add_parser("serve", help="Serve the local FastAPI workbench")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.workbench_commands",
            "cmd_serve_workbench",
        )
    )


def register_demo_subparsers(sub):
    demo = sub.add_parser("demo", help="List, run, and verify installed offline MSS-N demos")
    commands = demo.add_subparsers(dest="demo_command", required=True)
    listing = commands.add_parser("list", help="List the complete scenario catalog")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(
        func=partial(
            _dispatch, "omega_engine_pfp.entrypoints.cli.demo_commands", "cmd_list"
        )
    )
    run = commands.add_parser("run", help="Run into a fresh output directory")
    run.add_argument("scenario_id")
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument(
        "--live", action="store_true",
        help="Requires explicit model, output/call/cost bounds and provider credentials"
    )
    run.add_argument("--model", default=None)
    run.add_argument("--max-output-tokens", type=int)
    run.add_argument("--max-provider-calls", type=int)
    policy = run.add_mutually_exclusive_group()
    policy.add_argument("--max-estimated-cost-microusd", type=int)
    policy.add_argument("--max-cost-microusd", type=int)
    run.add_argument("--env-file", type=Path)
    run.set_defaults(
        func=partial(_dispatch, "omega_engine_pfp.entrypoints.cli.demo_commands", "cmd_run")
    )
    verify = commands.add_parser(
        "verify", help="Replay fixture receipts; integrity-check live receipts"
    )
    verify.add_argument("receipt", type=Path)
    verify.set_defaults(
        func=partial(
            _dispatch, "omega_engine_pfp.entrypoints.cli.demo_commands", "cmd_verify"
        )
    )


def register_challenge_subparsers(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    challenge = sub.add_parser("challenge", help="Challenge packet runner and commit-reveal suite")
    commands = challenge.add_subparsers(dest="challenge_command", required=True)

    # build
    build = commands.add_parser("build", help="Build participant and judge packets")
    build.add_argument("--challenge-id", required=True)
    build.add_argument("--spec", type=Path, required=True)
    build.add_argument("--public-cases", type=Path, required=True)
    build.add_argument("--hidden-cases", type=Path, required=True)
    build.add_argument("--checker-a", default="checker_exact_match_a")
    build.add_argument("--checker-b", default="checker_exact_match_b")
    build.add_argument("--output-dir", type=Path, default=Path("."))
    build.add_argument("--timeout-ms", type=int, default=5000)
    build.add_argument("--max-tokens", type=int, default=4096)
    build.add_argument("--operator", default="operator_alpha")
    build.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.challenge_commands",
            "cmd_challenge_build",
        )
    )

    # commit
    commit = commands.add_parser("commit", help="Commit judge hidden manifest before release")
    commit.add_argument("--challenge-id", required=True)
    commit.add_argument("--manifest", type=Path, required=True)
    commit.add_argument("--operator", default="operator_alpha")
    commit.add_argument("--version", default="v1.0.0")
    commit.add_argument("--output", type=Path, default=None)
    commit.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.challenge_commands",
            "cmd_challenge_commit",
        )
    )

    # freeze
    freeze = commands.add_parser("freeze", help="Freeze solver deliverable before reveal")
    freeze.add_argument("--challenge-id", required=True)
    freeze.add_argument("--deliverable", type=Path, required=True)
    freeze.add_argument("--commitment", type=Path, default=None)
    freeze.add_argument("--commitment-hash", default=None)
    freeze.add_argument("--output", type=Path, default=None)
    freeze.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.challenge_commands",
            "cmd_challenge_freeze",
        )
    )

    # score
    score = commands.add_parser("score", help="Execute challenge scoring with dual checkers")
    score.add_argument("--judge-packet", type=Path, required=True)
    score.add_argument("--commitment", type=Path, required=True)
    score.add_argument("--freeze", type=Path, required=True)
    score.add_argument("--deliverable", type=Path, required=True)
    score.add_argument("--output", type=Path, default=None)
    score.add_argument("--simulate-checker-fault", action="store_true", default=False)
    score.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.challenge_commands",
            "cmd_challenge_score",
        )
    )

    # status
    status = commands.add_parser("status", help="Report status of a challenge receipt")
    status.add_argument("--receipt", type=Path, required=True)
    status.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.challenge_commands",
            "cmd_challenge_status",
        )
    )

    # run-arms
    run_arms = commands.add_parser(
        "run-arms", help="Run matched arms comparison and exact McNemar test"
    )
    run_arms.add_argument("--arms-spec", type=Path, required=True)
    run_arms.add_argument("--outcomes", type=Path, default=None)
    run_arms.add_argument("--output", type=Path, default=None)
    run_arms.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.challenge_commands",
            "cmd_challenge_run_arms",
        )
    )


def _add_swarm_developer_commands(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    p_run = sub.add_parser("run-swarm", help="Run full composite developer swarm turn")
    p_run.add_argument("--contract", required=True, help="Path to SwarmTaskContractV1 (JSON/YAML)")
    p_run.add_argument(
        "--audit-profile",
        choices=["software", "mathematics", "natural_science", "paper_release", "formal_proof"],
        default=None,
        help="Audit profile override",
    )
    p_run.add_argument("--output-dir", default=None, help="Directory to emit evidence envelope and quad bundle")
    p_run.add_argument("--skip-harvest", action="store_true", help="Skip pre-clean harvest gate")
    p_run.add_argument("--max-rounds", type=int, default=3, help="Maximum repair rounds (default: 3)")
    p_run.add_argument("--auto-repair", action="store_true", help="Enable autonomous repair loop")
    p_run.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.swarm_developer",
            "cmd_run_swarm",
        )
    )

    p_audit = sub.add_parser("fireproof-audit", help="Run standalone Old Man fireproof audit")
    p_audit.add_argument("--contract", default=None, help="Path to SwarmTaskContractV1 to audit declared target paths")
    p_audit.add_argument("--patch", default=None, help="Candidate patch or directory to audit")
    p_audit.add_argument("--target", default=None, help="Target file or directory to audit")
    p_audit.add_argument(
        "--profile",
        choices=["software", "mathematics", "natural_science", "paper_release", "formal_proof"],
        default="software",
        help="Audit profile",
    )
    p_audit.add_argument("--report-out", default=None, help="Path to emit JSONL findings")
    p_audit.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.swarm_developer",
            "cmd_fireproof_audit",
        )
    )

    p_val = sub.add_parser("validate-contract", help="Validate SwarmTaskContractV1 schema and governance")
    p_val.add_argument("--contract", required=True, help="Path to contract file")
    p_val.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.swarm_developer",
            "cmd_validate_contract",
        )
    )


def register_swarm_developer_subparsers(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    _add_swarm_developer_commands(sub)

    # Grouped subparser: symbol-game swarm-developer <subcommand>
    sd_parser = sub.add_parser(
        "swarm-developer",
        help="Composite Swarm Developer SPOE entrypoint",
    )
    sd_sub = sd_parser.add_subparsers(dest="swarm_command", required=True)
    _add_swarm_developer_commands(sd_sub)


def register_mode_subparsers(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    mode_parser = sub.add_parser("mode", help="Discover, list, and validate operational mode contracts")
    commands = mode_parser.add_subparsers(dest="mode_command", required=True)

    listing = commands.add_parser("list", help="List all canonical operational modes from modes_manifest.yaml")
    listing.add_argument("--json", action="store_true", help="Output JSON format")
    listing.add_argument("--cluster", default=None, help="Filter by cluster name")
    listing.add_argument("--modes-dir", type=Path, default=None, help="Explicit modes directory override")
    listing.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.mode_commands",
            "cmd_mode_list",
        )
    )

    show = commands.add_parser("show", help="Show deep operational specification for a mode")
    show.add_argument("mode_id", type=int, help="Mode integer ID (1-20)")
    show.add_argument("--json", action="store_true", help="Output JSON format")
    show.add_argument("--modes-dir", type=Path, default=None, help="Explicit modes directory override")
    show.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.mode_commands",
            "cmd_mode_show",
        )
    )

    validate = commands.add_parser("validate", help="Validate dynamic discovery and catalog closure")
    validate.add_argument("--json", action="store_true", help="Output JSON format")
    validate.add_argument("--modes-dir", type=Path, default=None, help="Explicit modes directory override")
    validate.set_defaults(
        func=partial(
            _dispatch,
            "omega_engine_pfp.entrypoints.cli.mode_commands",
            "cmd_mode_validate",
        )
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="symbol-game", description="Symbol Game commands and offline MSS-N demo catalog"
    )
    sub = parser.add_subparsers(dest="command", required=False)
    register_code_change_subparsers(sub)
    register_gate11_subparsers(sub)
    register_glyph_subparsers(sub)
    register_prompt_subparsers(sub)
    register_run_subparsers(sub)
    register_turn_subparsers(sub)
    register_workbench_subparsers(sub)
    register_demo_subparsers(sub)
    register_challenge_subparsers(sub)
    register_swarm_developer_subparsers(sub)
    register_mode_subparsers(sub)
    from .level_engine_commands import register as register_level_engine
    register_level_engine(sub)
    return parser

