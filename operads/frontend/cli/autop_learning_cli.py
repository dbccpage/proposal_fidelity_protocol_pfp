"""Explicit imports and honest maintenance for AutoP compatibility entrypoint. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from pathlib import Path

from operads.frontend.presenters.autop_learning_presenter import (
    AutoPLearningPresenter,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--transcript", type=Path, action="append", default=[])
    parser.add_argument(
        "--host", choices=["autop", "adversary", "codex", "claude", "antigravity"], default="autop"
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--retry", action="store_true")
    parser.add_argument("--pending", action="store_true")
    parser.add_argument("--maintenance", action="store_true")
    parser.add_argument("--runtime-factory", help="Module:function returning LearningCompletion")
    return AutoPLearningPresenter.execute_learning(parser.parse_args(argv), parser)


if __name__ == "__main__":
    raise SystemExit(main())
