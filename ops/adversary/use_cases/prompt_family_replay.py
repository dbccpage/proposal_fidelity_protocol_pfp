"""Replay a call ledger into a validated prompt family.

Reads rows exactly as ``openrouter_seat_gateway.CallLedger`` writes them. Fields
the ledger does not hold stay ``None``: a reply with no stored digest yields a
call record but no output node and no repair step, and no checker verdict is
invented (``NOT_MEASURED``). The default terminal is a typed residual because no
external checker has run. AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from operations.domain.rop.result import Err, Refusal, Result
from adversary.domain.native import NativeOperationPort
from adversary.domain.prompt_family import (
    CallRecordV1,
    FitnessV1,
    PromptFamilyV1,
    PromptNodeV1,
    ReaderV1,
    RepairStepV1,
    ShapeV1,
    TerminalV1,
    text_digest,
    validate_family,
)

_REPLIED = frozenset({"OK", "MALFORMED"})


def _reader(row: Mapping[str, Any], facts: Mapping[str, Mapping[str, Any]]) -> ReaderV1:
    model = row.get("model") or "unrouted"
    known = facts.get(model, {})
    temp = row.get("temperature_sent")
    return ReaderV1(
        model=model,
        router=row.get("router") or "unrouted",
        seat_id=str(row.get("seat_id")),
        tier=str(row.get("tier")),
        config_digest=str(row.get("config_digest")),
        temperature=None if temp is None else str(temp),
        params_billion=known.get("params_billion"),
        open_weights=known.get("open_weights"),
    )


def family_from_ledger(
    *,
    bout_id: str,
    prompt_text: str,
    rows: Sequence[Mapping[str, Any]],
    model_facts: Mapping[str, Mapping[str, Any]] | None = None,
    terminal: TerminalV1 | None = None,
    native_support: NativeOperationPort,
) -> Result[PromptFamilyV1, Refusal]:
    facts = model_facts or {}
    mine = [r for r in rows if r.get("bout_id") == bout_id]
    if not mine:
        return Err(Refusal("FAMILY_NO_CALLS", f"no ledger rows for bout {bout_id!r}", "prompt_family_replay"))
    for row in mine:
        cost = row.get("cost_microusd")
        if cost is None:
            return Err(Refusal("FAMILY_COST_UNOBSERVED", "v1 call families require observed cost; preserve unknown native billing separately", "prompt_family_replay"))
        if type(cost) is not int or cost < 0:
            return Err(Refusal("FAMILY_COST", "cost_microusd must be a nonnegative integer", "prompt_family_replay"))

    root = PromptNodeV1(text_digest(prompt_text), "root", ShapeV1.from_text(prompt_text, native_support=native_support))
    readers: dict[str, ReaderV1] = {}
    nodes: dict[str, PromptNodeV1] = {root.node_id: root}
    calls: list[CallRecordV1] = []
    steps: list[RepairStepV1] = []

    for row in mine:
        reader = _reader(row, facts)
        readers[reader.digest()] = reader
        call = CallRecordV1(
            bout_id=bout_id,
            request_digest=str(row.get("request_digest")),
            reader_digest=reader.digest(),
            leg_index=int(row.get("leg_index") or 0),
            outcome=str(row.get("outcome")),
            cost_microusd=row["cost_microusd"],
            cost_source=row.get("cost_source"),
            input_tokens=row.get("input_tokens"),
            output_tokens=row.get("output_tokens"),
            max_tokens=row.get("max_tokens"),
            finish_reason=row.get("finish_reason"),
            ddc_letter=row.get("ddc_letter"),
            residual_colour=row.get("residual_colour"),
            reply_digest=row.get("reply_digest"),
        )
        calls.append(call)
        if call.outcome in _REPLIED and call.reply_digest:
            child = PromptNodeV1(
                call.reply_digest, "repaired_from", None, root.node_id, reader.digest()
            )
            nodes.setdefault(child.node_id, child)
            steps.append(
                RepairStepV1(
                    input_node_id=root.node_id,
                    output_node_id=child.node_id,
                    ddc_letter=call.ddc_letter,
                    residual_before=None,
                    residual_after=call.residual_colour,
                    call_ids=(call.call_id,),
                    fitness=FitnessV1(
                        cost_microusd=call.cost_microusd,
                        input_tokens=call.input_tokens or 0,
                        output_tokens=call.output_tokens or 0,
                    ),
                )
            )

    family = PromptFamilyV1(
        readers=tuple(readers.values()),
        nodes=tuple(nodes.values()),
        calls=tuple(calls),
        steps=tuple(steps),
        terminal=terminal or TerminalV1("TypedResidual", "NO_EXTERNAL_CHECKER_RUN"),
    )
    return validate_family(family, native_support=native_support)


def _program_digest(value) -> str:
    import hashlib
    import json

    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("DDC_PROGRAM_DUPLICATE_KEY")
            result[key] = item
        return result

    wire_value = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False), object_pairs_hook=unique)
    return hashlib.sha256(json.dumps(wire_value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _valid_ddc_receipt_id(receipt_id, bundle_version):
    """Validate the declared wire format without normalizing the retained ID."""
    if type(receipt_id) is not str:
        return False
    if bundle_version in ("core.adversary.reported-run-bundle.v1", "core.adversary.reported-run-bundle.v2"):
        if not receipt_id.startswith("sha256:"):
            return False
        digest = receipt_id[len("sha256:"):]
    elif bundle_version is None:
        digest = receipt_id
    else:
        return False
    return len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


def persist_ddc_program(*, output_dir, task_key, trace_path, prompt_text, family_id,
                        template_version, premises, stage_artifacts=None, mode_artifacts=None,
                        recover_existing=False, retained_context=None, current_open_obligations=None, native_support: NativeOperationPort):
    """Seal actual validated transitions with the existing versioned native writer.

    Caller supplies observed stage/mode artifacts; nothing is inferred from
    character names. Native billing remains absent rather than measured zero.
    """
    import json
    from datetime import datetime, timezone
    from pathlib import Path

    from pfp.domain.aggregates.research_run_root import semantic_dda_from_trace
    from adversary.domain.prompt_family import DdcProgramBinding
    from adversary.use_cases.skill_run_persistence import persist_skill_run

    stage_artifacts = {} if stage_artifacts is None else stage_artifacts
    mode_artifacts = {} if mode_artifacts is None else mode_artifacts
    if current_open_obligations is not None and (
            not isinstance(current_open_obligations, (list, tuple))
            or any(not isinstance(item, str) or not item.strip() for item in current_open_obligations)):
        raise ValueError("DDC_PROGRAM_CURRENT_SCOPE_INVALID")
    before = Path(trace_path).read_bytes()
    _, root = semantic_dda_from_trace(trace_path)
    if Path(trace_path).read_bytes() != before:
        raise ValueError("DDC_PROGRAM_SOURCE_CHANGED")
    binding = DdcProgramBinding(family_id=family_id, template_version=template_version,
        storage_task_key=task_key,
        prompt_sha256=text_digest(prompt_text).removeprefix("sha256:"),
        premises_sha256=_program_digest(premises), semantic_ddc_root=root,
        completed_stages=tuple(stage_artifacts), mode_ids=tuple(mode_artifacts),
        stage_artifacts_sha256=_program_digest(stage_artifacts),
        mode_artifacts_sha256=_program_digest(mode_artifacts))
    existing = Path(output_dir) / "runs" / task_key
    if recover_existing and existing.exists():
        load_ddc_program(existing, expected=binding, initial_task_id=task_key, native_support=native_support)
        return existing, binding
    stored = persist_skill_run(Path(output_dir), task_key=task_key, objective=prompt_text,
        verdict="OPEN_RESIDUAL", source="adversary_ddc_program",
        novella_md="Retained DDC procedure; fresh task-specific checks are required before acceptance.\n",
        created_utc=datetime.now(timezone.utc).isoformat(), work_status="partial",
        dda_steps=[json.loads(line) for line in before.decode("utf-8").splitlines()],
        summary={"ddc_program": binding.model_dump(mode="json"),
                 "stage_artifacts": json.loads(json.dumps(stage_artifacts)),
                 "mode_artifacts": json.loads(json.dumps(mode_artifacts)),
                 **({"retained_context": json.loads(json.dumps(retained_context, allow_nan=False))}
                    if retained_context is not None else {}),
                 "billing_status": "UNOBSERVED", "cost_usd": None,
                 "open_obligations": ["Fresh host acceptance of the current candidate is required."]
                    if current_open_obligations is None else list(current_open_obligations),
                 **({"reuse_obligations": ["Fresh host acceptance of the current candidate is required."]}
                    if current_open_obligations is not None else {})}, native_support=native_support)
    if isinstance(stored, Err):
        raise ValueError("DDC_PROGRAM_PERSIST_FAILED: " + stored.error.code + ": " + stored.error.message)
    # Completion includes actual sealed-byte readback, not just a writer return.
    load_ddc_program(stored.value, expected=binding, initial_task_id=task_key, native_support=native_support)
    return stored.value, binding


def load_ddc_program(run_path, *, expected, initial_task_id, native_support: NativeOperationPort):
    """Recheck native bundle custody, exact premises and semantic trace identity."""
    import json
    from pathlib import Path

    from pfp.domain.aggregates.research_run_root import semantic_dda_from_records
    from adversary.domain.prompt_family import DdcProgramBinding
    from adversary.infrastructure.teamwork_intelligence_host import read_intelligence
    from adversary.use_cases.persistence import _dda_tape
    from adversary.use_cases.skill_run_persistence import (
        SKILL_RUN_RECEIPT_SCHEMA,
        parse_dda_actions,
    )

    if type(expected) is not DdcProgramBinding:
        raise ValueError("DDC_PROGRAM_BINDING_REQUIRED")
    run_path = Path(run_path)
    source = read_intelligence(run_path, initial_task_id=initial_task_id)
    if source.coverage_gaps:
        raise ValueError("DDC_PROGRAM_CUSTODY_REFUSED: " + ";".join(source.coverage_gaps))
    summary = json.loads((run_path / "summary.json").read_bytes())
    receipt = json.loads((run_path / "receipt.json").read_bytes())
    required_metadata = {"source": "adversary_ddc_program", "task_key": expected.storage_task_key,
                         "authority_effect": "None", "terminal_verdict": "OPEN_RESIDUAL",
                         "checker_receipt": None, "checker_receipt_sha256": None}
    if (receipt.get("schema") != SKILL_RUN_RECEIPT_SCHEMA
            or any(key not in payload or payload[key] != value
                   for payload in (receipt, summary) for key, value in required_metadata.items())
            or receipt.get("receipt_id") != summary.get("receipt_id")
            or receipt.get("bundle_schema_version") != summary.get("bundle_schema_version")
            or not _valid_ddc_receipt_id(receipt.get("receipt_id"), receipt.get("bundle_schema_version"))
            or any(type(payload.get("objective")) is not str for payload in (receipt, summary))
            or any(text_digest(payload.get("objective", "")).removeprefix("sha256:") != expected.prompt_sha256
                   for payload in (receipt, summary))
            or summary.get("billing_status") != "UNOBSERVED"
            or "cost_usd" not in summary or summary["cost_usd"] is not None):
        raise ValueError("DDC_PROGRAM_METADATA_MISMATCH")
    stored = DdcProgramBinding.model_validate_json(json.dumps(summary["ddc_program"]))
    raw = (run_path / "ddc.jsonl").read_bytes()
    wrapped = parse_dda_actions(raw.decode("utf-8"), native_support=native_support)
    if isinstance(wrapped, Err):
        raise ValueError("DDC_PROGRAM_ENVELOPE_INVALID")
    records = tuple(row["payload"] for row in wrapped.value)
    if _dda_tape(records, native_support=native_support)[0] != raw:
        raise ValueError("DDC_PROGRAM_ENVELOPE_INVALID")
    steps, root = semantic_dda_from_records(records)
    if stored != expected or root != stored.semantic_ddc_root:
        raise ValueError("DDC_PROGRAM_BINDING_MISMATCH")
    retained_roots = [row.get("evidence", {}).get("retained_context_sha256")
                      for row in records if type(row.get("evidence")) is dict
                      and "retained_context_sha256" in row["evidence"]]
    if (retained_roots or "retained_context" in summary) and (
            len(retained_roots) != 1 or "retained_context" not in summary
            or retained_roots[0] != _program_digest(summary["retained_context"])):
        raise ValueError("DDC_PROGRAM_CONTEXT_MISMATCH: exact retained task bytes differ")
    if (_program_digest(summary["stage_artifacts"]) != stored.stage_artifacts_sha256
            or _program_digest(summary["mode_artifacts"]) != stored.mode_artifacts_sha256
            or tuple(map(int, summary["stage_artifacts"])) != stored.completed_stages
            or sorted(map(int, summary["mode_artifacts"])) != sorted(stored.mode_ids)):
        raise ValueError("DDC_PROGRAM_ARTIFACT_MISMATCH")
    after = read_intelligence(run_path, initial_task_id=initial_task_id)
    if after.source_id != source.source_id or after.coverage_gaps:
        raise ValueError("DDC_PROGRAM_SOURCE_CHANGED")
    return {"binding": stored.model_dump(mode="json"), "source_id": source.source_id,
            "steps": [{**step.to_dict(),
                **({"observed_procedure": records[index]["evidence"]["teamwork_procedure"]}
                   if type(records[index].get("evidence")) is dict
                   and "teamwork_procedure" in records[index]["evidence"] else {})}
                for index, step in enumerate(steps)], "fresh_checker_required": True,
            "billing_status": "UNOBSERVED", "cost_usd": None,
            "mathematical_acceptance": "UNVERIFIED", "authority_effect": "None"}


def prepare_ddc_reuse_turn(*, run_path, expected, current_prompt_text, current_premises,
                          task_id, attempt_id, system, user, answer_schema, native_support: NativeOperationPort):
    """Put the revalidated procedure in PFP context; never reuse its verdict."""
    import json
    from copy import deepcopy

    from pfp.infrastructure.task_turn import prepare_task_turn
    from adversary.domain.prompt_family import DdcProgramBinding

    if type(expected) is not DdcProgramBinding:
        raise ValueError("DDC_PROGRAM_BINDING_REQUIRED")
    premises_snapshot = deepcopy(current_premises)
    if (text_digest(current_prompt_text).removeprefix("sha256:") != expected.prompt_sha256
            or _program_digest(premises_snapshot) != expected.premises_sha256):
        raise ValueError("DDC_REUSE_PREMISES_MISMATCH")
    if user != current_prompt_text:
        raise ValueError("DDC_REUSE_TASK_MISMATCH")
    program = load_ddc_program(run_path, expected=expected, initial_task_id=task_id, native_support=native_support)
    task_input = {"seed": current_prompt_text, "premises": premises_snapshot}
    return prepare_task_turn(system=system, user=json.dumps(task_input, sort_keys=True, ensure_ascii=False),
        task_id=task_id, attempt_id=attempt_id, answer_schema=answer_schema,
        context={"ddc_reuse": program, "bound_task": task_input}, checker_id="ddc-reuse-shape-v1")
