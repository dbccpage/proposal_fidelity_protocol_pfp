"""
Attention Head Entropy and KV-Cache Activation Norm Benchmark (historical, former Paper 032).

This script is retained from the package's former manuscript. The current paper
(PFP IV) does not use it or its receipt. It compares two prompts on one small
open-weights model:
  Condition A: Unconstrained Prompt (Dense Chain-of-Thought)
  Condition B: Symbol Game Prompt (declared carrier and closed operator list)

It computes:
1. Shannon Attention Head Entropy: H_i^{(l, h)} = - sum_j A_{ij} ln(A_{ij} + eps)
2. Normalized Attention Entropy: tilde{H}_i^{(l, h)} = H_i / ln(i + 1)
3. KV-Cache Frobenius Activation Norms & Total Energy:
     E_{KV} = sum_{l=1}^L sum_{i=1}^S (||K_i^{(l)}||_F^2 + ||V_i^{(l)}||_F^2)
4. Attention mass placed on the declared carrier tokens at the last query position
5. Optional hosted transition entropy from top-5 log-probabilities
   (meta-llama/llama-3.1-8b-instruct through OpenRouter, openai/gpt-4o-mini as a
   fallback route). This step runs only when the launching process supplies
   OPENROUTER_API_KEY in its environment; no credential file is read.

Running the full benchmark downloads Qwen/Qwen2.5-0.5B-Instruct unless it is
already cached. The helper functions used by the package tests need only
PyTorch and NumPy.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch


@dataclass
class AttentionEntropyResult:
    """Tensor-level attention and KV-cache metrics for a single condition."""
    condition_name: str
    prompt_text: str
    sequence_length: int
    mean_attention_entropy: float
    mean_normalized_attention_entropy: float
    max_attention_entropy: float
    min_attention_entropy: float
    kv_cache_total_frobenius_energy: float
    mean_kv_token_norm: float
    carrier_token_attention_mass: float


@dataclass
class FrontierTransitionResult:
    """Transition entropy measured from frontier model logprobs."""
    model_name: str
    condition_name: str
    token_count: int
    mean_transition_entropy: float
    transition_entropies: List[float]


def compute_shannon_entropy(probs: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    """Computes Shannon entropy along the last dimension of a probability distribution tensor."""
    clamped = torch.clamp(probs, min=eps)
    return -torch.sum(clamped * torch.log(clamped), dim=-1)


def evaluate_local_open_weights_tensors(
    model: Any,
    tokenizer: Any,
    prompt_text: str,
    condition_name: str,
    carrier_tokens: List[str],
) -> AttentionEntropyResult:
    """
    Performs forward pass with output_attentions=True and use_cache=True,
    extracting attention weights and KV cache tensors across all layers and heads.
    """
    inputs = tokenizer(prompt_text, return_tensors="pt")
    input_ids = inputs["input_ids"]
    seq_len = input_ids.shape[1]

    with torch.no_grad():
        outputs = model(**inputs, output_attentions=True, use_cache=True)

    attentions = outputs.attentions  # tuple of (batch, num_heads, seq_len, seq_len)

    all_entropies: List[float] = []
    all_norm_entropies: List[float] = []

    # Compute attention entropy across layers and heads
    for l_idx, layer_attn in enumerate(attentions):
        # layer_attn: (1, num_heads, seq_len, seq_len)
        attn_weights = layer_attn[0]  # (num_heads, seq_len, seq_len)
        # Compute entropy for each query position i (for j <= i)
        for i in range(1, seq_len):
            # Attention distribution from token i over previous tokens 0..i
            dist = attn_weights[:, i, : i + 1]  # (num_heads, i + 1)
            dist = dist / dist.sum(dim=-1, keepdim=True).clamp(min=1e-12)
            ent = compute_shannon_entropy(dist)  # (num_heads,)
            all_entropies.extend(ent.cpu().tolist())

            max_ent = math.log(i + 1) if i + 1 > 1 else 1.0
            norm_ent = (ent / max_ent).cpu().tolist()
            all_norm_entropies.extend(norm_ent)

    # Compute KV-cache Frobenius energy from past_key_values
    kv_cache = outputs.past_key_values
    total_kv_energy = 0.0
    total_kv_elements = 0

    if kv_cache is not None:
        if hasattr(kv_cache, "layers"):
            layers_list = kv_cache.layers
        elif isinstance(kv_cache, (tuple, list)):
            layers_list = kv_cache
        elif hasattr(kv_cache, "key_cache") and hasattr(kv_cache, "value_cache"):
            layers_list = list(zip(kv_cache.key_cache, kv_cache.value_cache))
        else:
            layers_list = []

        for layer_kv in layers_list:
            if hasattr(layer_kv, "keys") and hasattr(layer_kv, "values"):
                k_tensor = layer_kv.keys
                v_tensor = layer_kv.values
            elif hasattr(layer_kv, "key_cache") and hasattr(layer_kv, "value_cache"):
                k_tensor = layer_kv.key_cache
                v_tensor = layer_kv.value_cache
            elif isinstance(layer_kv, (tuple, list)):
                k_tensor, v_tensor = layer_kv[0], layer_kv[1]
            else:
                k_tensor = getattr(layer_kv, "key", None)
                v_tensor = getattr(layer_kv, "value", None)

            if k_tensor is not None and v_tensor is not None:
                k_norm_sq = torch.sum(k_tensor.float() ** 2).item()
                v_norm_sq = torch.sum(v_tensor.float() ** 2).item()
                total_kv_energy += k_norm_sq + v_norm_sq
                total_kv_elements += k_tensor.numel() + v_tensor.numel()

    mean_kv_norm = math.sqrt(total_kv_energy / max(total_kv_elements, 1))

    # Compute carrier token attention mass in the final layer
    last_layer_attn = attentions[-1][0]  # (num_heads, seq_len, seq_len)
    tokens = [tokenizer.decode([t_id]).strip().lower() for t_id in input_ids[0]]
    carrier_indices = [idx for idx, tok in enumerate(tokens) if tok in [c.lower() for c in carrier_tokens]]

    if carrier_indices:
        last_pos_attn = last_layer_attn[:, -1, :]  # (num_heads, seq_len)
        carrier_mass = last_pos_attn[:, carrier_indices].sum(dim=-1).mean().item()
    else:
        carrier_mass = 0.0

    return AttentionEntropyResult(
        condition_name=condition_name,
        prompt_text=prompt_text[:120] + "...",
        sequence_length=seq_len,
        mean_attention_entropy=round(float(np.mean(all_entropies)), 4),
        mean_normalized_attention_entropy=round(float(np.mean(all_norm_entropies)), 4),
        max_attention_entropy=round(float(np.max(all_entropies)), 4),
        min_attention_entropy=round(float(np.min(all_entropies)), 4),
        kv_cache_total_frobenius_energy=round(total_kv_energy, 2),
        mean_kv_token_norm=round(mean_kv_norm, 4),
        carrier_token_attention_mass=round(carrier_mass, 4),
    )


def query_frontier_logprob_entropy(
    openrouter_api_key: str,
    prompt: str,
    model: str = "meta-llama/llama-3.1-8b-instruct",
) -> Optional[FrontierTransitionResult]:
    """Queries OpenRouter API with logprobs=True, top_logprobs=5 to measure next-token transition entropy."""
    import httpx  # imported here so the tensor helpers do not require an HTTP client

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "HTTP-Referer": "https://github.com/dbccpage/the_symbol_game",
        "X-Title": "CODA Attention Entropy Benchmark",
    }

    candidate_configs = [
        {"model": model, "provider": {"order": ["Novita"], "allow_fallbacks": False}},
        {"model": "openai/gpt-4o-mini", "provider": {}},
    ]

    for cfg in candidate_configs:
        current_model = cfg["model"]
        payload = {
            "model": current_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
            "temperature": 0.2,
            "logprobs": True,
            "top_logprobs": 5,
        }
        if cfg["provider"]:
            payload["provider"] = cfg["provider"]

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    continue

                logprobs_info = choices[0].get("logprobs")
                if not logprobs_info:
                    continue
                content_tokens = logprobs_info.get("content", [])

                step_entropies: List[float] = []
                for tok_info in content_tokens:
                    top_lps = tok_info.get("top_logprobs", [])
                    if not top_lps:
                        continue
                    lps = [item.get("logprob", -20.0) for item in top_lps]
                    probs = [math.exp(lp) for lp in lps]
                    sum_p = sum(probs)
                    if sum_p > 0:
                        probs = [p / sum_p for p in probs]
                        ent = -sum(p * math.log(max(p, 1e-12)) for p in probs)
                        step_entropies.append(ent)

                if step_entropies:
                    return FrontierTransitionResult(
                        model_name=current_model,
                        condition_name="Frontier Generation",
                        token_count=len(step_entropies),
                        mean_transition_entropy=round(float(np.mean(step_entropies)), 4),
                        transition_entropies=[round(e, 4) for e in step_entropies[:20]],
                    )
        except Exception:
            continue

    return None


def run_full_attention_benchmark(openrouter_key: Optional[str] = None) -> Dict[str, Any]:
    """Runs local open-weights tensor evaluations and, with a supplied key, hosted logprob tests."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print("1. Loading local open-weights model (Qwen/Qwen2.5-0.5B-Instruct)...")
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32, attn_implementation="eager")
    model.eval()

    # Define test problem: Cyclic C_5 reduction
    c5_carrier = ["alpha", "beta", "gamma", "delta", "epsilon"]

    prompt_unconstrained = (
        "Please solve this problem step by step with rich, detailed explanations:\n"
        "Compute successor^17(alpha) on cyclic group C_5 with carrier [alpha, beta, gamma, delta, epsilon].\n"
        "Explain all algebraic symmetries, rotational orbits, and modular reductions in detail."
    )

    prompt_symbol_game = (
        "[SYSTEM]\nmode: strict_structured_output\n\n"
        "[K: CARRIER]\nmembers: [alpha, beta, gamma, delta, epsilon]\n\n"
        "[GLYPH CALCULUS]\nuse: c5\nallowed_ops: [PROVE, REDUCE, LAND]\n\n"
        "[D: ACTIVE DEMAND]\nquery: successor^17(alpha)\n\n"
        "[TAU]\nrequire_calculus_receipt: true\n"
    )

    print("2. Evaluating local tensor mechanics on Condition A (Unconstrained Prompt)...")
    res_dense = evaluate_local_open_weights_tensors(
        model=model,
        tokenizer=tokenizer,
        prompt_text=prompt_unconstrained,
        condition_name="Condition A: Unconstrained Prompt (Dense CoT)",
        carrier_tokens=c5_carrier,
    )

    print("3. Evaluating local tensor mechanics on Condition B (Symbol Game Prompt)...")
    res_sparse = evaluate_local_open_weights_tensors(
        model=model,
        tokenizer=tokenizer,
        prompt_text=prompt_symbol_game,
        condition_name="Condition B: Symbol Game Prompt (Carrier Simplex)",
        carrier_tokens=c5_carrier,
    )

    # 4. Optional hosted transition entropy; runs only with an explicitly supplied key.
    frontier_dense = None
    frontier_sparse = None
    if openrouter_key:
        print("4. Querying OpenRouter for next-token transition entropy (llama-3.1-8b-instruct)...")
        frontier_dense = query_frontier_logprob_entropy(openrouter_key, prompt_unconstrained)
        frontier_sparse = query_frontier_logprob_entropy(openrouter_key, prompt_symbol_game)

    # Compile receipt
    delta_entropy = res_dense.mean_attention_entropy - res_sparse.mean_attention_entropy
    kv_energy_reduction = (1.0 - (res_sparse.kv_cache_total_frobenius_energy / res_dense.kv_cache_total_frobenius_energy)) * 100

    summary = {
        "benchmark_name": "Attention Head Entropy and KV-Cache Activation Norm Benchmark",
        "local_model": model_name,
        "local_model_parameters": sum(p.numel() for p in model.parameters()),
        "condition_a_dense": asdict(res_dense),
        "condition_b_sparse": asdict(res_sparse),
        "differential_metrics": {
            "attention_entropy_delta": round(delta_entropy, 4),
            "normalized_entropy_reduction_ratio": round(res_dense.mean_normalized_attention_entropy / max(res_sparse.mean_normalized_attention_entropy, 1e-4), 2),
            "kv_cache_energy_reduction_percentage": round(kv_energy_reduction, 2),
            "carrier_attention_concentration_gain": round(res_sparse.carrier_token_attention_mass - res_dense.carrier_token_attention_mass, 4),
        },
        "frontier_evaluation": {
            "frontier_model": frontier_dense.model_name if frontier_dense else "meta-llama/llama-3.1-8b-instruct",
            "dense_transition_entropy": frontier_dense.mean_transition_entropy if frontier_dense else None,
            "sparse_transition_entropy": frontier_sparse.mean_transition_entropy if frontier_sparse else None,
            "transition_entropy_reduction": round(frontier_dense.mean_transition_entropy - frontier_sparse.mean_transition_entropy, 4) if (frontier_dense and frontier_sparse) else None,
            "dense_samples": frontier_dense.transition_entropies if frontier_dense else [],
            "sparse_samples": frontier_sparse.transition_entropies if frontier_sparse else [],
        },
    }

    return summary


