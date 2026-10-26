"""CLI entrypoint for Prompt Civilization management and audit.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from ...domain.models import CivilizationState, PopulationTier
from ...domain.elenchus import SocraticElenchusBureau


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prompt Civilization CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect prompt status")
    inspect_parser.add_argument("--prompt-id", type=str, required=True)

    # Interrogate command
    interrogate_parser = subparsers.add_parser("interrogate", help="Run Socratic Elenchus interrogation")
    interrogate_parser.add_argument("--text", type=str, required=True)

    args = parser.parse_args(argv)

    if args.command == "interrogate":
        bureau = SocraticElenchusBureau()
        result = bureau.interrogate(args.text)
        print(f"Status: {result.status}")
        print(f"Refused: {result.is_refused}")
        print(f"Contradiction: {result.contradiction}")
        print(f"Fitness Score: {result.fitness_score}")
        return 1 if result.is_refused else 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
