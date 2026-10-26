"""Record the original finite consistency lesson through one accounted PFP run."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4

from omega_engine_pfp.infrastructure.estimated_gateway import create_accounted_openrouter_gateway
from omega_engine_pfp.infrastructure.pilot_matrix import complete_pilot_turn, validate_pilot_gateways
from omega_engine_pfp.infrastructure.synthesis_matrix import prepare_output_dir
from omega_engine_pfp.tests.demo_004.a_mechanism.consistency_teaching import conditions, tasks
from omega_engine_pfp.tests.demo_004.a_mechanism.consistency_teaching.host import host_verdict
from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1

DEFAULT_MODEL = "openai/gpt-4o-mini"
TEACHING_ITEMS = 3
TEACHING_RELATIONS = 3
TEACHING_SEED = 1


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def record_one(model: str = DEFAULT_MODEL, seed: int = TEACHING_SEED,
    style: str = "direct", n_items: int = TEACHING_ITEMS,
    n_relations: int = TEACHING_RELATIONS, *, gateway=None,
    output_path: Path | str | None = None, max_output_tokens: int = 2048) -> dict:
    """Keep the original task/conditions; the shared gateway owns cost and custody."""
    if type(model) is not str or not model.strip():
        raise ValueError("MODEL_REQUIRED")
    if output_path is not None and Path(output_path).exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    validate_pilot_gateways({model: gateway}, [model], max_tokens=max_output_tokens)
    if style not in ("direct", "cot"):
        raise ValueError(f"unknown judge style {style!r}")
    inst = tasks.generate_instance(n_items=n_items, n_relations=n_relations,
        poisoned=True, seed=seed)
    verdict = host_verdict(inst)
    if verdict != "CONTRADICTION" or not inst.poisoned:
        raise RuntimeError(f"teaching instance seed={seed} was not a planted contradiction")
    prompt = conditions._format_problem(inst) + (conditions._COT if style == "cot" else conditions._DIRECT)
    out = None
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        out = path.open("x", encoding="utf-8", newline="\n")
    try:
        exchange = complete_pilot_turn(gateway,
            CandidateRequest(user=prompt, decoding=DecodingParamsV1(temperature=None)),
            model=model, task_id="consistency-teaching", attempt_id="teaching:" + uuid4().hex,
            max_tokens=max_output_tokens)
        raw = exchange["content"] if exchange["ok"] else None
        model_verdict = conditions.parse_verdict(raw) if raw is not None else "UNKNOWN"
        receipt = {
            "schema_version": 2, "benchmark": "track_a_video_1_naked_prompt",
            "authority_effect": "None",
            "config": {"provider": "openrouter", "model": model,
                "backend": f"openrouter:{model}:{style}", "style": style,
                "n_items": n_items, "n_relations": n_relations, "seed": seed,
                "max_output_tokens": max_output_tokens, "temperature": None},
            "instance": {"items": inst.items, "edges": [[u, v, w] for u, v, w in inst.edges],
                "claims": [[u, v, d] for (u, v), d in inst.claims.items()],
                "poisoned": True, "ground_truth": inst.ground_truth},
            "host_verdict": verdict, "model_verdict": model_verdict, "model_raw": raw,
            "prompt": prompt, "laundered": model_verdict == "CONSISTENT",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pfp_exchange": exchange, "stop": exchange["stop"] or not exchange["ok"],
            "stop_reason": exchange["error"], "evidence_grade": "RECORDED_REPLY_WITH_FINITE_HOST_COMPARISON"
                if exchange["ok"] else "TYPED_REFUSAL",
        }
        receipt = json.loads(json.dumps(receipt, ensure_ascii=True, allow_nan=False))
        receipt["self_digest"] = _digest(receipt)
        if out is not None:
            json.dump(receipt, out, indent=2, ensure_ascii=True, allow_nan=False)
            out.write("\n")
        return receipt
    finally:
        if out is not None:
            out.close()


def record_main(argv=None) -> int:
    """Original easy/direct and hard/cot instances share one explicit allowance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--max-provider-calls", required=True, type=int)
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument("--max-cases", type=int, choices=(1, 2), default=2)
    parser.add_argument("--env-file", type=Path)
    policy = parser.add_mutually_exclusive_group(required=True)
    policy.add_argument("--max-cost-microusd", type=int)
    policy.add_argument("--max-estimated-cost-microusd", type=int)
    args = parser.parse_args(argv)
    if args.output_dir.exists():
        parser.error("OUTPUT_ALREADY_EXISTS")
    if not args.model.strip() or not 1 <= args.max_provider_calls <= 32 or args.max_output_tokens < 1:
        parser.error("explicit model and positive bounded call/output limits required")
    ceiling = args.max_cost_microusd if args.max_cost_microusd is not None else args.max_estimated_cost_microusd
    if ceiling < 1 or (args.max_estimated_cost_microusd is not None
            and (ceiling > 50000 or args.max_output_tokens > 3000)):
        parser.error("invalid financial policy")
    output = prepare_output_dir(args.output_dir)
    run_id = "consistency-teaching:" + uuid4().hex
    objective = hashlib.sha256(b"Original easy/direct and hard/cot finite consistency teaching").hexdigest()
    gateway = create_accounted_openrouter_gateway(args.model, args.max_output_tokens,
        env_file=args.env_file, max_cost_microusd=args.max_cost_microusd,
        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
        max_calls=args.max_provider_calls, accounting_path=output / "accounting.sqlite3",
        run_id=run_id, objective_sha256=objective)
    rows = []
    for name, style, items, relations in (("easy", "direct", 3, 3), ("hard", "cot", 8, 14))[:args.max_cases]:
        row = record_one(args.model, 1, style, items, relations, gateway=gateway,
            output_path=output / (name + ".json"), max_output_tokens=args.max_output_tokens)
        rows.append(row)
        print(f"{name}: host={row['host_verdict']} model={row['model_verdict']} stop={row['stop_reason']}")
        if row["stop"]:
            break
    return 2 if rows[-1]["stop"] else 0
