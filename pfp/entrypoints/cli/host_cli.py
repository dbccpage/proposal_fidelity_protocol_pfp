"""Presentation CLI for symgam through the canonical OEOS process seam.

The symgam wire format stays distinct from omega_symbol_game runtime actions.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Refusal, Result
from omega_engine_operating_system.adapters.rust_host import ffi


def locate_symgam() -> Path:
    """Compatibility lookup delegated to the owner; no cross-binary fallback."""
    located = ffi.locate_host_binary(binary_name=ffi.SYMGAM_BINARY)
    if isinstance(located, Err):
        refusal = located.unwrap_err()
        raise FileNotFoundError(f"{refusal.code}: {refusal.message}")
    return located.unwrap().binary


def run_host(args: list[str], stdin: bytes | None = None) -> Result[Mapping[str, Any], Refusal]:
    """Return the complete native record or a typed transport refusal."""
    if len(args) != 1:
        return Err(Refusal(code="HOST_MODE_UNSUPPORTED", message="one symgam mode is required"))
    return ffi.SymgamHost().request(args[0], stdin)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="omega_engine_pfp.entrypoints.cli.host_cli",
        description="Presentation driver for the native Symbol Game host (symgam).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("describe", help="Print host description JSON")
    p_board = sub.add_parser("classify-board", help="Read a board JSON on stdin")
    p_board.add_argument("file", nargs="?", type=Path)
    p_detect = sub.add_parser("detect", help="Read a candidate JSON on stdin")
    p_detect.add_argument("file", nargs="?", type=Path)
    ns = parser.parse_args(argv)
    try:
        if ns.cmd == "describe":
            result = run_host(["--describe"])
        elif ns.file is not None:
            with ns.file.open("rb") as source:
                payload = source.read(ffi.MAX_REQUEST_BYTES + 1)
            result = run_host([ns.cmd], stdin=payload)
        else:
            payload = sys.stdin.buffer.read(ffi.MAX_REQUEST_BYTES + 1)
            result = run_host([ns.cmd], stdin=payload)
    except OSError as error:
        result = Err(Refusal(code="HOST_REQUEST_UNREADABLE", message=str(error)))
    if isinstance(result, Err):
        refusal = result.unwrap_err()
        print(
            json.dumps(
                {"code": refusal.code, "detail": refusal.message, "authority_effect": "None"}
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(dict(result.unwrap()), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
