"""WF3 phase orchestration over existing PFP custody and one shared budget."""

import argparse
import base64
import json
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from operations.domain.rop.result import Err
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest, write_new
from pfp.infrastructure.workflow_accounting import create_accounted_openrouter_gateway
from pfp.infrastructure.pilot_matrix import validate_pilot_gateways
from pfp.infrastructure.workflow_runtime import WorkflowRuntime
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1, Provider
from adversary.infrastructure.providers.openai_compat import build_openai_compat_body

from . import workflow
from .structured import wire_schema

RUN_CAP = 4999
MINER_TOKENS = 1000
SOLVER_TOKENS = 1300
MINER_RUNTIME = WorkflowRuntime(workflow.MiningContract)


def read_json(path):
    return MINER_RUNTIME._read_json(Path(path))


def prepare_run(
    spec, root, budget_microusd=RUN_CAP, mining_capture=None, remaining_repair_microusd=None
):
    if type(budget_microusd) is not int or not 0 < budget_microusd <= RUN_CAP:
        raise ValueError("WF3_BUDGET_MUST_BE_POSITIVE_AND_NO_GREATER_THAN_4999")
    if remaining_repair_microusd is not None and (
        mining_capture is None
        or type(remaining_repair_microusd) is not int
        or not 0 < remaining_repair_microusd <= RUN_CAP
    ):
        raise ValueError("WF3_REPAIR_GUARD_REQUIRES_ONE_REUSED_MINING_CONTINUATION")
    spec = workflow.validate_task(spec)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    write_new(root / "task.json", spec)
    write_new(
        root / "plan.json",
        dict(
            workflow_id="WF3",
            version=workflow.VERSION,
            mining_calls=1,
            solver_agents=1,
            main_stages=1,
            maximum_provider_calls=2,
            maximum_new_provider_calls=1 if mining_capture else 2,
            remaining_repair_microusd=remaining_repair_microusd,
            retries=0,
            estimated_run_cap_microusd=budget_microusd,
            miner_max_output_tokens=MINER_TOKENS,
            solver_max_output_tokens=SOLVER_TOKENS,
            shared_accounting=True,
            authority_effect="None",
        ),
    )
    if mining_capture is not None:
        source = Path(mining_capture)
        raw = (source / "mining/response.raw").read_bytes()
        historical = source / "historical_evidence_manifest.json"
        write_new(
            root / "reused_mining.json",
            dict(
                source_run=str(source.resolve()),
                raw_sha256=digest(raw),
                historical_manifest_sha256=digest(historical.read_bytes()),
                origin="PREVIOUS_CAPTURE_HOST_RECHECK",
                new_mining_calls=0,
                interpretation="Original provider usage is counted in historical actions, not purchased again.",
            ),
        )
    return MINER_RUNTIME.prepare_run(spec, root / "mining")


def freeze_run(root):
    spec = workflow.validate_task(read_json(root / "task.json"))
    MINER_RUNTIME.replay_run(root / "mining")
    mining = read_json(root / "mining" / "receipt.json")
    if mining["status"] in {"INFRASTRUCTURE_ERROR", "CHECKER_DEFECT"}:
        raise ValueError("WF3_MINING_INFRASTRUCTURE_STOP")
    raw = (root / "mining" / "response.raw").read_bytes()
    screening = workflow.screen_mining(spec, raw, mining["check"])
    write_new(root / "screening.json", screening)
    if not screening["accepted"]:
        write_new(
            root / "stopped.json",
            dict(
                status="TYPED_REFUSAL",
                failure_class="WF3_MINING_SCREEN_FAILED",
                errors=screening["errors"],
                solver_calls=0,
                authority_effect="None",
            ),
        )
        return None
    attachment = workflow.freeze_attachment(raw, mining["check"], screening)
    write_new(root / "attachment.json", attachment)
    runtime = WorkflowRuntime(workflow.SolverContract(attachment))
    runtime.prepare_run(spec, root / "solver")
    return attachment


def _validate_frozen(root):
    if (root / "reused_mining.json").exists():
        reused = read_json(root / "reused_mining.json")
        source = Path(reused["source_run"])
        if (
            digest((source / "historical_evidence_manifest.json").read_bytes())
            != reused["historical_manifest_sha256"]
            or digest((source / "mining/response.raw").read_bytes()) != reused["raw_sha256"]
            or digest((root / "mining/response.raw").read_bytes()) != reused["raw_sha256"]
        ):
            raise ValueError("WF3_REUSED_MINING_CUSTODY_MISMATCH")
    spec = workflow.validate_task(read_json(root / "task.json"))
    MINER_RUNTIME.replay_run(root / "mining")
    mining = read_json(root / "mining" / "receipt.json")
    raw = (root / "mining" / "response.raw").read_bytes()
    screen = workflow.screen_mining(spec, raw, mining["check"])
    if canonical(screen) != canonical(read_json(root / "screening.json")):
        raise ValueError("WF3_SCREENING_REPLAY_MISMATCH")
    expected = workflow.freeze_attachment(raw, mining["check"], screen)
    actual = workflow.verify_attachment(read_json(root / "attachment.json"))
    if actual != expected:
        raise ValueError("WF3_MINING_LINEAGE_MISMATCH")
    return spec, actual


