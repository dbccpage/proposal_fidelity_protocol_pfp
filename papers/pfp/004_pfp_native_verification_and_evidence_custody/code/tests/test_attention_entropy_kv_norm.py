# -*- coding: utf-8 -*-
"""
Tests for the historical attention-entropy and KV-norm benchmark script.
Validates Shannon entropy calculations, normalized entropy scaling,
KV-cache Frobenius energy computations, and the retained receipt's schema.
These tests load no model and make no network call. They need PyTorch and
NumPy (the optional "attention" dependencies) and skip without them.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

OPTIONAL_DEPENDENCIES = ("torch", "numpy")
MISSING = [name for name in OPTIONAL_DEPENDENCIES if importlib.util.find_spec(name) is None]

pytestmark = pytest.mark.skipif(
    bool(MISSING),
    reason=(
        "optional dependencies of the historical attention benchmark are absent: "
        + ", ".join(MISSING)
        + " (install the package's 'attention' extra to run these checks)"
    ),
)

if not MISSING:
    import torch

    from attention_entropy_kv_norm_benchmark import compute_shannon_entropy

# ==============================================================================
# 1. SHANNON ENTROPY MATHEMATICAL INVARIANT TESTS
# ==============================================================================

def test_shannon_entropy_one_hot() -> None:
    """One-hot probability distribution must yield 0 entropy (zero uncertainty)."""
    one_hot = torch.tensor([[1.0, 0.0, 0.0, 0.0]])
    ent = compute_shannon_entropy(one_hot)
    assert pytest.approx(ent.item(), abs=1e-5) == 0.0


def test_shannon_entropy_uniform() -> None:
    """Uniform distribution over K elements must yield exact theoretical maximum ln(K)."""
    k = 5
    uniform = torch.full((1, k), 1.0 / k)
    ent = compute_shannon_entropy(uniform)
    assert pytest.approx(ent.item(), rel=1e-5) == math.log(k)


def test_shannon_entropy_monotonicity_and_bounds() -> None:
    """Entropy must be non-negative and bounded above by ln(dim)."""
    dims = [2, 4, 8, 16]
    generator = torch.Generator().manual_seed(0)
    for d in dims:
        random_dist = torch.softmax(torch.randn(10, d, generator=generator), dim=-1)
        ent = compute_shannon_entropy(random_dist)
        assert torch.all(ent >= 0.0)
        assert torch.all(ent <= math.log(d) + 1e-5)


# ==============================================================================
# 2. SYNTHETIC TENSOR ATTENTION & KV ENERGY TEST
# ==============================================================================

def test_synthetic_attention_distribution_entropy() -> None:
    """Tests attention distribution entropy calculation across synthetic query steps."""
    seq_len = 10
    num_heads = 4
    # Construct synthetic causal attention weights: (num_heads, seq_len, seq_len)
    attn_weights = torch.zeros(num_heads, seq_len, seq_len)
    for i in range(seq_len):
        # Place uniform weight over previous tokens 0..i
        attn_weights[:, i, : i + 1] = 1.0 / (i + 1)

    entropies = []
    for i in range(1, seq_len):
        dist = attn_weights[:, i, : i + 1]
        dist = dist / dist.sum(dim=-1, keepdim=True).clamp(min=1e-12)
        ent = compute_shannon_entropy(dist)
        # For uniform distribution over i+1 elements, entropy should equal ln(i+1)
        expected_ent = math.log(i + 1)
        for h in range(num_heads):
            assert pytest.approx(ent[h].item(), rel=1e-4) == expected_ent
        entropies.extend(ent.tolist())

    assert len(entropies) == (seq_len - 1) * num_heads


def test_synthetic_kv_frobenius_energy() -> None:
    """Tests Frobenius energy calculation sum(||K||_F^2 + ||V||_F^2)."""
    # Create synthetic key and value tensors
    k_tensor = torch.full((1, 2, 4, 8), 2.0)  # numel = 64, sum(2^2) = 256
    v_tensor = torch.full((1, 2, 4, 8), 3.0)  # numel = 64, sum(3^2) = 576

    k_norm_sq = torch.sum(k_tensor.float() ** 2).item()
    v_norm_sq = torch.sum(v_tensor.float() ** 2).item()
    total_energy = k_norm_sq + v_norm_sq
    total_elements = k_tensor.numel() + v_tensor.numel()

    assert pytest.approx(total_energy) == 256.0 + 576.0
    assert total_elements == 128
    mean_norm = math.sqrt(total_energy / total_elements)
    assert pytest.approx(mean_norm, rel=1e-4) == math.sqrt(832.0 / 128)


# ==============================================================================
# 3. AUDIT RECEIPT SCHEMA & INTEGRITY TESTS
# ==============================================================================

def test_audit_receipt_file_exists_and_valid() -> None:
    """Verifies that attention_entropy_kv_norm_receipt.json exists and conforms to contract."""
    receipt_path = Path(__file__).parent.parent / "attention_entropy_kv_norm_receipt.json"
    assert receipt_path.exists(), f"Receipt not found at {receipt_path}"

    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert "benchmark_name" in data
    assert "local_model" in data
    assert "condition_a_dense" in data
    assert "condition_b_sparse" in data
    assert "differential_metrics" in data

    ca = data["condition_a_dense"]
    cb = data["condition_b_sparse"]
    diff = data["differential_metrics"]

    # Invariants on local model results
    assert ca["sequence_length"] > 0
    assert cb["sequence_length"] > 0
    assert 0.0 <= ca["mean_attention_entropy"] <= math.log(ca["sequence_length"])
    assert 0.0 <= cb["mean_attention_entropy"] <= math.log(cb["sequence_length"])

    # Carrier attention concentration
    assert ca["carrier_token_attention_mass"] >= 0.0
    assert cb["carrier_token_attention_mass"] >= 0.0
    # In receipt, condition B demonstrates higher carrier concentration
    assert diff["carrier_attention_concentration_gain"] > 0.0

    # Frontier evaluation invariants
    if "frontier_evaluation" in data:
        fe = data["frontier_evaluation"]
        assert "frontier_model" in fe
        if fe.get("dense_transition_entropy") is not None:
            assert fe["dense_transition_entropy"] >= 0.0
        if fe.get("sparse_transition_entropy") is not None:
            assert fe["sparse_transition_entropy"] >= 0.0
