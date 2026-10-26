"""Deterministic N=1 scheduler and independent replay for the Woland stage."""

from __future__ import annotations

from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain import (
    AgentResultV1,
    LicensedWorkflowPlanV1,
    ProgressMeasureV1,
    SceneGraphV1,
    SceneVisitV1,
    StopConditionV1,
    SwarmDefinitionV1,
    SwarmProfileV1,
    SwarmRunStateV1,
    WorkPacketV1,
)


def validate_swarm_composition(
    definition: SwarmDefinitionV1,
    profile: SwarmProfileV1,
    graph: SceneGraphV1,
    plan: LicensedWorkflowPlanV1,
) -> Result[None, Refusal]:
    try:
        if type(definition) is not SwarmDefinitionV1:
            raise TypeError("definition must be exact SwarmDefinitionV1")
        if type(profile) is not SwarmProfileV1:
            raise TypeError("profile must be exact SwarmProfileV1")
        if type(graph) is not SceneGraphV1:
            raise TypeError("graph must be exact SceneGraphV1")
        if type(plan) is not LicensedWorkflowPlanV1:
            raise TypeError("plan must be exact LicensedWorkflowPlanV1")
        if profile.base_definition_id != definition.definition_id:
            raise ValueError("profile does not compose the supplied base definition")
        if profile.scene_graph_id != graph.graph_id:
            raise ValueError("profile does not bind the supplied scene graph")
        if plan.catalog_id != definition.skill_catalog_id:
            raise ValueError("workflow plan does not bind the definition catalog")
        seat_by_id = {seat.seat_id: seat for seat in definition.seat_requirements}
        assignments = {(item.scene_id, item.seat_id): item for item in plan.assignments}
        for scene in graph.scenes:
            for seat_id in scene.required_seat_ids:
                requirement = seat_by_id.get(seat_id)
                assignment = assignments.get((scene.scene_id, seat_id))
                if requirement is None:
                    raise ValueError(f"scene {scene.scene_id} requires an unknown seat")
                if assignment is None:
                    raise ValueError(
                        f"scene {scene.scene_id} skips required seat {seat_id}"
                    )
                if not set(requirement.required_operations).issubset(
                    assignment.operation_ids
                ):
                    raise ValueError(f"seat {seat_id} lacks its required operations")
            for seat_id in scene.required_seat_ids:
                requirement = seat_by_id[seat_id]
                agent_id = assignments[(scene.scene_id, seat_id)].agent_id
                for independent_seat in requirement.independent_from:
                    if (scene.scene_id, independent_seat) not in assignments:
                        continue
                    if (
                        assignments[(scene.scene_id, independent_seat)].agent_id
                        == agent_id
                    ):
                        raise ValueError(
                            f"seat {seat_id} is not independent from {independent_seat}"
                        )
        for seat in definition.seat_requirements:
            assigned_agents = {
                item.agent_id
                for item in plan.assignments
                if item.seat_id == seat.seat_id
            }
            for independent_seat in seat.independent_from:
                other_assigned = {
                    item.agent_id
                    for item in plan.assignments
                    if item.seat_id == independent_seat
                }
                if assigned_agents.intersection(other_assigned):
                    raise ValueError(
                        f"independent trust domains {seat.seat_id}/{independent_seat} "
                        "share an agent across scenes"
                    )
        return Ok(None)
    except (TypeError, ValueError) as exc:
        return Err(
            Refusal(
                code="OEAS_COMPOSITION_REFUSED",
                message=str(exc),
                locus="oeas-composition",
            )
        )


def stage_scheduler(
    definition: SwarmDefinitionV1,
    profile: SwarmProfileV1,
    graph: SceneGraphV1,
    plan: LicensedWorkflowPlanV1,
    stop: StopConditionV1,
    *,
    live: bool = False,
    retinue_mode: str = "core",
) -> Any:
    """Construct the one stage scheduler.

    ``live=False`` returns ``DeterministicSchedulerV1`` and is not the live path.
    ``live=True`` returns ``NativeHostScheduler``. The stage CLI and
    ``build_woland_runtime`` use the live scheduler. Neither entrypoint
    advances on its own: the step is ``advance_bout``.
    """
    if live:
        if type(retinue_mode) is not str or retinue_mode not in ("core", "full"):
            raise ValueError("retinue mode must be core or full")
        from omega_engine_woland.runtime import NativeHostScheduler

        return NativeHostScheduler(
            definition,
            profile,
            graph,
            plan,
            stop,
            retinue_mode=retinue_mode,
        )
    return DeterministicSchedulerV1(definition, profile, graph, plan, stop)


_STEP = "omega_engine_woland.stage.application.scheduler"


def advance_bout(
    scheduler: Any,
    state: SwarmRunStateV1,
    result: AgentResultV1,
    progress: ProgressMeasureV1,
) -> Result[SwarmRunStateV1, Refusal]:
    """The one scheduler step shared by a Woland bout, the stage CLI, and autopoiesis."""
    return scheduler.advance(state, result, progress)


