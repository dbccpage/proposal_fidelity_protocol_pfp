#!/usr/bin/env python3
"""Verify DDC paper demo tapes against native ddc_verify_tape action.

Part of release gate G3 and Local CI gate ddc_tape_native_v1.
Feeds all 18 DDC paper demo tapes through native ddc_verify_tape and compares
verdicts (lawful flag, letter tape, and receipt_head commitment).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_operating_system.adapters.rust_host.ffi import (
    RustSymbolGameHost,
)

if __package__ in (None, ""):
    from host_tools import ensure_symbol_game_host
else:
    from .host_tools import ensure_symbol_game_host

DEFAULT_DEMOS_PATH = (
    REPO_ROOT
    / "omega_engine"
    / "crates_rs"
    / "omega_symbol_game"
    / "tests"
    / "fixtures"
    / "ddc_paper_demos.json"
)


def verify_ddc_tapes(demos_path: Path, host: RustSymbolGameHost) -> int:
    if not demos_path.is_file():
        print(f"ddc_tape_native: FAIL (demos file not found: {demos_path})")
        return 1

    try:
        demos = json.loads(demos_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ddc_tape_native: FAIL (could not read demos JSON: {exc})")
        return 1

    failures = []
    print(f"ddc_tape_native: verifying {len(demos)} demo tape(s)...")

    for idx, demo in enumerate(demos, start=1):
        name = demo.get("name", f"demo_{idx}")
        expected_lawful = demo.get("lawful")
        expected_letters = demo.get("letters")
        expected_receipt_head = demo.get("receipt_head")

        req = {
            "initial_state": demo.get("initial_state"),
            "steps": demo.get("steps"),
        }

        res = host.invoke_runtime("ddc_verify_tape", req)
        if not res.is_ok or not res.value["success"]:
            failures.append(f"{name}: host invocation failed ({res})")
            continue

        val = res.value["result"]
        if val.get("lawful") != expected_lawful:
            failures.append(
                f"{name}: lawful mismatch (got {val.get('lawful')}, expected {expected_lawful})"
            )
        elif val.get("letters") != expected_letters:
            failures.append(
                f"{name}: letters mismatch (got {val.get('letters')!r}, expected {expected_letters!r})"
            )
        elif val.get("receipt_head") != expected_receipt_head:
            failures.append(
                f"{name}: receipt_head mismatch (got {val.get('receipt_head')!r}, expected {expected_receipt_head!r})"
            )

    if failures:
        print(f"ddc_tape_native: FAIL ({len(failures)} mismatch(es)):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"ddc_tape_native: PASS (all {len(demos)} demo tapes verified)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--demos-path",
        default=str(DEFAULT_DEMOS_PATH),
        help="Path to ddc_paper_demos.json fixture",
    )
    args = parser.parse_args(argv)

    binary = ensure_symbol_game_host(REPO_ROOT)
    if binary is None:
        print("ddc_tape_native: FAIL (could not build omega_symbol_game)")
        return 1

    host = RustSymbolGameHost(binary=binary)
    return verify_ddc_tapes(Path(args.demos_path).resolve(), host)


__all__ = ["DEFAULT_DEMOS_PATH", "verify_ddc_tapes", "main"]

if __name__ == "__main__":
    sys.exit(main())
