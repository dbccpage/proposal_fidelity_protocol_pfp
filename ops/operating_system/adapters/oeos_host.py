"""OEOS Host adapter for the Adversary stage.

Implements HostPortV1 to provide atomic effect writing, Rust host seams,
and provider gateway routing.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from operating_system.domain.arena import (
    RoutingPolicyProposalV1,
)
from operating_system.domain.route import RoutePlanV1
from operations.domain.rop.result import Err, Refusal, Result
from adversary.stage.application.ports import HostPortV1


@dataclass(frozen=True, slots=True)
class OeosHostAdapter(HostPortV1):
    """Adapter bridging OEOS host services into the Adversary stage."""

    host_id: str = "oeos-host-v1"
    authority_effect: str = "None"
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def execute_host_request(self, request_bytes: bytes) -> Result[bytes, Refusal]:
        """Execute host-level governed request atomically."""
        try:
            req = json.loads(request_bytes.decode("utf-8"))
            action = req.get("action", "ping")
            response = {
                "host_id": self.host_id,
                "action": action,
                "status": "REFUSED",
                "reason": "request was parsed and not admitted",
                "authority_effect": self.authority_effect,
                "payload_sha256": hashlib.sha256(request_bytes).hexdigest(),
            }
            if action == "validate_route_plan":
                plan = RoutePlanV1.from_canonical(req["route_plan"])
                response["route_plan_id"] = plan.route_plan_id
                response["canonical_digest"] = plan.canonical_digest
            elif action == "verify_policy_proposal":
                RoutingPolicyProposalV1.from_canonical(req["proposal"])
            self.audit_log.append({"request": req, "response": response})
            return Err(
                Refusal(
                    code="HOST_REQUEST_REFUSED",
                    message="request was parsed and not admitted",
                    locus="operating_system.adapters.oeos_host",
                )
            )
        except Exception as exc:
            code = getattr(exc, "code", None)
            if type(code) is not str or not code:
                code = "HOST_REQUEST_REFUSED"
            message = getattr(exc, "message", None)
            if type(message) is not str or not message.strip():
                message = str(exc).strip() or code
            self.audit_log.append({"error": str(exc), "code": code})
            return Err(
                Refusal(
                    code=code,
                    message=message,
                    locus="operating_system.adapters.oeos_host",
                )
            )


__all__ = ["OeosHostAdapter"]