def _new_gateway(root, model, tokens):
    spec = read_json(root / "task.json")
    return create_accounted_openrouter_gateway(
        model,
        tokens,
        max_estimated_cost_microusd=read_json(root / "plan.json")["estimated_run_cap_microusd"],
        max_calls=read_json(root / "plan.json")["maximum_new_provider_calls"],
        accounting_path=root / "accounting.sqlite3",
        run_id="wf0003:" + root.resolve().name,
        objective_sha256=digest(canonical(spec)),
        timeout=180,
    )


def dispatch_phase(runtime, spec, phase_root, gateway, model, tokens):
    """One bound action; the real ledger retains its two-call shared-run scope."""
    validate_pilot_gateways({model: gateway}, [model], max_tokens=tokens)
    budget = read_json(phase_root.parent / "plan.json")["estimated_run_cap_microusd"]
    if (
        type(budget) is not int
        or not 0 < budget <= RUN_CAP
        or gateway.scope["max_calls"]
        != read_json(phase_root.parent / "plan.json")["maximum_new_provider_calls"]
        or gateway.scope["limit_microusd"] != budget
    ):
        raise ValueError("WF3_SHARED_BUDGET_SCOPE_REQUIRED")
    if any(
        (phase_root / name).exists() for name in ("response.raw", "failure.json", "receipt.json")
    ):
        raise ValueError("WF3_PHASE_ALREADY_ATTEMPTED")
    stored, turn = runtime._load_preparation(phase_root)
    if stored != runtime.workflow.validate_task(spec):
        raise ValueError("WF3_TASK_MISMATCH")
    request = CandidateRequest(
        turn.prompt.system,
        turn.prompt.user,
        decoding=DecodingParamsV1(
            temperature=0.0,
            top_p=1.0,
            allow_fallbacks=False,
            require_parameters=True,
            response_format={"type": "json_object"}
            if runtime.workflow.WORKFLOW_ID == "WF3_MINER"
            else {
                "type": "json_schema",
                "json_schema": {
                    "name": "wf3_response",
                    "strict": True,
                    "schema": wire_schema(turn.prompt.response_schema),
                },
            },
        ),
    )
    wire = build_openai_compat_body(
        request, model=model, max_tokens=tokens, provider=Provider.OPENROUTER
    )
    remaining = read_json(phase_root.parent / "plan.json").get("remaining_repair_microusd")
    if remaining is not None:
        reserve, input_bytes = gateway._quote(request, model=model)
        write_new(
            phase_root / "repair_budget_preflight.json",
            dict(
                remaining_microusd=remaining,
                reservation_microusd=reserve,
                estimated_input_bytes=input_bytes,
                schema_bytes_included=True,
                provider_calls=0,
            ),
        )
        if reserve > remaining:
            failure = dict(
                status="INFRASTRUCTURE_ERROR",
                failure_class="WF3_REPAIR_REMAINING_BUDGET",
                confirmed_provider_calls=0,
                authority_effect="None",
            )
            write_new(phase_root / "failure.json", failure)
            return failure
    started = perf_counter()
    outcome = gateway.for_action(runtime.workflow.ATTEMPT_ID).complete_result(
        request, provider=Provider.OPENROUTER, model=model
    )
    elapsed = perf_counter() - started
    if isinstance(outcome, Err):
        failure = dict(
            status="INFRASTRUCTURE_ERROR",
            failure_class=outcome.error.code,
            provider_wire=outcome.error.response_metadata(),
            provider_invocations=1,
            confirmed_provider_calls=None,
            authority_effect="None",
        )
        write_new(phase_root / "failure.json", failure)
        return failure
    value = outcome.value
    c = value.candidate
    raw = c.content.encode("utf-8", errors="surrogatepass")
    details = {}
    finish_reason = None
    try:
        body = json.loads(value.reply_bytes)
        details = body.get("usage", {}).get("completion_tokens_details", {})
        finish_reason = body.get("choices", [{}])[0].get("finish_reason")
    except (ValueError, AttributeError, IndexError, TypeError):
        pass
    reasoning = details.get("reasoning_tokens") if type(details) is dict else None
    if type(reasoning) is not int or reasoning < 0:
        reasoning = None
    record = dict(
        request=wire,
        requested_model=model,
        served_model=c.model,
        provider=c.provider,
        generation_id=c.generation_id,
        transport=c.transport,
        provider_calls=1,
        prompt_tokens=c.input_tokens,
        completion_tokens=c.output_tokens,
        cost_usd=c.cost_usd,
        accounting_state=value.state,
        accounting_binding=gateway.binding,
        identity_error=c.model != model or c.provider != "openrouter",
        provider_elapsed_seconds=elapsed,
        reasoning_tokens=reasoning,
        finish_reason=finish_reason,
        tool_execution_count=0,
        raw_reply_base64=base64.b64encode(value.reply_bytes).decode("ascii"),
        raw_reply_sha256=digest(value.reply_bytes),
    )
    return runtime._finish(phase_root, raw, origin="ACCOUNTED_PROVIDER", provider_record=record)


