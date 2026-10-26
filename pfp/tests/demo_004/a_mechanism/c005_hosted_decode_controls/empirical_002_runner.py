"""
Bounded serial TEST-002 execution with explicit logit-bias token provenance.

Original prompts, cases, exact judges and the 96-token output default remain.
Use an explicit bias map/tokenizer or an existing local tokenizer directory;
this runner never downloads one. Paired observations require an explicit,
compatible TEST-001 input and replayed scores. Estimated allowances do not
enforce provider maximum liability. Host fixtures and requested payloads do
not demonstrate model performance or provider-honored decoding controls.

AuthorityEffect: None.
"""

from __future__ import annotations

__test__ = False

import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, TYPE_CHECKING
from uuid import uuid4

_worktree_root = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "omega_engine_pfp").is_dir() and (parent / "omega_engine_woland").is_dir()
    ),
    None,
)
if _worktree_root is not None and str(_worktree_root) not in sys.path:
    sys.path.insert(0, str(_worktree_root))

if TYPE_CHECKING:
    from openai import OpenAI

from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.budget_controller import (
    BudgetController,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.cases import (
    get_hidden_base_cases,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.checkers import (
    verify_consistency_certificate,
    verify_cycle_repair,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.controls import (
    build_logit_bias_map,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.runner import (
    mcnemar_exact_p_value,
    wilson_score_interval as wilson_score_interval,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.schemas import (
    validate_json_schema,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_001_runner import (
    SYSTEM_PROMPT,
    _complete_case,
    _trace_metadata,
    _observed,
    _run_sweep,
    _main,
    _hash,
    _public_input,
    _protocol_hash,
)
from omega_engine_pfp.infrastructure.synthesis_matrix import RunnerRefusal
from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn

from omega_engine_woland.domain.providers.types import DecodingParamsV1


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


def execute_single_case_logit_bias(
    case: dict[str, Any],
    client: OpenAI,
    model: str,
    bias_map: dict[int, int],
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
    """Execute one case under logit_bias steering."""
    kind = case.get("kind", "consistency")
    case_id = case.get("case_id", "unknown")

    if kind == "consistency":
        schema_name = "consistency_verdict"
        prompt = (
            f"{case.get('prompt')}\n"
            "Output strict JSON only with keys 'verdict' ('CONSISTENT' or 'INCONSISTENT') and 'certificate'. "
            "If CONSISTENT, certificate maps each node identifier to its integer potential. "
            "If INCONSISTENT, certificate must be empty {}."
        )
    else:
        schema_name = "cycle_repair_solution"
        prompt = (
            f"{case.get('prompt')}\n"
            "Output strict JSON only with keys 'status' ('SOLVED'), 'repaired' (list of integer strings), and 'weighted_l1' (string)."
        )

    bias = _normalize_bias_map(bias_map)
    provenance = dict(
        source="explicit_map",
        tokenizer=tokenizer_provenance or "unspecified_explicit_map",
        map_sha256=_hash(bias),
        model=model,
        provider_honored=None,
    )
    decoding = DecodingParamsV1(temperature=0.0, logit_bias=bias)
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
            control="logit_bias",
            provenance=provenance,
            dry_run=dry_run,
        ),
    )
    if not exchange["ok"]:
        parsed, parseable, valid_schema, _ = _observed(content, schema_name, "logit_bias")
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

    # Parse JSON
    content_str = content.strip()
    parsed: dict[str, Any] = {}
    is_parseable = False
    try:
        parsed = json.loads(content_str)
        is_parseable = True
    except Exception:
        # Check if model wrapped JSON in markdown code fence or prose
        start = content_str.find("{")
        end = content_str.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(content_str[start : end + 1])
                is_parseable = True
            except Exception:
                is_parseable = False

    if not is_parseable:
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
            error_message="Output does not contain valid JSON (prose leakage)",
        )

    # Schema shape validation
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

    # Exact Host Verification
    if kind == "consistency":
        edges = case.get("edges", [])
        verdict = parsed.get("verdict", "")
        cert = parsed.get("certificate", {})
        check = verify_consistency_certificate(edges, verdict, cert)
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


def _normalize_bias_map(bias_map):
    if not isinstance(bias_map, dict) or not bias_map:
        raise RunnerRefusal(
            "EXPLICIT_BIAS_OR_LOCAL_TOKENIZER_REQUIRED", "supply an explicit nonempty token map"
        )
    normalized = {}
    for token, value in bias_map.items():
        key = str(token)
        if (
            type(token) not in (int, str)
            or not key.isascii()
            or not key.isdecimal()
            or key != str(int(key))
            or type(value) is not int
            or not -100 <= value <= 100
            or key in normalized
        ):
            raise RunnerRefusal(
                "INVALID_LOGIT_BIAS",
                "use unique nonnegative token IDs and exact biases from -100 to 100",
            )
        normalized[key] = value
    return normalized


def _bias_map(bias_map, tokenizer, tokenizer_path, provenance):
    if sum(value is not None for value in (bias_map, tokenizer, tokenizer_path)) != 1:
        raise RunnerRefusal(
            "EXPLICIT_BIAS_OR_LOCAL_TOKENIZER_REQUIRED",
            "choose one explicit map or local tokenizer",
        )
    if tokenizer_path is not None:
        path = Path(tokenizer_path)
        if not path.is_dir():
            raise RunnerRefusal(
                "LOCAL_TOKENIZER_UNAVAILABLE", "tokenizer path must be an existing local directory"
            )
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RunnerRefusal(
                "LOCAL_TOKENIZER_DEPENDENCY_UNAVAILABLE", "install tokenizer support explicitly"
            ) from exc
        tokenizer = AutoTokenizer.from_pretrained(
            str(path), local_files_only=True, trust_remote_code=False
        )
        provenance = provenance or str(path.resolve())
    if tokenizer is not None:
        bias_map = build_logit_bias_map(tokenizer=tokenizer)
        provenance = provenance or str(
            getattr(tokenizer, "name_or_path", "explicit_tokenizer_object")
        )
    return _normalize_bias_map(bias_map), provenance or "unspecified_explicit_map"


def _paired_analysis(baseline_traces, current_traces, *, cases=None):
    """Replay binding and original judge results before counting supplied pairs.

    These are compatible observations, not authentication or proof that a
    provider honored either requested control.
    """
    unavailable = dict(
        status="UNAVAILABLE",
        reason="NO_BASELINE",
        paired_total=None,
        correctness_contingency=None,
        correctness_mcnemar_exact_p_value=None,
        correctness_statistically_significant=None,
        parseability_contingency=None,
        parseability_mcnemar_exact_p_value=None,
        parseability_statistically_significant=None,
    )
    if baseline_traces is None:
        return unavailable
    try:
        if isinstance(baseline_traces, (str, Path)):
            baseline_traces = [
                json.loads(line)
                for line in Path(baseline_traces).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        baseline = [asdict(row) if not isinstance(row, dict) else row for row in baseline_traces]
        current = [asdict(row) if not isinstance(row, dict) else row for row in current_traces]
        base_ids, current_ids = (
            [row["case_id"] for row in baseline],
            [row["case_id"] for row in current],
        )
        if (
            not current
            or len(set(base_ids)) != len(base_ids)
            or len(set(current_ids)) != len(current_ids)
            or set(base_ids) != set(current_ids)
        ):
            return dict(unavailable, reason="DUPLICATE_OR_INCOMPLETE_PAIRS")
        bank = {
            case["case_id"]: case for case in (get_hidden_base_cases() if cases is None else cases)
        }
        by_id = {row["case_id"]: row for row in baseline}
        compare_keys = (
            "task_id",
            "task_sha256",
            "input_sha256",
            "input_hash_scope",
            "case_sha256",
            "protocol_sha256",
            "model",
            "max_output_tokens",
            "temperature",
            "evidence_grade",
        )
        for row in current:
            old = by_id[row["case_id"]]
            if (
                old["control"] != "json_schema"
                or row["control"] != "logit_bias"
                or any(old[key] != row[key] for key in compare_keys)
            ):
                return dict(unavailable, reason="INCOMPATIBLE_TASK_OR_SETTINGS")
            case = bank[row["case_id"]]
            if (
                row["case_sha256"] != _hash(case)
                or row["input_sha256"] != _hash(_public_input(case))
                or row["protocol_sha256"] != _protocol_hash()
                or row["evidence_grade"] != "PFP_BOUND_PROPOSAL"
                or row["input_hash_scope"] != "original_public_task"
            ):
                return dict(unavailable, reason="UNVERIFIABLE_SOURCE_OR_GRADE")
            for trace in (old, row):
                reason = _recheck_trace(trace, case)
                if reason:
                    return dict(unavailable, reason=reason)
        b = c = both = neither = parse_b = parse_c = 0
        for row in current:
            old = by_id[row["case_id"]]
            b += old["is_correct"] and not row["is_correct"]
            c += not old["is_correct"] and row["is_correct"]
            both += old["is_correct"] and row["is_correct"]
            neither += not old["is_correct"] and not row["is_correct"]
            parse_b += old["is_parseable"] and not row["is_parseable"]
            parse_c += not old["is_parseable"] and row["is_parseable"]
        correct_p, parse_p = mcnemar_exact_p_value(b, c), mcnemar_exact_p_value(parse_b, parse_c)
        return dict(
            status="AVAILABLE",
            reason=None,
            paired_total=len(current),
            scope="rechecked supplied paired observations; no provider-honoring or causal claim",
            correctness_contingency={
                "both_correct": both,
                "schema_correct_bias_incorrect (b)": b,
                "schema_incorrect_bias_correct (c)": c,
                "both_incorrect": neither,
            },
            correctness_mcnemar_exact_p_value=correct_p,
            correctness_statistically_significant=correct_p < 0.05,
            parseability_contingency={
                "schema_parseable_bias_unparseable (b)": parse_b,
                "schema_unparseable_bias_parseable (c)": parse_c,
            },
            parseability_mcnemar_exact_p_value=parse_p,
            parseability_statistically_significant=parse_p < 0.05,
        )
    except (ValueError, KeyError, TypeError, IndexError, OSError):
        return dict(unavailable, reason="UNVERIFIABLE_BASELINE")


def _recheck_trace(trace, case):
    import base64
    from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls import (
        empirical_001_runner as schema_arm,
    )

    if trace["stop"] or trace["exchange"].get("attempt_state") not in {
        "CompletedSettled",
        "CompletedPendingSettlement",
    }:
        return "INCOMPLETE_OR_UNSETTLED_OBSERVATION"
    strict = trace["control"] == "json_schema"
    executor = schema_arm.execute_single_case if strict else execute_single_case_logit_bias
    args = [case, None, trace["model"]] + ([] if strict else [{"0": 0}]) + [BudgetController()]
    reference = executor(*args, dry_run=True, max_tokens=trace["max_output_tokens"])
    if trace["prompt"] != reference.prompt or trace["task_sha256"] != reference.task_sha256:
        return "PROMPT_OR_TASK_MISMATCH"
    schema_name = (
        "consistency_verdict" if case["kind"] == "consistency" else "cycle_repair_solution"
    )
    answer_schema = (
        (
            schema_arm.CONSISTENCY_JSON_SCHEMA
            if case["kind"] == "consistency"
            else schema_arm.CYCLE_REPAIR_JSON_SCHEMA
        )["schema"]
        if strict
        else {"anyOf": [{"type": "object"}, {"type": "array"}, {"type": "string", "minLength": 1}]}
    )
    turn = prepare_task_turn(
        system=SYSTEM_PROMPT,
        user=trace["prompt"],
        task_id=trace["task_id"],
        attempt_id=trace["attempt_id"],
        answer_schema=answer_schema,
        checker_id="pilot-original-judge-pending-v1",
    )
    request = trace["exchange"]["request"]
    if (
        request["model"] != trace["model"]
        or request["max_tokens"] != trace["max_output_tokens"]
        or request["temperature"] != trace["temperature"]
        or request["messages"]
        != [
            {"role": "system", "content": turn.prompt.system},
            {"role": "user", "content": turn.prompt.user},
        ]
    ):
        return "REQUEST_BINDING_MISMATCH"
    if strict:
        descriptor = request["response_format"]["json_schema"]
        if (
            descriptor["schema"] != turn.prompt.response_schema
            or descriptor["name"] != schema_name
            or descriptor["strict"] is not True
        ):
            return "REQUEST_CONTROL_MISMATCH"
    elif (
        "response_format" in request
        or _hash(request["logit_bias"]) != trace["control_provenance"]["map_sha256"]
    ):
        return "REQUEST_CONTROL_MISMATCH"
    wire = trace["exchange"]["provider_wire"]
    raw = base64.b64decode(wire["raw_reply_base64"], validate=True)
    if (
        hashlib.sha256(raw).hexdigest() != wire["raw_reply_sha256"]
        or len(raw) != wire["raw_reply_bytes"]
    ):
        return "RAW_REPLY_MISMATCH"
    content = json.loads(raw)["choices"][0]["message"]["content"]
    envelope = json.loads(content)
    if any(
        envelope.get(key) != turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")
    ):
        return "PFP_BINDING_MISMATCH"
    checked = turn.check_completion(content)
    proposal = envelope["answer"]
    observed = proposal if isinstance(proposal, str) else json.dumps(proposal)
    _, parseable, valid, _ = _observed(observed, schema_name, trace["control"])
    eligible = checked["schema_valid"] and checked["failure_class"] == "NONE"
    correct = False
    if eligible:
        rechecked = executor(
            *args, dry_run=True, mock_solution=proposal, max_tokens=trace["max_output_tokens"]
        )
        correct = rechecked.is_correct
    fields = dict(
        is_parseable=parseable, is_schema_valid=valid, is_correct=correct, judge_eligible=eligible
    )
    if any(type(trace[key]) is not bool or trace[key] != value for key, value in fields.items()):
        return "TAMPERED_STORED_SCORE"
    return None


def run_test_002_empirical_sweep(
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
    bias_map=None,
    tokenizer=None,
    tokenizer_path=None,
    tokenizer_provenance=None,
    baseline_traces=None,
) -> dict[str, Any]:
    bias, provenance = _bias_map(bias_map, tokenizer, tokenizer_path, tokenizer_provenance)
    report = _run_sweep(
        model,
        concurrency,
        execute=execute_single_case_logit_bias,
        test_id="TEST-002",
        control="logit_bias",
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
        bias_map=bias,
        tokenizer_provenance=provenance,
    )
    report["mcnemar_paired_analysis"] = _paired_analysis(
        baseline_traces, report["case_traces"], cases=cases
    )
    if output_dir is not None:
        from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_001_runner import (
            _persist,
        )

        _persist(report, Path(output_dir))
    return report


def main(argv=None):
    return _main(run_test_002_empirical_sweep, argv, bias=True)


if __name__ == "__main__":
    raise SystemExit(main())
