"""Gate 11 verification command handlers for Symbol Game CLI presentation layer.

These handlers are the composition root for Gate 11: each builds the native
exact adapter and hands it to the fixture host, so every Phi1, Gamma2 and class
in a Gate 11 record was issued by ``core_functional`` through the OEOS seam.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .io_utils import _read_json, _write_json, _write_verdict_md


def _functional_port():
    from pfp.infrastructure.adapters.exact_rust_adapter import (
        RustExactEngineAdapter,
    )

    return RustExactEngineAdapter()


def cmd_gate11_self(args: argparse.Namespace) -> int:
    from pfp.fixtures.gate11_residual_dual import host_verify_self

    result = host_verify_self(_functional_port())
    if args.out_dir is not None:
        out = Path(args.out_dir)
        _write_json(out / "host_record.json", result)
        _write_verdict_md(out / "HOST_VERDICT.md", result)
    else:
        _write_json(None, result)
    return 0 if result["overall_passed"] else 1


def cmd_gate11_ingest(args: argparse.Namespace) -> int:
    from pfp.fixtures.gate11_residual_dual import parse_gate11_symbolic_reply

    path = Path(args.reply)
    text = path.read_text(encoding="utf-8")
    result = parse_gate11_symbolic_reply(text, _functional_port())
    result["source_path"] = str(path)
    if args.out_dir is not None:
        out = Path(args.out_dir)
        _write_json(out / "host_record.json", result)
        _write_verdict_md(out / "HOST_VERDICT.md", result)
    else:
        _write_json(None, result)
    return 0 if result["overall_passed"] else 1


def cmd_gate11_project(args: argparse.Namespace) -> int:
    """Report exact Phi1/Gamma2 per frozen fixture and whether Gamma2 <= Phi1.

    Two defects are repaired here besides the tolerance. ``frozen_fixtures()``
    returns a tuple, so ``.items()`` raised ``AttributeError``; and the
    projection is a five-key mapping, so unpacking it into three names raised
    ``ValueError``. The command could not run, which is why the epsilon it
    carried had never been observed to matter.

    Exit code is 1 when an evaluated bound is *violated*. A refusal is not a
    violation: it records that Phi1 was never certified for that fixture, and
    leaves the exit code alone.
    """
    from pfp.fixtures.gate11_residual_dual import (
        contract_bound_holds,
        frozen_fixtures,
        project_fixture_phi_gamma,
    )
    from pfp.domain.shared_kernel.exact import to_canonical_string

    port = _functional_port()
    out: dict[str, Any] = {}
    violated = False
    for fixture in frozen_fixtures():
        projection = project_fixture_phi_gamma(port, fixture)
        phi1, gamma2 = projection["phi1"], projection["gamma2"]
        if phi1 is None:
            out[fixture.name] = {
                "phi1": None,
                "gamma2": None if gamma2 is None else to_canonical_string(gamma2),
                "contract_bound_holds": None,
                "refusal_reason": projection["phi1_refusal"],
                "authority_effect": "None",
            }
            continue
        # Exact over Q. No epsilon: the bound either holds or it does not.
        holds = contract_bound_holds(gamma2, phi1)
        violated = violated or not holds
        out[fixture.name] = {
            "phi1": to_canonical_string(phi1),
            "gamma2": to_canonical_string(gamma2),
            "is_exact": projection["is_exact"],
            "contract_bound_holds": holds,
            "refusal_reason": None,
            "authority_effect": "None",
        }
    _write_json(args.output, out)
    return 1 if violated else 0
