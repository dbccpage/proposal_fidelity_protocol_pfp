"""Finite graph diagnosis and licensed catalog search through injected ports.

Model turns influence proposal order and challenges, never verification.
Origin: adversary/use_cases/run_graph.py.
The claim is that model turns do not verify graph repairs.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter_ns
import warnings

from operations.domain.rop.result import Err, Refusal, Result
from adversary.domain.evidence import CandidateCheckV1, CheckerVerdict, sha256_ref
from adversary.domain.graph_ports import (
    GraphCheckerPort,
    GraphEvaluationPort,
    GraphLearningPort,
    GraphModelPort,
    GraphPersistencePort,
    GraphRunReferenceV1,
)
from adversary.domain.graph_task import (
    GraphCandidateEvaluationV1,
    GraphPatchV1,
    GraphTaskResultV1,
    GraphTaskV1,
    read_json,
)
from adversary.domain.intelligence_mining import canonical_bytes


def _residual(code: str, message: str) -> bytes:
    return canonical_bytes(
        {"status": "NOT_MEASURED", "code": code, "message": message, "authority_effect": "None"}
    )


def _optional_sha(payload) -> str | None:
    if not payload:
        return None
    return sha256_ref(payload)


def _obligation_fields(obligation: str) -> tuple[str, str]:
    if obligation == "CONSISTENCY":
        return "GRAPH_INCONSISTENT", "declared_graph_exactness"
    return "GRAPH_OBSERVER_BLIND_SPOT", "declared_edge_residual_coverage"


def _challenge_fields(item: GraphCandidateEvaluationV1, challenge_bytes: bytes) -> tuple[str, str]:
    proof = read_json(challenge_bytes)
    if (
        proof["candidate_ref"] != item.candidate_ref
        or proof["replay"].get("result", {}).get("valid") is not True
    ):
        raise ValueError("source challenge does not refute this candidate")
    obligation = read_json(bytes.fromhex(proof["turn"]["output_hex"]))["obligation"]
    if obligation not in {"CONSISTENCY", "OBSERVER_COVERAGE"}:
        raise ValueError("unsupported source challenge obligation")
    return _obligation_fields(obligation)


def _source_event_trigger(item: GraphCandidateEvaluationV1, challenge_bytes: bytes):
    if item.verified_repair:
        return "EXACT_REPAIR", "", ""
    if item.check.verdict is CheckerVerdict.REJECTED:
        failure_class = "GRAPH_PERMISSION_OR_FIDELITY"
        return "STRUCTURAL_DEFECT", failure_class, item.check.reason.split(":", 1)[0]
    if challenge_bytes:
        failure_class, target_pattern = _challenge_fields(item, challenge_bytes)
        return "DEFECT_HUNTER_REFUTATION", failure_class, target_pattern
    return "CATALOG_EVALUATION", "", ""


def source_event(
    task: GraphTaskV1, item: GraphCandidateEvaluationV1, challenge_bytes: bytes = b""
) -> bytes:
    trigger, failure_class, target_pattern = _source_event_trigger(item, challenge_bytes)
    return canonical_bytes(
        {
            "schema_version": "core.adversary.graph-source-event.v1",
            "letter": "R",
            "task_ref": task.task_ref,
            "candidate_ref": item.candidate_ref,
            "checker_receipt_ref": item.check.checker_receipt_sha256,
            "native_evidence_ref": _optional_sha(item.native_evidence_bytes),
            "trigger": trigger,
            "challenge_ref": _optional_sha(challenge_bytes),
            "failure_class": failure_class,
            "target_pattern": target_pattern,
            "authority_effect": "None",
        }
    )


def _new_graph_state(task: GraphTaskV1, mode: str) -> dict:
    return {
        "task": task,
        "mode": mode,
        "turns": [],
        "challenges": [],
        "pending_challenge": None,
        "captured_checks": [],
        "reporting_failure": None,
        "checker_calls": 0,
        "checker_elapsed_ns": 0,
    }


def _captured_record(raw: bytes) -> dict:
    try:
        record = read_json(raw)
        if isinstance(record, dict):
            return record
    except (ValueError, TypeError, UnicodeDecodeError):
        pass
    return {"status": "NOT_MEASURED", "code": "GRAPH_CAPTURE_INVALID_JSON",
        "raw_record_hex": raw.hex()}


def _challenge_history(challenges, pending) -> list:
    captured_rows = [_captured_record(raw) for raw in challenges]
    if pending is None:
        return captured_rows
    return captured_rows + [{"turn": _captured_record(pending), "status": "CHECK_INCOMPLETE"}]


def _checkpoint_history(state: dict, status: str) -> dict:
    task = state["task"]
    return {"schema_version": "core.adversary.graph-working.v1",
        "task_key": task.task_id, "task_ref": task.task_ref,
        "task_hex": task.to_bytes().hex(), "original_seed": task.carrier.prompt,
        "result": {"mode": state["mode"],
            "model_turns": [_captured_record(raw) for raw in state["turns"]],
            "challenges": _challenge_history(state["challenges"], state["pending_challenge"])},
        "candidate_checks": state["captured_checks"],
        "report_context": {"work_status": status, "mode": state["mode"],
            "evidence_verdict": "NOT_ESTABLISHED_BY_REPORTING", "authority_effect": "None"},
        "authority_effect": "None"}


def _invoke_checkpoint(callback, task, history) -> dict:
    try:
        report = callback(task, history)
        if not isinstance(report, dict):
            raise ValueError("GRAPH_REPORT_STATUS_INVALID")
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        report = {"status": "REPORTING_FAILED", "detail": str(exc)}
    return report


def _note_reporting_failure(state: dict, report: dict) -> None:
    if report.get("status") != "REPORTING_FAILED":
        return
    if report.get("detail") == state["reporting_failure"]:
        return
    state["reporting_failure"] = report.get("detail", "report projection unavailable")
    warnings.warn("Graph reporting failed; task outcome unchanged: " + state["reporting_failure"],
        RuntimeWarning)


def _checkpoint(owner: "RunGraphTask", state: dict, status="INCOMPLETE", failure=None) -> None:
    callback = getattr(owner.persistence, "checkpoint", None)
    if not callable(callback):
        return
    history = _checkpoint_history(state, status)
    if failure is not None:
        history["refusal"] = failure.to_dict()
    attempts = getattr(owner.model, "turn_history", ())
    if attempts:
        history["provider_attempts"] = list(attempts)
    _note_reporting_failure(state, _invoke_checkpoint(callback, state["task"], history))


def _refuse_graph_request(task, mode, persistence):
    if type(task) is not GraphTaskV1 or mode not in {"diagnose", "repair"}:
        return Err(Refusal("GRAPH_REQUEST_INVALID",
            "exact graph task and diagnose|repair mode required", "adversary.graph"))
    if persistence is None:
        return Err(Refusal("GRAPH_PERSISTENCE_UNAVAILABLE",
            "graph evidence persistence port is unbound", "adversary.graph"))
    return None


def _run_before_execute(owner: "RunGraphTask", state: dict):
    if owner.before_execute is None:
        return None
    try:
        ready = owner.before_execute(state["task"], state["mode"])
    except BaseException as exc:
        _checkpoint(owner, state, "INTERRUPTED", Refusal("GRAPH_PRE_EXECUTION_INTERRUPTED",
            f"{type(exc).__name__}: {exc}", "adversary.graph"))
        raise
    if ready.is_err:
        _checkpoint(owner, state, "REFUSED", ready.unwrap_err())
        return ready
    return None


def _checker_result(owner: "RunGraphTask", task, raw: bytes) -> CandidateCheckV1:
    if owner.checker is None:
        return CandidateCheckV1(CheckerVerdict.NOT_MEASURED, sha256_ref(raw), sha256_ref(raw),
            "unbound_graph_checker", reason="GRAPH_CHECKER_UNAVAILABLE")
    return owner.checker.check(task, raw)


def _require_check_binding(check, raw: bytes) -> None:
    if (
        type(check) is not CandidateCheckV1
        or check.candidate_id != sha256_ref(raw)
        or check.candidate_content_sha256 != sha256_ref(raw)
    ):
        raise ValueError("GRAPH_CHECK_BINDING_MISMATCH")


def _require_evaluation_binding(item, raw: bytes, check) -> None:
    if (
        type(item) is not GraphCandidateEvaluationV1
        or item.candidate_bytes != raw
        or item.check != check
    ):
        raise ValueError("GRAPH_EVALUATION_BINDING_MISMATCH")


def _accepted_evaluation(owner: "RunGraphTask", task, raw: bytes, check) -> GraphCandidateEvaluationV1:
    if owner.evaluator is None:
        return GraphCandidateEvaluationV1(raw, check, reason="GRAPH_VERIFIER_UNAVAILABLE")
    scored = owner.evaluator.evaluate(task, raw, check)
    if scored.is_ok:
        item = scored.unwrap()
        _require_evaluation_binding(item, raw, check)
        return item
    failure = scored.unwrap_err()
    return GraphCandidateEvaluationV1(raw, check, reason=f"{failure.code}: {failure.message}")


def _evaluate_candidate(owner: "RunGraphTask", state: dict, raw: bytes) -> GraphCandidateEvaluationV1:
    start = perf_counter_ns()
    state["checker_calls"] += 1
    check = _checker_result(owner, state["task"], raw)
    _require_check_binding(check, raw)
    item = GraphCandidateEvaluationV1(raw, check, reason=check.reason)
    if check.verdict is CheckerVerdict.ACCEPTED:
        item = _accepted_evaluation(owner, state["task"], raw, check)
    state["checker_elapsed_ns"] += perf_counter_ns() - start
    state["captured_checks"].append(item.to_dict())
    _checkpoint(owner, state)
    return item


def _catalog_language(task: GraphTaskV1) -> set:
    return {task.candidate_bytes(patch) for patch in task.repair_catalog}


def _catalog_has_edits(task: GraphTaskV1) -> bool:
    return any(patch.edits for patch in task.repair_catalog)


def _read_proposal(owner: "RunGraphTask", state: dict):
    proposed = owner.model.propose(state["task"])
    if proposed.is_err:
        err = proposed.unwrap_err()
        state["turns"].append(_residual(err.code, err.message))
        return None, 0
    turn = proposed.unwrap()
    state["turns"].append(turn)
    data = read_json(turn)
    if data.get("validation_outcome") != "VALID":
        return None, 0
    proposal_bytes = bytes.fromhex(data["output_hex"])
    # Actual bytes, not a provider's honored flag, decide finite membership.
    language = _catalog_language(state["task"])
    return proposal_bytes, int(proposal_bytes in language)


def _collect_proposal(owner: "RunGraphTask", state: dict, can_search: bool):
    if can_search and owner.model is not None:
        proposal_bytes, proposal_valid = _read_proposal(owner, state)
        _checkpoint(owner, state)
        return proposal_bytes, proposal_valid
    return None, 0


def _catalog_map(task: GraphTaskV1) -> dict:
    return {sha256_ref(task.candidate_bytes(patch)): task.candidate_bytes(patch)
        for patch in task.repair_catalog}


def _remaining_catalog(catalog: dict, ordered: list) -> list:
    return [raw for _, raw in sorted(catalog.items()) if raw not in ordered]


def _ordered_candidates(original, proposal_bytes, catalog: dict) -> list:
    ordered = [original.candidate_bytes]
    if proposal_bytes is not None and proposal_bytes not in ordered:
        ordered.append(proposal_bytes)
    ordered.extend(_remaining_catalog(catalog, ordered))
    return ordered


def _same_or_evaluate(owner, state, original, raw: bytes):
    if raw == original.candidate_bytes:
        return original
    return _evaluate_candidate(owner, state, raw)


def _evaluate_search(owner, state, original, ordered, can_search: bool) -> list:
    if not can_search:
        return []
    return [_same_or_evaluate(owner, state, original, raw)
        for raw in ordered[: state["task"].max_candidates]]


def _checked_refs(evaluations) -> set:
    return {item.candidate_ref for item in evaluations if item.independently_checked}


def _search_status(can_search, mode, evaluations, ordered, catalog, task):
    if not can_search:
        if mode == "repair":
            return False, "PERMISSIONS_MISSING"
        return False, "NOT_REQUESTED"
    complete = set(catalog) <= _checked_refs(evaluations)
    if complete:
        return True, "COMPLETE"
    if len(evaluations) < len(ordered) and len(evaluations) == task.max_candidates:
        return False, "BUDGET_EXHAUSTED"
    return False, "VERIFICATION_INCOMPLETE"


def _selected_repair(evaluations):
    verified = [item for item in evaluations if item.verified_repair]
    if not verified:
        return verified, None
    return verified, min(verified, key=lambda item: (item.edit_cost, item.candidate_ref))


def _critique_targets(original, selected) -> list:
    targets = [original]
    if selected is not None and selected.candidate_ref != original.candidate_ref:
        targets.append(selected)
    return targets


def _record_invalid_critique(state, turn, target) -> None:
    state["challenges"].append(canonical_bytes({
        "turn": turn,
        "candidate_ref": target.candidate_ref,
        "replay": read_json(_residual(
            "GRAPH_MODEL_TURN_UNCHECKED",
            "retained model turn has no checked graph answer",
        )),
    }))
    state["pending_challenge"] = None


def _record_critique_replay(state, turn, target, replay) -> None:
    record = {
        "turn": turn,
        "candidate_ref": target.candidate_ref,
        "replay": read_json(replay.unwrap()) if replay.is_ok else replay.unwrap_err().to_dict(),
    }
    state["challenges"].append(canonical_bytes(record))
    state["pending_challenge"] = None


def _localized_increment(replay) -> int:
    outcome = read_json(replay.unwrap())
    return int(outcome.get("valid", outcome.get("result", {}).get("valid")) is True)


def _apply_critique_round(owner, state, target, index):
    if not target.native_evidence_bytes:
        return None
    challenged = owner.model.critique(state["task"], target, index)
    if challenged.is_err:
        err = challenged.unwrap_err()
        state["challenges"].append(_residual(err.code, err.message))
        _checkpoint(owner, state)
        return (0, 0)
    state["pending_challenge"] = challenged.unwrap()
    _checkpoint(owner, state)
    turn = read_json(state["pending_challenge"])
    if turn.get("validation_outcome") != "VALID":
        _record_invalid_critique(state, turn, target)
        _checkpoint(owner, state)
        return (0, 0)
    raw = bytes.fromhex(turn["output_hex"])
    replay = owner.evaluator.challenge(state["task"], target, raw)
    _record_critique_replay(state, turn, target, replay)
    _checkpoint(owner, state)
    if replay.is_err:
        return (0, 0)
    return (1, _localized_increment(replay))


def _run_critiques(owner, state, original, selected):
    critic_valid = critic_localized = 0
    if owner.model is None or owner.evaluator is None:
        return critic_valid, critic_localized
    targets = _critique_targets(original, selected)
    for index in range(state["task"].critique_rounds):
        step = _apply_critique_round(owner, state, targets[index % len(targets)], index)
        if step is None:
            break
        critic_valid += step[0]
        critic_localized += step[1]
    return critic_valid, critic_localized


def _all_evaluations(original, evaluations):
    return tuple({item.candidate_ref: item for item in (original, *evaluations)}.values())


def _localized_challenges(challenges) -> dict:
    localized = {}
    for raw in challenges:
        proof = read_json(raw)
        if proof.get("replay", {}).get("result", {}).get("valid") is True:
            localized[proof["candidate_ref"]] = raw
    return localized


def _source_events(task, evaluations, challenges):
    localized = _localized_challenges(challenges)
    return tuple(source_event(task, item, localized.get(item.candidate_ref, b""))
        for item in evaluations)


def _harvest(owner, task, evaluations, events, challenges):
    if owner.learning is None:
        return _residual("MINING_REPLAY_UNAVAILABLE", "No graph learning replay port is bound.")
    return owner.learning.harvest(task, evaluations, events, tuple(challenges))


def _checked_catalog_count(evaluations, catalog) -> int:
    return len(_checked_refs(evaluations) & set(catalog))


def _graph_metrics(state, proposal_valid, verified, catalog, evaluations, challenges,
                   critic_valid, critic_localized) -> bytes:
    return canonical_bytes(
        {
            "proposal_turns": len(state["turns"]),
            "valid_proposals": proposal_valid,
            "proposal_validity_scope": "actual finite-language bytes and independently replayed decode receipt",
            "verified_repair_candidates": len(verified),
            "catalog_candidates": len(catalog),
            "verified_repair_coverage_scope": "declared catalog",
            "independently_checked_catalog_candidates": _checked_catalog_count(evaluations, catalog),
            "checker_calls": state["checker_calls"],
            "checker_elapsed_ns": state["checker_elapsed_ns"],
            "checker_cost_scope": "permission check plus native evaluation and certificate replay; excludes mining replay",
            "critic_rounds": len(challenges),
            "well_formed_critic_responses": critic_valid,
            "native_valid_challenges": critic_localized,
            "critic_localization_scope": "candidate-bound witness reproduced by native challenge checker",
        }
    )


def _graph_result(state, original, evaluations, selected, search_status, complete,
                  events, harvest, metrics) -> GraphTaskResultV1:
    return GraphTaskResultV1(
        state["task"].task_ref,
        state["mode"],
        original,
        tuple(evaluations),
        selected.candidate_ref if selected else None,
        search_status,
        complete,
        complete and selected is not None,
        tuple(state["turns"]),
        tuple(state["challenges"]),
        events,
        harvest,
        metrics,
    )


def _execute_graph(owner: "RunGraphTask", state: dict):
    task = state["task"]
    original = _evaluate_candidate(owner, state, task.candidate_bytes(GraphPatchV1()))
    can_search = state["mode"] == "repair" and _catalog_has_edits(task)
    proposal_bytes, proposal_valid = _collect_proposal(owner, state, can_search)
    catalog = _catalog_map(task)
    ordered = _ordered_candidates(original, proposal_bytes, catalog)
    evaluations = _evaluate_search(owner, state, original, ordered, can_search)
    complete, search_status = _search_status(
        can_search, state["mode"], evaluations, ordered, catalog, task)
    verified, selected = _selected_repair(evaluations)
    critic_valid, critic_localized = _run_critiques(owner, state, original, selected)
    all_evaluations = _all_evaluations(original, evaluations)
    events = _source_events(task, all_evaluations, state["challenges"])
    harvest = _harvest(owner, task, all_evaluations, events, state["challenges"])
    metrics = _graph_metrics(state, proposal_valid, verified, catalog, evaluations,
        state["challenges"], critic_valid, critic_localized)
    result = _graph_result(state, original, evaluations, selected, search_status, complete,
        events, harvest, metrics)
    return owner.persistence.persist(task, result)


def _execute_guarded(owner: "RunGraphTask", state: dict):
    try:
        return _execute_graph(owner, state)
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, AttributeError) as exc:
        failure = Refusal("GRAPH_EXECUTION_REFUSED", str(exc), "adversary.graph")
        _checkpoint(owner, state, "REFUSED", failure)
        return Err(failure)
    except BaseException as exc:
        _checkpoint(owner, state, "INTERRUPTED", Refusal("GRAPH_EXECUTION_INTERRUPTED",
            f"{type(exc).__name__}: {exc}", "adversary.graph"))
        raise


class RunGraphTask:
    def __init__(
        self,
        *,
        checker: GraphCheckerPort | None,
        evaluator: GraphEvaluationPort | None,
        persistence: GraphPersistencePort | None,
        model: GraphModelPort | None = None,
        learning: GraphLearningPort | None = None,
        before_execute: Callable[[GraphTaskV1, str], Result[None, Refusal]] | None = None,
    ) -> None:
        self.checker, self.evaluator, self.persistence = checker, evaluator, persistence
        self.model, self.learning = model, learning
        self.before_execute = before_execute

    def execute(self, task: GraphTaskV1, mode: str) -> Result[GraphRunReferenceV1, Refusal]:
        refusal = _refuse_graph_request(task, mode, self.persistence)
        if refusal is not None:
            return refusal
        state = _new_graph_state(task, mode)
        _checkpoint(self, state)
        ready = _run_before_execute(self, state)
        if ready is not None:
            return ready
        return _execute_guarded(self, state)
