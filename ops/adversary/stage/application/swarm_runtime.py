"""Swarm runtime execution and circuit terminalization for the Adversary stage.

Enforces:
- F-ADVERSARY-02: Preflight refusal and execution failure terminate with gate_status=NOT_RUN.
- The stage imports nothing from Adversary (test_oeas_architecture.py).
"""

from __future__ import annotations

from asyncio import CancelledError as AsyncCancelledError
from concurrent.futures import CancelledError as FutureCancelledError
from typing import Any


def _not_run_receipt(circuit: Any, refusal_code: str) -> Any:
    receipt_factory = getattr(circuit, "create_not_run_receipt", None)
    if callable(receipt_factory):
        return receipt_factory(refusal_code)
    return {
        "run_id": getattr(circuit, "run_id", "run-refused"),
        "profile_digest": "",
        "input_packet_digest": "",
        "output_packet_digest": "",
        "gate_status": "NOT_RUN",
        "refusal_code": refusal_code,
        "is_completed_gated_run": False,
        "open_residuals": [],
        "authority_effect": "None",
    }


def execute_circuit(circuit: Any) -> Any:
    """Execute a circuit, preserving failed or cancelled runs as non-completions."""
    if getattr(circuit, "fail_preflight", False):
        refusal_code = getattr(circuit, "refusal_code", "") or "PREFLIGHT_REFUSED"
        return _not_run_receipt(circuit, refusal_code)
    try:
        return circuit.execute()
    except (AsyncCancelledError, FutureCancelledError, KeyboardInterrupt):
        return _not_run_receipt(circuit, "OPERATOR_CANCELLED")
    except Exception:
        return _not_run_receipt(circuit, "EXECUTION_FAILED")


__all__ = ["execute_circuit"]
