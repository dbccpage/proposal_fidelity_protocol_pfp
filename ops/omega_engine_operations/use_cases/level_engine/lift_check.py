"""Certify the reading ladder's stage changes and compare with the frozen
expectations.

    python tools/lift_check.py            # record_reading's two steps

Prints each step's verdict (failing conditions by name) and the computed
depth.  Exits 1, naming the condition and its refusal code, when any verdict
differs from ``lifts/record_reading/expect.json`` (``LIFT_VERDICT_DRIFT``);
only a drift row prints a code, so an injection is seen by its code alone.

AuthorityEffect: None
"""

from __future__ import annotations

import sys

from omega_engine_operations.domain.level_engine_context import (
    current_context,
)

ROOT = current_context().runtime_root

from omega_engine_operations.use_cases.level_engine.research_engine.canon import (
    load_path,  # noqa: E402
)
from omega_engine_operations.use_cases.level_engine.research_engine.ladder_cert import (  # noqa: E402
    certify_ladder,
    drift,
    load_proposals,
)


def main(argv: list[str] | None = None) -> int:
    props = load_proposals()
    result = certify_ladder(props)
    for label, rows in (("carrier down map", result.steps), ("harness restriction, diagnostic", result.diagnostics)):
        for r in rows:
            failed = ",".join(c.name for c in r.conditions if not c.passed) or "-"
            print(f"{r.step} ({label}): licensed={r.licensed} conditions failing={failed}")
    print(f"chain: {'PASS' if result.chain.passed else result.chain.code} ({result.chain.detail})")
    print(f"computed depth D = {result.depth}")
    expected = load_path(ROOT / "lifts" / "record_reading" / "expect.json")
    assert isinstance(expected, dict)
    drifted = drift(result, expected)
    for row in drifted:
        print(row)
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