def _refused(code: str, message: str) -> Err:
    return Err(Refusal(code, message, _STEP))


def _first_edge(scheduler: Any, scene_id: str, status: str, residuals: tuple[str, ...]) -> Any:
    residual_set = set(residuals)
    for edge in scheduler.graph.transitions:
        if edge.source_scene_id != scene_id or status not in edge.trigger_statuses:
            continue
        if edge.residual_codes and not residual_set.intersection(edge.residual_codes):
            continue
        return edge
    return None


def _route_step(scheduler: Any, scene_id: str) -> Result[tuple[str, tuple[str, ...]], Refusal]:
    """Pick the status that makes the scheduler's first matching edge progress."""
    graph = getattr(scheduler, "graph", None)
    stop = getattr(scheduler, "stop", None)
    if graph is None or stop is None:
        return _refused("WOLAND_BOUT_ADVANCE_UNBOUND", "scheduler graph is not bound")
    scenes = {scene.scene_id: scene for scene in graph.scenes}
    scene = scenes.get(scene_id)
    if scene is None:
        return _refused(
            "OEAS_SCHEDULER_ADVANCE_REFUSED",
            "current scene is not in the scheduler graph",
        )
    stopped = set(stop.stop_on_statuses)
    if scene.terminal:
        for status in scene.allowed_result_statuses:
            if status not in stopped:
                return Ok((status, ()))
        return _refused(
            "OEAS_SCHEDULER_ADVANCE_REFUSED",
            "terminal scene has no non-stopping status",
        )
    outgoing: dict[str, list[Any]] = {}
    for edge in graph.transitions:
        outgoing.setdefault(edge.source_scene_id, []).append(edge)
    parent: dict[str, tuple[str, str, tuple[str, ...]] | None] = {scene_id: None}
    queue = [scene_id]
    target = None
    while queue:
        current = queue.pop(0)
        for edge in outgoing.get(current, ()):
            nxt = edge.target_scene_id
            if nxt in parent or nxt not in scenes:
                continue
            status = next((item for item in edge.trigger_statuses if item not in stopped), None)
            if status is None:
                continue
            residuals = tuple(edge.residual_codes)
            if _first_edge(scheduler, current, status, residuals) is not edge:
                continue
            parent[nxt] = (current, status, residuals)
            if scenes[nxt].terminal:
                target = nxt
                queue = []
                break
            queue.append(nxt)
    if target is None:
        return _refused("WOLAND_BOUT_ADVANCE_UNBOUND", "scheduler graph has no terminal path")
    cursor = target
    step: tuple[str, tuple[str, ...]] | None = None
    while cursor != scene_id:
        previous, status, residuals = parent[cursor]
        step = (status, residuals)
        cursor = previous
    if step is None:
        return _refused("WOLAND_BOUT_ADVANCE_UNBOUND", "scheduler graph has no terminal path")
    return Ok(step)


def finish_bout(
    scheduler: Any,
    state: SwarmRunStateV1,
    packet: WorkPacketV1,
) -> Result[SwarmRunStateV1, Refusal]:
    """Leave RUNNING only by ``advance_bout``. A completed bout is that result."""
    if scheduler is None:
        return _refused("WOLAND_SCHEDULER_MISSING", "a scheduler is required to finish a bout")
    limit = int(getattr(getattr(scheduler, "stop", None), "max_scene_steps", 20))
    taken = 0
    while state.terminal_status == "RUNNING":
        if taken > limit:
            return _refused("WOLAND_BOUT_ADVANCE_UNBOUNDED", "scheduler stayed RUNNING")
        choice = _route_step(scheduler, state.current_scene_id)
        if choice.is_err:
            return choice
        status, residuals = choice.unwrap()
        try:
            result = AgentResultV1(
                "bout_step",
                "PRODUCER",
                state.current_scene_id,
                packet.packet_id,
                status,
                residual_codes=residuals,
            )
            progress = ProgressMeasureV1(changed_state=1)
        except (TypeError, ValueError) as exc:
            return _refused("OEAS_SCHEDULER_ADVANCE_REFUSED", str(exc))
        advanced = advance_bout(scheduler, state, result, progress)
        if advanced.is_err:
            return advanced
        state = advanced.unwrap()
        taken += 1
    return Ok(state)