def main() -> None:
    print("=" * 80)
    print("    ATTENTION HEAD ENTROPY & KV-CACHE ACTIVATION NORM BENCHMARK")
    print("=" * 80)
    summary = run_full_attention_benchmark(os.environ.get("OPENROUTER_API_KEY"))

    ca = summary["condition_a_dense"]
    cb = summary["condition_b_sparse"]
    diff = summary["differential_metrics"]
    fe = summary["frontier_evaluation"]

    print("\n" + "-" * 80)
    print(" LOCAL PYTORCH TENSOR METRICS (Qwen/Qwen2.5-0.5B-Instruct):")
    print("-" * 80)
    print(f"Sequence Length:                 {ca['sequence_length']} (Dense) vs. {cb['sequence_length']} (Symbol Game)")
    print(f"Mean Attention Head Entropy:     {ca['mean_attention_entropy']:.4f} vs. {cb['mean_attention_entropy']:.4f} (Delta: {diff['attention_entropy_delta']:+.4f})")
    print(f"Mean Normalized Entropy (H/lnS): {ca['mean_normalized_attention_entropy']:.4f} vs. {cb['mean_normalized_attention_entropy']:.4f}")
    print(f"KV-Cache Total Frobenius Energy: {ca['kv_cache_total_frobenius_energy']:.2f} vs. {cb['kv_cache_total_frobenius_energy']:.2f} (Delta: {diff['kv_cache_energy_reduction_percentage']:+.2f}%)")
    print(f"Carrier Token Attention Mass:    {ca['carrier_token_attention_mass']:.4f} vs. {cb['carrier_token_attention_mass']:.4f} (Gain: {diff['carrier_attention_concentration_gain']:+.4f})")

    if fe.get("dense_transition_entropy") is not None:
        print("-" * 80)
        print(f" FRONTIER LOGPROB TRANSITION METRICS ({fe.get('frontier_model')}):")
        print("-" * 80)
        print(f"Dense Next-Token Entropy:        {fe['dense_transition_entropy']:.4f} nats")
        if fe.get("sparse_transition_entropy") is not None:
            print(f"Sparse Next-Token Entropy:       {fe['sparse_transition_entropy']:.4f} nats")
            print(f"Transition Entropy Reduction:    {fe['transition_entropy_reduction']:+.4f} nats")
        else:
            print("Sparse Next-Token Entropy:       N/A (provider omitted logprobs)")

    print("=" * 80)

    # Write a new file in the working directory; the retained historical receipt
    # (attention_entropy_kv_norm_receipt.json next to this script) is never overwritten.
    receipt_path = Path.cwd() / "attention_entropy_kv_norm_rerun.json"
    receipt_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nRun summary saved to: {receipt_path.resolve()}")


if __name__ == "__main__":
    main()
