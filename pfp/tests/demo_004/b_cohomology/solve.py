"""Thin challenge entrypoint using the shared cohomology solver port.

A mathematical certificate is not the city execution or Woland authorization.
Unavailable native operations remain explicit refusals.
"""

from __future__ import annotations

import json
import sys
from typing import Mapping

from omega_engine_pfp.domain.cohomology.certificate_checker import check_certificate
from omega_engine_pfp.domain.cohomology.solver import solve


def main() -> int:
    """Read one JSON case; succeed only for an independently checked result."""
    try:
        case = json.load(sys.stdin)
        if not isinstance(case, Mapping):
            raise ValueError("The case must be a JSON object")
        result = solve(case)
        check = check_certificate(case, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if check.passed and result.get("status") in ("SOLVED", "OUT_OF_SCOPE") else 1
    except (ValueError, TypeError, RuntimeError) as exc:
        print(
            json.dumps(
                {"status": "UNKNOWN", "refusal": "EXECUTION_UNAVAILABLE", "detail": str(exc)}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
