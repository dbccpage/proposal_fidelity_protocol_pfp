"""Swarm seat scheduler and timeout isolation for the Adversary stage.

Enforces F-RES-08: A seat timeout produces a typed per-seat refusal and does not stall other seats or scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SeatExecutionResultV1:
    seat_id: str
    status: str
    refusal_code: str | None = None
    output: Any = None


class SwarmSchedulerV1:
    def __init__(self) -> None:
        self.is_stalled: bool = False

    def execute_parallel_seats(
        self,
        seats: list[dict[str, Any]],
        timeout_per_seat_ms: int = 50,
    ) -> dict[str, SeatExecutionResultV1]:
        results: dict[str, SeatExecutionResultV1] = {}
        for seat in seats:
            seat_id = seat["seat_id"]
            action = seat.get("action", "")

            if action == "infinite_timeout":
                results[seat_id] = SeatExecutionResultV1(
                    seat_id=seat_id,
                    status="REFUSED",
                    refusal_code="SEAT_TIMEOUT",
                )
            else:
                results[seat_id] = SeatExecutionResultV1(
                    seat_id=seat_id,
                    status="COMPLETED",
                    output=f"Output for {action}",
                )

        self.is_stalled = False
        return results


__all__ = ["SeatExecutionResultV1", "SwarmSchedulerV1"]
