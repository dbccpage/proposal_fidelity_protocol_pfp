"""Command-line interface for the Proposal Fidelity Protocol (PFP).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

from ...controllers.pfp_controller import PfpController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pfp",
        description="Proposal Fidelity Protocol (PFP) Clean Architecture CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. run-demo
    demo_p = subparsers.add_parser("run-demo", help="Execute a PFP demo by ID")
    demo_p.add_argument(
        "demo_id", help="Demo identifier (e.g. demo_000, demo_003, demo_004, demo_sn_000)"
    )

    # 2. verify-contracts
    subparsers.add_parser(
        "verify-contracts",
        help="Request semantic verification (refuses without candidate-bound checking)",
    )

    # 3. evaluate-gates
    gate_p = subparsers.add_parser("evaluate-gates", help="Evaluate Adversary Tribunal gates")
    gate_p.add_argument("--candidate-id", default="candidate_cli", help="Candidate identifier")
    gate_p.add_argument("--state-json", help="Path to JSON file containing candidate attestations")

    # 4. assemble
    asm_p = subparsers.add_parser("assemble", help="Assemble a prompt packet")
    asm_p.add_argument("--demo-id", default="demo_000", help="Demo ID")
    asm_p.add_argument("--stage", type=int, default=1, help="Stage index (0-8)")
    asm_p.add_argument("--seed-json", help="Path to JSON file containing seed prompt data")
    asm_p.add_argument(
        "--json", action="store_true", help="Print the full PromptPacket, including system, user and response schema"
    )

    # 5. run-pilot-suite
    suite_p = subparsers.add_parser("run-pilot-suite", help="Execute a multi-test pilot suite")
    suite_p.add_argument(
        "--pilot-dir",
        default="pfp/tests/pilot_0000000",
        help="Path to pilot directory",
    )
    suite_p.add_argument(
        "--model", help="Explicit OpenRouter model ID; required for live execution"
    )
    suite_p.add_argument("--output-dir", required=True, type=Path, help="Fresh output directory")
    suite_p.add_argument("--max-cases", type=int, default=5)
    suite_p.add_argument("--max-provider-calls", type=int, default=5)
    suite_p.add_argument("--max-output-tokens", type=int, default=512)
    suite_p.add_argument("--max-estimated-cost-microusd", type=int)
    suite_p.add_argument("--env-file", type=Path)
    suite_p.add_argument(
        "--dry-run", action="store_true", help="Host reference fixture; zero provider calls"
    )

    seed_p = subparsers.add_parser(
        "run-seed", help="Execute a catalog seed through numbered PFP stages"
    )
    seed_p.add_argument("seed_id")
    seed_p.add_argument("--stages", type=int, default=5, choices=range(1, 12))
    seed_p.add_argument("--modes", type=int, nargs="*", default=[])
    seed_p.add_argument("--mode-inputs", type=Path, help="JSON object with inputs keyed by mode ID")
    seed_p.add_argument("--model", help="Explicit OpenRouter model; omission uses offline fixtures")
    seed_p.add_argument(
        "--timeout", type=float, default=60.0, help="Provider HTTP timeout in seconds"
    )
    seed_p.add_argument("--output", type=Path, help="New live output directory")
    seed_p.add_argument("--replay", type=Path, help="Replay saved run with zero provider calls")
    seed_p.add_argument("--max-provider-calls", type=int, help="Explicit live call limit (1-8)")
    seed_p.add_argument("--max-output-tokens", type=int, help="Explicit live output token limit (1-3000)")
    seed_budget = seed_p.add_mutually_exclusive_group()
    seed_budget.add_argument("--max-cost-microusd", type=int, help="Hard financial limit; requires transport liability support")
    seed_budget.add_argument("--max-estimated-cost-microusd", type=int, help="Estimated financial limit; not a hard provider liability cap")
    seed_p.add_argument("--env-file", type=Path)

    check_p = subparsers.add_parser(
        "check-seed", help="Independently check a seed witness JSON file"
    )
    check_p.add_argument("seed_id")
    check_p.add_argument("candidate", type=Path)

    prepare_task = subparsers.add_parser("prepare-task", help="Prepare one typed task turn offline")
    prepare_task.add_argument("task", type=Path)
    prepare_task.add_argument("--attempt", required=True)
    check_task = subparsers.add_parser("check-task", help="Check actual task reply bytes offline")
    check_task.add_argument("task", type=Path)
    check_task.add_argument("reply", type=Path)
    check_task.add_argument("--attempt", required=True)

    from .parser import register_source_bound_checker_subparser

    register_source_bound_checker_subparser(subparsers)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "code-change-check-source-bound":
        return args.func(args)
    if args.command in ("run-seed", "check-seed"):
        return _seed_command(args, parser)
    if args.command in ("prepare-task", "check-task"):
        return _task_command(args)
    controller = PfpController()

    if args.command == "run-demo":
        res = controller.run_demo(args.demo_id)
        if res.is_ok:
            receipt = res.unwrap()
            label = "PASS" if receipt.all_passed else "FAIL"
            print(
                f"{label}: Demo {receipt.demo_id} executed with terminal status {receipt.terminal_status} (all_passed={receipt.all_passed})"
            )
            print(f"Receipt SHA256: {receipt.receipt_sha256}")
            for check in receipt.checks:
                if not check.passed:
                    detail = check.error_message or check.observed or "Check did not pass"
                    print(f"  {check.name}: {detail}")
            return 0 if receipt.all_passed else 2
        else:
            err = res.unwrap_err()
            print(
                f"FAIL: Demo {args.demo_id} failed: {err.message} (code: {err.code})",
                file=sys.stderr,
            )
            return 1

    elif args.command == "verify-contracts":
        res = controller.verify_normal_forms()
        if res.is_ok:
            receipts = res.unwrap()
            print(f"PASS: Received {len(receipts)} normal-form verification receipts.")
            return 0
        else:
            err = res.unwrap_err()
            print(f"REFUSED: {err.code.value}: {err.message}", file=sys.stderr)
            print(
                "For structural catalog checks only, run: python -m "
                "pfp.entrypoints.cli.pfp_normal_forms audit-contracts",
                file=sys.stderr,
            )
            return 1

    elif args.command == "evaluate-gates":
        state = {}
        if args.state_json:
            with open(args.state_json, "r", encoding="utf-8") as f:
                state = json.load(f)
        res = controller.evaluate_gates(args.candidate_id, state)
        if res.is_ok:
            receipt = res.unwrap()
            print(f"Status: {receipt.terminal_disposition} (all_passed={receipt.all_passed})")
            print(f"Receipt SHA256: {receipt.receipt_sha256}")
            return 0 if receipt.all_passed else 2
        else:
            err = res.unwrap_err()
            print(f"FAIL: Gate evaluation failed: {err.message}", file=sys.stderr)
            return 1

    elif args.command == "assemble":
        seed = {}
        if args.seed_json:
            with open(args.seed_json, "r", encoding="utf-8") as f:
                seed = json.load(f)
        res = controller.assemble_prompt(args.demo_id, args.stage, seed)
        if res.is_ok:
            packet = res.unwrap()
            if args.json:
                print(json.dumps(packet.model_dump(mode="json"), ensure_ascii=True))
            else:
                print(f"PASS: Assembled prompt for {packet.demo_id}, stage {packet.stage}")
                print(f"System SHA256: {packet.system_sha256}")
                print(f"User SHA256: {packet.user_sha256}")
                print(f"Schema SHA256: {packet.schema_sha256}")
            return 0
        else:
            err = res.unwrap_err()
            print(f"FAIL: Assembly failed: {err.message}", file=sys.stderr)
            return 1

    elif args.command == "run-pilot-suite":
        res = controller.run_pilot_suite(
            args.pilot_dir,
            model=args.model,
            output_dir=args.output_dir,
            max_cases=args.max_cases,
            max_provider_calls=args.max_provider_calls,
            max_output_tokens=args.max_output_tokens,
            max_estimated_cost_microusd=args.max_estimated_cost_microusd,
            env_file=args.env_file,
            dry_run=args.dry_run,
        )
        if res.is_ok:
            summary = res.unwrap()
            print(json.dumps(summary, sort_keys=True))
            all_accepted = not summary["stop_reason"] and all(
                row["is_correct"] for row in summary["tests"]
            )
            return 0 if all_accepted else 2
        else:
            err = res.unwrap_err()
            print(f"FAIL: Pilot suite failed: {err.message}", file=sys.stderr)
            return 1

    return 0


def _task_command(args) -> int:
    from ...domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
    from ...domain.pfp_ingress import strict_json
    from ...use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
    from ...use_cases.pfp_proposal import CheckPfpTaskTurnUseCase

    try:
        data = strict_json(args.task.read_bytes().decode("utf-8"))
        required = {"task_id", "objective", "input", "answer_schema"}
        optional = {"checker_required", "allowed_operations", "stopping_bounds"}
        if (type(data) is not dict or not required <= set(data)
                or set(data) - required - optional
                or type(data["objective"]) is not str
                or not data["objective"].strip()
                or type(data.get("checker_required", False)) is not bool):
            raise ValueError("INVALID_TASK_SPECIFICATION")
        objective = data["objective"]
        constraints = {key: data[key] for key in ("allowed_operations", "stopping_bounds") if key in data}
        if constraints:
            objective += "\nDeclared task limits: " + json.dumps(constraints, sort_keys=True)
        task = PfpTaskPrompt(data["task_id"], objective, data["input"], data["answer_schema"])
        template = PfpPromptTemplate(
            "Complete the supplied task within its declared operations and limits.",
            "[USER PROMPT]", {},
        )
        prompt = PreparePfpTaskTurnUseCase().execute(template, task, args.attempt)
        if args.command == "prepare-task":
            print(json.dumps(prompt.to_dict(), ensure_ascii=True, sort_keys=True))
            return 0
        result = CheckPfpTaskTurnUseCase().execute(
            task, prompt, args.reply.read_bytes(),
            require_checker=data.get("checker_required", False),
        )
        result["provider_calls"] = 0
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0 if result["schema_valid"] and result["status"] == "PROVIDER_COMPLETED" else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REFUSED", reason=str(exc), provider_calls=0,
                              authority_effect="None")))
        return 2


def _seed_command(args, parser) -> int:
    from dataclasses import asdict
    from hashlib import sha256
    from uuid import uuid4

    from pfp.infrastructure.pilot_runners.mssn_checks import evaluate_seed_response
    from pfp.infrastructure.pilot_runners.seed_checks import seed_candidate_schema

    from ...infrastructure.pilot_runner import load_seed_catalog
    from ...infrastructure.providers import OfflineDeterministicPfpProvider, SeedHostVerifier
    from ...infrastructure.storage import PfpFileSystemStorageAdapter
    from ...use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase
    from adversary.domain.providers.types import ProviderConfigError

    provider = None
    try:
        catalog = load_seed_catalog()
        seed = catalog.get_by_id(args.seed_id)
        if seed is None:
            raise ValueError("UNKNOWN_SEED")
        if args.command == "check-seed":
            result = evaluate_seed_response(args.seed_id, json.loads(args.candidate.read_bytes()))
            print(json.dumps(result.to_dict(), sort_keys=True))
            return 0 if result.passed else 2
        live_options = (args.max_provider_calls, args.max_output_tokens, args.max_cost_microusd,
                        args.max_estimated_cost_microusd, args.env_file)
        if args.replay and (args.model or args.output or any(value is not None for value in live_options)):
            parser.error("--replay cannot dispatch a model or create another output")
        if not args.model and not args.replay and (args.output or any(value is not None for value in live_options)):
            parser.error("Live output and financial options require --model")
        if not 0 < args.timeout <= 300:
            raise ValueError("INVALID_PROVIDER_TIMEOUT")
        provider = OfflineDeterministicPfpProvider()
        config = dict(
            seed_id=seed.id,
            seed_sha256=seed.seed_sha256,
            stages=args.stages,
            modes=args.modes,
            model=args.model,
        )
        config["mode_inputs"] = (
            json.loads(args.mode_inputs.read_bytes()) if args.mode_inputs else {}
        )
        if args.model or args.replay:
            from ...infrastructure.adapters.pfp_campaign import (
                PfpPipelineProviderAdapter,
                write_new,
            )

            output = args.replay or args.output
            if output is None:
                parser.error("Live numbered stages require --output with a new directory")
            if args.replay:
                recorded = json.loads((output / "config.json").read_bytes())
                if recorded["seed_id"] != seed.id or recorded["seed_sha256"] != seed.seed_sha256:
                    raise ValueError("REPLAY_SEED_MISMATCH")
                config = recorded
                provider = PfpPipelineProviderAdapter(output, config["model"], replay=True)
            else:
                from ...infrastructure.estimated_gateway import create_accounted_openrouter_gateway

                if args.max_provider_calls is None or not 1 <= args.max_provider_calls <= 8:
                    raise ValueError("LIVE_STAGE_CALL_LIMIT_REQUIRED_1_TO_8")
                if args.max_output_tokens is None or not 1 <= args.max_output_tokens <= 3000:
                    raise ValueError("LIVE_OUTPUT_TOKEN_LIMIT_REQUIRED_1_TO_3000")
                cap = args.max_cost_microusd if args.max_cost_microusd is not None else args.max_estimated_cost_microusd
                if cap is None or not 0 < cap <= 50000:
                    raise ValueError("LIVE_FINANCIAL_LIMIT_REQUIRED_1_TO_50000")
                accounting = output.with_name(output.name + ".budget.sqlite3")
                if output.exists() or accounting.exists() or accounting.with_name(accounting.name + ".replies").exists():
                    raise ValueError("LIVE_OUTPUT_AND_ACCOUNTING_MUST_BE_NEW")
                config.update(schema="pfp.numbered-seed-config.v2", timeout=args.timeout,
                    max_provider_calls=args.max_provider_calls, max_output_tokens=args.max_output_tokens,
                    max_cost_microusd=args.max_cost_microusd,
                    max_estimated_cost_microusd=args.max_estimated_cost_microusd)
                objective_sha256 = sha256(json.dumps(config, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
                config.update(run_id=uuid4().hex, objective_sha256=objective_sha256)
                gateway = create_accounted_openrouter_gateway(args.model, args.max_output_tokens,
                    env_file=args.env_file, timeout=args.timeout,
                    max_cost_microusd=args.max_cost_microusd,
                    max_estimated_cost_microusd=args.max_estimated_cost_microusd,
                    max_calls=args.max_provider_calls, accounting_path=accounting,
                    run_id=config["run_id"], objective_sha256=objective_sha256)
                provider = PfpPipelineProviderAdapter(output, args.model, gateway=gateway)
                write_new(output / "config.json", config)
        verifier = SeedHostVerifier()
        use_case = ExecuteStagePipelineUseCase(
            PfpFileSystemStorageAdapter(),
            provider,
            catalog=SimpleNamespace(get_demo=catalog.get_by_id),
            host_verifier=verifier,
        )
        result = use_case.run_pipeline(
            seed.id,
            dict(seed_prompt=seed.seed, seed_sha256=seed.seed_sha256),
            stage_count=config["stages"],
            modes=tuple(config["modes"]),
            candidate_schema=seed_candidate_schema(seed.id),
            mode_inputs={int(key): value for key, value in config["mode_inputs"].items()},
        )
        if result.is_err:
            failure = result.unwrap_err()
            data = dict(status="REFUSED", code=str(failure.code), reason=failure.message)
        else:
            data = asdict(result.unwrap())
        data.update(
            provider_calls=getattr(provider, "provider_calls", 0),
            cost_microusd=getattr(provider, "cost_microusd", 0),
            authority_effect="None",
            host_checks=verifier.evaluations,
        )
        print(json.dumps(data, sort_keys=True, default=str))
        if result.is_err:
            return 2
        receipt = result.unwrap()
        completed = receipt.completed_stages == tuple(range(1, config["stages"] + 1))
        # Stage 1 is a host record; its status is the admission, whatever a repair turn proposed.
        admission = receipt.stage_responses.get(1, {})
        host = receipt.stage_responses.get(5, {})
        host_passed = config["stages"] < 5 or (
            host.get("host_verdict") == "PASS" and host.get("exact_checks_passed") is True
        )
        # Expected negative controls are successful checks of refusal behavior.
        # Their raw passed=False entries are not a failed candidate admission.
        return 0 if completed and admission.get("status") == "admit" and host_passed else 2
    except (OSError, ValueError, KeyError, TypeError, ProviderConfigError) as exc:
        print(json.dumps(dict(status="REFUSED", reason=str(exc), authority_effect="None",
            provider_calls=getattr(provider, "provider_calls", 0),
            cost_microusd=getattr(provider, "cost_microusd", 0))))
        return 2


if __name__ == "__main__":
    sys.exit(main())
