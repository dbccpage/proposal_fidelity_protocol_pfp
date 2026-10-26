"""Offline finite-QM reference prompt, compilation and candidate checking.

AuthorityEffect: None. This entrypoint makes no provider calls.
"""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from omega_engine_pfp.domain.pfp_ingress import strict_json
from omega_engine_pfp.infrastructure.finite_qm_prompt import (
    prepare_finite_qm_turn,
    render_system_prompt,
)
from omega_engine_pfp.infrastructure.yaml_loading import strict_yaml_load


def verify_source_pins(work_unit: dict, source_root: Path):
    root = source_root.resolve()
    pins = work_unit["operad_slots"]["slot_m1_layer0_ambient_carrier"]["source_pins"]
    for pin in pins:
        path = (root / pin["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("SOURCE_OUTSIDE_DECLARED_ROOT")
        if sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError("SOURCE_DIGEST_MISMATCH:" + pin["path"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    system = subs.add_parser("system", help="Print the finite-QM derivation system prompt")
    system.add_argument("--output", type=Path)
    for name in ("prepare", "check"):
        command = subs.add_parser(name)
        command.add_argument("work_unit", type=Path)
        command.add_argument("--source-root", type=Path, required=True)
        command.add_argument("--attempt", required=True)
        command.add_argument(
            "--compact",
            action="store_true",
            help="Compatibility flag; prompts always select task-relevant operations",
        )
        command.add_argument("--stage", choices=("P1_DERIVE", "P3_REPAIR"), default="P1_DERIVE")
        command.add_argument("--failure-code", action="append", default=[])
        if name == "check":
            command.add_argument("reply", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "system":
            content = render_system_prompt()
            if args.output:
                with args.output.open("x", encoding="utf-8", newline="\n") as out:
                    out.write(content)
            else:
                print(content, end="")
            return 0
        raw = args.work_unit.read_text(encoding="utf-8")
        unit = strict_json(raw) if args.work_unit.suffix == ".json" else strict_yaml_load(raw)
        turn = prepare_finite_qm_turn(
            unit,
            attempt_id=args.attempt,
            compact=args.compact,
            stage_id=args.stage,
            failure_codes=tuple(args.failure_code),
        )
        verify_source_pins(unit, args.source_root)
        if args.command == "prepare":
            print(
                json.dumps(
                    dict(
                        status="PROMPT_PREPARED",
                        provider_calls=0,
                        authority_effect="None",
                        checker_status="NOT_RUN",
                        binding=turn.binding,
                        **turn.prompt.to_dict(),
                    ),
                    ensure_ascii=True,
                    sort_keys=True,
                )
            )
            return 0
        judges, native = (), None
        from omega_engine_pfp.infrastructure.finite_qm_cochain_judge import (
            CHECKER_ID,
            NativeCochainJudge,
        )

        if unit["checker_id"] == CHECKER_ID:
            from omega_engine_pfp.ffi import RustSymbolGameHost

            native = NativeCochainJudge(RustSymbolGameHost())
            judges = ((CHECKER_ID, native),)
        result = turn.check(args.reply.read_bytes(), judges=judges, require_checker=True)
        if native:
            result["native_receipts"] = native.receipts
        result.update(
            provider_calls=0,
            capture_origin="SUBMITTED_BYTES_NOT_A_LIVE_RUN",
            source_pins_verified=True,
        )
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0 if result["status"] == "HOST_ACCEPTED" else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(
            json.dumps(
                dict(
                    status="INFRASTRUCTURE_ERROR",
                    reason=str(exc),
                    provider_calls=0,
                    authority_effect="None",
                )
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
