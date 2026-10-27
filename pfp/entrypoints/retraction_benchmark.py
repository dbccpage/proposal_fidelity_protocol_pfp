"""Bounded current Paper 008 graph benchmark and zero-send replay."""

import argparse
import json
from pathlib import Path

from pfp.infrastructure.retraction_benchmark import (
    CONDITIONS,
    DEFAULT_MODEL,
    replay_outputs,
    run_conditions,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=["hinted"])
    parser.add_argument("--tasks", nargs="+")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--max-output-tokens", type=int, default=128)
    parser.add_argument("--max-provider-calls", type=int)
    parser.add_argument("--max-estimated-cost-microusd", type=int)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    if args.replay and (args.live or args.output_dir or args.model or args.env_file):
        parser.error("--replay cannot be combined with new execution settings")
    if not args.replay and args.output_dir is None:
        parser.error("new runs require a fresh --output-dir")
    if args.live and (not args.model or args.max_provider_calls is None
                     or args.max_estimated_cost_microusd is None):
        parser.error("--live requires explicit --model, --max-provider-calls and --max-estimated-cost-microusd")
    if not args.live and args.model:
        parser.error("--model requires --live; offline uses the labelled deterministic stub")
    try:
        if args.replay:
            report = replay_outputs(args.replay)
        else:
            run_conditions(args.conditions, model=args.model or DEFAULT_MODEL, live=args.live,
                output_dir=args.output_dir, task_ids=args.tasks,
                max_output_tokens=args.max_output_tokens,
                max_provider_calls=args.max_provider_calls if args.max_provider_calls is not None else 24,
                max_estimated_cost_microusd=args.max_estimated_cost_microusd, env_file=args.env_file)
            report = json.loads((args.output_dir / "summary.json").read_text(encoding="utf-8"))
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps(dict(status="REFUSED", reason=str(exc), authority_effect="None")))
        return 2
    print(json.dumps(report, ensure_ascii=True))
    return 0 if report.get("completed", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
