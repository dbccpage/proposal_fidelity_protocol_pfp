"""
Bounded serial TEST-001 execution through the existing accounted PFP gateway.

The original 100-case catalog, prompts, strict answer schemas and exact host
judges remain available. Current calls select a bounded prefix (default five)
and retain the original 96-token output default. Estimated gateway allowances
do not enforce provider maximum liability. Host dry fixtures provide reference
self-consistency only; neither schema success nor fixtures prove a provider
honored its control or establish model performance.

AuthorityEffect: None.
"""

from __future__ import annotations

__test__ = False

import argparse
import datetime
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from functools import partial
from pathlib import Path
from typing import Any, TYPE_CHECKING
from uuid import uuid4

_worktree_root = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "pfp").is_dir() and (parent / "adversary").is_dir()
    ),
    None,
)
if _worktree_root is not None and str(_worktree_root) not in sys.path:
    sys.path.insert(0, str(_worktree_root))

if TYPE_CHECKING:
    from openai import OpenAI

from pilots.llm_mechanism.c005_hosted_decode_controls.budget_controller import (
    BudgetController,
)
from pilots.llm_mechanism.c005_hosted_decode_controls.cases import (
    get_hidden_base_cases,
)
from pilots.llm_mechanism.c005_hosted_decode_controls.checkers import (
    verify_consistency_certificate,
    verify_cycle_repair,
)
from pilots.llm_mechanism.c005_hosted_decode_controls.runner import (
    wilson_score_interval,
)
from pilots.llm_mechanism.c005_hosted_decode_controls.schemas import (
    CONSISTENCY_JSON_SCHEMA,
    CYCLE_REPAIR_JSON_SCHEMA,
    validate_json_schema,
)
from pfp.infrastructure.estimated_gateway import (
    DurableRunGateway,
    EstimatedBudgetGateway,
)
from pfp.infrastructure.pilot_matrix import (
    complete_pilot_turn,
    make_pilot_gateways,
    validate_pilot_gateways,
)
from pfp.infrastructure.synthesis_matrix import RunnerRefusal, prepare_output_dir
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1

SYSTEM_PROMPT = "Solve the supplied C005 task; put the complete task JSON proposal in answer."


@dataclass
class CaseExecutionTrace:
    case_id: str
    kind: str
    prompt: str
    generation_id: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    cost_usd: float | None
    latency_sec: float
    finish_reason: str | None
    raw_content: str
    is_parseable: bool
    is_schema_valid: bool
    is_correct: bool
    error_type: str | None
    error_message: str | None
    parsed_payload: dict[str, Any] = field(default_factory=dict)

    exchange: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    task_id: str = ""
    attempt_id: str = ""
    task_sha256: str = ""
    input_sha256: str = ""
    input_hash_scope: str = "original_public_task"
    case_sha256: str = ""
    protocol_sha256: str = ""
    max_output_tokens: int = 96
    temperature: float = 0.0
    evidence_grade: str = "UNVERIFIED"
    control: str = ""
    control_provenance: dict[str, Any] = field(default_factory=dict)
    judge_eligible: bool = False
    stop: bool = False


