"""QM/classical experiment adapter. Mathematics executes in sovereign Rust.

AuthorityEffect: None. Successful transport can contain a native refusal.
The complete runtime envelope is retained; there is no Python solver fallback.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err, Refusal, Result


def evaluate(
    experiment: Mapping[str, Any], *, host: RustSymbolGameHost
) -> Result[Mapping[str, Any], Refusal]:
    """Evaluate a declared experiment and return the complete railway outcome."""
    return host.invoke_runtime("qm_classical_evaluate", experiment)


def verify(
    experiment: Mapping[str, Any], certificate: Mapping[str, Any], *, host: RustSymbolGameHost
) -> Result[Mapping[str, Any], Refusal]:
    """Replay the complete certificate against the supplied experiment in Rust."""
    return host.invoke_runtime(
        "qm_classical_verify", {"experiment": experiment, "certificate": certificate}
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--certificate", type=Path)
    args = parser.parse_args()
    host = RustSymbolGameHost(binary=args.binary, timeout_seconds=60)
    try:
        experiment = json.loads(args.experiment.read_text(encoding="utf-8"))
        if args.certificate:
            certificate = json.loads(args.certificate.read_text(encoding="utf-8"))
            outcome = verify(experiment, certificate, host=host)
        else:
            outcome = evaluate(experiment, host=host)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error), "authority_effect": "None"}))
        return 2
    if isinstance(outcome, Err):
        print(json.dumps({"error": str(outcome.error), "authority_effect": "None"}))
        return 2
    print(json.dumps(outcome.value, indent=2, sort_keys=True))
    return 0 if outcome.value["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
