"""WF4 custody and six-action accounting; five solvers share one atomic reservation."""

import argparse
import base64
import json
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from operations.domain.rop.result import Err
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest, write_new
from pfp.infrastructure.workflow_accounting import create_accounted_openrouter_gateway
from pfp.infrastructure.workflow_runtime import WorkflowRuntime, source_bytes
from pfp.workflows.measurement import measure_seed
from pfp.workflows.wf0003 import workflow as wf3
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1, Provider
from adversary.infrastructure.providers.openai_compat import build_openai_compat_body

from . import workflow

RUN_CAP, MINER_TOKENS, SOLVER_TOKENS = 4999, 1000, 400
MODEL = "meta-llama/llama-3.3-70b-instruct"
MINER = WorkflowRuntime(workflow.MiningContract)
EXTERNAL_SOURCES = (
    "adversary/infrastructure/lggr_adapter.py",
    "adversary/domain/swarm_models.py",
    "adversary/domain/providers/types.py",
    "adversary/infrastructure/providers/budget_ledger.py",
    "adversary/infrastructure/providers/openai_compat.py",
)


def read(path):
    return MINER._read_json(Path(path))


def implementation():
    return dict(
        pfp=MINER.source_identity(),
        external={name: digest(source_bytes(name)) for name in EXTERNAL_SOURCES},
    )


def gateway(root, model, tokens):
    return create_accounted_openrouter_gateway(
        model,
        tokens,
        max_estimated_cost_microusd=read(root / "plan.json")["estimated_run_cap_microusd"],
        max_calls=6,
        accounting_path=root / "accounting.sqlite3",
        run_id="wf0004:" + root.resolve().name,
        objective_sha256=digest(canonical(read(root / "task.json"))),
        timeout=180,
    )


def prepare_run(spec, root, budget_microusd=RUN_CAP):
    spec = workflow.validate_task(spec)
    if type(budget_microusd) is not int or not 0 < budget_microusd <= RUN_CAP:
        raise ValueError("WF4_BUDGET_MUST_BE_POSITIVE_AND_NO_GREATER_THAN_4999")
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    write_new(root / "task.json", spec)
    write_new(root / "seed_features.json", measure_seed(spec))
    write_new(
        root / "plan.json",
        dict(
            workflow_id="WF4",
            version=workflow.VERSION,
            mining_calls=1,
            solver_agents=5,
            main_stages=1,
            maximum_provider_calls=6,
            retries=0,
            estimated_run_cap_microusd=budget_microusd,
            miner_max_output_tokens=MINER_TOKENS,
            solver_max_output_tokens=SOLVER_TOKENS,
            shared_accounting=True,
            implementation=implementation(),
            authority_effect="None",
        ),
    )
    sources = ["pfp/" + name for name in MINER.source_files] + list(EXTERNAL_SOURCES)
    for name in sources:
        target = root / "source_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        write_new(target, source_bytes(name))
    write_new(
        root / "source_snapshot/manifest.json",
        dict(files={name: digest(source_bytes(name)) for name in sources}),
    )
    return MINER.prepare_run(spec, root / "mining")


def request(runtime, phase):
    _, turn = runtime._load_preparation(phase)
    return CandidateRequest(
        turn.prompt.system,
        turn.prompt.user,
        decoding=DecodingParamsV1(
            temperature=0.0,
            top_p=1.0,
            allow_fallbacks=False,
            require_parameters=True,
            response_format={"type": "json_object"},
        ),
    )


def scope_check(bound, root, tokens, model):
    expected = dict(
        run_id="wf0004:" + root.resolve().name,
        objective_sha256=digest(canonical(read(root / "task.json"))),
        limit_microusd=read(root / "plan.json")["estimated_run_cap_microusd"],
        max_calls=6,
        safety_multiplier=2,
        stop_percent=80,
    )
    if (
        any(bound.scope.get(k) != v for k, v in expected.items())
        or bound.path != (root / "accounting.sqlite3").resolve()
        or bound.max_output_tokens != tokens
        or bound.model != model
    ):
        raise ValueError("WF4_SHARED_BUDGET_SCOPE_REQUIRED")


