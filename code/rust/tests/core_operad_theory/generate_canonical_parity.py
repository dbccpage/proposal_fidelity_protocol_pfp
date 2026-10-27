"""Retired: refresh the Python-generated operation vectors checked by Rust canonical parity.

Usage: python engine/crates_rs/tests/core_operad_theory/generate_canonical_parity.py [--check | --write]

The independent Python side of this parity test was the Python higher-operad
kernel (`engine.kernel.higher_operad.model`), retired in f4c6fcf3. Without
it there is nothing independent to regenerate from, so both modes fail closed
with RUNTIME_RETIRED (exit 2) and write nothing. `fixtures/canonical_parity.json`
stays as the frozen record the kernel last produced; `canonical_parity.rs`
still checks the Rust kernel against it. The generator's implementation
remains in git history before this retirement.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import sys

RUNTIME_RETIRED = "RUNTIME_RETIRED"
MESSAGE = (
    f"{RUNTIME_RETIRED}: the Python higher-operad kernel this generator used as the "
    "independent side of the parity test is retired; fixtures/canonical_parity.json "
    "is frozen and is not regenerated"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check the fixture (default)")
    mode.add_argument("--write", action="store_true", help="regenerate the fixture")
    parser.parse_args()
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
