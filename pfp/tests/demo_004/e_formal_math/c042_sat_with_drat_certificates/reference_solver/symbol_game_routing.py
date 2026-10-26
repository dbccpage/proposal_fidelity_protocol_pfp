# AuthorityEffect: None.
"""
Symbol Game Routing Engine for C042 SAT Encodings with DRAT Certificates.

Exploratory model matrix (not an SG-CP v1 evaluation) with two methods:
- M1: single-turn prompt with the certificate grammar.
- M3: up to three rounds with checker diagnostics and antibodies.

Custody and scoring rules:
- The provider key comes from the process environment only (no .env file is read).
- The prompt never contains the case's ``expected_kind`` or triviality metadata, and the
  canonical CNF is sent in full.
- Antibodies are scoped to one run and one arm (model x method); each round records the IDs
  it injected.
- Provider failures are INFRA_ERROR, not wrong answers; replies are kept in full.
- UNKNOWN is an abstention, and a verified refutation of a trivially refutable formula (empty
  clause, or refuted by unit propagation) is reported separately and never counted as solved.
- The report states counts only; it draws no conclusions.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.drat_checker import get_canonical_cnf
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual
from omega_engine_pfp.infrastructure.formal_matrix import (
    INFRA_ERROR,
    PARSE_FAILURE,
    ArmAntibodyStore,
    call_openrouter,
    extract_json_object,
    model_label,
    map_back,
    new_run_nonce,
    opaque_token,
    participant_view,
    run_folder,
    write_json,
)

# Keys that give away the verdict or its triviality; never shown to a model.
WITHHELD_KEYS = frozenset(
    {"expected_kind", "trivially_refutable", "trivially_refutable_note", "category"}
)


def problem_view(case: dict[str, Any]) -> dict[str, Any]:
    return {
        k: v for k, v in case.items() if k not in WITHHELD_KEYS and not k.startswith("expected")
    }


def format_prompt_m1(case: dict[str, Any]) -> list[dict[str, str]]:
    """M1: certificate grammar, full canonical CNF."""
    cnf_text, cnf_hash = get_canonical_cnf(case)
    system_msg = (
        "You are an exact SAT solver and DRAT certificate generator.\n"
        "Output ONLY valid RFC 8785 JSON without markdown codeblocks or conversational text.\n"
        "Schema if SAT:\n"
        '{"case_id": "<id>", "status": "SOLVED", "kind": "SAT", "solution": {...}}\n'
        "Schema if UNSAT:\n"
        f'{{"case_id": "<id>", "status": "SOLVED", "kind": "UNSAT", "proof_format": "DRAT", "proof_text": "...", "cnf_sha256": "{cnf_hash}"}}\n'
        "CRITICAL INVARIANTS: All solution values must be exact integers (no booleans). DRAT proof_text must derive the empty clause 0."
    )
    view = problem_view(case)
    user_msg = (
        f"Case ID: {view['case_id']}\n"
        f"Family: {view['family']}\n"
        f"Problem Specification: {json.dumps(view)}\n"
        f"Canonical CNF (complete, {len(cnf_text)} characters):\n{cnf_text}\n"
        f"CNF SHA256: {cnf_hash}\n"
        "Emit JSON answer."
    )
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def format_prompt_m3(
    case: dict[str, Any],
    round_num: int,
    last_error: str | None = None,
    antibodies: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """M3: rounds with checker diagnostics and this arm's own antibodies."""
    cnf_text, cnf_hash = get_canonical_cnf(case)
    system_msg = (
        "You are an exact SAT & DRAT certificate synthesizer under The Symbol Game.\n"
        "Output ONLY valid RFC 8785 JSON:\n"
        '{"case_id": "<id>", "status": "SOLVED", "kind": "SAT"|"UNSAT", ...}\n'
        f'For UNSAT: "proof_format": "DRAT", "proof_text": "<clauses ending with 0>", "cnf_sha256": "{cnf_hash}"\n'
        "If you encounter a checker rejection, apply a Lift (Λ): revise unit propagation or assign alternative variable values."
    )
    view = problem_view(case)
    user_msg = (
        f"Round {round_num} for Case {view['case_id']}:\n"
        f"Family: {view['family']}\n"
        f"Problem: {json.dumps(view)}\n"
        f"Canonical CNF (complete, {len(cnf_text)} characters):\n{cnf_text}\n"
    )
    if antibodies:
        user_msg += "\n--- ANTIBODIES FROM EARLIER ROUNDS OF THIS RUN AND ARM (DO NOT REPEAT THESE MISTAKES) ---\n"
        for ab in antibodies[-3:]:
            user_msg += f"- Rejected: {ab['failed']} -> Reason: {ab['diagnostic']}\n"
    if last_error:
        user_msg += f"\nChecker Rejection Diagnostic from Round {round_num - 1}: {last_error}\n"
        user_msg += "Propose an alternative verified certificate."
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def classify_outcome(ok: bool, answer: dict[str, Any], meta: dict[str, Any]) -> str:
    if ok and meta.get("trivial_refutation"):
        return "VERIFIED_TRIVIAL"
    if ok:
        return "VERIFIED"
    if answer.get("status") == "UNKNOWN":
        return "ABSTAINED"
    return "REJECTED"


