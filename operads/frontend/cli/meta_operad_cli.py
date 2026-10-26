"""Meta-operad CLI: plans are observations, and unbound execution is refused."""

import argparse
import sys
from typing import Sequence

from omega_engine_operads.domain.ddc_execution.errors import OperadDomainError
from omega_engine_operads.domain.ddc_execution.execution import ExecutionPlan
from omega_engine_operads.domain.operad.errors import Err
from omega_engine_operads.infrastructure.ddc_execution.runtime import (
    build_meta_operad_engine,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Declared operad execution (AuthorityEffect: None)"
    )
    parser.add_argument("skill_id")
    parser.add_argument("--agent", default=None)
    parser.add_argument("--input", nargs="*", default=[])
    parser.add_argument("--output", default=None)
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate a plan without evaluating or writing"
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    try:
        engine = build_meta_operad_engine()
        result = engine.execute_morphism(
            args.skill_id,
            args.input,
            agent_id=args.agent,
            output_hint=args.output,
            dry_run=args.dry_run,
        )
        if isinstance(result, Err):
            print(f"[OPERAD_REFUSED] {result.error.code}: {result.error.detail}", file=sys.stderr)
            return 1
        outcome = result.value
        if isinstance(outcome, ExecutionPlan):
            signature = outcome.operation.signature
            print(f"=== OPERAD METASKILL ENGINE: {args.skill_id} [DRY_RUN_PLAN] ===")
            print(
                f"  Signature: ({', '.join(signature.source_colours)}) -> {signature.target_colour}"
            )
            print("  Evaluation: not executed; residual unmeasured; evidence unchanged")
        else:
            record = outcome.record
            print(f"=== OPERAD METASKILL ENGINE: {args.skill_id} [EXECUTED] ===")
            print(f"  Residual: {record.residual_before} -> {record.residual_after}")
            print(f"  Output: {record.output.path} (sha256: {record.output.sha256})")
        print("  AuthorityEffect: None")
        return 0
    except OperadDomainError as exc:
        print(f"[OPERAD_REFUSED] {exc.code}: {exc.detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
