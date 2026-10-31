"""WF5 rewrite preservation, six-call shared accounting, custody and replay."""

import argparse
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from operations.domain.rop.result import Err
from pfp.infrastructure.adapters.pfp_campaign import (
    canonical,
    digest,
    micro,
    write_new,
)
from pfp.infrastructure.workflow_accounting import (
    _read_run_state,
    create_accounted_openrouter_gateway,
)
from pfp.infrastructure.workflow_runtime import WorkflowRuntime, source_bytes
from pfp.workflows.measurement import measure_seed
from pfp.workflows.wf0003 import workflow as wf3
from pfp.workflows.wf0004 import runner as shared
from adversary.domain.providers.types import Provider
from adversary.infrastructure.providers.anthropic_messages import provider_output_schema

from . import rewrite, workflow

RUN_CAP, MINER_TOKENS, SOLVER_TOKENS, MODEL = (
    shared.RUN_CAP,
    shared.MINER_TOKENS,
    224,
    shared.MODEL,
)
MINER = WorkflowRuntime(workflow.MiningContract)
read, capture = shared.read, shared.capture
EXTERNAL_SOURCES = (
    *shared.EXTERNAL_SOURCES,
    "adversary/infrastructure/providers/anthropic_messages.py",
    "adversary/infrastructure/providers/gateway.py",
    "adversary/infrastructure/providers/http.py",
    "adversary/domain/providers/attempt.py",
    "adversary/domain/providers/budget.py",
    "adversary/use_cases/providers/completion.py",
)
DRIVER_FILES = {"comparison.json", "timing.json", "report.md", "experiment_manifest.json"}


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
        run_id="wf0005:" + root.resolve().name,
        objective_sha256=digest(canonical(read(root / "task.json"))),
        timeout=180,
    )


def request(runtime, phase):
    req = shared.request(runtime, phase)
    if runtime.workflow.WORKFLOW_ID == "WF5_MINER":
        _, turn = runtime._load_preparation(phase)
        req = replace(
            req,
            decoding=replace(
                req.decoding,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "wf5_mining",
                        "strict": True,
                        "schema": mining_wire_schema(turn.prompt.response_schema),
                    },
                },
            ),
        )
    return req


def mining_wire_schema(schema):
    """Provider encoding of singleton public constants; host schema stays exact."""
    original = schema["properties"]["answer"]["properties"]["operad_candidates"]["items"][
        "properties"
    ]
    if any(
        original[name] != {"const": fixed}
        for name, fixed in dict(
            arity=1,
            source_colours=["IntegerList"],
            target_colour="Integer",
            witness_refs=["task_result"],
        ).items()
    ):
        raise ValueError("WF5_WIRE_REQUIRES_FIXED_PUBLIC_SIGNATURE")

    def convert(value):
        if type(value) is list:
            return [convert(item) for item in value]
        if type(value) is not dict:
            return value
        if "const" in value:
            fixed = value["const"]
            if type(fixed) is str:
                return dict(type="string", enum=[fixed])
            if type(fixed) is int:
                return dict(type="integer", enum=[fixed])
            if type(fixed) is list and len(fixed) == 1 and type(fixed[0]) is str:
                return dict(
                    type="array", items=dict(type="string", enum=fixed), minItems=1, maxItems=1
                )
            raise ValueError("WF5_UNSUPPORTED_PROVIDER_CONSTANT")
        result = {key: convert(item) for key, item in value.items()}
        if (
            "enum" in result
            and "type" not in result
            and all(type(item) is str for item in result["enum"])
        ):
            result["type"] = "string"
        return result

    wire = convert(provider_output_schema(schema))
    # Generic WF3 arity union is redundant under this fixed unary signature.
    # Keep it in the exact host schema; avoid contradictory branches in the
    # provider grammar projection, whose bounds are pruned again by its codec.
    wire["properties"]["answer"]["properties"]["operad_candidates"]["items"].pop("allOf", None)
    return wire