def execute_single_case(
    case: dict[str, Any],
    client: OpenAI,
    model: str,
    budget_ctrl: BudgetController,
    *,
    gateway=None,
    task_id="C005:empirical",
    attempt_id=None,
    max_tokens: int = 96,
    dry_run: bool = False,
    mock_solution=None,
    tokenizer_provenance: str | None = None,
) -> CaseExecutionTrace:
    """Execute one case against OpenRouter with live budget accounting."""
    kind = case.get("kind", "consistency")
    case_id = case.get("case_id", "unknown")

    # Format prompt explicitly according to contract
    if kind == "consistency":
        schema = CONSISTENCY_JSON_SCHEMA
        schema_name = "consistency_verdict"
        prompt = (
            f"{case.get('prompt')}\n"
            'If CONSISTENT, certificate maps each node identifier to its integer potential (e.g. {"n0": "0", "n1": "2"}). '
            "If INCONSISTENT, certificate must be empty {}."
        )
    else:
        schema = CYCLE_REPAIR_JSON_SCHEMA
        schema_name = "cycle_repair_solution"
        prompt = (
            f"{case.get('prompt')}\n"
            'repaired must be exactly a list of integer strings in cycle order (e.g. ["1", "3", "-4"]). '
            'weighted_l1 must be the total integer cost as a string (e.g. "1").'
        )

    provenance = dict(source="original_declared_schema", name=schema_name, provider_honored=None)
    decoding = DecodingParamsV1(
        temperature=0.0, response_format={"type": "json_schema", "json_schema": schema}
    )
    attempt_id = attempt_id or uuid4().hex
    exchange = _complete_case(
        case,
        client if gateway is None else gateway,
        model,
        budget_ctrl,
        prompt=prompt,
        decoding=decoding,
        task_id=task_id,
        attempt_id=attempt_id,
        max_tokens=max_tokens,
        dry_run=dry_run,
        mock_solution=mock_solution,
    )
    content = exchange.get("observed_content", "")
    usage = exchange["usage"]
    gen_id, p_tok, c_tok = (
        usage.get("generation_id"),
        usage.get("prompt_tokens"),
        usage.get("completion_tokens"),
    )
    t_tok = p_tok + c_tok if p_tok is not None and c_tok is not None else None
    cost_usd, latency, finish_reason = (
        exchange["cost"],
        exchange["elapsed"],
        exchange.get("finish_reason"),
    )
    make_trace = partial(
        CaseExecutionTrace,
        **_trace_metadata(
            case,
            model,
            task_id=task_id,
            attempt_id=attempt_id,
            max_tokens=max_tokens,
            exchange=exchange,
            control="json_schema",
            provenance=provenance,
            dry_run=dry_run,
        ),
    )
    if not exchange["ok"]:
        parsed, parseable, valid_schema, _ = _observed(content, schema_name, "json_schema")
        return make_trace(
            case_id=case_id,
            kind=kind,
            prompt=prompt,
            generation_id=gen_id,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            cost_usd=cost_usd,
            latency_sec=latency,
            finish_reason=finish_reason,
            raw_content=content,
            is_parseable=parseable,
            is_schema_valid=valid_schema,
            is_correct=False,
            error_type="PFP_ERROR",
            error_message=exchange["error"],
            parsed_payload=parsed,
        )

    # 2. Parse JSON
    try:
        parsed = json.loads(content.strip())
    except Exception as exc:
        return make_trace(
            case_id=case_id,
            kind=kind,
            prompt=prompt,
            generation_id=gen_id,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            cost_usd=cost_usd,
            latency_sec=latency,
            finish_reason=finish_reason,
            raw_content=content,
            is_parseable=False,
            is_schema_valid=False,
            is_correct=False,
            error_type="PARSE_ERROR",
            error_message=f"{type(exc).__name__}: {exc}",
        )

    # 3. Schema validation
    valid_schema, schema_err = validate_json_schema(parsed, schema_name)
    if not valid_schema:
        return make_trace(
            case_id=case_id,
            kind=kind,
            prompt=prompt,
            generation_id=gen_id,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            cost_usd=cost_usd,
            latency_sec=latency,
            finish_reason=finish_reason,
            raw_content=content,
            is_parseable=True,
            is_schema_valid=False,
            is_correct=False,
            error_type="SCHEMA_ERROR",
            error_message=schema_err,
            parsed_payload=parsed,
        )

    # 4. Exact Host Verification
    if kind == "consistency":
        edges = case.get("edges", [])
        verdict = parsed.get("verdict", "")
        cert = parsed.get("certificate", {})
        check = verify_consistency_certificate(edges, verdict, cert)
        # Also check ground truth consistency verdict match
        expected_verdict = case.get("expected_verdict")
        matches_truth = verdict == expected_verdict
        is_correct = check.is_valid and matches_truth

        err_type = (
            None if is_correct else ("VERDICT_MISMATCH" if not matches_truth else "FALSE_WITNESS")
        )
        err_msg = (
            None
            if is_correct
            else (
                f"Model returned {verdict}, expected {expected_verdict}"
                if not matches_truth
                else check.error_message
            )
        )

        return make_trace(
            case_id=case_id,
            kind=kind,
            prompt=prompt,
            generation_id=gen_id,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            cost_usd=cost_usd,
            latency_sec=latency,
            finish_reason=finish_reason,
            raw_content=content,
            is_parseable=True,
            is_schema_valid=True,
            is_correct=is_correct,
            error_type=err_type,
            error_message=err_msg,
            parsed_payload=parsed,
        )

    elif kind == "cycle_repair":
        claims = [e[2] for e in case.get("edges", [])]
        weights = case.get("weights", [1] * len(claims))
        repaired = parsed.get("repaired", [])
        decl_cost = parsed.get("weighted_l1")
        check = verify_cycle_repair(claims, weights, repaired, decl_cost)
        is_correct = check.is_valid and check.is_optimal

        err_type = (
            None if is_correct else ("SUBOPTIMAL_REPAIR" if check.is_valid else "INVALID_REPAIR")
        )
        return make_trace(
            case_id=case_id,
            kind=kind,
            prompt=prompt,
            generation_id=gen_id,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            cost_usd=cost_usd,
            latency_sec=latency,
            finish_reason=finish_reason,
            raw_content=content,
            is_parseable=True,
            is_schema_valid=True,
            is_correct=is_correct,
            error_type=err_type,
            error_message=check.error_message,
            parsed_payload=parsed,
        )

    return make_trace(
        case_id=case_id,
        kind=kind,
        prompt=prompt,
        generation_id=gen_id,
        prompt_tokens=p_tok,
        completion_tokens=c_tok,
        total_tokens=t_tok,
        cost_usd=cost_usd,
        latency_sec=latency,
        finish_reason=finish_reason,
        raw_content=content,
        is_parseable=True,
        is_schema_valid=True,
        is_correct=False,
        error_type="UNKNOWN_KIND",
        error_message=f"Unknown task kind {kind}",
        parsed_payload=parsed,
    )


