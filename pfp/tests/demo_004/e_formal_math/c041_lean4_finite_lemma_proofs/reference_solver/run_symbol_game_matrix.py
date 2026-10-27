# AuthorityEffect: None.
"""
Multi-Method & Multi-Tier Matrix Sweeper for C041 Symbol Game Research.

Sweeps:
- Methods: M1 (Logits), M2 (Attention), M3 (Retraction with antibodies), M4 (Scratchpad), M5 (Runes)
- Model Tiers:
    8B: meta-llama/llama-3.1-8b-instruct
    70B: meta-llama/llama-3.3-70b-instruct
    500B: deepseek/deepseek-chat
    Frontier: openai/gpt-4o

Writes one run folder under <intelligence root>/_ic/darpa/symbol_game/matrix_runs/c041/
holding each arm's record, c041_matrix_comparison.json and c041_matrix_report.md. The report
states counts only; it draws no conclusions. Exploratory; not an SG-CP v1 evaluation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.infrastructure.formal_matrix import (  # noqa: E402
    new_run_nonce,
    run_folder,
)
from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.symbol_game_experiment import (  # noqa: E402
    load_calibrated_10_lemma_panel,
    parse_cli,
    run_benchmark_panel,
)

TIERS = [
    ("8b", "meta-llama/llama-3.1-8b-instruct"),
    ("70b", "meta-llama/llama-3.3-70b-instruct"),
    ("500b", "deepseek/deepseek-chat"),
    ("frontier", "openai/gpt-4o"),
]

METHODS = [
    "M1_LOGITS",
    "M2_ATTENTION",
    "M3_RETRACTION",
    "M4_SCRATCHPAD",
    "M5_RUNES",
]


def run_full_matrix(tiers=None, methods=None, *, gateways=None, max_tokens=512,
    max_estimated_cost_microusd=None, max_provider_calls=None, case_limit=None,
    env_file=None, cases=None) -> List[Dict[str, Any]]:
    from pfp.infrastructure.pilot_matrix import _scope, make_pilot_gateways, validate_pilot_gateways

    active_tiers = TIERS if tiers is None else tiers
    active_methods = METHODS if methods is None else methods
    cases = load_calibrated_10_lemma_panel() if cases is None else cases
    if (not active_tiers or not active_methods or set(active_methods) - set(METHODS)
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
    folder = run_folder("c041", nonce)
    if gateways is None:
        gateways = make_pilot_gateways(model_ids, max_output_tokens=max_tokens,
            max_estimated_cost_microusd=max_estimated_cost_microusd, max_calls=max_provider_calls,
            accounting_path=folder / "budget.sqlite3", env_file=env_file)

    results = []
    print(
        f"Executing Symbol Game matrix: {len(active_tiers)} tiers x {len(active_methods)} methods on {len(cases)} lemmas."
    )

    stopped = False
    for tier_index, (tier_name, model_id) in enumerate(active_tiers):
        for method_index, method in enumerate(active_methods):
            try:
                res = run_benchmark_panel(model=model_id, method=method, cases=cases, folder=folder,
                    gateway=gateways[model_id], max_tokens=max_tokens, task_id=f"c041:{nonce}",
                    attempt_id=f"{nonce}:tier-{tier_index}:method-{method_index}")
                res["tier"] = tier_name
                results.append(res)
                if res["stop"]:
                    stopped = True
                    break
            except Exception as e:  # recorded, never silently turned into a result
                results.append(
                    {
                        "tier": tier_name,
                        "model": model_id,
                        "method": method,
                        "error": f"{type(e).__name__}: {e}",
                    }
                )
                print(f"ERROR executing ({tier_name}, {method}): {e}")
                stopped = True
                break
        if stopped:
            break

    report_lines = [
        "# C041 model matrix run",
        "",
        "Exploratory; not an SG-CP v1 evaluation. Per-arm records (prompts, raw replies, outcomes,",
        "`lean --version`) are in this folder. Refusals are counted separately and never as verified.",
        "",
        "| Tier | Model | Method | Verified / answered | Outcomes | Billed cost ($) |",
        "| :--- | :--- | :--- | :---: | :--- | ---: |",
    ]
    for r in results:
        if "error" in r:
            report_lines.append(
                f"| {r['tier']} | `{r['model']}` | {r['method']} | n/a | ERROR: {r['error']} | n/a |"
            )
            continue
        cost = "unknown" if r["total_cost_usd"] is None else f"{r['total_cost_usd']:.5f}"
        report_lines.append(
            f"| {r.get('tier', 'N/A')} | `{r['model']}` | {r['method']} | {r['passed_cases']}/{r['answered_cases']} | "
            f"{json.dumps(r['outcome_counts'], sort_keys=True)} | {cost} |"
        )
    report_lines += ["", "This script reports counts only and draws no conclusions from them."]
    (folder / "c041_matrix_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8", newline="\n"
    )
    (folder / "c041_matrix_comparison.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"\nWrote matrix report and data to {folder}")
    return results


def main(argv=None) -> List[Dict[str, Any]]:
    args = parse_cli(argv)
    return run_full_matrix(args.tiers, args.method, max_tokens=args.max_output_tokens,
        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
        max_provider_calls=args.max_provider_calls, case_limit=args.case_limit, env_file=args.env_file)


if __name__ == "__main__":
    main()
