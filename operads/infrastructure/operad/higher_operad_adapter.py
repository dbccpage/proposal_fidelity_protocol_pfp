"""Strict V3 composition metadata through the OEOS native host."""

from __future__ import annotations

from dataclasses import asdict
from typing import Tuple

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err, Ok, Result

from ...application.ports.strict_operad_port import StrictOperadPort
from ...domain.entities.operation_v3 import OperationV3
from ...domain.errors.domain_errors import DomainInvariantError, OeopDomainError


class HigherOperadAdapter(StrictOperadPort):
    def verify_composition(
        self,
        root_op: OperationV3,
        child_ops: Tuple[OperationV3, ...],
        slot_bindings: Tuple[Tuple[int, OperationV3], ...],
    ) -> Result[bool, OeopDomainError]:
        # Refuse non-integer slots before the no-float JSON transport boundary.
        for slot, _ in slot_bindings:
            if not isinstance(slot, int) or isinstance(slot, bool):
                return Err(DomainInvariantError(
                    "SLOT_INDEX_NOT_AN_INTEGER", "Slot must be an exact integer",
                ))
        try:
            payload = {
                "root_operation": asdict(root_op),
                "slot_bindings": [[slot, asdict(child)] for slot, child in slot_bindings],
            }
            response = RustSymbolGameHost().invoke_runtime("workflow_composition_v3", payload)
        except (TypeError, ValueError) as exc:
            return Err(DomainInvariantError("STRICT_COMPOSITION_INPUT_INVALID", str(exc)))
        if isinstance(response, Err):
            return Err(DomainInvariantError(response.error.code, response.error.message))
        envelope = response.value
        if type(envelope) is not dict or envelope.get("success") is not True:
            return Err(DomainInvariantError(
                "STRICT_COMPOSITION_NATIVE_UNAVAILABLE", "Native composition validation failed",
            ))
        reply = envelope.get("result")
        if type(reply) is dict and type(reply.get("refusal")) is dict:
            refusal = reply["refusal"]
            if type(refusal.get("code")) is str and type(refusal.get("message")) is str:
                return Err(DomainInvariantError(refusal["code"], refusal["message"]))
        outcome = reply.get("outcome") if type(reply) is dict else None
        if (
            type(reply) is not dict or reply.get("refusal") is not None
            or type(outcome) is not dict or outcome.get("is_valid") is not True
            or outcome.get("authority_effect") != "None"
        ):
            return Err(DomainInvariantError(
                "STRICT_COMPOSITION_NATIVE_INVALID", "No exact non-authorizing native decision",
            ))
        return Ok(True)

    def authorize_term(
        self,
        agent_id: str,
        term_expr: str,
    ) -> Result[str, OeopDomainError]:
        return Err(DomainInvariantError(
            code="LICENSE_WITNESS_REQUIRED",
            message=(
                "Cannot authorize a term without a bound AgentLicense witness "
                "and canonical operation term"
            ),
        ))
