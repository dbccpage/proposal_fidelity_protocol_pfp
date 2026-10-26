"""Unified Presentation CLI for Symbol Game.

Deep module composition root coordinating CLI command execution across LLM Turn,
Prompt Artifacts, Code Change Proposals, Gate 11, and Symbol Game runs.

AuthorityEffect: None (const).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from .parser import build_parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI execution entrypoint with top-level --prompt routing."""
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and (raw_args[0].startswith("--prompt") or raw_args[0] == "-p"):
        raw_args.insert(0, "run-turn")
    elif not raw_args:
        raw_args = ["--help"]
    parser = build_parser()
    args = parser.parse_args(raw_args)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    if getattr(args, "claimed_valid", None) is not None:
        args.claimed_valid = args.claimed_valid == "true"
    try:
        return int(args.func(args))
    except (TypeError, ValueError, RuntimeError, OSError, KeyError) as exc:
        sys.stderr.write(f"REFUSED: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
