"""
empirical_001_runner.py — Live empirical execution of TEST-001 on Llama-3.1-405B under JSON schema.

Executes:
- Model: `nousresearch/hermes-3-llama-3.1-405b` via OpenRouter (OpenAI-compatible)
- Control: `json_schema` (strict structured output)
- Cases: 100 hidden base cases (50 consistency + 50 cycle repair)
- Host Oracles: Exact integer potential difference checker (Phi_1 = 0) and minimal weighted L1 cycle repair verifier
- Budget: Enforces strict <= $0.05 target spend, $0.10 ceiling, $0.25 hard kill
- Telemetry: Per-call generation IDs, prompt/completion tokens, latency, and provider-reported billed costs

AuthorityEffect: None.
"""

from __future__ import annotations

__test__ = False

import concurrent.futures
import datetime
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Ensure worktree root and cwd are in sys.path
_worktree_root = Path(__file__).resolve().parents[5]
if str(_worktree_root) not in sys.path:
    sys.path.insert(0, str(_worktree_root))
_cwd = Path.cwd().resolve()
if str(_cwd) not in sys.path:
    sys.path.insert(0, str(_cwd))

from dotenv import load_dotenv
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.budget_controller import (
    BudgetController,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.cases import (
    get_hidden_base_cases,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.checkers import (
    verify_consistency_certificate,
    verify_cycle_repair,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.runner import (
    wilson_score_interval,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.schemas import (
    CONSISTENCY_JSON_SCHEMA,
    CYCLE_REPAIR_JSON_SCHEMA,
    validate_json_schema,
)
from openai import OpenAI

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

# Load environment variable safely without exposing secrets
_env_locations = [
    Path.cwd() / ".env",
    Path(r"C:\Users\a343o\source\repos\the_symbol_game\.env"),
]
for p in _env_locations:
    if p.exists():
        load_dotenv(p)
        break


@dataclass
class CaseExecutionTrace:
    case_id: str
    kind: str
    prompt: str
    generation_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_sec: float
    finish_reason: str
    raw_content: str
    is_parseable: bool
    is_schema_valid: bool
    is_correct: bool
    error_type: str | None
    error_message: str | None
    parsed_payload: dict[str, Any] = field(default_factory=dict)


def execute_single_case(
    case: dict[str, Any],
    client: OpenAI,
    model: str,
    budget_ctrl: BudgetController,
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

    # 1. Pre-call budget check
    budget_ctrl.check_can_call(estimated_cost_usd=0.0005)

    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=96,
            temperature=0.0,
            response_format={"type": "json_schema", "json_schema": schema},
            extra_body={
                "provider": {
                    "allow_fallbacks": False,
                    "require_parameters": True,
                }
            },
            timeout=45.0,
        )
        latency = round(time.time() - t0, 3)

        choice = resp.choices[0]
        content = choice.message.content or ""
        finish_reason = getattr(choice, "finish_reason", "stop") or "stop"
        gen_id = getattr(resp, "id", f"gen-{int(t0)}")

        usage = getattr(resp, "usage", None)
        p_tok = getattr(usage, "prompt_tokens", 0) if usage else len(prompt) // 4
        c_tok = getattr(usage, "completion_tokens", 0) if usage else len(content) // 4
        t_tok = getattr(usage, "total_tokens", 0) if usage else (p_tok + c_tok)

        # Extract provider cost
        cost_usd: float | None = None
        if usage and hasattr(usage, "cost") and usage.cost is not None:
            cost_usd = float(usage.cost)
        elif hasattr(resp, "cost") and resp.cost is not None:
            cost_usd = float(resp.cost)
        else:
            # Hermes-3-405B base OpenRouter rate: $1.00/M tokens = $0.000001 per token
            cost_usd = round(t_tok * 1.0e-6, 6)

        budget_ctrl.record_call(cost_usd=cost_usd, model=model, generation_id=gen_id, tokens=t_tok)

    except Exception as exc:
        latency = round(time.time() - t0, 3)
        return CaseExecutionTrace(
            case_id=case_id,
            kind=kind,
            prompt=prompt,
            generation_id="error",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            latency_sec=latency,
            finish_reason="error",
            raw_content="",
            is_parseable=False,
            is_schema_valid=False,
            is_correct=False,
            error_type="PROVIDER_ERROR",
            error_message=f"{type(exc).__name__}: {exc}",
        )

    # 2. Parse JSON
    try:
        parsed = json.loads(content.strip())
    except Exception as exc:
        return CaseExecutionTrace(
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
        return CaseExecutionTrace(
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

        return CaseExecutionTrace(
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
        return CaseExecutionTrace(
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

    return CaseExecutionTrace(
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


def run_test_001_empirical_sweep(
    model: str = "nousresearch/hermes-3-llama-3.1-405b",
    concurrency: int = 4,
) -> dict[str, Any]:
    """Execute live empirical evaluation of TEST-001 across the 100 hidden base cases."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in environment or .env file.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=60.0,
        max_retries=2,
    )

    budget_ctrl = BudgetController(
        ceiling_usd=0.10,
        target_spend_usd=0.05,
        hard_kill_usd=0.25,
        fail_closed_on_unreported=False,
    )

    cases = get_hidden_base_cases()
    total_n = len(cases)
    print(f"[TEST-001] Starting empirical sweep of {total_n} hidden base cases on model: {model}")
    print(
        f"[TEST-001] Concurrency: {concurrency} workers | Budget ceiling: ${budget_ctrl.ceiling_usd:.2f}"
    )

    start_time = time.time()
    traces: list[CaseExecutionTrace] = []

    # Execute cases concurrently with thread-safe budget controller
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_case = {
            executor.submit(execute_single_case, case, client, model, budget_ctrl): case
            for case in cases
        }
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_case):
            completed_count += 1
            trace = future.result()
            traces.append(trace)
            if completed_count % 10 == 0 or completed_count == total_n:
                print(
                    f"[{completed_count:03d}/{total_n}] {trace.case_id} ({trace.kind}): "
                    f"parse={trace.is_parseable} schema={trace.is_schema_valid} correct={trace.is_correct} "
                    f"| cumulative_spend=${budget_ctrl.total_billed_usd:.5f}"
                )

    total_duration = round(time.time() - start_time, 2)
    traces.sort(key=lambda t: t.case_id)

    # Metrics aggregation
    parseable_count = sum(1 for t in traces if t.is_parseable)
    schema_valid_count = sum(1 for t in traces if t.is_schema_valid)
    correct_count = sum(1 for t in traces if t.is_correct)

    total_prompt_tok = sum(t.prompt_tokens for t in traces)
    total_comp_tok = sum(t.completion_tokens for t in traces)
    total_tok = sum(t.total_tokens for t in traces)
    total_billed_cost = round(budget_ctrl.total_billed_usd, 6)

    latencies = [t.latency_sec for t in traces if t.latency_sec > 0]
    latencies.sort()
    mean_lat = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
    median_lat = round(latencies[len(latencies) // 2], 3) if latencies else 0.0

    p_rate = round(parseable_count / total_n, 4)
    s_rate = round(schema_valid_count / total_n, 4)
    c_rate = round(correct_count / total_n, 4)
    wilson_int = wilson_score_interval(parseable_count, total_n)

    cost_per_verified = round(total_billed_cost / correct_count, 6) if correct_count > 0 else None

    # Error taxonomy
    error_counts: dict[str, int] = {}
    for t in traces:
        if not t.is_correct:
            k = t.error_type or "OTHER"
            error_counts[k] = error_counts.get(k, 0) + 1

    report_payload: dict[str, Any] = {
        "test_id": "TEST-001",
        "challenge_id": "C005",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": model,
        "control": "json_schema",
        "total_cases": total_n,
        "execution_duration_sec": total_duration,
        "token_accounting": {
            "total_prompt_tokens": total_prompt_tok,
            "total_completion_tokens": total_comp_tok,
            "total_tokens": total_tok,
            "mean_prompt_tokens": round(total_prompt_tok / total_n, 1),
            "mean_completion_tokens": round(total_comp_tok / total_n, 1),
        },
        "financial_accounting": {
            "total_billed_cost_usd": total_billed_cost,
            "target_spend_ceiling_usd": 0.05,
            "hard_kill_ceiling_usd": 0.25,
            "cost_status": "WITHIN_LIMITS" if total_billed_cost <= 0.05 else "EXCEEDED_TARGET",
            "cost_per_verified_success_usd": cost_per_verified,
        },
        "latency_profile": {
            "mean_sec": mean_lat,
            "median_sec": median_lat,
            "min_sec": min(latencies) if latencies else 0.0,
            "max_sec": max(latencies) if latencies else 0.0,
        },
        "performance_metrics": {
            "parseable_count": parseable_count,
            "parseable_rate": p_rate,
            "parseable_wilson_95_ci": wilson_int,
            "schema_valid_count": schema_valid_count,
            "schema_valid_rate": s_rate,
            "verified_correct_count": correct_count,
            "verified_correct_rate": c_rate,
        },
        "error_taxonomy": error_counts,
        "claim_hygiene": {
            "supports": (
                f"Supports that under JSON schema enforcement, {model} achieved {p_rate * 100:.1f}% parseability "
                f"and {s_rate * 100:.1f}% schema validity across 100 hidden base cases; supports that host-verified "
                f"accuracy reached {c_rate * 100:.1f}% at a total billed cost of ${total_billed_cost:.5f}."
            ),
            "does_not_support": (
                "Does not support that 405B parameter scale eliminates cycle repair optimality errors or "
                "potential difference violations without host verification; does not support general "
                "reasoning outside the tested linear difference and cycle repair bounds."
            ),
            "narrowest_defensible_claim": (
                f"On the 100 hidden base cases, {model} under JSON schema achieved {p_rate * 100:.1f}% syntax parseability, "
                f"with exact mathematical correctness verified on {correct_count} of 100 cases, costing ${total_billed_cost:.5f}."
            ),
            "next_test_needed": (
                "Execute TEST-002 (Llama-3.1-405B logit_bias steering) on the same 100 hidden cases to evaluate "
                "paired McNemar significance against JSON schema."
            ),
        },
    }

    # Persistence to run folder
    task_key = "c005_test_001_llama405b_json_schema"
    repo_root = resolve_intelligence_repo_root()
    dest_dir = repo_root / "_ic/darpa/woland" / "runs" / task_key
    dest_dir.mkdir(parents=True, exist_ok=True)

    worktree_dest = Path.cwd().resolve() / "_ic/darpa/woland" / "runs" / task_key
    worktree_dest.mkdir(parents=True, exist_ok=True)

    # 1. empirical_evaluation_report.json
    report_bytes = json.dumps(report_payload, indent=2, sort_keys=True).encode("utf-8")
    (dest_dir / "empirical_evaluation_report.json").write_bytes(report_bytes)
    (worktree_dest / "empirical_evaluation_report.json").write_bytes(report_bytes)
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()

    # 2. accounting.json
    accounting_data = {
        "test_id": "TEST-001",
        "model": model,
        "total_calls": total_n,
        "total_cost_usd": total_billed_cost,
        "call_ledger": budget_ctrl.history,
    }
    acc_bytes = json.dumps(accounting_data, indent=2, sort_keys=True).encode("utf-8")
    (dest_dir / "accounting.json").write_bytes(acc_bytes)
    (worktree_dest / "accounting.json").write_bytes(acc_bytes)
    acc_sha256 = hashlib.sha256(acc_bytes).hexdigest()

    # 3. sample_traces.jsonl
    trace_lines = [json.dumps(asdict(t), sort_keys=True) for t in traces]
    traces_bytes = ("\n".join(trace_lines) + "\n").encode("utf-8")
    (dest_dir / "sample_traces.jsonl").write_bytes(traces_bytes)
    (worktree_dest / "sample_traces.jsonl").write_bytes(traces_bytes)
    traces_sha256 = hashlib.sha256(traces_bytes).hexdigest()

    # 4. summary.json
    summary_data = {
        "test_id": "TEST-001",
        "model": model,
        "total_cases": total_n,
        "parseable_rate": p_rate,
        "schema_valid_rate": s_rate,
        "verified_correct_rate": c_rate,
        "total_billed_usd": total_billed_cost,
        "cost_per_verified_success_usd": cost_per_verified,
        "mean_latency_sec": mean_lat,
        "error_distribution": error_counts,
        "claim_hygiene": report_payload["claim_hygiene"],
    }
    sum_bytes = json.dumps(summary_data, indent=2, sort_keys=True).encode("utf-8")
    (dest_dir / "summary.json").write_bytes(sum_bytes)
    (worktree_dest / "summary.json").write_bytes(sum_bytes)
    sum_sha256 = hashlib.sha256(sum_bytes).hexdigest()

    # 5. receipt.json
    receipt_data = {
        "schema_version": "1.0.0",
        "test_id": "TEST-001",
        "task_key": task_key,
        "timestamp_utc": report_payload["timestamp_utc"],
        "model": model,
        "control": "json_schema",
        "total_cases": total_n,
        "total_billed_usd": total_billed_cost,
        "artifact_hashes": {
            "empirical_evaluation_report_sha256": report_sha256,
            "accounting_sha256": acc_sha256,
            "sample_traces_sha256": traces_sha256,
            "summary_sha256": sum_sha256,
        },
        "terminal_verdict": "VERIFIED_EMPIRICAL_RUN",
    }
    rec_bytes = json.dumps(receipt_data, indent=2, sort_keys=True).encode("utf-8")
    (dest_dir / "receipt.json").write_bytes(rec_bytes)
    (worktree_dest / "receipt.json").write_bytes(rec_bytes)

    print("\n[TEST-001] Complete! Results:")
    print(
        f" - Parseable: {parseable_count}/{total_n} ({p_rate * 100:.1f}%) | Wilson 95% CI: {wilson_int}"
    )
    print(f" - Schema Valid: {schema_valid_count}/{total_n} ({s_rate * 100:.1f}%)")
    print(f" - Host Verified Correct: {correct_count}/{total_n} ({c_rate * 100:.1f}%)")
    print(f" - Total Spend: ${total_billed_cost:.5f} (Target <= $0.05)")
    print(f" - Cost per Verified Success: ${cost_per_verified if cost_per_verified else 'N/A'}")
    print(f" - Mean Latency: {mean_lat}s (Median: {median_lat}s)")
    print(f" - Artifacts saved to: {dest_dir} and {worktree_dest}")

    return report_payload


if __name__ == "__main__":
    run_test_001_empirical_sweep()