def capture(runtime, phase, req, outcome, bound, model, tokens, elapsed):
    if isinstance(outcome, Err):
        record = dict(
            status="INFRASTRUCTURE_ERROR",
            failure_class=outcome.error.code,
            confirmed_provider_calls=None,
            authority_effect="None",
        )
        write_new(phase / "failure.json", record)
        return record
    value, c = outcome.value, outcome.value.candidate
    try:
        body = json.loads(value.reply_bytes)
    except (ValueError, UnicodeError):
        body = {}
    record = dict(
        request=build_openai_compat_body(
            req, model=model, max_tokens=tokens, provider=Provider.OPENROUTER
        ),
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
        accounting_binding=bound.binding,
        identity_error=c.model != model or c.provider != "openrouter",
        provider_elapsed_seconds=elapsed,
        finish_reason=body.get("choices", [{}])[0].get("finish_reason"),
        reasoning_tokens=body.get("usage", {})
        .get("completion_tokens_details", {})
        .get("reasoning_tokens"),
        tool_execution_count=0,
        raw_reply_base64=base64.b64encode(value.reply_bytes).decode(),
        raw_reply_sha256=digest(value.reply_bytes),
    )
    return runtime._finish(
        phase,
        c.content.encode("utf-8", errors="surrogatepass"),
        origin="ACCOUNTED_PROVIDER",
        provider_record=record,
    )


def freeze_run(root):
    spec = workflow.validate_task(read(root / "task.json"))
    MINER.replay_run(root / "mining")
    checked = read(root / "mining/receipt.json")["check"]
    raw = (root / "mining/response.raw").read_bytes()
    screen = wf3.screen_mining(spec, raw, checked)
    write_new(root / "screening.json", screen)
    if not screen["accepted"]:
        return None
    attachment = wf3.freeze_attachment(raw, checked, screen)
    profile = workflow.freeze_profile(spec, attachment)
    write_new(root / "attachment.json", attachment)
    write_new(root / "profile.json", profile)
    for i in range(1, 6):
        WorkflowRuntime(workflow.SolverContract(attachment, profile, i)).prepare_run(
            spec, root / f"agent-{i}"
        )
    return attachment, profile


def _runtime(root, i):
    return WorkflowRuntime(
        workflow.SolverContract(read(root / "attachment.json"), read(root / "profile.json"), i)
    )


def summarize(root):
    plan, spec = read(root / "plan.json"), read(root / "task.json")
    if plan["implementation"] != implementation():
        raise ValueError("WF4_IMPLEMENTATION_MISMATCH")
    MINER.replay_run(root / "mining")
    mining = read(root / "mining/receipt.json")
    raw = (root / "mining/response.raw").read_bytes()
    screen = wf3.screen_mining(spec, raw, mining["check"])
    if screen != read(root / "screening.json") or not screen["accepted"]:
        raise ValueError("WF4_MINING_REPLAY_MISMATCH")
    attachment = wf3.freeze_attachment(raw, mining["check"], screen)
    if attachment != read(root / "attachment.json") or workflow.freeze_profile(
        spec, attachment
    ) != read(root / "profile.json"):
        raise ValueError("WF4_FROZEN_LINEAGE_MISMATCH")
    receipts = [mining]
    for i in range(1, 6):
        _runtime(root, i).replay_run(root / f"agent-{i}")
        receipts.append(read(root / f"agent-{i}/receipt.json"))
    result = workflow.evaluate_global(spec, [row["check"] for row in receipts[1:]])
    providers = [row.get("provider") for row in receipts]
    accounted = all(
        p
        and p["accounting_state"] == "CompletedSettled"
        and not p["identity_error"]
        and p["cost_usd"] is not None
        for p in providers
    )
    if any(p is not None for p in providers) and not accounted:
        result.update(
            status="INFRASTRUCTURE_ERROR", failure_class="WF4_UNSETTLED_OR_WRONG_PROVIDER"
        )
    result.update(
        workflow_id="WF4",
        version=workflow.VERSION,
        captured_provider_actions=sum(p is not None for p in providers),
        prompt_tokens=sum(p["prompt_tokens"] for p in providers) if accounted else None,
        completion_tokens=sum(p["completion_tokens"] for p in providers) if accounted else None,
        cost_usd=float(sum(Decimal(str(p["cost_usd"])) for p in providers)) if accounted else None,
        provider_service_seconds=sum(p["provider_elapsed_seconds"] for p in providers)
        if accounted
        else None,
        task_complexity="Same seed and finite integer task; controller overhead measured separately.",
        newly_emitted_operads=sum(
            len(read(root / f"agent-{i}/collection.json")["operads"]) for i in range(1, 6)
        ),
        emitted_operad_references=sum(
            len(read(root / f"agent-{i}/collection.json")["operad_references"]) for i in range(1, 6)
        ),
        emitted_ddc_moves=sum(
            len(read(root / f"agent-{i}/collection.json")["ddc_moves"]) for i in range(1, 6)
        ),
        audited_hallucinations=None,
        learning_evidence="REFERENCE_REUSE_ONLY; no causal learning claim",
        concurrency=read(root / "concurrency.json"),
    )
    if (
        accounted
        and Decimal(str(result["cost_usd"])) * 1000000 > plan["estimated_run_cap_microusd"]
    ):
        result.update(status="INFRASTRUCTURE_ERROR", failure_class="WF4_OBSERVED_BUDGET_EXCEEDED")
    return result


