"""Translate nomination DTOs through the canonical native process seam."""

from __future__ import annotations

from typing import Any, Mapping

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_operads.domain.skill_garden.cull import (
    CullPolicy,
    CullReport,
    GardenSnapshot,
)


class NativeCullPolicyAdapter:
    def _invoke(self, operation: str, **payload: Any) -> Result[Mapping[str, Any], Refusal]:
        response = RustSymbolGameHost().invoke_runtime_with_file(
            "skill_garden_cull",
            {"operation": operation, **payload},
            file_action="skill_garden_cull_file",
        )
        if isinstance(response, Err):
            return response
        envelope = response.value
        if not envelope["success"]:
            return Err(Refusal("SKILL_CULL_DISPATCH_FAILED", str(envelope["error"]), __name__))
        result = envelope["result"]
        if result["refusal"] is not None:
            error = result["refusal"]
            return Err(Refusal(error["code"], error["message"], __name__))
        return Ok(result["outcome"])

    def validate_policy(self, policy: object) -> Result[Mapping[str, Any], Refusal]:
        return self._invoke("validate_policy", policy=policy)

    def nominate(self, policy: CullPolicy, snapshot: GardenSnapshot) -> Result[CullReport, Refusal]:
        policy_wire = dict(policy._asdict(), sensor_epoch=policy.sensor_epoch.date().isoformat())

        def observations(rows):
            return {row.skill_id: {"at_us": row.at_us, "date": row.date} for row in rows}

        response = self._invoke(
            "nominate",
            policy=policy_wire,
            now_us=snapshot.now_us,
            first_us=snapshot.first_us,
            last_us=snapshot.last_us,
            roster=list(snapshot.roster),
            last_used=observations(snapshot.last_used),
            births=observations(snapshot.births),
            parity_green=snapshot.parity_green,
        )
        if isinstance(response, Err):
            return response
        report = response.value
        return Ok(
            CullReport(
                refusals=tuple(report["refusals"]),
                candidates=tuple(report["candidates"]),
                exempt=tuple(report["exempt"]),
                in_grace=tuple(report["in_grace"]),
                used_recently=tuple(report["used_recently"]),
                roster_size=report["roster_size"],
                span_days=report["span_days"],
            )
        )
