# Lesson 950.03 -- 2. Why Layer 2 Logit Masking is Leaky

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_950_03_2_why_layer_2_logit_masking_is_leaky.ipynb](../notebooks/lesson_950_03_2_why_layer_2_logit_masking_is_leaky.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Why Layer 2 Logit Masking is Leaky

Even if logit biases are applied during autoregressive generation:
1. **Finite Temperature Tails**: If finite additive logit biases $\Delta l$ are used instead of hard $-\infty$, softmax produces non-zero probability tails:
   $$P(\text{fluff}) = \frac{e^{l_i + \Delta l}}{\sum_j e^{l_j + \Delta l}} > 0$$
2. **Local Greed vs. Global Consistency**: Next-token masking cannot guarantee that a sequence of locally valid tokens does not produce a global cycle or mathematical contradiction.
3. **The Solution**: Layer 3 Verification. The host acts as an independent execution sandbox that accepts or refuses the candidate move.

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that an external Layer 3 host replay oracle reliably intercepts invalid operator proposals that pass Layer 2 generation.
> - Demonstrates that prompt fences restrict token support without altering underlying model weights.
>
> **CANNOT-Show**:
> - Does not show that Layer 2 logit masking can completely replace host-side verification.
> - Does not claim that fine-tuning or prompt engineering permanently alters transformer parameters at inference.

## 4. Student Exercises

### Exercise 03.1: Three-Layer Failure Modes
Suppose an LLM says: *"I have modified my internal weights to guarantee that I will never hallucinate again."* Which layer of sovereignty has been breached by this statement?

<details>
<summary><b>Click to reveal solution</b></summary>
Layer 1 (Train Time). At inference time, model weights $W$ are immutable constants stored in memory. Prompts enter strictly as inputs to row lookups; the autoregressive forward pass cannot alter model weights. The model's claim is an ungrounded hallucination.
</details>

## 5. Anchors

- **Paper 032 Sections**: §1.1–§1.3
- **Ledger IDs**: `PO032-C15` through `PO032-C21`
- **Code**: `notebook_lib/llm_client.py`
- **Audit Receipt**: `papers/032.../code/attention_entropy_kv_norm_receipt.json`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `03_three_layer_sovereignty`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/_theory/README.md](../../../../../research/mssn_sn_tower/_theory/README.md)
- [research/mssn_sn_tower/_theory/03_the_symbol_game.md](../../../../../research/mssn_sn_tower/_theory/03_the_symbol_game.md)
- [research/mssn_sn_tower/_theory/09_authority_fences.md](../../../../../research/mssn_sn_tower/_theory/09_authority_fences.md)
