#!/usr/bin/env python3
"""CLI interface for Discrete Deformation Calculus Operad Engine. AuthorityEffect: None."""

from __future__ import annotations

import argparse

from omega_engine_operads.frontend.presenters.ddc_operad_presenter import (
    DdcOperadPresenter,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DDC Action Tape Operad CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p_parse = sub.add_parser("parse", help="Parse and verify DDC tape JSONL")
    p_parse.add_argument(
        "--tape", type=str, required=True, help="Path to ddc.jsonl file or run directory"
    )
    p_parse.add_argument(
        "--output-receipt", type=str, help="Destination path for JSON operad receipt"
    )
    p_parse.add_argument(
        "--persist", action="store_true", help="Persist receipt to default evidence vault"
    )
    p_parse.set_defaults(func=DdcOperadPresenter.cmd_parse)
    p_comp = sub.add_parser("compress", help="Compress verified tape into operad_signature.json")
    p_comp.add_argument(
        "--tape", type=str, required=True, help="Path to ddc.jsonl file or run directory"
    )
    p_comp.add_argument("--skill-id", type=str, required=True, help="Skill ID to record")
    p_comp.add_argument(
        "--skill-name", type=str, default="Verified DDC Skill", help="Skill display name"
    )
    p_comp.add_argument("--claimed-residual", type=str, help="Claimed residual effect")
    p_comp.add_argument("--apply-changes", action="store_true", help="Apply changes")
    p_comp.set_defaults(func=DdcOperadPresenter.cmd_compress)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