def _summary(root):
    spec, attachment = _validate_frozen(root)
    solver_runtime = WorkflowRuntime(workflow.SolverContract(attachment))
    solver_runtime.replay_run(root / "solver")
    receipts = {phase: read_json(root / phase / "receipt.json") for phase in ("mining", "solver")}
    providers = {phase: record.get("provider") for phase, record in receipts.items()}
    reused = (root / "reused_mining.json").exists()
    active_providers = {
        phase: value for phase, value in providers.items() if not (reused and phase == "mining")
    }
    accounted = all(active_providers.values())

    def total(key):
        values = [record.get(key) if record else None for record in active_providers.values()]
        return sum(values) if all(value is not None for value in values) else None

    costs = [record["cost_usd"] if record else None for record in active_providers.values()]
    cost = (
        float(sum(Decimal(str(value)) for value in costs))
        if all(v is not None for v in costs)
        else None
    )
    collection = read_json(root / "solver" / "collection.json")
    mined = attachment["payload"]["operads"]
    emitted = [row["record"] for row in collection["operads"]]

    def signature(op):
        if (
            type(op) is not dict
            or type(op.get("source_colours")) is not list
            or any(type(value) is not str for value in op["source_colours"])
            or type(op.get("target_colour")) is not str
            or type(op.get("arity")) is not int
        ):
            return None
        return tuple(op["source_colours"]), op["target_colour"], op["arity"]

    signatures = {signature(op) for op in mined}
    matched = [
        op["id"] for op in emitted if signature(op) is not None and signature(op) in signatures
    ]
    check = receipts["solver"]["check"]
    return dict(
        workflow_id="WF3",
        version=workflow.VERSION,
        status=receipts["solver"]["status"],
        main_solver_responses=1,
        mining_responses=1,
        new_provider_calls=(1 if reused else 2)
        if accounted
        else (
            0 if all(r["origin"] == "HAND_AUTHORED_FIXTURE" for r in receipts.values()) else None
        ),
        failure_class=receipts["solver"]["failure_class"],
        maximum_provider_calls=2,
        mining_reused=reused,
        shared_estimated_run_cap_microusd=read_json(root / "plan.json")[
            "estimated_run_cap_microusd"
        ],
        prompt_tokens=total("prompt_tokens"),
        completion_tokens=total("completion_tokens"),
        provider_elapsed_seconds=total("provider_elapsed_seconds"),
        cost_usd=cost,
        reasoning_tokens=total("reasoning_tokens"),
        tool_execution_count=0,
        phases={
            phase: dict(status=receipts[phase]["status"], provider=providers[phase])
            for phase in receipts
        },
        attachment_sha256=attachment["sha256"],
        mined_operad_count=len(mined),
        solver_operad_count=len(emitted),
        solver_ddc_count=len(collection["ddc_moves"]),
        mined_signature_reuse_ids=matched,
        learning_evidence="SIGNATURE_OVERLAP_ONLY; no causal learning claim or admission",
        schema_valid=check["schema_valid"],
        operad_structure_valid=check.get("operad_structure_valid"),
        l2_grounding_valid=check.get("l2_grounding_valid"),
        l2_checked_slots=check.get("l2_checked_slots", []),
        l2_errors=check.get("l2_errors", []),
        task_correct=True
        if check.get("task_status") == "HOST_ACCEPTED"
        else (False if check.get("task_failure_class") == "CERTIFICATE" else None),
        failure_observations=dict(
            schema_failures=sum(not r["check"]["schema_valid"] for r in receipts.values()),
            structural_errors=len(check.get("structure_errors", [])),
            wrong_task_results=int(check.get("task_failure_class") == "CERTIFICATE"),
            output_limit_phases=[
                phase for phase, p in providers.items() if p and p.get("finish_reason") == "length"
            ],
            audited_hallucinations=None,
            hallucination_audit="NOT_AUDITED; errors are classified separately",
        ),
        authority_effect="None",
    )


