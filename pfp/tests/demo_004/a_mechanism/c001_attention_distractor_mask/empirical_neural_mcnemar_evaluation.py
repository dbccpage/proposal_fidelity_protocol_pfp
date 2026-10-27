"""
empirical_neural_mcnemar_evaluation.py — Empirical neural model inference on real weights
with eager attention hooks and McNemar statistical significance evaluation.

Exploratory evaluation on real model weights (Qwen2.5-0.5B-Instruct).
This is not the frozen 7B run declared in pipeline.json.
Intervention arms:
- Arm A (Baseline): Symbol Game prompt with distractor spans, unmasked eager attention.
- Arm F-null (Validity Gate): Attention hook with empty mask; must reproduce Arm A token IDs 100%.
- Arm F-distractor (Treatment): Eager distractor-key attention masking when the distractor
  attention mass exceeds tau (a single-signal threshold rule, `attention_mass_masking_decision`;
  not a two-signal immune decision).
- Arm F-delete (Distractor Removal): Distractor spans deleted from prompt text.

Adheres strictly to:
- Zero-Float Law: exact Fraction arithmetic for all statistical counting, chi^2, and binomial p-values.
- Claim Hygiene Rule: includes 4-part Claim Discipline without forbidden hype verbs.
- Reverse Write Order & Pure UTF-8 encoding without BOM.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import math
import re
import time
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import torch
except ImportError:  # Statistical and parsing helpers do not require model extras.
    torch = None

from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.attention_hook import (
    HARD_KILL_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    apply_distractor_key_mask,
    attention_mass_masking_decision,
    is_masking_authorized,
    resolve_fluff_positions,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_hidden_base_set,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solver import (
    verify_certificate,
)

from adversary.domain.providers.budget import BudgetController

DEFAULT_LOCAL_SNAPSHOT: Path = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--Qwen--Qwen2.5-0.5B-Instruct"
    / "snapshots"
    / "7ae557604adf67be50417f59c2c2f167def9a775"
)
DEFAULT_MODEL_ID: str = "Qwen/Qwen2.5-0.5B-Instruct"
DEFAULT_MODEL_REVISION: str = "7ae557604adf67be50417f59c2c2f167def9a775"

# Global model cache to avoid repeated weight loading
_CACHED_MODEL: Any = None
_CACHED_TOKENIZER: Any = None
_CACHED_MODEL_SOURCE: Optional[str] = None


def get_or_load_neural_model(
    model_source: Optional[str | Path] = None,
) -> Tuple[Any, Any, str]:
    """Loads and caches the neural model and tokenizer with eager attention implementation."""
    global _CACHED_MODEL, _CACHED_TOKENIZER, _CACHED_MODEL_SOURCE

    if torch is None:
        raise RuntimeError(
            "Neural evaluation requires the optional torch and transformers packages"
        )
    from transformers import AutoModelForCausalLM, AutoTokenizer

    source_path = (
        str(model_source)
        if model_source is not None
        else (str(DEFAULT_LOCAL_SNAPSHOT) if DEFAULT_LOCAL_SNAPSHOT.is_dir() else DEFAULT_MODEL_ID)
    )

    if (
        _CACHED_MODEL is not None
        and _CACHED_TOKENIZER is not None
        and _CACHED_MODEL_SOURCE == source_path
    ):
        return _CACHED_MODEL, _CACHED_TOKENIZER, _CACHED_MODEL_SOURCE

    revision = {"revision": DEFAULT_MODEL_REVISION} if source_path == DEFAULT_MODEL_ID else {}
    tok = AutoTokenizer.from_pretrained(source_path, **revision)
    model = AutoModelForCausalLM.from_pretrained(
        source_path,
        dtype=torch.float32,
        attn_implementation="eager",
        **revision,
    )
    model.eval()

    _CACHED_MODEL = model
    _CACHED_TOKENIZER = tok
    _CACHED_MODEL_SOURCE = source_path
    return _CACHED_MODEL, _CACHED_TOKENIZER, _CACHED_MODEL_SOURCE


def compute_mcnemar_exact(b: int, c: int) -> Dict[str, Any]:
    """Computes exact McNemar test statistic and exact two-sided binomial p-value."""
    total = b + c
    if total == 0:
        return {
            "b": b,
            "c": c,
            "total_discordant": 0,
            "chi2": "0",
            "p_value": "1",
            "p_value_float": 1.0,
            "is_significant_alpha_0_05": False,
        }

    chi2_frac = Fraction((b - c) ** 2, total)
    k_min = max(b, c)
    num_tails = sum(math.comb(total, k) for k in range(k_min, total + 1))
    p_val_raw = Fraction(2 * num_tails, 2**total)
    p_val = min(Fraction(1, 1), p_val_raw)

    return {
        "b": b,
        "c": c,
        "total_discordant": total,
        "chi2": str(chi2_frac),
        "chi2_float": float(chi2_frac),
        "p_value": str(p_val),
        "p_value_float": float(p_val),
        "is_significant_alpha_0_05": bool(p_val < Fraction(5, 100)),
    }


def remove_distractor_spans(text: str, spans: Sequence[Tuple[int, int]]) -> str:
    """Removes distractor spans from text (Arm F-delete)."""
    sorted_spans = sorted(spans, key=lambda s: s[0])
    pieces: List[str] = []
    last_idx = 0
    for start, end in sorted_spans:
        if start > last_idx:
            pieces.append(text[last_idx:start])
        last_idx = max(last_idx, end)
    if last_idx < len(text):
        pieces.append(text[last_idx:])
    return "".join(pieces)


def format_chat_prompt(
    prompt_text: str,
    kind: str,
    tokenizer: Any,
) -> str:
    """Formats the Symbol Game prompt with instruction framing."""
    contracts = {
        "verdict": (
            'Return {"status":"SOLVED","kind":"verdict","answer":"CONSISTENT",'
            '"potential":{"vertex":"integer"}} with a potential for every vertex, '
            'or {"status":"SOLVED","kind":"verdict","answer":"CONTRADICTION",'
            '"cycle":["A","B","C","A"]} with a closed declared-edge cycle of nonzero signed sum.'
        ),
        "repair": (
            'Return {"status":"SOLVED","kind":"repair","edge":["u","v"],'
            '"value":"integer"} specifying exactly one declared edge replacement that makes all relations consistent.'
        ),
        "audit": (
            'Check the supplied claimed potential. Return {"status":"SOLVED","kind":"audit",'
            '"answer":"ACCEPT"}, or {"status":"SOLVED","kind":"audit","answer":"REJECT",'
            '"violated":["u","v"]} naming a relation that the claimed potential violates.'
        ),
    }
    if kind not in contracts:
        raise ValueError(f"Unsupported case kind: {kind!r}")
    user_instruction = (
        f"{prompt_text}\n\n"
        "Task: Determine the exact Symbol Game solution.\n"
        "Output ONLY a valid JSON object matching the contract, for example:\n"
        f"{contracts[kind]} Use canonical decimal integer strings.\n"
        'If unable to supply a certificate, return {"status":"UNKNOWN","refusal":"NO_CERTIFICATE"}.'
    )
    messages = [
        {
            "role": "system",
            "content": "You are an exact constraint reasoning engine. Output ONLY valid JSON.",
        },
        {"role": "user", "content": user_instruction},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def parse_neural_output(decoded_text: str, kind: str) -> Dict[str, Any]:
    """Parses model generation into a structured solution dictionary."""
    text = decoded_text.strip()

    # Decode a complete object, including nested potential dictionaries. Neither
    # prose keywords nor incomplete JSON constitute a certificate.
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, dict) and "status" in parsed:
        if parsed.get("status") == "SOLVED" and parsed.get("kind") != kind:
            return {"status": "UNKNOWN", "refusal": "WRONG_TASK_KIND"}
        return parsed

    return {"status": "UNKNOWN", "refusal": "UNPARSEABLE_OUTPUT"}


def measure_attention_on_positions(
    attentions: Sequence[torch.Tensor],
    target_positions: Sequence[int],
    layer: int = -1,
) -> float:
    """Measures mean attention mass from final query position onto target key positions."""
    if not target_positions:
        return 0.0
    if not attentions or attentions[layer] is None:
        raise ValueError("Model did not return eager attention tensors")
    # attentions[layer]: [batch, heads, seq, seq]
    last_row = attentions[layer][0].mean(0)[-1]
    valid_indices = [idx for idx in target_positions if 0 <= idx < len(last_row)]
    if not valid_indices:
        return 0.0
    return float(last_row[valid_indices].sum().item())


def tokenize_case_prompt(
    case: Dict[str, Any],
    tokenizer: Any,
) -> Tuple[Any, List[int]]:
    """Resolve distractor keys on the exact chat input used for inference."""
    prompt_text = case["prompt_text"]
    chat_prompt = format_chat_prompt(prompt_text, case["kind"], tokenizer)
    if not prompt_text or chat_prompt.count(prompt_text) != 1:
        raise ValueError("Chat template must preserve the case text exactly once")
    shift = chat_prompt.index(prompt_text)
    spans = []
    for start, end in case.get("distractor_spans", []):
        if not (0 <= start < end <= len(prompt_text)):
            raise ValueError("Distractor span lies outside the case text")
        spans.append((start + shift, end + shift))
    # A chat template already includes its special tokens. Use the same single
    # encoding for offsets and inference, and never fall back to word indices.
    inputs = tokenizer(
        chat_prompt,
        return_tensors="pt",
        return_offsets_mapping=True,
        add_special_tokens=False,
    )
    offsets = inputs.pop("offset_mapping", None)
    if offsets is None:
        raise ValueError("Neural masking requires tokenizer character offsets")
    positions = resolve_fluff_positions(chat_prompt, spans, offset_mapping=offsets)
    return inputs, positions


def run_single_neural_case(
    case: Dict[str, Any],
    model: Any,
    tokenizer: Any,
    max_new_tokens: int = 256,
) -> Dict[str, Any]:
    """Executes all four intervention arms on a single case with physical neural inference."""
    if torch is None:
        raise RuntimeError("Neural evaluation requires torch")
    if type(max_new_tokens) is not int or max_new_tokens < 1:
        raise ValueError("max_new_tokens must be a positive integer")
    kind = case["kind"]
    prompt_text = case["prompt_text"]
    distractor_spans = case.get("distractor_spans", [])

    # Format baseline prompt
    inputs_a, fluff_positions = tokenize_case_prompt(case, tokenizer)
    seq_len_a = inputs_a["input_ids"].shape[1]
    pos_ids_a = torch.arange(seq_len_a, dtype=torch.long).unsqueeze(0)

    # -----------------------------------------------------------------------
    # Arm A: Baseline (unmasked)
    # -----------------------------------------------------------------------
    with torch.no_grad():
        out_a = model.generate(
            input_ids=inputs_a["input_ids"],
            attention_mask=inputs_a["attention_mask"],
            position_ids=pos_ids_a,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
    tokens_gen_a = out_a[0][seq_len_a:].tolist()
    decoded_a = tokenizer.decode(tokens_gen_a, skip_special_tokens=True)
    sol_a = parse_neural_output(decoded_a, kind)
    valid_a, _msg_a = verify_certificate(case, sol_a)

    # -----------------------------------------------------------------------
    # Arm F-null: Validity Gate (mask with empty fluff, must match A 100%)
    # -----------------------------------------------------------------------
    mask_f_null, pos_ids_null = apply_distractor_key_mask(
        model=model,
        attention_mask=inputs_a["attention_mask"],
        fluff_positions=[],
        danger_gate_decision=None,
        return_position_ids=True,
        attn_implementation="eager",
    )
    with torch.no_grad():
        out_f_null = model.generate(
            input_ids=inputs_a["input_ids"],
            attention_mask=mask_f_null,
            position_ids=pos_ids_null,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
    tokens_gen_f_null = out_f_null[0][seq_len_a:].tolist()
    f_null_matches_a = tokens_gen_f_null == tokens_gen_a

    # -----------------------------------------------------------------------
    # Arm F-distractor: Treatment (eager attention masked on distractor keys)
    # -----------------------------------------------------------------------
    fluff_mass_unmasked = 0.0
    if fluff_positions:
        with torch.no_grad():
            fwd_unmasked = model(
                input_ids=inputs_a["input_ids"],
                attention_mask=inputs_a["attention_mask"],
                position_ids=pos_ids_a,
                output_attentions=True,
            )
            fluff_mass_unmasked = measure_attention_on_positions(
                fwd_unmasked.attentions, fluff_positions
            )
    # The gate consumes the measured signal, converted exactly from the finite
    # floating point observation. This does not make neural arithmetic exact.
    danger_mass = Fraction.from_float(fluff_mass_unmasked)
    danger_decision = attention_mass_masking_decision(fluff_positions, danger_mass)
    is_auth = is_masking_authorized(danger_decision)

    mask_f_dist, pos_ids_dist = apply_distractor_key_mask(
        model=model,
        attention_mask=inputs_a["attention_mask"],
        fluff_positions=fluff_positions,
        danger_gate_decision=danger_decision,
        return_position_ids=True,
        attn_implementation="eager",
    )

    # Measure attention mass before and after masking
    fluff_mass_masked = 0.0
    if fluff_positions:
        with torch.no_grad():
            fwd_masked = model(
                input_ids=inputs_a["input_ids"],
                attention_mask=mask_f_dist,
                position_ids=pos_ids_dist,
                output_attentions=True,
            )
            fluff_mass_masked = measure_attention_on_positions(
                fwd_masked.attentions, fluff_positions
            )

    with torch.no_grad():
        out_f_dist = model.generate(
            input_ids=inputs_a["input_ids"],
            attention_mask=mask_f_dist,
            position_ids=pos_ids_dist,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
    tokens_gen_f_dist = out_f_dist[0][seq_len_a:].tolist()
    decoded_f_dist = tokenizer.decode(tokens_gen_f_dist, skip_special_tokens=True)
    sol_f_dist = parse_neural_output(decoded_f_dist, kind)
    valid_f_dist, _msg_dist = verify_certificate(case, sol_f_dist)

    # -----------------------------------------------------------------------
    # Arm F-delete: Distractor Removal Baseline (spans deleted from prompt)
    # -----------------------------------------------------------------------
    cleaned_prompt_text = remove_distractor_spans(prompt_text, distractor_spans)
    chat_prompt_del = format_chat_prompt(cleaned_prompt_text, kind, tokenizer)
    inputs_del = tokenizer(chat_prompt_del, return_tensors="pt", add_special_tokens=False)
    seq_len_del = inputs_del["input_ids"].shape[1]
    pos_ids_del = torch.arange(seq_len_del, dtype=torch.long).unsqueeze(0)

    with torch.no_grad():
        out_del = model.generate(
            input_ids=inputs_del["input_ids"],
            attention_mask=inputs_del["attention_mask"],
            position_ids=pos_ids_del,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
    tokens_gen_del = out_del[0][seq_len_del:].tolist()
    decoded_del = tokenizer.decode(tokens_gen_del, skip_special_tokens=True)
    sol_del = parse_neural_output(decoded_del, kind)
    valid_del, _msg_del = verify_certificate(case, sol_del)

    return {
        "case_id": case["case_id"],
        "kind": kind,
        "fluff_positions_count": len(fluff_positions),
        "fluff_positions": fluff_positions,
        "input_token_ids": inputs_a["input_ids"][0].tolist(),
        "deleted_input_token_ids": inputs_del["input_ids"][0].tolist(),
        "is_masking_authorized": is_auth,
        "danger_gate_attention_mass": str(danger_mass),
        "fluff_mass_unmasked": fluff_mass_unmasked,
        "fluff_mass_masked": fluff_mass_masked,
        "f_null_matches_a": f_null_matches_a,
        "masking_verified": bool(is_auth and fluff_mass_unmasked > 0 and fluff_mass_masked <= 1e-7),
        "arm_a": {
            "output_tokens": tokens_gen_a,
            "decoded_text": decoded_a,
            "parsed_solution": sol_a,
            "is_valid": valid_a,
            "verification_message": _msg_a,
        },
        "arm_f_null": {"output_tokens": tokens_gen_f_null},
        "arm_f_distractor": {
            "output_tokens": tokens_gen_f_dist,
            "decoded_text": decoded_f_dist,
            "parsed_solution": sol_f_dist,
            "is_valid": valid_f_dist,
            "verification_message": _msg_dist,
        },
        "arm_f_delete": {
            "output_tokens": tokens_gen_del,
            "decoded_text": decoded_del,
            "parsed_solution": sol_del,
            "is_valid": valid_del,
            "verification_message": _msg_del,
        },
    }


def run_empirical_neural_mcnemar_evaluation(
    n_cases: int = 10,
    base_seed: int = 2026,
    model_source: Optional[str | Path] = None,
    max_new_tokens: int = 256,
) -> Dict[str, Any]:
    """Runs physical neural inference across intervention arms on real model weights
    and executes exact McNemar statistical significance testing."""
    # Pre-dispatch budget verification (Local PyTorch CPU bills $0.00)
    budget_ctrl = BudgetController(limit_microusd=HARD_KILL_CEILING_MICROUSD)
    assert budget_ctrl.spent_microusd <= TARGET_BUDGET_MICROUSD

    hidden_cases = generate_hidden_base_set(base_seed=base_seed)
    if type(n_cases) is not int or not 1 <= n_cases <= len(hidden_cases):
        raise ValueError(f"n_cases must be between 1 and {len(hidden_cases)}")
    if type(max_new_tokens) is not int or max_new_tokens < 1:
        raise ValueError("max_new_tokens must be a positive integer")
    eval_cases = hidden_cases[:n_cases]

    t_start = time.time()
    model, tokenizer, model_id = get_or_load_neural_model(model_source)

    traces: List[Dict[str, Any]] = []
    f_null_all_matched = True

    # Contingency table counters: F-distractor vs Arm A
    a_f_vs_a = 0
    b_f_vs_a = 0
    c_f_vs_a = 0
    d_f_vs_a = 0

    # Contingency table counters: F-distractor vs F-delete
    a_f_vs_del = 0
    b_f_vs_del = 0
    c_f_vs_del = 0
    d_f_vs_del = 0

    pass_count_a = 0
    pass_count_f_dist = 0
    pass_count_del = 0

    for idx, case in enumerate(eval_cases):
        trace = run_single_neural_case(case, model, tokenizer, max_new_tokens=max_new_tokens)
        traces.append(trace)

        if not trace["f_null_matches_a"]:
            f_null_all_matched = False

        v_a = trace["arm_a"]["is_valid"]
        v_f = trace["arm_f_distractor"]["is_valid"]
        v_del = trace["arm_f_delete"]["is_valid"]

        if v_a:
            pass_count_a += 1
        if v_f:
            pass_count_f_dist += 1
        if v_del:
            pass_count_del += 1

        # Paired counts: F-distractor vs Arm A
        if v_a and v_f:
            a_f_vs_a += 1
        elif (not v_a) and v_f:
            b_f_vs_a += 1
        elif v_a and (not v_f):
            c_f_vs_a += 1
        else:
            d_f_vs_a += 1

        # Paired counts: F-distractor vs F-delete
        if v_del and v_f:
            a_f_vs_del += 1
        elif (not v_del) and v_f:
            b_f_vs_del += 1
        elif v_del and (not v_f):
            c_f_vs_del += 1
        else:
            d_f_vs_del += 1

    total_eval = len(eval_cases)
    elapsed_sec = time.time() - t_start

    mcnemar_f_vs_a = compute_mcnemar_exact(b=b_f_vs_a, c=c_f_vs_a)
    mcnemar_f_vs_del = compute_mcnemar_exact(b=b_f_vs_del, c=c_f_vs_del)
    authorized_count = sum(trace["is_masking_authorized"] for trace in traces)
    verified_mask_count = sum(trace["masking_verified"] for trace in traces)
    mechanism_verified = authorized_count > 0 and verified_mask_count == authorized_count
    usable_for_inference = f_null_all_matched and mechanism_verified
    for comparison in (mcnemar_f_vs_a, mcnemar_f_vs_del):
        comparison["usable_for_inference"] = usable_for_inference
        if not usable_for_inference:
            comparison["is_significant_alpha_0_05"] = None

    supports = [
        f"Records model outputs and certificate scores across {total_eval} cases on {model_id}.",
        "Computes exact rational contingency tables and two-sided binomial p-values from those scores.",
    ]
    if f_null_all_matched:
        supports.append("F-null reproduces Arm A output token IDs for every evaluated case.")
    else:
        supports.append(
            "F-null differs from Arm A; the paired comparison is invalid for inference."
        )
    if not mechanism_verified:
        supports.append(
            "Masking efficacy inference is withheld: no intervention was authorized or an authorized mask failed verification."
        )
    supports.append(
        f"The measured danger signal authorized {authorized_count} interventions; "
        f"{verified_mask_count} have measured post-mask attention mass at or below 1e-7."
    )

    acc_a = Fraction(pass_count_a, total_eval)
    acc_f = Fraction(pass_count_f_dist, total_eval)
    acc_del = Fraction(pass_count_del, total_eval)

    report: Dict[str, Any] = {
        "benchmark": "C001: Distractor-Key Attention Masking at Task Level",
        "evaluation_type": "PHYSICAL_NEURAL_MODEL_INFERENCE_ON_REAL_WEIGHTS",
        "benchmark_scope": "EXPLORATORY_NEURAL_PILOT",
        "matches_frozen_pipeline": False,
        "is_empirical_measurement": True,
        "is_synthetic_fixture": False,
        "model_id": model_id,
        "model_revision": getattr(getattr(model, "config", None), "_commit_hash", None),
        "device": "cpu",
        "attention_implementation": "eager",
        "sample_size": total_eval,
        "elapsed_seconds": round(elapsed_sec, 2),
        "validity_gate": {
            "f_null_reproduces_arm_a_exactly": f_null_all_matched,
            "gate_status": "PASSED" if f_null_all_matched else "FAILED",
        },
        "mechanism_measurements": {
            "gate_status": "PASSED" if mechanism_verified else "UNVERIFIED",
            "authorized_cases": authorized_count,
            "verified_mask_cases": verified_mask_count,
            "attention_mass_tolerance": 1e-7,
        },
        "traces": traces,
        "accuracy": {
            "Arm_A_baseline": str(acc_a),
            "Arm_A_baseline_float": float(acc_a),
            "F_distractor_treatment": str(acc_f),
            "F_distractor_treatment_float": float(acc_f),
            "F_delete_baseline": str(acc_del),
            "F_delete_baseline_float": float(acc_del),
        },
        "comparison_F_distractor_vs_Arm_A": {
            "table_2x2": {
                "both_pass_a": a_f_vs_a,
                "A_fail_F_pass_b": b_f_vs_a,
                "A_pass_F_fail_c": c_f_vs_a,
                "both_fail_d": d_f_vs_a,
            },
            "mcnemar": mcnemar_f_vs_a,
        },
        "comparison_F_distractor_vs_F_delete": {
            "table_2x2": {
                "both_pass_a": a_f_vs_del,
                "Delete_fail_F_pass_b": b_f_vs_del,
                "Delete_pass_F_fail_c": c_f_vs_del,
                "both_fail_d": d_f_vs_del,
            },
            "mcnemar": mcnemar_f_vs_del,
        },
        "claim_discipline": {
            "supports": supports,
            "does_not_support": [
                "Does not satisfy the frozen 7B model and tokenizer contract in pipeline.json.",
                "Does not claim that distractor masking generalizes to black-box hosted APIs that do not expose attention tensors.",
                "Does not claim that small open-weights models achieve high unassisted task-level zero-shot accuracy on complex topological constraint systems without chain-of-thought or host solvers.",
                "Does not describe toy setting findings as mathematical proofs of transformer cognition.",
            ],
            "narrowest_defensible_claim": (
                f"On {model_id}, {total_eval} case traces record neural outputs and certificate scores. "
                f"F-null validity gate: {'PASSED' if f_null_all_matched else 'FAILED'}. "
                f"Attention suppression was measured in {verified_mask_count} authorized cases. "
                f"Paired comparison: {'eligible for inference' if usable_for_inference else 'inference withheld'}."
            ),
            "next_test_needed": (
                "Execute the full 200 hidden-case sweep on accelerated GPU hardware (CUDA) and test structured chain-of-thought decoding."
            ),
        },
    }

    # Persist report and sample traces if run directory exists
    run_dir = Path("_ic/darpa/adversary/runs/c001_mechanism_pilot")
    if run_dir.is_dir():
        rep_path = run_dir / "empirical_neural_mcnemar_report.json"
        rep_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

        traces_path = run_dir / "neural_sample_traces.jsonl"
        with traces_path.open("w", encoding="utf-8") as f:
            for tr in traces:
                f.write(json.dumps(tr, sort_keys=True) + "\n")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Empirical Neural Model Inference on Real Weights with McNemar Evaluation"
    )
    parser.add_argument(
        "--cases", type=int, default=5, help="Number of hidden base cases to evaluate (default: 5)"
    )
    args = parser.parse_args()

    print(f"=== EMPIRICAL NEURAL MODEL INFERENCE ON REAL WEIGHTS ({args.cases} CASICS) ===")
    rep = run_empirical_neural_mcnemar_evaluation(n_cases=args.cases)
    print(f"Model ID: {rep['model_id']}")
    print(f"Validity Gate (F-null == Arm A): {rep['validity_gate']['gate_status']}")
    print(f"Elapsed: {rep['elapsed_seconds']}s")
    print(f"Arm A Accuracy: {rep['accuracy']['Arm_A_baseline']}")
    print(f"F-distractor Accuracy: {rep['accuracy']['F_distractor_treatment']}")
    print(f"F-delete Accuracy: {rep['accuracy']['F_delete_baseline']}")
    print("\n--- F-distractor vs Arm A McNemar ---")
    print(
        f"Discordant pairs: b={rep['comparison_F_distractor_vs_Arm_A']['table_2x2']['A_fail_F_pass_b']}, c={rep['comparison_F_distractor_vs_Arm_A']['table_2x2']['A_pass_F_fail_c']}"
    )
    print(f"Exact Chi^2: {rep['comparison_F_distractor_vs_Arm_A']['mcnemar']['chi2']}")
    print(f"Exact p-value: {rep['comparison_F_distractor_vs_Arm_A']['mcnemar']['p_value']}")
    print(
        f"Significant (alpha=0.05): {rep['comparison_F_distractor_vs_Arm_A']['mcnemar']['is_significant_alpha_0_05']}"
    )
    print("\nNarrowest Defensible Claim:")
    print(rep["claim_discipline"]["narrowest_defensible_claim"])
