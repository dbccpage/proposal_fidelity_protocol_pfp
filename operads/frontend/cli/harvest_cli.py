"""CLI entrypoint for Autopoietic Harvest. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
from omega_engine_operads.frontend.presenters.harvest_presenter import (
    HarvestPresenter,
)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_harvest_cli(argv: Optional[List[str]] = None) -> int:
    root = default_repo_root()
    parser = argparse.ArgumentParser(prog="harvest_cli", description="Omega Autopoietic Harvester")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd, help_text in [
        ("ingest-all", "Harvest into vault"),
        ("status", "Show vault stats"),
        ("verify-vault", "Verify CAS objects"),
        ("pre-clean-teamwork", "Pre-clean gate"),
    ]:
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("--vault-dir", type=Path, default=intelligence_path(root, "_intelligence/harvest"))
        if cmd == "verify-vault":
            p.add_argument(
                "--snapshots-dir",
                type=Path,
                default=None,
                help="Optional path to snapshots directory",
            )
        if cmd in ("ingest-all", "pre-clean-teamwork"):
            p.add_argument("--teamwork-dir", type=Path, default=root / ".agents" / "teamwork")
            p.add_argument(
                "--antibodies-dir", type=Path, default=intelligence_path(root, "_intelligence/antibodies")
            )
            p.add_argument(
                "--skills-register",
                type=Path,
                default=root / "omega_engine_operads" / "skills" / "ooutwire" / "proposed_skills_register.md",
            )
            if cmd == "pre-clean-teamwork":
                p.add_argument(
                    "--clear-after",
                    action="store_true",
                    help="Clear teamwork directory after CAS pass",
                )
    args = parser.parse_args(argv)
    default_vault = intelligence_path(root, "_intelligence/harvest")
    args.archive_snapshots_dir = (
        intelligence_path(root, "_intelligence/archive/harvest/snapshots")
        if args.vault_dir == default_vault else None
    )
    return HarvestPresenter.dispatch(args)


def main(argv: Optional[List[str]] = None) -> int:
    return run_harvest_cli(argv)


if __name__ == "__main__":
    sys.exit(run_harvest_cli())