def seal_run(root):
    result = summarize(root)
    write_new(root / "summary.json", result)
    members = [
        "seed_features.json",
        "task.json",
        "plan.json",
        "screening.json",
        "attachment.json",
        "profile.json",
        "summary.json",
        "concurrency.json",
        "mining/receipt_manifest.json",
        "source_snapshot/manifest.json",
    ]
    members += [f"agent-{i}/receipt_manifest.json" for i in range(1, 6)]
    if (root / "batch_preflight.json").exists():
        members.append("batch_preflight.json")
    write_new(
        root / "manifest.json",
        dict(
            workflow_id="WF4", files={name: digest((root / name).read_bytes()) for name in members}
        ),
    )
    return result


def replay_run(root):
    root = Path(root)
    manifest = read(root / "manifest.json")
    expected = {
        "seed_features.json",
        "task.json",
        "plan.json",
        "screening.json",
        "attachment.json",
        "profile.json",
        "summary.json",
        "concurrency.json",
        "mining/receipt_manifest.json",
        "source_snapshot/manifest.json",
    }
    expected.update(f"agent-{i}/receipt_manifest.json" for i in range(1, 6))
    if (root / "batch_preflight.json").exists():
        expected.add("batch_preflight.json")
    if manifest.get("workflow_id") != "WF4" or set(manifest.get("files", {})) != expected:
        raise ValueError("WF4_MANIFEST_INVALID")
    for name, checksum in manifest["files"].items():
        if digest((root / name).read_bytes()) != checksum:
            raise ValueError("WF4_RECEIPT_DIGEST_MISMATCH")
    snapshot = root / "source_snapshot"
    for name, checksum in read(snapshot / "manifest.json")["files"].items():
        target = (snapshot / name).resolve()
        if not target.is_relative_to(snapshot.resolve()) or digest(target.read_bytes()) != checksum:
            raise ValueError("WF4_ARCHIVED_SOURCE_MISMATCH")
    result = summarize(root)
    if read(root / "seed_features.json") != measure_seed(read(root / "task.json")):
        raise ValueError("WF4_SEED_MEASUREMENT_MISMATCH")
    if result != read(root / "summary.json"):
        raise ValueError("WF4_SUMMARY_REPLAY_MISMATCH")
    return dict(**result, replay_verified=True, provider_calls_in_this_command=0)


def stop(root, code):
    value = dict(
        workflow_id="WF4",
        status="INFRASTRUCTURE_ERROR",
        failure_class=code,
        authority_effect="None",
        note="Retain all partial artifacts; no retry or fallback.",
    )
    write_new(root / "stopped.json", value)
    return value


