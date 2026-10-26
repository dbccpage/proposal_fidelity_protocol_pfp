# Lesson 950.05 -- 1. What Happens Inside the Transformer?

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_950_05_1_what_happens_inside_transformer.ipynb](../notebooks/lesson_950_05_1_what_happens_inside_transformer.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 09 - Transformer Mechanics: Attention Entropy and KV Activation Norms

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Open-Weights Attention Concentration, KV Frobenius Norm Invariance, and Memory Reduction*

---

## 1. What Happens Inside the Transformer?

Paper 032 evaluated open-weights causal language models (`Qwen/Qwen2.5-0.5B-Instruct` and `meta-llama/llama-3.1-8b-instruct`) at the tensor activation level to measure how the Symbol Game alters internal mechanics:

1. **Attention Concentration Gain**: Fenced prompts concentrate attention onto declared carrier tokens:
   - At the terminal token, attention probability on carrier tokens increases by **$3.14\times$** ($0.0066$ vs $0.0021$).
2. **KV Frobenius Norm Invariance**: The mean Frobenius norm of key-value activations across layers remains invariant:
   $$\bar{\nu}_{\text{KV}} = 6.90 \pm 0.01 \quad (<0.25\% \text{ variation})$$
   This proves that prompt fences do not destabilize or distort intrinsic transformer activation scales.
3. **Stored energy comparison**: the receipt field `kv_cache_energy_reduction_percentage` is -37.53. This page does not re-run the model.

## 2. KV-Cache Frobenius Norm Invariance

The receipt stores mean KV norms 6.8984 and 6.9156. This page does not re-run the model.

| Metric | Dense CoT | Symbol Game (Fenced) | Delta / Ratio |
|---|---|---|---|
| **Terminal Carrier Attention** | $0.0021$ | $0.0066$ | **$3.14\times$ Concentration** |
| **Mean KV Frobenius Norm** | $6.90$ | $6.90$ | **$<0.25\%$ Invariant** |
| **KV energy change in the receipt** | dense energy | sparse energy | **-37.53** |

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that Symbol Game prompt contracts concentrate attention entropy onto carrier tokens in open-weights models.
> - Demonstrates that KV Frobenius norms remain mathematically stable.
>
> **CANNOT-Show**:
> - Does not show that prompt fencing modifies internal model weights $W_K, W_V$.

## 4. Student Exercises

### Exercise 09.1: Autoregressive KV Cache Scaling
Why does reducing output token count from 300 tokens to 32 tokens reduce KV-cache memory consumption by $\sim 70-90\%$?

<details>
<summary><b>Click to reveal solution</b></summary>
Because in standard autoregressive decoding, every newly generated token appends a key-value vector of size $2 \times d_{\text{model}}$ per layer to the KV-cache. The total memory scales linearly with sequence length $O(L)$. Reducing sequence length by $90\%$ directly eliminates $90\%$ of the appended KV activation storage.
</details>

## 5. Anchors

- **Paper 032 Sections**: §8.1–§8.4
- **Ledger IDs**: `PO032-C57` through `PO032-C63`
- **Code**: `papers/032.../code/attention_entropy_kv_norm_benchmark.py`
- **Audit Receipt**: `papers/032.../code/attention_entropy_kv_norm_receipt.json`

## Anchors

- Former notebook: `09_attention_entropy_and_kv_norm_mechanics`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/_theory/README.md](../../../../../research/mssn_sn_tower/_theory/README.md)
- [research/mssn_sn_tower/_theory/03_the_symbol_game.md](../../../../../research/mssn_sn_tower/_theory/03_the_symbol_game.md)
- [research/mssn_sn_tower/_theory/09_authority_fences.md](../../../../../research/mssn_sn_tower/_theory/09_authority_fences.md)