def _hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _public_input(case):
    return {key: case[key] for key in ("kind", "prompt", "edges", "weights") if key in case}


def _protocol_hash() -> str:
    root = Path(__file__).parent
    return _hash(
        {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ("cases.py", "schemas.py", "checkers.py")
        }
    )


def _reference_answer(case):
    if case.get("kind", "consistency") == "consistency":
        return dict(verdict=case["expected_verdict"], certificate=case["expected_certificate"])
    return dict(
        status="SOLVED",
        repaired=case["expected_repaired"],
        weighted_l1=case["expected_weighted_l1"],
    )


def _observed(content, schema_name, control):
    """Original parsing/shape diagnostics; these do not authorize a judge call."""
    parsed, parseable = {}, False
    try:
        parsed, parseable = json.loads(content.strip()), True
    except (ValueError, TypeError):
        if control == "logit_bias":
            start, end = content.find("{"), content.rfind("}")
            if start != -1 and end > start:
                try:
                    parsed, parseable = json.loads(content[start : end + 1]), True
                except ValueError:
                    pass
    valid, reason = (
        validate_json_schema(parsed, schema_name) if parseable else (False, "PARSE_ERROR")
    )
    return parsed, parseable, valid, reason


def _trace_metadata(
    case, model, *, task_id, attempt_id, max_tokens, exchange, control, provenance, dry_run
):
    protocol = _protocol_hash()
    return dict(
        exchange=exchange,
        model=model,
        task_id=task_id,
        attempt_id=attempt_id,
        task_sha256=_hash({"challenge": "C005", "kind": case.get("kind"), "protocol": protocol}),
        input_sha256=_hash(_public_input(case)),
        case_sha256=_hash(case),
        protocol_sha256=protocol,
        max_output_tokens=max_tokens,
        temperature=0.0,
        evidence_grade="HOST_REFERENCE_SELF_CONSISTENCY" if dry_run else "PFP_BOUND_PROPOSAL",
        control=control,
        control_provenance=provenance,
        judge_eligible=exchange["ok"],
        stop=exchange["stop"],
    )


def _legacy_cap(budget_ctrl):
    try:
        values = [
            Decimal(str(getattr(budget_ctrl, key)))
            for key in ("ceiling_usd", "hard_kill_usd", "total_billed_usd")
        ]
    except (InvalidOperation, AttributeError) as exc:
        raise RunnerRefusal("INVALID_LEGACY_BUDGET", "legacy ceiling must be finite") from exc
    if any(not value.is_finite() for value in values) or min(values[:2]) <= 0 or values[2] < 0:
        raise RunnerRefusal("INVALID_LEGACY_BUDGET", "legacy ceiling must be positive and finite")
    return (min(values[:2]) - values[2]) * 1_000_000


def _accounting_states(gateway):
    if not isinstance(gateway, (EstimatedBudgetGateway, DurableRunGateway)):
        return {}
    limit = (
        gateway.limit
        if isinstance(gateway, EstimatedBudgetGateway)
        else gateway.scope["limit_microusd"]
    )
    with gateway.ledger.transaction(limit) as state:
        return {
            f"{kind}:{key}": row["state"]
            for kind in ("attempts", "action_claims")
            for key, row in state.get(kind, {}).items()
        }