class DeterministicSchedulerV1:
    """Canonical causal scheduler for the initial single-worker profile."""

    def __init__(
        self,
        definition: SwarmDefinitionV1,
        profile: SwarmProfileV1,
        graph: SceneGraphV1,
        plan: LicensedWorkflowPlanV1,
        stop: StopConditionV1,
    ) -> None:
        validated = validate_swarm_composition(definition, profile, graph, plan)
        if isinstance(validated, Err):
            raise ValueError(validated.error.message)
        if definition.max_parallelism != 1:
            raise ValueError("DeterministicSchedulerV1 requires N=1")
        if type(stop) is not StopConditionV1:
            raise TypeError("stop must be exact StopConditionV1")
        self.definition = definition
        self.profile = profile
        self.graph = graph
        self.plan = plan
        self.stop = stop

    def start(self, run_key: str, packet: WorkPacketV1) -> SwarmRunStateV1:
        if type(packet) is not WorkPacketV1:
            raise TypeError("packet must be exact WorkPacketV1")
        if packet.scene_id != self.graph.entry_scene_id:
            raise ValueError("initial work packet must target the graph entry scene")
        if packet.budget_units > self.stop.max_total_budget:
            raise ValueError("work packet budget exceeds the stop condition")
        return SwarmRunStateV1(
            run_key=run_key,
            profile_id=self.profile.profile_id,
            current_scene_id=self.graph.entry_scene_id,
            visit_counts=(SceneVisitV1(self.graph.entry_scene_id, 1),),
            result_ids=(),
            progress_measure_ids=(),
            remaining_budget=packet.budget_units,
            scene_steps=0,
            dry_rounds=0,
        )

    def advance(
        self,
        state: SwarmRunStateV1,
        result: AgentResultV1,
        progress: ProgressMeasureV1,
    ) -> Result[SwarmRunStateV1, Refusal]:
        try:
            if type(state) is not SwarmRunStateV1:
                raise TypeError("state must be exact SwarmRunStateV1")
            if type(result) is not AgentResultV1:
                raise TypeError("result must be exact AgentResultV1")
            if type(progress) is not ProgressMeasureV1:
                raise TypeError("progress must be exact ProgressMeasureV1")
            if state.terminal_status != "RUNNING":
                raise ValueError("a terminal run cannot advance")
            if result.scene_id != state.current_scene_id:
                raise ValueError("agent result scene differs from current run scene")

            result_ids = (*state.result_ids, result.result_id)
            progress_ids = (*state.progress_measure_ids, progress.measure_id)
            steps = state.scene_steps + 1
            budget = max(0, state.remaining_budget - 1)
            dry = 0 if progress.progressed else state.dry_rounds + 1
            current_scene = next(
                scene
                for scene in self.graph.scenes
                if scene.scene_id == state.current_scene_id
            )

            terminal = "RUNNING"
            target = state.current_scene_id
            if result.status in self.stop.stop_on_statuses:
                terminal = result.status
            elif current_scene.terminal:
                terminal = "COMPLETED"
            elif steps >= self.stop.max_scene_steps or budget == 0:
                terminal = "EXHAUSTED"
            elif dry >= self.stop.max_dry_rounds:
                terminal = "HOLD"
            else:
                residuals = set(result.residual_codes)
                eligible = tuple(
                    edge
                    for edge in self.graph.transitions
                    if edge.source_scene_id == state.current_scene_id
                    and result.status in edge.trigger_statuses
                    and (
                        not edge.residual_codes
                        or residuals.intersection(edge.residual_codes)
                    )
                )
                if not eligible:
                    terminal = "HOLD"
                else:
                    target = eligible[0].target_scene_id

            visits = {item.scene_id: item.count for item in state.visit_counts}
            if terminal == "RUNNING":
                visits[target] = visits.get(target, 0) + 1
                scene = next(item for item in self.graph.scenes if item.scene_id == target)
                if visits[target] > scene.max_visits:
                    over_visit = target
                    terminal = "HOLD"
                    target = state.current_scene_id
                    if visits[over_visit] > 64:
                        visits[over_visit] = 64
            return Ok(
                SwarmRunStateV1(
                    run_key=state.run_key,
                    profile_id=state.profile_id,
                    current_scene_id=target,
                    visit_counts=tuple(
                        SceneVisitV1(scene_id, count)
                        for scene_id, count in sorted(visits.items())
                    ),
                    result_ids=result_ids,
                    progress_measure_ids=progress_ids,
                    remaining_budget=budget,
                    scene_steps=steps,
                    dry_rounds=dry,
                    terminal_status=terminal,
                )
            )
        except (TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="OEAS_SCHEDULER_ADVANCE_REFUSED",
                    message=str(exc),
                    locus="oeas-scheduler-advance",
                )
            )

    def replay(
        self,
        run_key: str,
        packet: WorkPacketV1,
        results: tuple[AgentResultV1, ...],
        progress_measures: tuple[ProgressMeasureV1, ...],
    ) -> SwarmRunStateV1:
        if type(results) is not tuple or type(progress_measures) is not tuple:
            raise TypeError("replay inputs must be exact tuples")
        if len(results) != len(progress_measures):
            raise ValueError("replay result/progress arities differ")
        state = self.start(run_key, packet)
        for result, progress in zip(results, progress_measures, strict=True):
            adv_res = self.advance(state, result, progress)
            if adv_res.is_err:
                raise ValueError(adv_res.unwrap_err().message)
            state = adv_res.unwrap()
        return state


__all__ = ["DeterministicSchedulerV1", "advance_bout", "finish_bout", "validate_swarm_composition"]
