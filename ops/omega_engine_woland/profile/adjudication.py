"""Total scene-seat adjudication for the Woland profile."""

from __future__ import annotations

from omega_engine_woland.stage.domain import AgentResultV1

from .models import WolandSeatResultV1
from .topology import WolandProfileAssemblyV1

_STATUS_RANK = {"PASS": 0, "PROPOSED": 1, "FINDING": 2, "HOLD": 3, "REFUSE": 4}


def adjudicate_woland_scene(
    *,
    assembly: WolandProfileAssemblyV1,
    scene_id: str,
    work_packet_id: str,
    seat_results: tuple[WolandSeatResultV1, ...],
) -> AgentResultV1:
    """Require every scene seat exactly once before a transition can be proposed."""

    if type(assembly) is not WolandProfileAssemblyV1:
        raise TypeError("assembly must be exact WolandProfileAssemblyV1")
    if type(seat_results) is not tuple or any(
        type(item) is not WolandSeatResultV1 for item in seat_results
    ):
        raise TypeError("seat_results must be an exact typed tuple")
    scene = next(
        (item for item in assembly.graph.scenes if item.scene_id == scene_id), None
    )
    if scene is None:
        raise ValueError("scene is absent from the Woland graph")
    by_seat = {item.seat_id: item.result for item in seat_results}
    if len(by_seat) != len(seat_results):
        raise ValueError("scene results duplicate a seat")
    if set(by_seat) != set(scene.required_seat_ids):
        raise ValueError("scene results do not cover every required seat exactly once")
    assignments = {
        item.seat_id: item
        for item in assembly.plan.assignments
        if item.scene_id == scene_id
    }
    requirements = {
        item.seat_id: item for item in assembly.definition.seat_requirements
    }
    for seat_id, result in by_seat.items():
        assignment = assignments[seat_id]
        if result.scene_id != scene_id or result.work_packet_id != work_packet_id:
            raise ValueError("seat result has a substituted scene or work packet")
        if result.agent_id != assignment.agent_id:
            raise ValueError(
                "seat result producer differs from the licensed assignment"
            )
        if result.trust_domain != requirements[seat_id].trust_domain:
            raise ValueError(
                "seat result trust domain differs from the required domain"
            )

    inspector = by_seat.get("soviet-inspector")
    if inspector is not None and inspector.status not in {"PASS", "PROPOSED"}:
        status = inspector.status
    else:
        status = max(
            (result.status for result in by_seat.values()),
            key=_STATUS_RANK.__getitem__,
        )
    ordered_results = tuple(by_seat[seat_id] for seat_id in sorted(by_seat))
    return AgentResultV1(
        agent_id="woland-scene-adjudicator",
        trust_domain="EVALUATOR",
        scene_id=scene_id,
        work_packet_id=work_packet_id,
        status=status,
        candidate_ids=tuple(
            sorted(
                {item for result in ordered_results for item in result.candidate_ids}
            )
        ),
        challenge_ids=tuple(
            sorted(
                {item for result in ordered_results for item in result.challenge_ids}
            )
        ),
        artifact_refs=tuple(
            sorted(
                {item for result in ordered_results for item in result.artifact_refs}
            )
        ),
        residual_codes=tuple(
            sorted(
                {item for result in ordered_results for item in result.residual_codes}
            )
        ),
        causal_parent_ids=tuple(result.result_id for result in ordered_results),
    )


__all__ = ["adjudicate_woland_scene"]
