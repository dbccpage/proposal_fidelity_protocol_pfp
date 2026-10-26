"""Bounded execution of original plain and templated pilot-suite prompts.

Dispatches plain and templated P* prompts, grades responses against sovereign host gates,
and compiles cost, token, latency, and accuracy comparisons.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

import yaml

from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.pilots.checker_registry import evaluate_candidate, strict_json


class PilotSuiteDispatchPort(Protocol):
    """Port for chat dispatch. The composition root supplies the adapter."""

    def preflight(
        self, model, *, max_provider_calls, max_output_tokens, max_estimated_cost_microusd=None
    ): ...

    def prepare_run(self, output_dir, run_id, objective_sha256): ...

    def dispatch_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        timeout_sec: int = 90,
        max_retries: int = 4,
        *,
        attempt_id=None,
    ) -> Dict[str, Any]: ...


def sanitize_raw_reply(raw: str) -> Tuple[bool, bool, int, Any]:
    if not isinstance(raw, str):
        return False, False, 0, None
    cleaned = raw.strip()
    fenced = cleaned.startswith("```")
    if fenced:
        cleaned = re.sub(r"^```(?:json|yaml)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        parsed = strict_json(cleaned)
        return fenced, True, len(raw) - len(cleaned), parsed
    except ValueError:
        return fenced, False, len(raw), None


def extract_answer_from_text(raw_text: str, parsed_json: Optional[Any]) -> Optional[int]:
    if isinstance(parsed_json, dict) and "answer" in parsed_json:
        val = parsed_json["answer"]
        if isinstance(val, int) and not isinstance(val, bool):
            return val
        if isinstance(val, str) and val.strip().lstrip("-").isdigit():
            return int(val.strip())

    patterns = [
        r'"answer"\s*:\s*(-?\d+)',
        r'answer\s*[:=]\s*(-?\d+)',
        r'x\s*\+\s*y\s*=\s*(-?\d+)',
        r'add<x,\s*y>\s*=\s*(-?\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None


class EvaluatePilotSuiteUseCase:
    """Orchestrates 22-test pilot execution across plain and templated prompt forms."""

    def __init__(self, provider: Optional[PilotSuiteDispatchPort] = None) -> None:
        self.provider = provider

    def build_test_specs(self, pilot_dir: Path | str) -> List[Dict[str, Any]]:
        """Build test specifications for the 22 pilot tests (11 plain + 11 P*)."""
        pilot_path = Path(pilot_dir).resolve()
        seed_file = pilot_path / "seed.yaml"
        if not seed_file.is_file():
            return []
        seed_data = yaml.safe_load(seed_file.read_text(encoding="utf-8"))

        test_specs: List[Dict[str, Any]] = []

        # 1. Plain Seed
        test_specs.append({
            "test_id": "seed_plain",
            "test_kind": "plain_input",
            "case_id": "seed",
            "source_file": "seed.yaml",
            "source_path": str(seed_file),
            "response_filename": "response_seed_plain.yaml",
            "messages": [{"role": "user", "content": seed_data["seed_prompt"].strip()}],
        })

        # 2. Plain Rewrites 01 to 10
        for i in range(1, 11):
            s_file = f"seed_rewrite_{i:02d}.yaml"
            t_path = pilot_path / "tests" / f"test_{i:02d}"
            s_path = pilot_path / s_file
            if not s_path.is_file():
                if (t_path / s_file).is_file():
                    s_path = t_path / s_file
                elif (t_path / "input.yaml").is_file():
                    s_path = t_path / "input.yaml"
            if s_path.is_file():
                s_data = yaml.safe_load(s_path.read_text(encoding="utf-8"))
                test_specs.append({
                    "test_id": f"rewrite_{i:02d}_plain",
                    "test_kind": "plain_input",
                    "case_id": f"rewrite_{i:02d}",
                    "source_file": s_file,
                    "source_path": str(s_path),
                    "response_filename": f"response_rewrite_{i:02d}_plain.yaml",
                    "messages": [{"role": "user", "content": s_data["seed_prompt"].strip()}],
                })

        # 3. Templated P* Seed
        p_star_file = pilot_path / "p_star.yaml"
        if not p_star_file.is_file():
            t11_named = pilot_path / "tests" / "test_11" / "p_star.yaml"
            t11_p = pilot_path / "tests" / "test_11" / "input.yaml"
            if t11_named.is_file():
                p_star_file = t11_named
            elif t11_p.is_file():
                p_star_file = t11_p
        if p_star_file.is_file():
            p_star_data = yaml.safe_load(p_star_file.read_text(encoding="utf-8"))
            test_specs.append({
                "test_id": "p_star_seed",
                "test_kind": "p_star_templated",
                "case_id": "seed",
                "source_file": "p_star.yaml",
                "source_path": str(p_star_file),
                "response_filename": "response_p_star_seed.yaml",
                "messages": [
                    {"role": "system", "content": p_star_data["system_prompt"].strip()},
                    {
                        "role": "user",
                        "content": f"{p_star_data['user_prompt'].strip()}\n\nReturn JSON matching this response schema:\n{p_star_data['response_schema'].strip()}",
                    },
                ],
            })

        # 4. Templated P* Rewrites 01 to 10
        for i in range(1, 11):
            p_file = f"p_star_rewrite_{i:02d}.yaml"
            t_path = pilot_path / "tests" / f"test_{i+11:02d}"
            p_path = pilot_path / p_file
            if not p_path.is_file():
                if (t_path / p_file).is_file():
                    p_path = t_path / p_file
                elif (t_path / "input.yaml").is_file():
                    p_path = t_path / "input.yaml"
            if p_path.is_file():
                p_data = yaml.safe_load(p_path.read_text(encoding="utf-8"))
                test_specs.append({
                    "test_id": f"p_star_rewrite_{i:02d}",
                    "test_kind": "p_star_templated",
                    "case_id": f"rewrite_{i:02d}",
                    "source_file": p_file,
                    "source_path": str(p_path),
                    "response_filename": f"response_p_star_rewrite_{i:02d}.yaml",
                    "messages": [
                        {"role": "system", "content": p_data["system_prompt"].strip()},
                        {
                            "role": "user",
                            "content": f"{p_data['user_prompt'].strip()}\n\nReturn JSON matching this response schema:\n{p_data['response_schema'].strip()}",
                        },
                    ],
                })

        return test_specs

    def build_obfuscated_v2_specs(self, pilot_dir: Path | str) -> List[Dict[str, Any]]:
        """Build test specifications for the obfuscated rewrites v2 (rewrites 03, 06, 07, 08, 09, 10)."""
        pilot_path = Path(pilot_dir).resolve()
        specs: List[Dict[str, Any]] = []
        v2_map = {3: 22, 6: 23, 7: 24, 8: 25, 9: 26, 10: 27}
        for i in [3, 6, 7, 8, 9, 10]:
            p_file = f"p_star_rewrite_{i:02d}_v2.yaml"
            t_path = pilot_path / "tests" / f"test_{v2_map[i]:02d}"
            p_path = pilot_path / p_file
            if not p_path.is_file():
                if (t_path / p_file).is_file():
                    p_path = t_path / p_file
                elif (t_path / "input.yaml").is_file():
                    p_path = t_path / "input.yaml"
            if p_path.is_file():
                p_data = yaml.safe_load(p_path.read_text(encoding="utf-8"))
                specs.append({
                    "test_id": f"p_star_rewrite_{i:02d}_v2",
                    "test_kind": "p_star_templated",
                    "case_id": f"rewrite_{i:02d}",
                    "source_file": p_file,
                    "source_path": str(p_path),
                    "response_filename": f"response_p_star_rewrite_{i:02d}_v2.yaml",
                    "messages": [
                        {"role": "system", "content": p_data["system_prompt"].strip()},
                        {
                            "role": "user",
                            "content": f"{p_data['user_prompt'].strip()}\n\nReturn JSON matching this response schema:\n{p_data['response_schema'].strip()}",
                        },
                    ],
                })
        return specs

    def execute(
        self,
        pilot_dir: Path | str,
        model: Optional[str] = None,
        test_specs: Optional[List[Dict[str, Any]]] = None,
        results_suffix: str = "",
        *,
        output_dir=None,
        max_cases=5,
        max_provider_calls=5,
        max_output_tokens=512,
        max_estimated_cost_microusd=None,
        dry_run=False,
    ) -> Result[Dict[str, Any], DomainError]:
        """Bounded current execution; source dossiers and prior results are read-only.

        New reports are explicitly versioned for nullable accounting/partial runs.
        The original spec builders and independent candidate judge remain unchanged.
        """
        from hashlib import sha256
        from uuid import uuid4

        try:
            pilot_path = Path(pilot_dir).resolve()
            if not pilot_path.is_dir() or not (pilot_path / "seed.yaml").is_file():
                raise ValueError("PILOT_SEED_REQUIRED")
            if type(dry_run) is not bool:
                raise ValueError("INVALID_DRY_RUN")
            if type(max_cases) is not int or not 0 < max_cases <= 64:
                raise ValueError("INVALID_CASE_LIMIT")
            if type(max_provider_calls) is not int or not 0 < max_provider_calls <= 64:
                raise ValueError("INVALID_CALL_LIMIT")
            if type(max_output_tokens) is not int or not 0 < max_output_tokens <= 3000:
                raise ValueError("INVALID_OUTPUT_BOUND")
            if max_estimated_cost_microusd is not None and (
                type(max_estimated_cost_microusd) is not int
                or not 0 < max_estimated_cost_microusd <= 50000
            ):
                raise ValueError("INVALID_ESTIMATED_BUDGET")
            if results_suffix and re.fullmatch(r"[A-Za-z0-9_-]+", results_suffix) is None:
                raise ValueError("INVALID_RESULTS_SUFFIX")
            spec_file = pilot_path / "spec.yaml"
            spec_data = (
                yaml.safe_load(spec_file.read_text(encoding="utf-8")) if spec_file.is_file() else {}
            )
            pilot_id = spec_data.get("pilot_id", pilot_path.name)
            checker_id = spec_data.get("host_gate", {}).get("checker_id", "PFP-01-EXACT-LINALG")
            seed = yaml.safe_load((pilot_path / "seed.yaml").read_text(encoding="utf-8"))
            expected = seed["expected_outcome"]["answer"]
            specs = list(self.build_test_specs(pilot_path) if test_specs is None else test_specs)[
                :max_cases
            ]
            if not specs:
                raise ValueError("NO_CASE_SELECTED")
            if output_dir is None:
                raise ValueError("OUTPUT_DIR_REQUIRED")
            output = Path(output_dir)
            if output.exists():
                raise ValueError("OUTPUT_DIR_EXISTS")
            reserved = {
                f"comparison_results{results_suffix}.yaml",
                f"comparison_results{results_suffix}.md",
                "accounting.sqlite3",
                "accounting.sqlite3-wal",
                "accounting.sqlite3-shm",
                "accounting.sqlite3.replies",
            }
            reserved = {name.casefold() for name in reserved}
            for spec in specs:
                required = {
                    "test_id",
                    "test_kind",
                    "case_id",
                    "source_file",
                    "response_filename",
                    "messages",
                }
                if (
                    type(spec) is not dict
                    or not required <= set(spec)
                    or any(
                        type(spec[key]) is not str or not spec[key]
                        for key in ("test_id", "case_id", "source_file")
                    )
                    or spec["test_kind"] not in ("plain_input", "p_star_templated")
                ):
                    raise ValueError("INVALID_TEST_SPEC")
                filename = spec["response_filename"]
                if (
                    not isinstance(filename, str)
                    or filename in ("", ".", "..")
                    or filename != filename.rstrip(". ")
                    or Path(filename).name != filename
                    or "/" in filename
                    or "\\" in filename
                    or ":" in filename
                    or filename.casefold() in reserved
                ):
                    raise ValueError("INVALID_RESPONSE_FILENAME")
                reserved.add(filename.casefold())
                source = Path(spec.get("source_path") or pilot_path / spec["source_file"])
                if not source.is_file():
                    raise ValueError("SOURCE_FILE_MISSING")
                if not spec["messages"] or any(
                    set(item) != {"role", "content"}
                    or type(item["role"]) is not str
                    or not item["role"]
                    or type(item["content"]) is not str
                    for item in spec["messages"]
                ):
                    raise ValueError("INVALID_MESSAGES")
            if len({spec["test_id"] for spec in specs}) != len(specs):
                raise ValueError("DUPLICATE_TEST_ID")
            if not dry_run:
                if type(model) is not str or not model.strip():
                    raise ValueError("EXPLICIT_MODEL_REQUIRED")
                if self.provider is None or not callable(getattr(self.provider, "preflight", None)):
                    raise ValueError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
                self.provider.preflight(
                    model,
                    max_provider_calls=max_provider_calls,
                    max_output_tokens=max_output_tokens,
                    max_estimated_cost_microusd=max_estimated_cost_microusd,
                )
            run_id = "pilot-suite:" + uuid4().hex
            objective = sha256(
                json.dumps(
                    dict(
                        pilot_id=pilot_id,
                        model=model,
                        checker_id=checker_id,
                        tests=[
                            dict(test_id=spec["test_id"], messages=spec["messages"])
                            for spec in specs
                        ],
                    ),
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            output.mkdir(parents=True)
            provider = None if dry_run else self.provider
            if provider is not None:
                provider.prepare_run(output, run_id, objective)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return Result.err(DomainError(RefusalCode.INFRASTRUCTURE_FAILURE, str(exc)))

        summaries = []
        stop = None
        grade = "HOST_REFERENCE_SELF_CONSISTENCY" if dry_run else "PFP_BOUND_PROPOSAL"
        for index, spec in enumerate(specs):
            if dry_run:
                # The host oracle is used only here, never in the provider task input.
                proposal = (
                    expected
                    if checker_id
                    in ("PFP-03-EXACT-FOL-DEDUCTION", "PFP-04-EXACT-EPISTEMIC-REFUSAL")
                    else {"answer": expected}
                )
                raw = json.dumps(proposal)
                dispatch = dict(
                    raw_reply=raw,
                    reasoning=None,
                    duration_seconds=0.0,
                    tokens_per_second=None,
                    usage={},
                    cost=dict(total_cost_usd=0.0, total_cost_microusd=0),
                    exchange=None,
                    cost_may_be_incurred=False,
                )
            else:
                dispatch = provider.dispatch_messages(
                    spec["messages"], model=model, attempt_id=f"{run_id}:{index}:{spec['test_id']}"
                )
                raw = dispatch["raw_reply"]
            exchange = dispatch["exchange"]
            fenced, valid, debt, parsed = sanitize_raw_reply(raw)
            eligible = valid and (dry_run or exchange["ok"])
            extracted = extract_answer_from_text(raw, parsed) if eligible else None
            if eligible:
                gate = evaluate_candidate(checker_id, expected, parsed)
                status, reason = gate.status.value, gate.reason
            else:
                status, reason = (
                    "MALFORMED",
                    (exchange["error"] if exchange else "Invalid fixture JSON"),
                )
            if exchange and exchange["stop"]:
                stop = exchange["error"] or "PFP_TERMINAL_STOP"
            source = Path(spec.get("source_path") or pilot_path / spec["source_file"])
            payload_bytes = len(
                "".join(item["content"] for item in spec["messages"]).encode("utf-8")
            )
            usage, cost = dispatch["usage"], dispatch["cost"]
            cost_usd = cost["total_cost_usd"]
            response = dict(
                schema="pfp.pilot-response.accounted.v2",
                authority_effect="None",
                test_id=spec["test_id"],
                test_kind=spec["test_kind"],
                pilot_id=pilot_id,
                case_id=spec["case_id"],
                request_id=f"{run_id}:{index}",
                trial_status="STOPPED" if stop else "COMPLETED",
                model_id=model or "host-fixture",
                evidence_grade=grade,
                raw_reply=raw,
                reasoning_content=dispatch["reasoning"],
                parsed_response=parsed,
                extracted_answer=extracted,
                input_metadata=dict(
                    source_file=spec["source_file"],
                    source_file_bytes=source.stat().st_size,
                    payload_bytes=payload_bytes,
                    messages_count=len(spec["messages"]),
                ),
                sanitization=dict(
                    fence_stripped=fenced, is_valid_json=valid, structure_leakage_debt_chars=debt
                ),
                evaluation=dict(
                    checker_id=checker_id,
                    expected=expected,
                    received=extracted,
                    status=status,
                    reason=reason,
                    judge_eligible=eligible,
                ),
                exchange=exchange,
                receipt=dict(
                    provider="host-fixture" if dry_run else "accounted-pfp",
                    duration_seconds=dispatch["duration_seconds"],
                    usage=usage,
                    cost=cost,
                ),
            )
            (output / spec["response_filename"]).write_text(
                yaml.safe_dump(response, sort_keys=False, allow_unicode=True), encoding="utf-8"
            )
            summaries.append(
                dict(
                    test_id=spec["test_id"],
                    test_kind=spec["test_kind"],
                    case_id=spec["case_id"],
                    source_file=spec["source_file"],
                    response_file=spec["response_filename"],
                    payload_kb=round(payload_bytes / 1024, 3),
                    source_kb=round(source.stat().st_size / 1024, 3),
                    duration_seconds=dispatch["duration_seconds"],
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    reasoning_tokens=usage.get("reasoning_tokens"),
                    total_tokens=usage.get("total_tokens"),
                    cost_usd=cost_usd,
                    cost_microusd=cost["total_cost_microusd"],
                    tokens_per_second=dispatch["tokens_per_second"],
                    extracted_answer=extracted,
                    is_correct=status == "ACCEPTED",
                    gate_status=status,
                    gate_reason=reason,
                    completed=not bool(stop),
                    judge_eligible=eligible,
                    evidence_grade=grade,
                    attempted_send=dispatch["cost_may_be_incurred"],
                )
            )
            if stop:
                break

        def aggregate(entries):
            count = len(entries)
            completed = [item for item in entries if item["completed"] and item["judge_eligible"]]
            correct = sum(item["is_correct"] for item in completed)
            known = sum(item["cost_usd"] for item in entries if item["cost_usd"] is not None)
            total = known if all(item["cost_usd"] is not None for item in entries) else None
            duration = sum(item["duration_seconds"] for item in entries)

            def avg(key):
                return (
                    sum(item[key] for item in entries) / count
                    if count and all(item[key] is not None for item in entries)
                    else None
                )

            return dict(
                count=count,
                completed_count=sum(item["completed"] for item in entries),
                judge_eligible_count=len(completed),
                malformed_or_infrastructure_count=count - len(completed),
                avg_time_sec=duration / count if count else None,
                total_time_sec=duration,
                total_cost_usd=total,
                known_cost_subtotal_usd=known,
                avg_cost_usd=total / count if count and total is not None else None,
                avg_prompt_tokens=avg("prompt_tokens"),
                avg_completion_tokens=avg("completion_tokens"),
                avg_total_tokens=avg("total_tokens"),
                avg_payload_kb=avg("payload_kb"),
                accuracy_ratio=f"{correct}/{len(completed)}",
                accuracy_percent=correct / len(completed) * 100 if completed else None,
            )

        plain = aggregate([row for row in summaries if row["test_kind"] == "plain_input"])
        templated = aggregate([row for row in summaries if row["test_kind"] == "p_star_templated"])
        plain_ids = {
            row["case_id"]
            for row in summaries
            if row["test_kind"] == "plain_input" and row["completed"] and row["judge_eligible"]
        }
        templated_ids = {
            row["case_id"]
            for row in summaries
            if row["test_kind"] == "p_star_templated" and row["completed"] and row["judge_eligible"]
        }
        paired = (
            bool(plain_ids)
            and plain_ids == templated_ids
            and len(plain_ids) == plain["count"] == plain["judge_eligible_count"]
            and len(templated_ids) == templated["count"] == templated["judge_eligible_count"]
        )

        def ratio(key):
            return (
                templated[key] / plain[key]
                if paired and plain[key] and templated[key] is not None
                else None
            )

        comparison = dict(
            schema="pfp.pilot-comparison-results.accounted.v2",
            authority_effect="None",
            pilot_id=pilot_id,
            model_id=model or "host-fixture",
            checker_id=checker_id,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            run_id=run_id,
            objective_sha256=objective,
            total_tests=len(summaries),
            planned_tests=len(specs),
            unattempted_test_ids=[spec["test_id"] for spec in specs[len(summaries) :]],
            stop_reason=stop,
            evidence_grade=grade,
            output_dir=str(output),
            max_output_tokens=max_output_tokens,
            provider_calls=sum(row["attempted_send"] for row in summaries),
            financial_policy="host_fixture" if dry_run else "existing_accounted_gateway",
            aggregates=dict(
                plain_inputs=plain,
                p_star_templated=templated,
                overall=aggregate(summaries),
                ratios_templated_vs_plain=dict(
                    status="AVAILABLE" if paired else "UNAVAILABLE",
                    reason=None
                    if paired
                    else "Every compared row must belong to a unique completed judge-eligible plain/P* pair",
                    cost_ratio=ratio("total_cost_usd"),
                    latency_ratio=ratio("total_time_sec"),
                    tokens_ratio=ratio("avg_total_tokens"),
                    payload_kb_ratio=ratio("avg_payload_kb"),
                ),
            ),
            tests=summaries,
            scope="Finite original host checks; PFP binding is not mathematical admission. Dry fixtures are not model evidence; no causal or provider control-honoring claim.",
        )
        (output / f"comparison_results{results_suffix}.yaml").write_text(
            yaml.safe_dump(comparison, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        lines = [
            f"# {pilot_id}: bounded pilot suite",
            "",
            f"Evidence grade: {grade}",
            f"Stop reason: {stop}",
            "",
            comparison["scope"],
            "",
            "| Test | Status | Cost USD |",
            "|---|---|---|",
        ]
        lines.extend(
            f"| {row['test_id']} | {row['gate_status']} | {row['cost_usd'] if row['cost_usd'] is not None else 'UNKNOWN'} |"
            for row in summaries
        )
        (output / f"comparison_results{results_suffix}.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )
        return Result.ok(comparison)
