"""CLI composition entry point for read-only Intelligence Metabolism."""

from __future__ import annotations

import sys

from pciv.frontend.presenters.metabolism_presenter import (
    run_metabolism_cli,
)


def main(argv: list[str] | None = None) -> int:
    return run_metabolism_cli(argv)


if __name__ == "__main__":
    sys.exit(main())
