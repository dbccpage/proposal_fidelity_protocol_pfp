# AuthorityEffect: None.
"""
Symbol Game Multi-Method & Multi-Scale Exploration Engine for C041.

Evaluates 5 experimental methods across 4 parameter scale tiers:
Methods:
  M1 (Logits): Grammar constraint & negative logit bias against banned tactics.
  M2 (Attn): Pinned attention steering, system isolation & invariant frames.
  M3 (Retract): Multi-turn retraction with autonomous lifts & antibody injection from Cemetery.
  M4 (Scratch): Formal goal-state scratchpads decoupling planning from Lean syntax.
  M5 (Runes): Hieroglyphic Egyptian rune prompt encoding stripping English prose prior.

Scale Tiers (via OpenRouter):
  Tier 1 (8B): meta-llama/llama-3.1-8b-instruct
  Tier 2 (70B): meta-llama/llama-3.3-70b-instruct
  Tier 3 (500B MoE): deepseek/deepseek-chat
  Tier 4 (1000B+ Frontier): openai/gpt-4o

Exploratory; not an SG-CP v1 evaluation. Custody and scoring rules:
- The provider key comes from the process environment only (no .env file is read).
- A reply without a JSON object is a PARSE_FAILURE; no answer is ever invented for it.
- Provider failures are INFRA_ERROR, not wrong answers; replies are kept in full.
- M3 antibodies are scoped to one run and one arm (model x method); each round records the
  antibody IDs it injected.
- Only kernel-verified PROOF or REFUTATION answers count as verified; refusals (UNKNOWN,
  OUT_OF_SCOPE) are counted separately.
- Each run writes prompts, raw replies, per-case outcomes and `lean --version` to a new
  folder under the intelligence root.

Method names describe experimental prompt variants; no attention or logit hooks are implemented.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if p.name == "certified_challenges"), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator import evaluate_dual  # noqa: E402
from pfp.infrastructure.formal_matrix import (  # noqa: E402
    INFRA_ERROR,
    PARSE_FAILURE,
    ArmAntibodyStore,
    RunnerConfigError,
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
from c041_lean4_finite_lemma_proofs.reference_solver.lean_compiler import lean_version  # noqa: E402

# Hieroglyphic rune mapping for M5
RUNE_MAP = {
    "∀": "𓁿",
    "∃": "𓇯",
    "→": "𓈖",
    "↔": "𓊪",
    "∧": "𓉐",
    "∨": "𓊝",
    "¬": "𓆙",
    "=": "𓎛",
    "≠": "𓏏",
    "+": "𓐍",
    "*": "𓃀",
    "<": "𓅃",
    "≤": "𓆓",
}

RUNE_REV_MAP = {v: k for k, v in RUNE_MAP.items()}


def encode_runes(text: str) -> str:
    """Translates standard mathematical symbols into hieroglyphic runes."""
    encoded = text
    for sym, rune in RUNE_MAP.items():
        encoded = encoded.replace(sym, rune)
    return encoded


def decode_runes(text: str) -> str:
    """Translates hieroglyphic runes back to mathematical symbols."""
    decoded = text
    for rune, sym in RUNE_REV_MAP.items():
        decoded = decoded.replace(rune, sym)
    return decoded


def format_messages_m1_logits(case: Dict[str, Any]) -> List[Dict[str, str]]:
    """M1: Logits / Grammar Masking prompt."""
    system_msg = (
        "You are an exact Lean 4 theorem prover. Output ONLY a valid JSON object:\n"
        '{"status": "SOLVED", "kind": "PROOF"|"REFUTATION", "proof": "by <tactics>"}\n'
        "ABSOLUTE CONSTRAINT: Forbidden tactics: sorry, native_decide, axiom, unsafe, partial.\n"
        "Allowed tactics: decide, rfl, omega, simp, intro, cases, revert, constructor."
    )
    user_msg = (
        f"Case ID: {case['case_id']}\n"
        f"Prelude:\n{case.get('prelude', '')}\n"
        f"Statement: {case['statement']}\n"
        "Emit JSON answer."
    )
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def format_messages_m2_attention(case: Dict[str, Any]) -> List[Dict[str, str]]:
    """M2: Attention Steering with Pinned Invariant Frames."""
    system_msg = (
        "<INVARIANT_FRAME>\n"
        "DOMAIN: Core Lean 4 (leanprover/lean4:v4.34.1)\n"
        "AXIOM_CLOSURE: [propext, Quot.sound]\n"
        "ATTENTION_LOCK: Target statement decidability structure\n"
        "OUTPUT_FORMAT: Raw RFC 8785 JSON only. Zero prose.\n"
        "</INVARIANT_FRAME>"
    )
    user_msg = (
        f'<GOAL_SPEC id="{case["case_id"]}">\n'
        f"<PRELUDE>{case.get('prelude', '')}</PRELUDE>\n"
        f"<PROPOSITION>{case['statement']}</PROPOSITION>\n"
        "</GOAL_SPEC>\n"
        'JSON format: {"status": "SOLVED", "kind": "PROOF"|"REFUTATION", "proof": "..."}'
    )
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def format_messages_m3_retraction(
    case: Dict[str, Any],
    round_num: int,
    last_error: Optional[str] = None,
    antibodies: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """M3: Multi-Round Retraction with Injected Antibodies and Autonomous Lifts."""
    system_msg = (
        "You are participating in The Symbol Game. You must synthesize a Lean 4 proof or refutation.\n"
        "Output ONLY a valid JSON object:\n"
        '{"status": "SOLVED", "kind": "PROOF"|"REFUTATION", "proof": "by <tactics>", "aux": []}\n'
        'CRITICAL: "kind" must strictly be "PROOF" or "REFUTATION". Never set "kind" to "LIFT".\n'
        'If you encounter a timeout or Lean error, apply a Lift (Λ): provide an auxiliary lemma in "aux" or an alternate tactic (decide, omega, simp, cases) in "proof".'
    )
    msgs = [{"role": "system", "content": system_msg}]

    user_body = f"Round {round_num} for Case {case['case_id']}:\nStatement: {case['statement']}\n"
    if case.get("prelude"):
        user_body += f"Prelude:\n{case['prelude']}\n"

    if antibodies:
        user_body += "\n--- ANTIBODIES FROM EARLIER ROUNDS OF THIS RUN AND ARM (DO NOT REPEAT THESE MISTAKES) ---\n"
        for ab in antibodies[-3:]:  # Last 3 antibodies of this run and arm
            user_body += f"- Failed Proof: `{ab['failed']}` -> Error: {ab['diagnostic']}\n"

    if last_error:
        user_body += f"\nCompiler Diagnostic from Round {round_num - 1}: {last_error}\n"
        user_body += "Propose an alternative tactic lift (Λ) to bypass this obstruction."

    msgs.append({"role": "user", "content": user_body})
    return msgs


def format_messages_m4_scratchpad(case: Dict[str, Any]) -> List[Dict[str, str]]:
    """M4: Structured Goal-State Scratchpad."""
    system_msg = (
        "You are an expert formal mathematician. First, analyze the goal in a <scratchpad> block:\n"
        "<scratchpad>\n"
        "Domain bounds: ...\n"
        "Truth status: TRUE (PROOF) or FALSE (REFUTATION)\n"
        "Tactic strategy: (e.g. decide, range split, witness)\n"
        "</scratchpad>\n"
        "Then output the final JSON on the next line:\n"
        '{"status": "SOLVED", "kind": "PROOF"|"REFUTATION", "proof": "..."}'
    )
    user_msg = (
        f"Case: {case['case_id']}\n"
        f"Prelude:\n{case.get('prelude', '')}\n"
        f"Statement: {case['statement']}\n"
        "Analyze in scratchpad, then emit JSON."
    )
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def format_messages_m5_runes(case: Dict[str, Any]) -> List[Dict[str, str]]:
    """M5: Hieroglyphic Egyptian Rune Prompting."""
    encoded_stmt = encode_runes(case["statement"])
    system_msg = (
        "𓊝 𓉐 𓊪 THE SYMBOL GAME RUNE MATRIX 𓊪 𓉐 𓊝\n"
        "Runes: 𓁿=∀, 𓇯=∃, 𓈖=→, 𓉐=∧, 𓊝=∨, 𓆙=¬, 𓎛==, 𓏏=≠, 𓐍=+, 𓃀=*, 𓅃=<, 𓆓=≤.\n"
        "Evaluate truth of Rune Proposition and emit Lean 4 tactic in JSON:\n"
        '{"status": "SOLVED", "kind": "PROOF"|"REFUTATION", "proof": "by <tactic>"}'
    )
    user_msg = f"RUNE PROPOSITION: {encoded_stmt}\nLEAN STATEMENT: {case['statement']}\nEmit JSON."
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def extract_json_answer(raw_text: str, case_id: str) -> Optional[Dict[str, Any]]:
    """The JSON answer in the reply, or None. Never invents an answer from prose."""
    parsed = extract_json_object(raw_text)
    if parsed is not None and "case_id" not in parsed:
        parsed["case_id"] = case_id
    return parsed


FORMATTERS = {
    "M1_LOGITS": format_messages_m1_logits,
    "M2_ATTENTION": format_messages_m2_attention,
    "M4_SCRATCHPAD": format_messages_m4_scratchpad,
    "M5_RUNES": format_messages_m5_runes,
}


def _accounting_states(gateway) -> dict[str, str]:
    from pfp.infrastructure.estimated_gateway import DurableRunGateway, EstimatedBudgetGateway

    if not isinstance(gateway, (DurableRunGateway, EstimatedBudgetGateway)):
        return {}
    limit = gateway.limit if isinstance(gateway, EstimatedBudgetGateway) else gateway.scope["limit_microusd"]
    with gateway.ledger.transaction(limit) as state:
        return {f"{kind}:{identity}": row["state"]
            for kind in ("attempts", "action_claims")
            for identity, row in state.get(kind, {}).items()}


def _round(
    api_key: str, model: str, msgs: List[Dict[str, Any]], case: Dict[str, Any],
    *, gateway=None, max_tokens: int = 512, task_id=None, attempt_id=None, token=None,
) -> Dict[str, Any]:
    before = _accounting_states(gateway)
    res = call_openrouter(
        api_key, model, msgs, max_tokens=max_tokens, title="The Symbol Game C041 Explorer",
        gateway=gateway, task_id=task_id, attempt_id=attempt_id,
    )
    rec: Dict[str, Any] = {**res, "messages": msgs, "stop": res.get("stop", not res["ok"])}
    after = _accounting_states(gateway)
    rec["cost_may_be_incurred"] = bool(res.get("provider_wire") is not None or res["ok"]
        or any(after[key] != "refused_before_dispatch" for key in after.keys() - before.keys()))
    if not res["ok"]:
        rec.update(outcome=INFRA_ERROR, error=res["error"], verified=False)
        return rec
    rec.update(content=res["content"], usage=res["usage"])
    ans = extract_json_answer(res["content"], token or case["case_id"])
    if ans is None:
        rec.update(outcome=PARSE_FAILURE, verified=False, msg="Reply contained no JSON object")
        return rec
    ans = map_back(ans, token or case["case_id"], case["case_id"])
    ok, msg, meta = evaluate_dual(case, ans)
    rec.update(ans=ans, verified=ok, msg=msg, outcome=meta.get("outcome", "REJECTED"))
    return rec


def run_experiment_on_lemma(
    api_key: str,
    case: Dict[str, Any],
    model: str,
    method: str,
    store: Optional[ArmAntibodyStore] = None,
    *, gateway=None, max_tokens: int = 512, task_id=None, attempt_id=None,
) -> Dict[str, Any]:
    """Runs one lemma through one method; M3 uses only this run's and arm's antibodies."""
    t0 = time.time()
    if method not in {*FORMATTERS, "M3_RETRACTION"}:
        raise RunnerConfigError("UNKNOWN_EXPERIMENT_METHOD")
    task_id = task_id or f"c041:{new_run_nonce()}"
    attempt_id = attempt_id or new_run_nonce()
    token = opaque_token(attempt_id, 0)
    public_case = participant_view(case, token)
    rounds: List[Dict[str, Any]] = []
    if method == "M3_RETRACTION":
        store = store or ArmAntibodyStore(f"{model}_{method}")
        last_error: Optional[str] = None
        for r in range(1, 4):
            injected = store.active(case["case_id"])
            public_antibodies = [{**ab,
                "failed": str(ab["failed"]).replace(case["case_id"], token),
                "diagnostic": str(ab["diagnostic"]).replace(case["case_id"], token),
            } for ab in injected]
            msgs = format_messages_m3_retraction(
                public_case, round_num=r,
                last_error=last_error.replace(case["case_id"], token) if last_error else None,
                antibodies=public_antibodies,
            )
            rec = _round(api_key, model, msgs, case, gateway=gateway, max_tokens=max_tokens,
                task_id=task_id, attempt_id=f"{attempt_id}:round-{r}", token=token)
            rec["round"] = r
            rec["injected_antibody_ids"] = [ab["antibody_id"] for ab in injected[-3:]]
            rounds.append(rec)
            if rec["verified"] or rec["stop"]:
                break
            if not rec["ok"]:
                last_error = rec.get("error", "PFP reply was invalid")
                continue
            if rec["outcome"] == INFRA_ERROR:
                break
            last_error = rec.get("msg")
            store.mint(
                case["case_id"],
                (rec.get("ans") or {}).get("proof", rec.get("content", "")),
                last_error or "",
            )
    else:
        rec = _round(api_key, model, FORMATTERS[method](public_case), case,
            gateway=gateway, max_tokens=max_tokens, task_id=task_id,
            attempt_id=f"{attempt_id}:round-1", token=token)
        rec["round"] = 1
        rounds.append(rec)
    final = rounds[-1]
    usage = [r.get("usage") or {} for r in rounds]
    executed = [r for r in rounds if r["cost_may_be_incurred"]]
    costs = [(r.get("usage") or {}).get("cost") for r in executed]
    known_cost = sum(cost for cost in costs if cost is not None)
    return {
        "case_id": case["case_id"],
        "method": method,
        "model": model,
        "verified": bool(final["verified"]),
        "outcome": final["outcome"],
        "eval_msg": final.get("msg", final.get("error", "")),
        "final_answer": final.get("ans"),
        "prompt_tokens": sum(u.get("prompt_tokens", 0) or 0 for u in usage),
        "completion_tokens": sum(u.get("completion_tokens", 0) or 0 for u in usage),
        "cost_usd": None if any(cost is None for cost in costs) else known_cost,
        "cost_known_subtotal_usd": known_cost,
        "stop": bool(final.get("stop")),
        "duration_sec": time.time() - t0,
        "rounds": rounds,
    }


def run_benchmark_panel(
    model: str,
    method: str,
    cases: List[Dict[str, Any]],
    folder: Optional[Path] = None,
    *, gateway=None, max_tokens: int = 512, task_id=None, attempt_id=None,
) -> Dict[str, Any]:
    """Runs the panel for one (method, model) arm and writes its record to the run folder."""
    from pfp.infrastructure.pilot_matrix import validate_pilot_gateways

    if not cases or method not in {*FORMATTERS, "M3_RETRACTION"}:
        raise RunnerConfigError("EMPTY_OR_UNKNOWN_EXPERIMENT_SELECTION")
    validate_pilot_gateways({model: gateway}, [model], max_tokens=max_tokens)
    if folder is None:
        folder = run_folder("c041", new_run_nonce())
    arm = f"{method}_{model.replace('/', '_')}"
    if (folder / f"{arm}.json").exists():
        raise RunnerConfigError("OUTPUT_FILE_EXISTS")
    task_id = task_id or f"c041:{new_run_nonce()}"
    attempt_id = attempt_id or new_run_nonce()
    store = ArmAntibodyStore(arm, folder)
    outcomes = []
    for idx, case in enumerate(cases):
        res = run_experiment_on_lemma("", case, model=model, method=method, store=store,
            gateway=gateway, max_tokens=max_tokens, task_id=task_id,
            attempt_id=f"{attempt_id}:case-{idx}")
        print(
            f"[{res['outcome']}] [{idx + 1}/{len(cases)}] {case['case_id']} | {str(res['eval_msg'])[:60]}"
        )
        outcomes.append(res)
        if res["stop"]:
            break

    counts: Dict[str, int] = {}
    for o in outcomes:
        counts[o["outcome"]] = counts.get(o["outcome"], 0) + 1
    answered = len(outcomes) - counts.get(INFRA_ERROR, 0)
    verified = sum(1 for o in outcomes if o["verified"])
    known_cost = sum(o["cost_known_subtotal_usd"] for o in outcomes)
    total_cost = None if any(o["cost_usd"] is None for o in outcomes) else known_cost
    summary = {
        "method": method,
        "model": model,
        "label": model_label(model),
        "status": "exploratory; not an SG-CP v1 evaluation",
        "lean_version": lean_version(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(outcomes),
        "answered_cases": answered,
        "passed_cases": verified,
        "pass_rate_of_answered": (verified / answered) if answered else None,
        "outcome_counts": counts,
        "total_cost_usd": total_cost,
        "total_cost_known_subtotal_usd": known_cost,
        "cost_per_verified_success_usd": (total_cost / verified) if verified and total_cost is not None else None,
        "stop": bool(outcomes[-1]["stop"]),
        "stop_reason": outcomes[-1]["rounds"][-1].get("error") if outcomes[-1]["stop"] else None,
        "method_scope": "experimental prompt variant; no attention or logit hooks",
        "total_prompt_tokens": sum(o["prompt_tokens"] for o in outcomes),
        "total_completion_tokens": sum(o["completion_tokens"] for o in outcomes),
        "outcomes": outcomes,
    }
    write_json(folder / f"{arm}.json", summary)
    print(
        f"Completed {arm}: {verified}/{answered} verified of answered; outcomes {counts}; saved in {folder}"
    )
    return summary


def load_calibrated_10_lemma_panel() -> List[Dict[str, Any]]:
    """Loads the 10 calibrated benchmark lemmas from participant_packet/examples."""
    ex_dir = _pkg_root / "participant_packet" / "examples"
    panel_ids = [
        "c041_pub_01",  # Fin 5 commutativity (PROOF)
        "c041_pub_02",  # Fin 7 prime zero divisors (PROOF)
        "c041_pub_03",  # Bool identity (PROOF)
        "c041_pub_04",  # Small bounded Nat (PROOF)
        "c041_pub_05",  # Bounded Nat inequality (PROOF)
        "c041_pub_06",  # Bounded Nat modulo (PROOF)
        "c041_pub_07",  # Fin 6 composite zero divisors (REFUTATION)
        "c041_pub_08",  # False list equality (REFUTATION)
        "c041_pub_09",  # Klein 4-group associativity (PROOF)
        "c041_pub_10",  # Cyclic 4 identity (PROOF)
    ]
    cases = []
    for pid in panel_ids:
        cpath = ex_dir / f"{pid}.json"
        with open(cpath, "r", encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def parse_cli(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Symbol Game Multi-Method Experiment")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--model", action="append")
    selection.add_argument("--tier", action="append", choices=["8b", "70b", "500b", "1000b", "frontier"])
    parser.add_argument(
        "--method",
        choices=["M1_LOGITS", "M2_ATTENTION", "M3_RETRACTION", "M4_SCRATCHPAD", "M5_RUNES"],
        action="append", required=True,
    )
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

    model_tier_map = {
        "8b": "meta-llama/llama-3.1-8b-instruct",
        "70b": "meta-llama/llama-3.3-70b-instruct",
        "500b": "deepseek/deepseek-chat",
        "1000b": "openai/gpt-4o",
        "frontier": "openai/gpt-4o",
    }
    args.tiers = [(tier, model_tier_map[tier]) for tier in args.tier] if args.tier else [(model, model) for model in args.model]
    return args


def main(argv=None) -> None:
    from c041_lean4_finite_lemma_proofs.reference_solver.run_symbol_game_matrix import run_full_matrix

    args = parse_cli(argv)
    run_full_matrix(args.tiers, args.method, max_tokens=args.max_output_tokens,
        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
        max_provider_calls=args.max_provider_calls, case_limit=args.case_limit, env_file=args.env_file)


if __name__ == "__main__":
    main()
