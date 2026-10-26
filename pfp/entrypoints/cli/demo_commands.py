"""Thin demo CLI: package composition and JSON presentation only."""

import json
from dataclasses import asdict


def cmd_list(args):
    from omega_engine_pfp.infrastructure.demos.catalog import scenarios

    rows = [asdict(s) for s in scenarios()]
    if args.json:
        print(json.dumps(rows, sort_keys=True))
    else:
        for row in rows:
            print(f"{row['scenario_id']:<30} {row['title']}")
    return 0


def cmd_run(args):
    from omega_engine_pfp.infrastructure.demos.execution import run

    receipt = run(
        args.scenario_id,
        args.output_dir,
        live=args.live,
        model=args.model,
        max_output_tokens=args.max_output_tokens,
        max_provider_calls=args.max_provider_calls,
        max_cost_microusd=args.max_cost_microusd,
        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
        env_file=args.env_file,
    )
    print(
        json.dumps(
            {
                "scenario_id": args.scenario_id,
                "receipt": str(args.output_dir.resolve() / "receipt.json"),
                "result": receipt["result"]["status"],
                "AuthorityEffect": "None",
            },
            sort_keys=True,
        )
    )
    return 1 if receipt["result"]["status"] in {"FAILED", "TYPED_REFUSAL"} else 0


def cmd_verify(args):
    from omega_engine_pfp.infrastructure.demos.execution import verify

    print(json.dumps(verify(args.receipt), sort_keys=True))
    return 0