def _complete_case(
    case,
    gateway,
    model,
    budget_ctrl,
    *,
    prompt,
    decoding,
    task_id,
    attempt_id,
    max_tokens,
    dry_run,
    mock_solution,
):
    if dry_run:
        proposal = _reference_answer(case) if mock_solution is None else mock_solution
        return dict(
            ok=True,
            content=proposal if isinstance(proposal, str) else json.dumps(proposal),
            observed_content=proposal if isinstance(proposal, str) else json.dumps(proposal),
            usage={},
            cost=0.0,
            elapsed=0.0,
            finish_reason="host_fixture",
            request={},
            pfp=None,
            raw_body=None,
            provider_wire=None,
            error=None,
            attempt_state=None,
            stop=False,
            cost_may_be_incurred=False,
        )
    error = None
    if isinstance(gateway, (EstimatedBudgetGateway, DurableRunGateway)):
        try:
            limit = (
                gateway.limit
                if isinstance(gateway, EstimatedBudgetGateway)
                else gateway.scope["limit_microusd"]
            )
            if Decimal(limit) > _legacy_cap(budget_ctrl):
                raise RunnerRefusal(
                    "LEGACY_BUDGET_CEILING_CONFLICT", "gateway exceeds the remaining legacy ceiling"
                )
        except RunnerRefusal as exc:
            error = exc.code
    before = _accounting_states(gateway)
    result = (
        dict(
            ok=False,
            content=None,
            usage={},
            elapsed=0.0,
            request={},
            pfp=None,
            raw_body=None,
            provider_wire=None,
            error=error,
            attempt_state=None,
            stop=True,
        )
        if error
        else complete_pilot_turn(
            gateway,
            CandidateRequest(SYSTEM_PROMPT, prompt, decoding=decoding),
            model=model,
            task_id=task_id,
            attempt_id=attempt_id,
            max_tokens=max_tokens,
        )
    )
    after = _accounting_states(gateway)
    incurred = bool(
        result.get("provider_wire") is not None
        or result["ok"]
        or any(after[key] != "refused_before_dispatch" for key in after.keys() - before.keys())
    )
    observed, finish = result["content"] or "", None
    try:
        choice = json.loads(result["raw_body"])["choices"][0]
        finish = choice.get("finish_reason")
        if not result["ok"]:
            candidate = choice["message"]["content"]
            try:
                envelope = json.loads(candidate)
                proposal = envelope["answer"]
                observed = proposal if isinstance(proposal, str) else json.dumps(proposal)
            except (ValueError, KeyError, TypeError):
                observed = candidate if isinstance(candidate, str) else ""
    except (ValueError, KeyError, TypeError, IndexError):
        pass
    return dict(
        result,
        observed_content=observed,
        finish_reason=finish,
        cost=result["usage"].get("cost") if incurred else 0.0,
        cost_may_be_incurred=incurred,
    )