def run(spec, root, model=MODEL, *, gateway_factory=gateway, budget_microusd=RUN_CAP):
    root, started = Path(root), perf_counter()
    if model != MODEL:
        raise ValueError("WF4_COMPARISON_MODEL_MUST_BE_LLAMA_3_3_70B")
    prepare_run(spec, root, budget_microusd)
    bound = gateway_factory(root, model, MINER_TOKENS)
    scope_check(bound, root, MINER_TOKENS, model)
    req, tick = request(MINER, root / "mining"), perf_counter()
    outcome = bound.for_action(workflow.MiningContract.ATTEMPT_ID).complete_result(
        req, provider=Provider.OPENROUTER, model=model
    )
    mining = capture(
        MINER, root / "mining", req, outcome, bound, model, MINER_TOKENS, perf_counter() - tick
    )
    if mining["status"] == "INFRASTRUCTURE_ERROR" or outcome.value.state != "CompletedSettled":
        return stop(root, "WF4_MINING_PROVIDER_STOP")
    frozen = freeze_run(root)
    if frozen is None:
        return stop(root, "WF4_MINING_SCREEN_FAILED")
    bound = gateway_factory(root, model, SOLVER_TOKENS)
    scope_check(bound, root, SOLVER_TOKENS, model)
    runtimes = {f"wf0004-agent-{i}": _runtime(root, i) for i in range(1, 6)}
    requests = {
        key: request(rt, root / f"agent-{i}") for i, (key, rt) in enumerate(runtimes.items(), 1)
    }
    with bound.ledger.transaction(bound.limit) as state:
        spent = state["spent"]
    quotes = {key: bound._quote(req, model=model)[0] for key, req in requests.items()}
    write_new(
        root / "batch_preflight.json",
        dict(
            reservations_microusd=quotes,
            settled_before_batch_microusd=spent,
            simultaneous_liability_microusd=spent + sum(quotes.values()),
            stop_at_microusd=bound.limit * 80 // 100,
            schema_bytes_included=True,
            estimated_not_vendor_enforced=True,
        ),
    )
    batch = bound.complete_batch_result(requests, provider=Provider.OPENROUTER, model=model)
    if isinstance(batch, Err):
        return stop(root, batch.error.code)
    intervals = {
        key: dict(started=row["started"] - started, ended=row["ended"] - started)
        for key, row in batch.value.items()
    }
    events = sorted(
        [(r["started"], 1) for r in intervals.values()]
        + [(r["ended"], -1) for r in intervals.values()]
    )
    active = peak = 0
    for _, change in events:
        active += change
        peak = max(peak, active)
    write_new(
        root / "concurrency.json",
        dict(
            origin="ACCOUNTED_HOST_INVOCATION_INTERVALS",
            intervals=intervals,
            peak_in_flight=peak,
            solver_wall_seconds=max(r["ended"] for r in intervals.values())
            - min(r["started"] for r in intervals.values()),
            workflow_wall_seconds=perf_counter() - started,
            provider_compute_parallelism="UNOBSERVED",
        ),
    )
    failures = []
    for i, (key, rt) in enumerate(runtimes.items(), 1):
        row = batch.value[key]
        receipt = capture(
            rt,
            root / f"agent-{i}",
            requests[key],
            row["outcome"],
            bound,
            model,
            SOLVER_TOKENS,
            row["ended"] - row["started"],
        )
        if receipt["status"] == "INFRASTRUCTURE_ERROR":
            failures.append(key)
    if failures:
        return stop(root, "WF4_BATCH_PROVIDER_STOP:" + ",".join(failures))
    return seal_run(root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        command = sub.add_parser(name)
        command.add_argument("--task", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--budget-microusd", type=int, default=RUN_CAP)
    command = sub.add_parser("replay")
    command.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    value = (
        replay_run(args.run)
        if args.command == "replay"
        else (
            prepare_run(read(args.task), args.output, args.budget_microusd)
            if args.command == "prepare"
            else run(read(args.task), args.output, budget_microusd=args.budget_microusd)
        )
    )
    print(json.dumps(value, indent=2))
    return 0 if value.get("status") in (None, "HOST_ACCEPTED") else 1
