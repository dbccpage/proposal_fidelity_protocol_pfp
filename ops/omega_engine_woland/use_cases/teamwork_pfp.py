"""Prepare and replay each Woland model contribution through the shared PFP boundary.

This application operation performs no provider dispatch or host effects.
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import TYPE_CHECKING

from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
from omega_engine_pfp.use_cases.pfp_proposal import REPAIR_RULES
from omega_engine_woland.domain.native_gate_check import native_digest
from omega_engine_woland.infrastructure.prompt_geometry import (
    observe_prepared_turn, observe_teamwork_reply, organized_teamwork_seed,
    semantic_geometry_context, trim_geometry_context,
)

if TYPE_CHECKING:
    from .teamwork import TeamworkAction


def _prepared_attempt(action, turn) -> int:
    prefix = action.action_id + ":"
    attempt_id = turn.binding.get("attempt_id", "")
    if not isinstance(attempt_id, str) or not attempt_id.startswith(prefix):
        raise ValueError("PFP_ACTION_BINDING_MISMATCH")
    suffix = attempt_id[len(prefix):]
    if suffix not in {"0", "1", "2", "3"}:
        raise ValueError("PFP_ATTEMPT_INVALID")
    attempt = int(suffix)
    expected = prepare_teamwork_turn(action, attempt=attempt, observe=False)
    if (turn.binding != expected.binding or turn.task != expected.task
            or turn.prompt != expected.prompt):
        raise ValueError("PFP_ACTION_BINDING_MISMATCH")
    return attempt


def hella_preflight(action) -> dict:
    """An in-process syntax check of the supplied action, not task acceptance."""
    operation = _validated_operation(action)
    wire = json.dumps(action.model_dump(mode="json"), ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")
    semantic_wire = json.dumps(semantic_geometry_context(action.model_dump(mode="json")),
        ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    version = action.workflow_version.rsplit(".", 1)[1] if action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4") else "v2"
    checks = {
        "workflow_" + version: action.workflow_version == "omega.woland.teamwork." + version,
        "hella_role": action.role_id == "hella" and action.communication == "deterministic",
        "objective_nonblank": bool(action.objective.strip()),
        "plan_digest": len(action.plan_sha256) == 64 and all(
            c in "0123456789abcdef" for c in action.plan_sha256),
        "json_round_trip": json.loads(wire) == action.model_dump(mode="json"),
    }
    return {**({'operation_validation': operation} if operation else {}),
        "checker_id": "woland.hella.syntax.v1", "action_id": action.action_id,
        "input_sha256": hashlib.sha256(semantic_wire).hexdigest(), "checks": checks,
        "findings": [name + " failed" for name, passed in checks.items() if not passed]}


def validate_teamwork_observation(action, observation) -> None:
    """Replay actual bytes; stored verdicts and role labels cannot admit prose."""
    if observation.blocked and "pfp" not in observation.metadata:
        code = observation.metadata.get("failure_code")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("PFP_RAW_REPLY_REQUIRED")
        return
    if action.communication == "deterministic":
        record = hella_preflight(action)
        raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        check = observation.check
        if (observation.metadata.get("execution_kind") != "deterministic"
                or observation.metadata.get("deterministic_check") != record or check is None
                or check.initial_task_id != action.initial_task_id
                or check.source_id != action.plan_sha256
                or check.checker_id != record["checker_id"]
                or check.command != ("woland", "teamwork", "check", "hella")
                or check.output_sha256 != hashlib.sha256(raw).hexdigest()
                or check.exit_status != (1 if record["findings"] else 0)
                or check.artifacts != action.artifacts
                or observation.findings != tuple(record["findings"])):
            raise ValueError("HELLA_CHECK_REQUIRED: replay the deterministic preflight")
        return
    if action.communication == "host":
        if observation.metadata.get("execution_kind") != "host":
            raise ValueError("HOST_CHECK_REQUIRED")
        return
    record = observation.metadata.get("pfp")
    if type(record) is not dict:
        raise ValueError("PFP_RAW_REPLY_REQUIRED")
    attempt = observation.metadata.get("pfp_attempt")
    if type(attempt) is not int or not 0 <= attempt <= 3:
        raise ValueError("PFP_ATTEMPT_INVALID")
    turn = prepare_teamwork_turn(action, attempt=attempt, observe=False)
    try:
        replayed = turn.replay(record)
        raw = base64.b64decode(record["raw_reply_base64"], validate=True)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError("PFP_REPLAY_MISMATCH") from exc
    # JSON storage normalizes tuples to arrays; compare the retained wire values.
    if any(json.dumps(record.get(key), sort_keys=True) != json.dumps(value, sort_keys=True)
           for key, value in replayed.items()):
        raise ValueError("PFP_REPLAY_MISMATCH: stored verdict differs from actual bytes")
    # The replay must see the same remote-template stamp the live check saw; it can only
    # mark lessons proposed-only, never installed.
    stamp = observation.metadata.get("remote_executor")
    expected = check_teamwork_reply(action, turn, raw, worker=observation.worker, observe=False,
        **({"metadata": {"remote_executor": stamp}} if type(stamp) is str and stamp else {}))
    if "pfp_prepared_prompts" in expected.metadata and (
            observation.metadata.get("pfp_prepared_prompts") != expected.metadata["pfp_prepared_prompts"]):
        raise ValueError("PFP_PREPARED_PROMPT_MISMATCH")
    if action.operation_binding is not None and (
            observation.metadata.get('operation_execution') != expected.metadata.get('operation_execution')):
        raise ValueError('OPERATION_EXECUTION_MISMATCH')
    if (observation.metadata.get("execution_kind") != "pfp"
            or observation.metadata.get("host_tools_executed") is not False
            or observation.metadata.get("installed_changes") is not False
            or observation.content != expected.content
            or observation.findings != expected.findings
            or (not observation.blocked and observation.summary != expected.summary)
            or (expected.blocked and not observation.blocked)):
        raise ValueError("PFP_OBSERVATION_MISMATCH: retain the checked proposal")
    if action.kind == "learn":
        for key in ("lessons", "proposed_only", "installed_changes", "changed_paths",
                    "no_change_reason", "verification", "consumed_ddc_root", "consumed_procedure_sha256"):
            if observation.metadata.get(key) != expected.metadata.get(key):
                raise ValueError("PFP_OBSERVATION_MISMATCH: retain checked learning")

def prepare_teamwork_turn(action: TeamworkAction, *, attempt: int = 0, feedback=None, observe: bool = True):
    if action.communication != "pfp":
        raise ValueError("PFP_NOT_APPLICABLE: use the deterministic host operation")
    if type(attempt) is not int or not 0 <= attempt <= 3:
        raise ValueError("PFP_ATTEMPT_INVALID")
    _validated_operation(action)
    expected_feedback = REPAIR_RULES["TASK_ENVELOPE"] if attempt else None
    if feedback is not None and feedback != expected_feedback:
        raise ValueError("PFP_FEEDBACK_INVALID")
    feedback = expected_feedback
    compact = bool(action.brief and action.brief.response_profile in ("compact-v1", "compact-v2"))
    bounded = bool(action.brief and action.brief.context_profile == "bounded-v1")
    nonblank = {"type": "string", "minLength": 1, "pattern": r"\S"}
    schema = nonblank
    if action.kind in ("review", "learn"):
        properties = {
            "summary": nonblank,
            "findings": {"type": "array", "items": nonblank},
        }
        required = ["summary", "findings"]
        if action.kind == "learn":
            properties.update(lessons={"type": "array", "items": {"anyOf": [
                nonblank, {"type": "object", "minProperties": 1}]}},
                changed_paths={"type": "array", "items": nonblank},
                no_change_reason={"type": "string"}, verification={"type": "array"})
            required.append("lessons")
            if action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
                if action.ddc_program is None:
                    raise ValueError("DDC_READBACK_REQUIRED: Bezdomny requires the host-read procedure")
                properties.update(consumed_ddc_root={"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    consumed_procedure_sha256={"type": "string", "pattern": "^[0-9a-f]{64}$"})
                required.extend(("consumed_ddc_root", "consumed_procedure_sha256"))
        schema = dict(type="object", properties=properties, required=required,
            additionalProperties=False)
    if compact:
        if action.kind in ("build", "repair") and action.brief.checked_reuse_result is not None:
            result = action.brief.checked_reuse_result
            schema = {"type": "object", "properties": {
                "recipe_id": {"type": "string", "const": result.recipe_id},
                "candidate_sha256": {"type": "string", "const": result.target_candidate_sha256},
            }, "required": ["recipe_id", "candidate_sha256"], "additionalProperties": False}
        elif action.kind in ("build", "repair") and action.brief.artifact_schema is not None:
            schema = action.brief.artifact_schema
        elif action.kind in ("review", "learn"):
            properties = {"summary": {**nonblank, "maxLength": 300},
                "findings": {"type": "array", "maxItems": 8,
                    "items": {**nonblank, "maxLength": 400}}}
            required = ["summary", "findings"]
            if action.kind == "learn":
                properties["lessons"] = {"type": "array", "maxItems": 6,
                    "items": {**nonblank, "maxLength": 400}}
                required.append("lessons")
                for name in ("consumed_ddc_root", "consumed_procedure_sha256"):
                    properties[name] = {"type": "string", "const": action.ddc_program.learning_reply_binding[name]}
                    required.append(name)
                # IDE learning retains its explicit changed-file/no-change obligation.
                properties["no_change_reason"] = {"type": "string", "maxLength": 400}
                properties["changed_paths"] = {"type": "array", "items": nonblank, "maxItems": 20}
                required.extend(("no_change_reason", "changed_paths"))
            schema = dict(type="object", properties=properties, required=required,
                additionalProperties=False)
    context = semantic_geometry_context(action.model_dump(mode="json"))
    if action.workflow_version == "omega.woland.teamwork.v4":
        selection = context["native_gate_check"]
        if selection.get("kernel_check") is not None:
            context["kernel_obligation"] = {key: selection["kernel_check"][key] for key in
                ("proof_artifact_path", "required_declarations", "axiom_policy", "toolchain_pin")}
        context["native_gate_check"] = {"binding_sha256": native_digest(selection),
            "policy": selection["policy"], "binary_sha256": selection["binary_sha256"]}
        program = context.get("ddc_program")
        if program is not None:
            nested = program["premises"].get("native_gate_check")
            if nested is not None and nested.get("kernel_check") is not None:
                program["premises"]["native_gate_check"] = {
                    "binding_sha256": native_digest(nested), "policy": nested["policy"],
                    "binary_sha256": nested["binary_sha256"]}
        context.pop("native_host_observations", None)
        batches = context["native_gate_batches"]
        context["native_gate_batches"] = [{key: batch[key] for key in ("path", "sha256", "receipt_sha256")}
                                          for batch in batches]
        if batches:
            summary = batches[-1]["summary"]
            context["native_gate_diagnostics"] = {"checkpoint": batches[-1]["scope"]["stage"],
                "coverage_complete": summary["coverage_complete"], "all_pass": summary["all_pass"],
                "counts": {status: list(summary["outcomes"].values()).count(status)
                           for status in sorted(set(summary["outcomes"].values()))},
                "residuals": summary["residuals"], "authority_effect": "None"}
    instructions = action.instructions
    if compact:
        if not bounded:
            context = _compact_context(action, context)
            instructions = instructions.partition("\nTask brief (")[0]
        instructions += (" Return only the bound JSON response instance. "
            "A QUERY_USER_MORE_INFO artifact asks for missing task premises; it is not a solved result. "
            "Do not invent premises or claim host checks, trust, native admission or installed changes. "
            "Review missing-input requests against the declared task, without requiring a speculative solution.")
        if action.brief.response_profile == "compact-v2":
            instructions += (" Keep summary at most 150 characters, and each finding or lesson at most 200. "
                "Findings are concrete new artifact defects; do not put approval, known missing inputs or "
                "'no new defects' in findings. A host-checked clarification remains NOT_SOLVED. "
                "Historical finding and DDC certificate digests reference retained evidence; their full text "
                "is not included in this prompt. Do not claim to have read omitted text.")
    if bounded:
        context = _bounded_context(action, context)
        instructions = _without_duplicate_brief(action, instructions)
        instructions += (" Historical certificate text and long earlier contributions are digest-bound "
            "references to retained evidence. Read that evidence with host tools when needed; do not "
            "claim omitted text was read. Current task requirements and unresolved findings remain intact. "
            "This evidence view does not change the answer contract or grant authority.")
    trim_geometry_context(context)
    turn = prepare_task_turn(
        system="You are a practical Woland teamwork operator. " + instructions,
        user=organized_teamwork_seed(action), task_id=action.initial_task_id or action.action_id,
        attempt_id=f"{action.action_id}:{attempt}", answer_schema=schema,
        context=context,
        checker_id="woland-role-shape-v1:" + action.kind, feedback=feedback)
    if bounded:
        # Match Natasha's existing per-string limit on the *serialized* retained
        # preparation, including escaping, schema and binding, before dispatch.
        prepared = {"system": turn.prompt.system, "user": turn.prompt.user,
            "response_schema": turn.prompt.response_schema, "binding": turn.binding}
        size = len(json.dumps(prepared, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode("utf-8"))
        if size > 65_536:
            raise ValueError(f"PFP_CONTEXT_BUDGET_EXCEEDED: protected preparation requires {size} UTF-8 bytes; limit 65536")
    return observe_prepared_turn(action, turn) if observe else turn


def _compact_context(action, full_context, *, evidence_references=None):
    """Project role facts, binding the semantic action without reporting fields."""
    context = {key: full_context[key] for key in (
        "action_id", "run_id", "kind", "role_id", "phase", "workflow_version", "plan_sha256",
        "candidate", "findings", "artifacts", "check_source_id", "check_source_paths",
        "checker_id", "stopped_reason", "stopped_status", "evaluations_used", "evaluation_limit",
        "role_contributions", "learning_context", "route", "operator", "intelligence",
        "source_reads", "check_command", "kernel_obligation") if key in full_context}
    profile_v2 = action.brief.response_profile == "compact-v2" if evidence_references is None else evidence_references
    context["response_profile"] = ("omega.woland.role-prompt.compact.v2" if profile_v2
                                   else "omega.woland.role-prompt.compact.v1")
    context["full_action_sha256"] = native_digest(semantic_geometry_context(action.model_dump(mode="json")))
    context["brief"] = {key: full_context["brief"][key] for key in
        ("deliverable", "constraints", "acceptance", "skills", "anti_skills", "builder",
         "reviewer", "repairer", "scene")}
    seat_operads = [{"skill_id": item.skill_id, "guidance": item.guidance}
                    for item in action.brief.operads if action.role_id in item.seats]
    if seat_operads:
        context["brief"]["operads"] = seat_operads
    if action.brief.task_premises is not None:
        context["task_premises"] = action.brief.task_premises
    if action.brief.checked_reuse_result is not None:
        result = action.brief.checked_reuse_result
        context["checked_reuse"] = {"recipe_id": result.recipe_id,
            "registry_sha256": result.registry_sha256,
            "semantic_ddc_root": result.semantic_ddc_root,
            "candidate_sha256": result.target_candidate_sha256,
            "candidate": action.brief.checked_reuse_candidate,
            "outcome": result.outcome, "mathematical_acceptance": result.mathematical_acceptance,
            "role": "Host-checked registered recipe; builder acknowledges its exact identity. Original task is freshly rechecked after all reviewers."}
    for key in ("native_gate_check", "native_gate_batches", "native_gate_diagnostics"):
        if key in full_context:
            context[key] = full_context[key]
    # Native residuals are linked by exact receipt digest; no PASS is inferred.
    if "native_gate_diagnostics" in context:
        diagnostics = context["native_gate_diagnostics"]
        diagnostics["residual_count"] = len(diagnostics.pop("residuals"))
        diagnostics["semantic_admission"] = "NOT_ESTABLISHED"
    if action.ddc_program is not None:
        program = action.ddc_program
        context["ddc_program"] = {
            "binding": program.binding.model_dump(mode="json"),
            "procedure_sha256": program.procedure_sha256,
            "learning_reply_binding": program.learning_reply_binding,
            "steps": program.model_dump(mode="json")["steps"],
            "host_observation": program.host_observation.model_dump(mode="json") if program.host_observation else None,
            "fresh_checker_required": True, "mathematical_acceptance": "UNVERIFIED",
            "authority_effect": "None",
        }
        if profile_v2:
            projected = context["ddc_program"]
            projected.update(run_path=program.run_path, source_id=program.source_id,
                model_view="host-readback-structure-with-certificate-digests.v1",
                certificate_text_included=False)
            steps = []
            for original in projected["steps"]:
                step = dict(original)
                certificate = step.pop("certificate")
                step.update(certificate_sha256=hashlib.sha256(certificate.encode("utf-8")).hexdigest(),
                    certificate_characters=len(certificate), complete_step_sha256=native_digest(original))
                if "observed_procedure" in step:
                    procedure = step.pop("observed_procedure")
                    step["observed_procedure_reference"] = {
                        "sha256": native_digest(procedure), "items": len(procedure),
                        "model_view": "digest-reference.v1; observed procedure text omitted"}
                steps.append(step)
            projected["steps"] = steps
    if profile_v2:
        context["brief"]["clarification_policy"] = action.brief.clarification_policy
        if "clarification_context" in full_context:
            context["clarification_context"] = _clarification_reference(full_context["clarification_context"])
        context["role_contributions"] = [{
            **{key: value for key, value in row.items() if key != "findings"},
            "findings_count": len(row["findings"]), "findings_sha256": native_digest(row["findings"]),
        } for row in context.get("role_contributions", [])]
        if context.get("intelligence") is not None:
            context["intelligence"] = _historical_intelligence_reference(context["intelligence"])
        context["source_reads"] = [_historical_intelligence_reference(row)
                                   for row in context.get("source_reads", [])]
        if context.get("learning_context") is not None:
            learning = dict(context["learning_context"])
            for key in ("learning", "digestion"):
                if learning.get(key) is not None:
                    learning[key] = _learning_observation_reference(learning[key])
            if learning.get("clarification_context") is not None:
                learning["clarification_context"] = _clarification_reference(learning["clarification_context"])
            context["learning_context"] = learning
        context["historical_findings_view"] = "digest-references.v1; current unresolved findings remain in findings"
    return context


def _without_duplicate_brief(action, instructions):
    """Remove only the exact typed brief duplicate, retaining suffix guidance."""
    head, marker, tail = instructions.partition("\nTask brief (")
    if not marker or "): " not in tail:
        return instructions
    body = tail.partition("): ")[2]
    try:
        decoded, end = json.JSONDecoder().raw_decode(body)
        visible = action.brief.model_dump(mode="json", exclude={"forge_preparation"})
        # A historical action can be explicitly prepared using a new view;
        # this selection is not a new task requirement.
        for value in (decoded, visible):
            value.pop("context_profile", None)
        if decoded != visible:
            return instructions
    except (ValueError, TypeError, AttributeError):
        return instructions
    return head + body[end:]


def _bounded_context(action, full_context):
    """Reuse the existing v2 evidence view without changing reply semantics."""
    context = _compact_context(action, full_context, evidence_references=True)
    context["context_profile"] = "omega.woland.context.bounded.v1"
    context["response_profile"] = action.brief.response_profile

    def retained_text(record, field):
        value = record.get(field)
        if not isinstance(value, str):
            return
        raw = value.encode("utf-8")
        if len(raw) > 768:
            record[field] = raw[:768].decode("utf-8", errors="ignore")
            record[field + "_reference"] = {"sha256": hashlib.sha256(raw).hexdigest(),
                "utf8_bytes": len(raw), "model_view": "prefix-only; full text retained in action history"}

    for row in context.get("role_contributions", []):
        retained_text(row, "summary")
    learning = context.get("learning_context")
    if learning:
        for key in ("learning", "digestion"):
            record = learning.get(key)
            if record:
                retained_text(record, "content")
                retained_text(record, "summary")
    return context


def _historical_intelligence_reference(record):
    return {**{key: value for key, value in record.items() if key != "findings"},
        "complete_record_sha256": native_digest(record),
        "findings_reference": {"sha256": native_digest(record["findings"]),
            "count": len(record["findings"]),
            "model_view": "digest-reference.v1; historical finding text omitted"}}


def _learning_observation_reference(record):
    projected = {key: value for key, value in record.items()
                 if key not in ("metadata", "ddc_program", "intelligence")}
    projected["complete_observation_sha256"] = native_digest(record)
    if record.get("intelligence") is not None:
        projected["intelligence"] = _historical_intelligence_reference(record["intelligence"])
    if record.get("ddc_program") is not None:
        program = record["ddc_program"]
        projected["ddc_program_reference"] = {key: program[key]
            for key in ("binding", "source_id", "run_path", "learning_reply_binding")}
    metadata = record["metadata"]
    if metadata.get("role_id") == "host_digestion":
        findings = projected.pop("findings")
        projected["findings_reference"] = {"sha256": native_digest(findings), "count": len(findings),
            "model_view": "digest-reference.v1; current unresolved findings remain in action findings"}
    projected["metadata_reference"] = {"sha256": native_digest(metadata),
        "model_view": "digest-reference.v1; raw wires and unlisted metadata omitted"}
    projected["metadata"] = {key: value for key, value in metadata.items() if key in (
        "role_id", "learning_stage", "lessons", "learning_findings", "changed_paths", "no_change_reason",
        "verification", "consumed_ddc_root", "consumed_procedure_sha256", "installed_changes", "proposed_only",
        "run_budget", "cost_usd", "input_tokens", "output_tokens", "failure_code", "attempt_state",
        "attempt_id", "generation_id", "provider", "model", "transport", "request_digest")}
    if isinstance(metadata.get("pfp"), dict):
        projected["metadata"]["pfp"] = {key: value for key, value in metadata["pfp"].items()
                                         if key != "raw_reply_base64"}
    return projected


def _clarification_reference(record):
    projected = dict(record)
    if "advisory_findings" in projected:
        findings = projected.pop("advisory_findings")
        projected["advisory_findings_reference"] = {"sha256": native_digest(findings), "count": len(findings),
            "model_view": "digest-reference.v1; current unresolved findings remain in action findings"}
    return projected



def _validated_operation(action):
    if action.operation_binding is None:
        if action.operation_required:
            raise ValueError('RETINUE_OPERATION_BINDING_REQUIRED')
        return None
    from omega_engine_woland.infrastructure.operad_binding import validate_operation_binding
    legacy = action.brief is None or action.brief.context_profile == "legacy-v1"
    return validate_operation_binding(action.operation_binding, role_id=action.role_id,
        preparation_profile="legacy-v1" if legacy else None)


def check_teamwork_reply(action, turn, raw, *, worker, metadata=None, judges=(), observe: bool = True):
    from .teamwork import TeamworkObservation

    attempt = _prepared_attempt(action, turn)
    checked = turn.check(raw, judges=judges)
    metadata = {**(metadata or {}), "pfp": checked, "host_tools_executed": False,
        "installed_changes": False,
        "role_id": action.role_id, "execution_kind": "pfp", "pfp_attempt": attempt}
    if action.brief is not None and action.brief.density_dimension is not None:
        metadata["pfp_prepared_prompts"] = {"system":turn.prompt.system, "user":turn.prompt.user,
            "response_schema":turn.prompt.response_schema, "binding":turn.binding}
    reply_geometry = observe_teamwork_reply(action, raw) if observe else None
    if reply_geometry is not None:
        prepared = turn if turn.observation_metadata else observe_prepared_turn(action, turn)
        metadata["density"] = {**prepared.observation_metadata["density"], "reply":reply_geometry}
    operation = _validated_operation(action)
    if operation:
        metadata['operation_execution'] = {**operation,
            'input_sha256': turn.binding['input_sha256'],
            'executed_operation_ids': operation['operation_ids'],
            'executed_guard_ids': [guard['op_id'] for guard in operation['guards']],
            'reply_checker_id': turn.binding['checker_id'],
            'outcome': checked['failure_class'], 'authority_effect': 'None'}
    if not checked["schema_valid"] or checked["failure_class"] != "NONE":
        code = ("MALFORMED_LEARNING" if action.kind == "learn" else
            "MALFORMED_REVIEW" if action.kind == "review" else "PFP_" + checked["failure_class"])
        return TeamworkObservation(action_id=action.action_id, worker=worker, blocked=True,
            summary="PFP reply rejected; the original task remains open.",
            metadata={**metadata, "failure_code": code})
    answer = checked["answer"]
    if action.kind in ("review", "learn"):
        if action.kind == "learn":
            if action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
                program = action.ddc_program
                if (program is None or answer["consumed_ddc_root"] != program.binding.semantic_ddc_root
                        or answer["consumed_procedure_sha256"] != program.procedure_sha256):
                    return TeamworkObservation(action_id=action.action_id, worker=worker, blocked=True,
                        summary="PFP reply rejected; the original task remains open.",
                        metadata={**metadata, "failure_code": "DDC_CONSUMPTION_MISMATCH"})
                metadata.update(consumed_ddc_root=answer["consumed_ddc_root"],
                    consumed_procedure_sha256=answer["consumed_procedure_sha256"])
            # A remote provider template stamps its name; the openrouter: prefix is the older marker.
            remote = worker.startswith("openrouter:") or bool(metadata.get("remote_executor"))
            metadata.update(lessons=answer["lessons"], learning_findings=answer["findings"],
                proposed_only=remote, installed_changes=False,
                changed_paths=[] if remote else answer.get("changed_paths", []))
            for key in ("no_change_reason", "verification"):
                if key in answer and not remote:
                    metadata[key] = answer[key]
            findings = tuple(answer["findings"])
            if not remote and not findings:
                paths = metadata.get("changed_paths", [])
                reason = metadata.get("no_change_reason", "")
                changed = isinstance(paths, (list, tuple)) and bool(paths) and all(
                    isinstance(path, str) and path.strip() for path in paths)
                if not changed and not (isinstance(reason, str) and reason.strip()):
                    return TeamworkObservation(
                        action_id=action.action_id, worker=worker, blocked=True,
                        summary="PFP reply rejected; the original task remains open.",
                        metadata={**metadata, "failure_code": "LEARNING_OUTCOME_REQUIRED"})
        else:
            findings = tuple(answer["findings"])
        return TeamworkObservation(action_id=action.action_id, worker=worker,
            summary=answer["summary"], findings=findings, metadata=metadata)
    if action.kind in ("build", "repair") and action.brief and action.brief.checked_reuse_result is not None:
        # The model acknowledges an exact host-derived candidate; it does not
        # supply new candidate bytes or a mathematical certificate.
        answer = action.brief.checked_reuse_candidate
        metadata["artifact_encoding"] = "checked-ddc-reuse-acknowledgement-v1"
        metadata["checked_reuse_candidate_sha256"] = action.brief.checked_reuse_result.target_candidate_sha256
    elif action.kind in ("build", "repair") and action.brief and action.brief.artifact_schema is not None:
        answer = json.dumps(answer, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        metadata["artifact_encoding"] = "canonical-json-from-bound-answer-v1"
    return TeamworkObservation(action_id=action.action_id, worker=worker, content=answer,
        summary="PFP-checked proposal; task correctness remains unverified.", metadata=metadata)