def _one_call(
    api_key: str, model_id: str, msgs: list[dict[str, str]], case_id: str,
    *, gateway=None, max_tokens=512, task_id=None, attempt_id=None, token=None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    res = call_openrouter(
        api_key, model_id, msgs, max_tokens=max_tokens, title="The Symbol Game C042 SAT/DRAT Explorer",
        gateway=gateway, task_id=task_id, attempt_id=attempt_id,
    )
    rec: dict[str, Any] = {**res, "messages": msgs, "stop": res.get("stop", not res["ok"])}
    if not res["ok"]:
        rec.update(outcome=INFRA_ERROR, error=res["error"])
        return rec, None
    rec.update(content=res["content"], reasoning=res["reasoning"], usage=res["usage"])
    answer = extract_json_object(res["content"])
    if answer is None:
        rec["outcome"] = PARSE_FAILURE
        return rec, None
    answer.setdefault("case_id", token or case_id)
    return rec, map_back(answer, token or case_id, case_id)


def run_case(
    api_key: str, model_id: str, method: str, case: dict[str, Any], store: ArmAntibodyStore,
    *, gateway=None, max_tokens=512, task_id=None, attempt_id=None,
) -> dict[str, Any]:
    if method not in {"M1_LOGITS", "M3_RETRACTION"}:
        raise ValueError("UNKNOWN_EXPERIMENT_METHOD")
    case_id = case["case_id"]
    task_id = task_id or f"c042:{new_run_nonce()}"
    attempt_id = attempt_id or new_run_nonce()
    token = opaque_token(attempt_id, 0)
    public_case = participant_view(case, token, WITHHELD_KEYS)
    rounds: list[dict[str, Any]] = []
    outcome = PARSE_FAILURE
    last_error: str | None = None
    for r in range(1, 2 if method == "M1_LOGITS" else 4):
        injected = store.active(case_id) if method == "M3_RETRACTION" else []
        public_antibodies = [{**ab,
            "failed": str(ab["failed"]).replace(case_id, token),
            "diagnostic": str(ab["diagnostic"]).replace(case_id, token),
        } for ab in injected]
        msgs = (
            format_prompt_m1(public_case)
            if method == "M1_LOGITS"
            else format_prompt_m3(public_case, r,
                last_error.replace(case_id, token) if last_error else None, public_antibodies)
        )
        rec, answer = _one_call(api_key, model_id, msgs, case_id, gateway=gateway,
            max_tokens=max_tokens, task_id=task_id, attempt_id=f"{attempt_id}:round-{r}", token=token)
        rec["round"] = r
        rec["injected_antibody_ids"] = [ab["antibody_id"] for ab in injected[-3:]]
        rounds.append(rec)
        if answer is None:
            outcome = rec["outcome"]
            if rec["stop"]:
                break
            last_error = "Reply contained no JSON object"
            continue
        ok, msg, meta = evaluate_dual(case, answer)
        outcome = classify_outcome(ok, answer, meta)
        rec.update(answer=answer, verified=ok, message=msg, outcome=outcome)
        if ok:
            break
        last_error = msg
        if method == "M3_RETRACTION":
            store.mint(case_id, answer.get("solution") or answer.get("proof_text") or answer, msg)
    return {"case_id": case_id, "outcome": outcome, "rounds": rounds,
        "stop": bool(rounds[-1].get("stop"))}


def _summary(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o["outcome"]] = counts.get(o["outcome"], 0) + 1
    answered = len(outcomes) - counts.get(INFRA_ERROR, 0)
    return {
        "cases": len(outcomes),
        "answered": answered,
        "verified_nontrivial": counts.get("VERIFIED", 0),
        "verified_trivial_excluded": counts.get("VERIFIED_TRIVIAL", 0),
        "outcomes": counts,
    }


def run_c042_symbol_game_matrix(
    tiers: list[tuple[str, str]] | None = None,
    methods: list[str] | None = None,
    *, gateways=None, max_tokens=512, max_estimated_cost_microusd=None,
    max_provider_calls=None, case_limit=None, env_file=None, cases=None,
) -> Path:
    """Runs the public panel across tiers and methods; writes one run folder and returns it."""
    from omega_engine_pfp.infrastructure.pilot_matrix import _scope, make_pilot_gateways, validate_pilot_gateways

    active_tiers = tiers if tiers is not None else [
        ("8b", "meta-llama/llama-3.1-8b-instruct"),
        ("70b", "meta-llama/llama-3.3-70b-instruct"),
    ]
    active_methods = methods if methods is not None else ["M1_LOGITS", "M3_RETRACTION"]
    cases = cases if cases is not None else [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((_pkg_root / "participant_packet" / "examples").glob("*.json"))
    ]

    if (not active_tiers or not active_methods or set(active_methods) - {"M1_LOGITS", "M3_RETRACTION"}
            or len(set(active_methods)) != len(active_methods) or not cases):
        raise ValueError("EMPTY_OR_UNKNOWN_EXPERIMENT_SELECTION")
    if case_limit is not None and (type(case_limit) is not int or case_limit < 1):
        raise ValueError("INVALID_CASE_LIMIT")
    cases = cases[:case_limit]
    model_ids = [model for _, model in active_tiers]
    if len(set(model_ids)) != len(model_ids):
        raise ValueError("DUPLICATE_EXPERIMENT_MODEL")
    if type(max_tokens) is not int or max_tokens < 1:
        raise ValueError("INVALID_OUTPUT_BOUND")
    if max_estimated_cost_microusd is not None and (type(max_estimated_cost_microusd) is not int or not 0 < max_estimated_cost_microusd <= 50000):
        raise ValueError("INVALID_COST_BOUND")
    if max_provider_calls is not None and (type(max_provider_calls) is not int or not 0 < max_provider_calls <= 64):
        raise ValueError("INVALID_CALL_BOUND")
    if gateways is None:
        if max_estimated_cost_microusd is None or max_provider_calls is None or max_tokens > 3000:
            raise ValueError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
    else:
        validate_pilot_gateways(gateways, model_ids, max_tokens=max_tokens)
        scope = _scope(gateways[model_ids[0]], model_ids[0], max_tokens)
        if ((max_estimated_cost_microusd is not None and scope[2] > max_estimated_cost_microusd)
                or (max_provider_calls is not None and scope[3] > max_provider_calls)):
            raise ValueError("PFP_GATEWAY_ALLOWANCE_EXCEEDS_EXPLICIT_BOUND")
    nonce = new_run_nonce()
    folder = run_folder("c042", nonce)
    if gateways is None:
        gateways = make_pilot_gateways(model_ids, max_output_tokens=max_tokens,
            max_estimated_cost_microusd=max_estimated_cost_microusd, max_calls=max_provider_calls,
            accounting_path=folder / "budget.sqlite3", env_file=env_file)
    record: dict[str, Any] = {
        "challenge": "c042_sat_with_drat_certificates",
        "run_nonce": nonce,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "status": "exploratory model matrix; not an SG-CP v1 evaluation",
        "withheld_case_keys": sorted(WITHHELD_KEYS),
        "arms": [],
    }
    stopped = False
    for tier_index, (tier_name, model_id) in enumerate(active_tiers):
        for method_index, method in enumerate(active_methods):
            arm = f"{tier_name}_{method}"
            store = ArmAntibodyStore(arm, folder)
            outcomes = []
            for case_index, case in enumerate(cases):
                result = run_case("", model_id, method, case, store, gateway=gateways[model_id],
                    max_tokens=max_tokens, task_id=f"c042:{nonce}",
                    attempt_id=f"{nonce}:tier-{tier_index}:method-{method_index}:case-{case_index}")
                outcomes.append(result)
                if result["stop"]:
                    stopped = True
                    record["stop_reason"] = result["rounds"][-1].get("error")
                    break
                time.sleep(0.5)
            record["arms"].append(
                {
                    "arm": arm,
                    "tier": tier_name,
                    "model": model_id,
                    "method": method,
                    "label": model_label(model_id),
                    "summary": _summary(outcomes),
                    "outcomes": outcomes,
                }
            )
            write_json(folder / "run_record.json", record)
            print(f"{arm}: {_summary(outcomes)}")
            if stopped:
                break
        if stopped:
            break
    (folder / "report.md").write_text(render_report(record), encoding="utf-8", newline="\n")
    return folder


def render_report(record: dict[str, Any]) -> str:
    lines = [
        "# C042 model matrix run",
        "",
        f"Run `{record['run_nonce']}`, started {record['started_utc']}. Exploratory; not an SG-CP v1 evaluation.",
        "Prompts, raw replies and per-case results are in `run_record.json` in this folder.",
        "Verified refutations of trivially refutable formulas are counted separately and not as solved.",
        "",
        "| Arm | Model | Cases | Answered | Verified (non-trivial) | Verified (trivial, excluded) | Outcomes |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | :--- |",
    ]
    for arm in record["arms"]:
        s = arm["summary"]
        lines.append(
            f"| {arm['arm']} | `{arm['model']}` | {s['cases']} | {s['answered']} | {s['verified_nontrivial']} | "
            f"{s['verified_trivial_excluded']} | {json.dumps(s['outcomes'], sort_keys=True)} |"
        )
    lines.append("")
    lines.append("This script reports counts only and draws no conclusions from them.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> Path:
    import argparse

    parser = argparse.ArgumentParser(description="Exploratory C042 accounted experiment")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--model", action="append")
    selection.add_argument("--tier", action="append", choices=["8b", "70b"])
    parser.add_argument("--method", action="append", choices=["M1_LOGITS", "M3_RETRACTION"], required=True)
    parser.add_argument("--max-provider-calls", type=int, required=True)
    parser.add_argument("--max-estimated-cost-microusd", type=int, required=True)
    parser.add_argument("--max-output-tokens", type=int, required=True)
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    if not 0 < args.max_provider_calls <= 64 or not 0 < args.max_estimated_cost_microusd <= 50000 or not 0 < args.max_output_tokens <= 3000:
        parser.error("explicit estimated bounds require 1..64 calls, 1..50000 microusd and 1..3000 output tokens")
    if args.case_limit is not None and args.case_limit < 1:
        parser.error("case limit must be positive")
    tier_map = {"8b": "meta-llama/llama-3.1-8b-instruct", "70b": "meta-llama/llama-3.3-70b-instruct"}
    tiers = [(tier, tier_map[tier]) for tier in args.tier] if args.tier else [(model, model) for model in args.model]
    return run_c042_symbol_game_matrix(tiers, args.method, max_tokens=args.max_output_tokens,
        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
        max_provider_calls=args.max_provider_calls, case_limit=args.case_limit, env_file=args.env_file)


if __name__ == "__main__":
    main()