def _run_sweep(
    model,
    concurrency,
    *,
    execute,
    test_id,
    control,
    cases,
    selected_case,
    max_cases,
    max_tokens,
    gateway,
    output_dir,
    max_estimated_cost_microusd,
    max_provider_calls,
    env_file,
    budget_ctrl,
    dry_run,
    bias_map=None,
    tokenizer_provenance=None,
):
    """One serial loop and the existing continuing PFP ledger for either arm."""
    if type(concurrency) is not int or concurrency < 1:
        raise RunnerRefusal(
            "INVALID_CONCURRENCY", "legacy concurrency must be positive; execution is serial"
        )
    if type(max_cases) is not int or max_cases < 1:
        raise RunnerRefusal("INVALID_CASE_LIMIT", "select a positive bounded case count")
    if type(max_tokens) is not int or max_tokens < 1:
        raise RunnerRefusal("INVALID_OUTPUT_BOUND", "output tokens must be positive")
    if type(max_provider_calls) is not int or not 0 < max_provider_calls <= 64:
        raise RunnerRefusal("INVALID_CALL_LIMIT", "call allowance must be from 1 to 64")
    if max_estimated_cost_microusd is not None and (
        type(max_estimated_cost_microusd) is not int or not 0 < max_estimated_cost_microusd <= 50000
    ):
        raise RunnerRefusal(
            "INVALID_ESTIMATED_BUDGET", "estimated allowance must be from 1 to 50000 microUSD"
        )
    bank = list(get_hidden_base_cases() if cases is None else cases)
    selected = [case for case in bank if selected_case is None or selected_case in case["case_id"]][
        :max_cases
    ]
    if not selected:
        raise RunnerRefusal("NO_CASE_SELECTED", "selection contains no original tasks")
    if len({case["case_id"] for case in selected}) != len(selected):
        raise RunnerRefusal("DUPLICATE_CASE_ID", "selected case identities must be unique")
    budget_ctrl = budget_ctrl if budget_ctrl is not None else BudgetController()
    cap = _legacy_cap(budget_ctrl)
    if not dry_run:
        if gateway is None:
            if max_estimated_cost_microusd is None:
                raise RunnerRefusal(
                    "PFP_ACCOUNTED_GATEWAY_REQUIRED",
                    "supply a gateway or explicit estimated policy",
                )
            if output_dir is None:
                raise RunnerRefusal(
                    "OUTPUT_DIR_REQUIRED", "gateway accounting needs an explicit new directory"
                )
            limit = max_estimated_cost_microusd
        else:
            try:
                validate_pilot_gateways({model: gateway}, [model], max_tokens=max_tokens)
            except ValueError as exc:
                raise RunnerRefusal(str(exc), "PFP gateway preflight failed") from exc
            limit = (
                gateway.limit
                if isinstance(gateway, EstimatedBudgetGateway)
                else gateway.scope["limit_microusd"]
            )
            calls = (
                gateway.max_calls
                if isinstance(gateway, EstimatedBudgetGateway)
                else gateway.scope["max_calls"]
            )
            if calls > max_provider_calls:
                raise RunnerRefusal(
                    "PFP_CALL_ALLOWANCE_CONFLICT", "gateway exceeds the requested call cap"
                )
            if max_estimated_cost_microusd is not None and limit > max_estimated_cost_microusd:
                raise RunnerRefusal(
                    "PFP_COST_ALLOWANCE_CONFLICT", "gateway exceeds the requested cost cap"
                )
        if Decimal(limit) > cap:
            raise RunnerRefusal(
                "LEGACY_BUDGET_CEILING_CONFLICT", "gateway exceeds the remaining legacy ceiling"
            )
    out = prepare_output_dir(Path(output_dir)) if output_dir is not None else None
    if gateway is None and not dry_run:
        try:
            gateway = make_pilot_gateways(
                [model],
                max_output_tokens=max_tokens,
                max_estimated_cost_microusd=max_estimated_cost_microusd,
                max_calls=max_provider_calls,
                accounting_path=out / "accounting.sqlite3",
                env_file=env_file,
            )[model]
        except ValueError as exc:
            raise RunnerRefusal(str(exc), "PFP gateway composition failed") from exc
    start, traces, stop = time.monotonic(), [], None
    run_id = uuid4().hex
    for index, case in enumerate(selected):
        args = [case, gateway, model]
        if bias_map is not None:
            args.append(bias_map)
        args.append(budget_ctrl)
        trace = execute(
            *args,
            max_tokens=max_tokens,
            task_id="C005:empirical",
            attempt_id=f"{run_id}:{index}",
            dry_run=dry_run,
            tokenizer_provenance=tokenizer_provenance,
        )
        traces.append(trace)
        print(
            f"{test_id} case-{index + 1}: correct={trace.is_correct} error={trace.error_type}",
            flush=True,
        )
        if trace.stop:
            stop = trace.error_message or "PFP_TERMINAL_STOP"
            break
    n = len(traces)
    parseable, valid, correct = (
        sum(bool(getattr(trace, key)) for trace in traces)
        for key in ("is_parseable", "is_schema_valid", "is_correct")
    )
    costs = [trace.cost_usd for trace in traces]
    known = sum(cost for cost in costs if cost is not None)
    total = None if any(cost is None for cost in costs) else known

    def tokens(key):
        values = [getattr(trace, key) for trace in traces]
        return None if any(value is None for value in values) else sum(values)

    p_tokens, c_tokens, total_tokens = (
        tokens("prompt_tokens"),
        tokens("completion_tokens"),
        tokens("total_tokens"),
    )
    latencies = sorted(trace.latency_sec for trace in traces)
    mean = sum(latencies) / n
    errors = {}
    for trace in traces:
        if not trace.is_correct:
            key = trace.error_type or "OTHER"
            errors[key] = errors.get(key, 0) + 1
    grade = "HOST_REFERENCE_SELF_CONSISTENCY" if dry_run else "PFP_BOUND_PROPOSAL"
    report = dict(
        test_id=test_id,
        challenge_id="C005",
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model=model,
        control=control,
        total_cases=n,
        planned_cases=len(selected),
        original_case_count=len(bank),
        concurrency_requested=concurrency,
        actual_concurrency=1,
        stop_reason=stop,
        evidence_grade=grade,
        max_output_tokens=max_tokens,
        original_max_output_tokens=96,
        execution_duration_sec=time.monotonic() - start,
        token_accounting=dict(
            total_prompt_tokens=p_tokens,
            total_completion_tokens=c_tokens,
            total_tokens=total_tokens,
            mean_prompt_tokens=p_tokens / n if p_tokens is not None else None,
            mean_completion_tokens=c_tokens / n if c_tokens is not None else None,
        ),
        financial_accounting=dict(
            total_billed_cost_usd=total,
            known_cost_subtotal_usd=known,
            target_spend_ceiling_usd=budget_ctrl.target_spend_usd,
            hard_kill_ceiling_usd=budget_ctrl.hard_kill_usd,
            legacy_ceiling_usd=budget_ctrl.ceiling_usd,
            cost_status="UNKNOWN"
            if total is None
            else "WITHIN_TARGET"
            if total <= budget_ctrl.target_spend_usd
            else "EXCEEDED_TARGET",
            cost_per_verified_success_usd=total / correct
            if total is not None and correct
            else None,
            policy="host_fixture"
            if dry_run
            else "accounted_gateway; estimated policy does not enforce provider maximum liability",
        ),
        latency_profile=dict(
            mean_sec=mean,
            median_sec=latencies[n // 2],
            min_sec=min(latencies),
            max_sec=max(latencies),
        ),
        performance_metrics=dict(
            parseable_count=parseable,
            parseable_rate=parseable / n,
            parseable_wilson_95_ci=wilson_score_interval(parseable, n),
            schema_valid_count=valid,
            schema_valid_rate=valid / n,
            verified_correct_count=correct,
            verified_correct_rate=correct / n,
        ),
        error_taxonomy=errors,
        case_traces=[asdict(trace) for trace in traces],
        claim_hygiene=dict(
            supports=f"Observed {n} attempted cases; {correct} proposals passed the original exact host checks.",
            does_not_support="Host fixtures and payload/schema success do not establish model performance, provider-honored controls or causal superiority. PFP envelope overhead changes the original 96-token transport.",
            narrowest_defensible_claim="Finite host self-consistency only."
            if dry_run
            else "Bound/accounted proposals with separate original host checks; no general reasoning or control-honoring claim.",
            next_test_needed="Explicit control-honored probes and compatible paired model observations before empirical interpretation.",
        ),
    )
    if out is not None and test_id == "TEST-001":
        _persist(report, out)
    return report


def _persist(report, out):
    """Retain the original output names only, in the caller's new directory."""

    def dump(name, value):
        raw = json.dumps(value, sort_keys=True, indent=2).encode("utf-8")
        (out / name).write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    traces = report["case_traces"]
    observed_replies = sum(trace["exchange"].get("provider_wire") is not None for trace in traces)
    uncertain_calls = any(
        trace["exchange"].get("cost_may_be_incurred")
        and trace["exchange"].get("provider_wire") is None
        for trace in traces
    )
    hashes = dict(
        empirical_evaluation_report_sha256=dump("empirical_evaluation_report.json", report),
        accounting_sha256=dump(
            "accounting.json",
            dict(
                test_id=report["test_id"],
                model=report["model"],
                total_calls=None if uncertain_calls else observed_replies,
                attempted_cases=report["total_cases"],
                observed_provider_replies=observed_replies,
                total_cost_usd=report["financial_accounting"]["total_billed_cost_usd"],
                call_ledger=[trace["exchange"] for trace in report["case_traces"]],
            ),
        ),
    )
    raw = (
        "\n".join(json.dumps(trace, sort_keys=True) for trace in report["case_traces"]) + "\n"
    ).encode()
    (out / "sample_traces.jsonl").write_bytes(raw)
    hashes["sample_traces_sha256"] = hashlib.sha256(raw).hexdigest()
    summary = dict(
        test_id=report["test_id"],
        model=report["model"],
        control=report["control"],
        total_cases=report["total_cases"],
        **report["performance_metrics"],
        total_billed_usd=report["financial_accounting"]["total_billed_cost_usd"],
        cost_per_verified_success_usd=report["financial_accounting"]["cost_per_verified_success_usd"],
        mean_latency_sec=report["latency_profile"]["mean_sec"],
        claim_hygiene=report["claim_hygiene"],
        evidence_grade=report["evidence_grade"],
        stop_reason=report["stop_reason"],
    )
    if "mcnemar_paired_analysis" in report:
        summary["mcnemar_vs_test_001_schema"] = report["mcnemar_paired_analysis"]
        hashes["mcnemar_paired_analysis_sha256"] = dump(
            "mcnemar_paired_analysis.json", report["mcnemar_paired_analysis"]
        )
    hashes["summary_sha256"] = dump("summary.json", summary)
    dump(
        "receipt.json",
        dict(
            schema_version="1.0.0",
            test_id=report["test_id"],
            task_key="c005_test_001_llama405b_json_schema"
            if report["test_id"] == "TEST-001"
            else "c005_test_002_llama405b_logit_bias",
            timestamp_utc=report["timestamp_utc"],
            model=report["model"],
            control=report["control"],
            total_cases=report["total_cases"],
            total_billed_usd=report["financial_accounting"]["total_billed_cost_usd"],
            artifact_hashes=hashes,
            terminal_verdict=None,
            verdict_status="NOT_ADJUDICATED",
            evidence_grade=report["evidence_grade"],
            authority_effect="None",
            stop_reason=report["stop_reason"],
        ),
    )


def run_test_001_empirical_sweep(
    model: str = "nousresearch/hermes-3-llama-3.1-405b",
    concurrency: int = 4,
    *,
    gateway=None,
    output_dir=None,
    cases=None,
    selected_case=None,
    max_cases=5,
    max_tokens=96,
    max_estimated_cost_microusd=None,
    max_provider_calls=5,
    env_file=None,
    budget_ctrl=None,
    dry_run=False,
) -> dict[str, Any]:
    return _run_sweep(
        model,
        concurrency,
        execute=execute_single_case,
        test_id="TEST-001",
        control="json_schema",
        cases=cases,
        selected_case=selected_case,
        max_cases=max_cases,
        max_tokens=max_tokens,
        gateway=gateway,
        output_dir=output_dir,
        max_estimated_cost_microusd=max_estimated_cost_microusd,
        max_provider_calls=max_provider_calls,
        env_file=env_file,
        budget_ctrl=budget_ctrl,
        dry_run=dry_run,
    )


def _main(run, argv=None, *, bias=False):
    parser = argparse.ArgumentParser(
        description="Bounded serial C005 PFP empirical runner; dry mode is a host fixture."
    )
    parser.add_argument("--model", default="nousresearch/hermes-3-llama-3.1-405b")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--case", dest="selected_case")
    parser.add_argument("--max-cases", type=int, default=5)
    parser.add_argument("--max-output-tokens", dest="max_tokens", type=int, default=96)
    parser.add_argument("--max-provider-calls", type=int, default=5)
    parser.add_argument("--max-estimated-cost-microusd", type=int)
    parser.add_argument("--budget-ceiling", type=float, default=0.10)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    if bias:
        parser.add_argument("--bias-map", type=Path, help="explicit JSON token-ID to bias map")
        parser.add_argument(
            "--tokenizer-path", type=Path, help="explicit local tokenizer; no downloads"
        )
        parser.add_argument(
            "--baseline-traces", type=Path, help="explicit TEST001 sample_traces.jsonl"
        )
    values = vars(parser.parse_args(argv))
    values["budget_ctrl"] = BudgetController(ceiling_usd=values.pop("budget_ceiling"))
    if bias and values["bias_map"] is not None:
        values["tokenizer_provenance"] = str(values["bias_map"])
        values["bias_map"] = json.loads(values["bias_map"].read_text(encoding="utf-8"))
    try:
        result = run(**values)
    except RunnerRefusal as exc:
        print(f"REFUSED {exc}")
        return 2
    print(json.dumps(result, indent=2))
    return 2 if result["stop_reason"] else 0


def main(argv=None):
    return _main(run_test_001_empirical_sweep, argv)


if __name__ == "__main__":
    raise SystemExit(main())