def finish_run(root):
    result = _summary(root)
    write_new(root / "summary.json", result)
    names = (
        "task.json",
        "plan.json",
        "screening.json",
        "attachment.json",
        "summary.json",
        "mining/receipt_manifest.json",
        "solver/receipt_manifest.json",
    )
    if (root / "reused_mining.json").exists():
        names += ("reused_mining.json",)
    write_new(
        root / "manifest.json",
        dict(workflow_id="WF3", files={name: digest((root / name).read_bytes()) for name in names}),
    )
    return result


def replay_run(root):
    root = Path(root)
    expected = {
        "task.json",
        "plan.json",
        "screening.json",
        "attachment.json",
        "summary.json",
        "mining/receipt_manifest.json",
        "solver/receipt_manifest.json",
    }
    if (root / "reused_mining.json").exists():
        expected.add("reused_mining.json")
    manifest = read_json(root / "manifest.json")
    if manifest.get("workflow_id") != "WF3" or set(manifest.get("files", {})) != expected:
        raise ValueError("WF3_MANIFEST_INVALID")
    if any(
        digest((root / name).read_bytes()) != checksum
        for name, checksum in manifest["files"].items()
    ):
        raise ValueError("RECEIPT_DIGEST_MISMATCH")
    result = _summary(root)
    if canonical(result) != canonical(read_json(root / "summary.json")):
        raise ValueError("WF3_SUMMARY_REPLAY_MISMATCH")
    return dict(**result, replay_verified=True, provider_calls_in_this_command=0)


def run(
    spec,
    root,
    model,
    gateway_factory=None,
    *,
    budget_microusd=RUN_CAP,
    mining_capture=None,
    remaining_repair_microusd=None,
):
    started = perf_counter()
    root = Path(root)
    prepare_run(spec, root, budget_microusd, mining_capture, remaining_repair_microusd)
    factory = gateway_factory or _new_gateway
    mining = (
        MINER_RUNTIME.check_run(
            root / "mining", Path(mining_capture) / "mining/response.raw", fixture=False
        )
        if mining_capture
        else dispatch_phase(
            MINER_RUNTIME,
            spec,
            root / "mining",
            factory(root, model, MINER_TOKENS),
            model,
            MINER_TOKENS,
        )
    )
    if mining["status"] in {"INFRASTRUCTURE_ERROR", "CHECKER_DEFECT"}:
        write_new(root / "stopped.json", dict(phase="mining", result=mining, solver_calls=0))
        return mining
    attachment = freeze_run(root)
    if attachment is None:
        return read_json(root / "stopped.json")
    runtime = WorkflowRuntime(workflow.SolverContract(attachment))
    result = dispatch_phase(
        runtime, spec, root / "solver", factory(root, model, SOLVER_TOKENS), model, SOLVER_TOKENS
    )
    if result["status"] in {"INFRASTRUCTURE_ERROR", "CHECKER_DEFECT"}:
        write_new(root / "stopped.json", dict(phase="solver", result=result))
        return result
    write_new(root / "timing.json", dict(end_to_end_seconds=perf_counter() - started))
    return finish_run(root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        sub = commands.add_parser(name)
        sub.add_argument("task", type=Path)
        sub.add_argument("--output", type=Path, required=True)
        if name == "run":
            sub.add_argument("--model", required=True)
            sub.add_argument("--budget-microusd", type=int, default=RUN_CAP)
    for name in ("check-mining", "check", "replay"):
        sub = commands.add_parser(name)
        sub.add_argument("run", type=Path)
        if name != "replay":
            sub.add_argument("reply", type=Path)
            sub.add_argument("--fixture", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_run(read_json(args.task), args.output)
            result = dict(status="MINING_PREPARED", binding=result["binding"], provider_calls=0)
        elif args.command == "run":
            result = run(
                read_json(args.task), args.output, args.model, budget_microusd=args.budget_microusd
            )
        elif args.command == "check-mining":
            MINER_RUNTIME.check_run(args.run / "mining", args.reply, fixture=args.fixture)
            attachment = freeze_run(args.run)
            result = dict(
                status="SOLVER_PREPARED" if attachment else "TYPED_REFUSAL", provider_calls=0
            )
        elif args.command == "check":
            _, attachment = _validate_frozen(args.run)
            runtime = WorkflowRuntime(workflow.SolverContract(attachment))
            runtime.check_run(args.run / "solver", args.reply, fixture=args.fixture)
            result = finish_run(args.run)
        else:
            result = replay_run(args.run)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        if result["status"] in {"INFRASTRUCTURE_ERROR", "CHECKER_DEFECT"}:
            return 3
        return (
            2
            if result["status"] == "TYPED_REFUSAL" or result.get("failure_class", "NONE") != "NONE"
            else 0
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REFUSED", reason=str(exc), authority_effect="None")))
        return 2