def prior_binding(path, spec, _seen=()):
    """Verify settled historical custody without regrading an older implementation."""
    path = Path(path).resolve()
    if path in _seen or len(_seen) >= 8:
        raise ValueError("WF5_REPAIR_HISTORY_CYCLE_OR_DEPTH")
    manifest = read(path / "manifest.json")
    if manifest.get("workflow_id") != "WF5" or read(path / "task.json") != spec:
        raise ValueError("WF5_REPAIR_PRIOR_TASK_MISMATCH")
    for name, checksum in manifest["files"].items():
        target = (path / name).resolve()
        if not target.is_relative_to(path) or digest(target.read_bytes()) != checksum:
            raise ValueError("WF5_REPAIR_PRIOR_CUSTODY_MISMATCH")
    _, state = _read_run_state(path / "accounting.sqlite3")
    p = read(path / "mining/provider.json")
    if (
        read(path / "stopped.json")["status"] not in {"CHECKER_DEFECT", "TYPED_REFUSAL"}
        or len(state["attempts"]) != 1
        or any(v["state"] != "settled" for v in state["attempts"].values())
        or state["run_scope"]["limit_microusd"]
        != read(path / "plan.json")["estimated_run_cap_microusd"]
        or state["run_scope"]["objective_sha256"] != digest(canonical(spec))
        or p["accounting_state"] != "CompletedSettled"
        or p["served_model"] != MODEL
        or p["requested_model"] != MODEL
        or p["cost_usd"] is None
        or any((path / f"agent-{i}").exists() for i in range(1, 6))
    ):
        raise ValueError("WF5_REPAIR_REQUIRES_ONE_SETTLED_FAILED_MINER")
    previous = None
    if (path / "prior_attempt.json").exists():
        previous = read(path / "prior_attempt.json")
        if previous != prior_binding(previous["source_run"], spec, (*_seen, path)):
            raise ValueError("WF5_REPAIR_PRIOR_CHAIN_MISMATCH")
    if state["run_scope"]["limit_microusd"] > (
        previous["maximum_repair_limit_microusd"] if previous else RUN_CAP
    ):
        raise ValueError("WF5_REPAIR_PRIOR_ALLOWANCE_RESET")
    charged = state["spent"]
    if (
        type(charged) is not int
        or charged != micro(p["cost_usd"])
        or not 0 <= charged < RUN_CAP * 80 // 100
    ):
        raise ValueError("WF5_REPAIR_NO_REMAINING_ALLOWANCE")
    charged += previous["prior_charged_microusd"] if previous else 0
    if charged >= RUN_CAP * 80 // 100:
        raise ValueError("WF5_REPAIR_NO_REMAINING_ALLOWANCE")
    cap = min(RUN_CAP - charged, ((RUN_CAP * 80 // 100 - charged) * 100) // 80)
    return dict(
        source_run=str(path),
        manifest_sha256=digest((path / "manifest.json").read_bytes()),
        custody="HISTORICAL_BYTES_VERIFIED; no current-source regrading",
        prior_provider_actions=1 + (previous["prior_provider_actions"] if previous else 0),
        prior_cost_usd=float(
            Decimal(str(p["cost_usd"]))
            + (Decimal(str(previous["prior_cost_usd"])) if previous else Decimal(0))
        ),
        prior_charged_microusd=charged,
        original_limit_microusd=RUN_CAP,
        original_stop_microusd=RUN_CAP * 80 // 100,
        maximum_repair_limit_microusd=cap,
        maximum_additional_actions=6,
    )


def prepare_run(spec, root, budget_microusd=RUN_CAP, previous_attempt=None):
    spec = workflow.validate_task(spec)
    if type(budget_microusd) is not int or not 0 < budget_microusd <= RUN_CAP:
        raise ValueError("WF5_BUDGET_MUST_BE_POSITIVE_AND_NO_GREATER_THAN_4999")
    previous = prior_binding(previous_attempt, spec) if previous_attempt is not None else None
    if previous is not None:
        budget_microusd = min(budget_microusd, previous["maximum_repair_limit_microusd"])
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    if previous is not None:
        write_new(root / "prior_attempt.json", previous)
    write_new(root / "task.json", spec)
    write_new(root / "original_seed.txt", spec["seed_prompt"].encode("utf-8"))
    write_new(root / "seed_features.json", measure_seed(spec))
    write_new(
        root / "plan.json",
        dict(
            workflow_id="WF5",
            version=workflow.VERSION,
            rewrite_provider_calls=0,
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
    tick = perf_counter()
    bundle = rewrite.lower(spec)
    write_new(root / "rewrite.json", bundle)
    write_new(
        root / "rewrite_timing.json", dict(wall_seconds=perf_counter() - tick, provider_calls=0)
    )
    if bundle["payload"]["status"] != "HOST_ACCEPTED":
        return stop(root, bundle["payload"]["failure_class"], status="TYPED_REFUSAL")
    write_new(root / "rewritten_seed.pfp", bundle["payload"]["wire"].encode())
    write_new(root / "rewritten_task.json", rewrite.rewritten_task(spec, bundle))
    MINER.prepare_run(spec, root / "mining")
    return dict(status="PREPARED", rewrite_sha256=bundle["sha256"], provider_calls=0)


def scope_check(bound, root, tokens, model):
    expected = dict(
        run_id="wf0005:" + root.resolve().name,
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
        raise ValueError("WF5_SHARED_BUDGET_SCOPE_REQUIRED")


def frozen(root):
    spec, bundle = read(root / "task.json"), read(root / "rewrite.json")
    rewritten = rewrite.rewritten_task(spec, bundle)
    if (
        rewritten != read(root / "rewritten_task.json")
        or (root / "rewritten_seed.pfp").read_bytes() != bundle["payload"]["wire"].encode()
    ):
        raise ValueError("WF5_REWRITTEN_TASK_MISMATCH")
    MINER.replay_run(root / "mining")
    raw, checked = (
        (root / "mining/response.raw").read_bytes(),
        read(root / "mining/receipt.json")["check"],
    )
    screening = wf3.screen_mining(rewritten, raw, checked)
    if screening["accepted"] and not any(
        op["arity"] == 1
        and op["source_colours"] == ["IntegerList"]
        and op["target_colour"] == "Integer"
        for op in checked["answer"]["operad_candidates"]
    ):
        screening["accepted"] = False
        screening["errors"].append("WF5_MINED_INTEGER_LIST_OPERATION_REQUIRED")
    attachment = wf3.freeze_attachment(raw, checked, screening) if screening["accepted"] else None
    return spec, bundle, rewritten, screening, attachment


def freeze_run(root):
    spec, bundle, rewritten, screening, attachment = frozen(root)
    write_new(root / "screening.json", screening)
    if attachment is None:
        return False
    profile = workflow.freeze_profile(rewritten, attachment)
    write_new(root / "attachment.json", attachment)
    write_new(root / "profile.json", profile)
    for i in range(1, 6):
        WorkflowRuntime(workflow.SolverContract(attachment, profile, bundle, i)).prepare_run(
            spec, root / f"agent-{i}"
        )
    return True


def runtime(root, i):
    return WorkflowRuntime(
        workflow.SolverContract(
            read(root / "attachment.json"),
            read(root / "profile.json"),
            read(root / "rewrite.json"),
            i,
        )
    )


def summarize(root):
    spec, bundle, rewritten, screening, attachment = frozen(root)
    if (
        not screening["accepted"]
        or screening != read(root / "screening.json")
        or attachment != read(root / "attachment.json")
    ):
        raise ValueError("WF5_MINING_LINEAGE_MISMATCH")
    if workflow.freeze_profile(rewritten, attachment) != read(root / "profile.json"):
        raise ValueError("WF5_PROFILE_MISMATCH")
    receipts = [read(root / "mining/receipt.json")]
    for i in range(1, 6):
        runtime(root, i).replay_run(root / f"agent-{i}")
        receipts.append(read(root / f"agent-{i}/receipt.json"))
    result = workflow.evaluate_global(spec, [r["check"] for r in receipts[1:]])
    providers = [r.get("provider") for r in receipts]
    accounted = all(
        p
        and p["accounting_state"] == "CompletedSettled"
        and not p["identity_error"]
        and p["cost_usd"] is not None
        for p in providers
    )

    def total(key):
        return sum(p[key] for p in providers) if accounted else None

    cost = float(sum(Decimal(str(p["cost_usd"])) for p in providers)) if accounted else None
    if any(providers) and not accounted:
        result.update(
            status="INFRASTRUCTURE_ERROR", failure_class="WF5_ACCOUNTING_OR_PROVIDER_IDENTITY"
        )
    if (
        cost is not None
        and Decimal(str(cost)) * 1000000 > read(root / "plan.json")["estimated_run_cap_microusd"]
    ):
        result.update(status="INFRASTRUCTURE_ERROR", failure_class="WF5_OBSERVED_BUDGET_EXCEEDED")
    collections = [read(root / f"agent-{i}/collection.json") for i in range(1, 6)]
    result.update(
        workflow_id="WF5",
        version=workflow.VERSION,
        rewrite_status=bundle["payload"]["status"],
        rewrite_sha256=bundle["sha256"],
        rewrite_provider_calls=0,
        captured_provider_actions=sum(p is not None for p in providers),
        prompt_tokens=total("prompt_tokens"),
        completion_tokens=total("completion_tokens"),
        cost_usd=cost,
        provider_service_seconds=total("provider_elapsed_seconds"),
        newly_emitted_operads=sum(len(c["operads"]) for c in collections),
        emitted_operad_references=sum(len(c["operad_references"]) for c in collections),
        emitted_ddc_moves=sum(len(c["ddc_moves"]) for c in collections),
        audited_hallucinations=None,
        learning_evidence="REFERENCE_REUSE_ONLY; no causal learning claim",
        concurrency=read(root / "concurrency.json"),
    )
    return result


def members(root):
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.relative_to(root).as_posix() not in DRIVER_FILES | {"manifest.json"}
    )


def seal(root):
    write_new(
        root / "manifest.json",
        dict(
            workflow_id="WF5",
            files={name: digest((root / name).read_bytes()) for name in members(root)},
        ),
    )


def stop(root, code, *, status="INFRASTRUCTURE_ERROR"):
    result = dict(
        workflow_id="WF5",
        status=status,
        failure_class=code,
        note="Retain partial evidence; no paid retries or fallback.",
        authority_effect="None",
    )
    write_new(root / "stopped.json", result)
    seal(root)
    return result


def replay_run(root):
    root = Path(root)
    manifest = read(root / "manifest.json")
    if manifest.get("workflow_id") != "WF5" or sorted(manifest.get("files", {})) != members(root):
        raise ValueError("WF5_MANIFEST_INVALID")
    for name, checksum in manifest["files"].items():
        target = (root / name).resolve()
        if not target.is_relative_to(root.resolve()) or digest(target.read_bytes()) != checksum:
            raise ValueError("WF5_RECEIPT_DIGEST_MISMATCH")
    if read(root / "plan.json")["implementation"] != implementation():
        raise ValueError("WF5_IMPLEMENTATION_MISMATCH")
    spec, bundle = read(root / "task.json"), read(root / "rewrite.json")
    if (root / "prior_attempt.json").exists():
        previous = read(root / "prior_attempt.json")
        if (
            previous != prior_binding(previous["source_run"], spec)
            or read(root / "plan.json")["estimated_run_cap_microusd"]
            > previous["maximum_repair_limit_microusd"]
        ):
            raise ValueError("WF5_REPAIR_BINDING_MISMATCH")
    if (
        bundle != rewrite.lower(spec)
        or (root / "original_seed.txt").read_bytes() != spec["seed_prompt"].encode()
        or read(root / "seed_features.json") != measure_seed(spec)
    ):
        raise ValueError("WF5_ORIGINAL_OR_REWRITE_MISMATCH")
    if (root / "stopped.json").exists():
        result = read(root / "stopped.json")
        if (root / "mining/receipt_manifest.json").exists():
            MINER.replay_run(root / "mining")
        for i in range(1, 6):
            if (root / f"agent-{i}/receipt_manifest.json").exists():
                runtime(root, i).replay_run(root / f"agent-{i}")
    else:
        result = summarize(root)
        if result != read(root / "summary.json"):
            raise ValueError("WF5_SUMMARY_REPLAY_MISMATCH")
    return dict(**result, replay_verified=True, provider_calls_in_this_command=0)


def run(
    spec,
    root,
    model=MODEL,
    *,
    gateway_factory=gateway,
    budget_microusd=RUN_CAP,
    previous_attempt=None,
):
    if model != MODEL:
        raise ValueError("WF5_COMPARISON_REQUIRES_LLAMA_3_3_70B")
    root, started = Path(root), perf_counter()
    prepared = prepare_run(spec, root, budget_microusd, previous_attempt)
    if prepared["status"] != "PREPARED":
        return prepared
    bound = gateway_factory(root, model, MINER_TOKENS)
    scope_check(bound, root, MINER_TOKENS, model)
    req, tick = request(MINER, root / "mining"), perf_counter()
    outcome = bound.for_action(workflow.MiningContract.ATTEMPT_ID).complete_result(
        req, provider=Provider.OPENROUTER, model=model
    )
    receipt = capture(
        MINER, root / "mining", req, outcome, bound, model, MINER_TOKENS, perf_counter() - tick
    )
    if (
        isinstance(outcome, Err)
        or receipt["status"] == "INFRASTRUCTURE_ERROR"
        or outcome.value.state != "CompletedSettled"
    ):
        return stop(root, "WF5_MINING_PROVIDER_STOP")
    if not freeze_run(root):
        return stop(root, "WF5_MINING_SCREEN_FAILED", status="TYPED_REFUSAL")
    bound = gateway_factory(root, model, SOLVER_TOKENS)
    scope_check(bound, root, SOLVER_TOKENS, model)
    runtimes = {f"wf0005-agent-{i}": runtime(root, i) for i in range(1, 6)}
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
        peak = max(active, peak)
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
    failed = []
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
            failed.append(key)
    if failed:
        return stop(root, "WF5_BATCH_PROVIDER_STOP:" + ",".join(failed))
    result = summarize(root)
    write_new(root / "summary.json", result)
    seal(root)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        command = sub.add_parser(name)
        command.add_argument("--task", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--budget-microusd", type=int, default=RUN_CAP)
        command.add_argument("--previous-attempt", type=Path)
    command = sub.add_parser("replay")
    command.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    result = (
        replay_run(args.run)
        if args.command == "replay"
        else prepare_run(read(args.task), args.output, args.budget_microusd, args.previous_attempt)
        if args.command == "prepare"
        else run(
            read(args.task),
            args.output,
            budget_microusd=args.budget_microusd,
            previous_attempt=args.previous_attempt,
        )
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") in {"PREPARED", "HOST_ACCEPTED"} else 1
