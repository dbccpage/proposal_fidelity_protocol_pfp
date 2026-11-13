# WF54: Five-seam mechanism showcase

**Status:** runnable offline (needs `torch` for the open-weight seam); no live campaign. **Kind:** experiment design. **Builds on:** [WF12](../wf12_mechanism_control_arms/README.md), [WF24](../wf24_pinned_token_operational_scratchpad/README.md), [WF27](../wf27_hinted_retraction_with_a_stationary_loop_detector/README.md).

**Goal:** Show each place a host can intervene in a model call (sampling, logits and grammar, scratchpad, attention and residual stream, weights from verified receipts) and what each can and cannot certify.

**The check:** the host oracle for each seam; a model reply is evidence, never a verdict.

This folder was `benchmarks/llm_mechanisms/` until 2026-11-13; older records keep that path.

## Details

This benchmark package demonstrates and tests all five physical intervention loci of an open-weight or hosted language model call under PFP's strict sovereignty boundary (`AuthorityEffect: None`):

1. **Seam 1 — Sampling Parameters (`SamplingConfigV1`, `evaluate_sampling_seam`):**
   - Regulates `temperature`, `top_p`, `seed`, and `n_samples` under `WholeRunBudget`.
   - Collapses redundant `T=0` replicates (`N > 1` at `T=0`) via operadic trace quotienting (`quotient_workflows`).
   - Compares `greedy_first`, `majority_vote`, and `certificate_first`, showing that when a modal error has higher sample frequency than a valid witness, `majority_vote` selects the uncertified modal error (`DELIVERED_UNCERTIFIED`) while `certificate_first` selects only a draw certified by `HostOracleContext` (`HOST_CERTIFIED`) or refuses (`NO_CERTIFIED_SAMPLE`).

2. **Seam 2 — Logit & Grammar-Constrained Decoding (`LogitGrammarControllerV1`, `verify_decode_receipt_exact`):**
   - Enforces `CARRIER_MASK`, `LOGIT_BIAS` (`|bias| <= 1000`), and SHA-256-pinned finite token tries (`JSON_SCHEMA`, `GBNF`) with `DecodeControlReceipt` and `DecodeControlReceiptV2`.
   - Demonstrates the Layer-2 vs. Layer-3 boundary (Lesson `950_03_2`): Layer-2 token-trie masking eliminates syntax and wire-format refusals on Call 1 (`wire_syntax_valid = True`), but an on-grammar mathematically wrong answer still passes Layer 2 and requires Layer-3 `HostOracleContext` verification to refuse (`semantically_certified = False`).

3. **Seam 3 — Host-Controlled Scratchpad (`HostScratchSessionV1`, `detect_stationary_attractor_exact`):**
   - Implements the `C006` coboundary-repair working-memory ledger over $K_4$ ($b_1 = 3$, initial $\Phi_1 = 7$) with `AM-4` stationary attractor detection (`RepeatedCut`, `RepeatedSettledAssert`) and `Treg` circuit-breaker suspension.
   - Keeps turn prompts bounded (`last_two_turns`) compared with uncompacted chain-of-thought history, descends $\Phi_1: 7 \to 4 \to 1 \to 0$ across the 3 open cycle chords, refuses mutated vertex potentials (`POTENTIAL_COBOUNDARY_MISMATCH`), and certifies `ACCEPTED_ZERO_DEFECT`.

4. **Seam 4 — Attention Heads, KV Surgery & Residual Steering (`OpenWeightMechanismRunnerV1`, `evaluate_attention_intervention_gate`):**
   - Supports both `Llama`/`Qwen` (`model.model.layers`) and multimodal `Gemma 4` (`model.language_model.layers`) eager attention layouts via `resolve_transformer_layers`.
   - Verifies 4D carrier attention bias ($\delta = 0$ null vs. $\delta = 6$ shift), per-head scaling/ablation ($\alpha = 1$ null vs. $\alpha = 0$ ablation), clean-to-corrupted head patching, contrastive residual steering paired against an orthogonal equal-L2-norm random vector (`build_equal_norm_random_vector`), and incremental KV-cache parity (`token_exact = True`).
   - Enforces EIS Two-Signal regulation before authorizing distractor-attention masking: refuses `TWO_SIGNAL_COLLAPSE` when `observer_id = 'attention_probe'` and requires both Signal 1 ($\text{mass} > \tau$) and an independent allowlisted Host Signal 2 (`host.public_smoke`).

5. **Seam 5 — Weights / `finetune_on_antibodies` from Verified Receipt Triples (`ReceiptToWeightPipelineV1`, `LowRankWeightAdapterV1`):**
   - Extracts `VerifiedReceiptTripleV1` records directly from PFP candidate run receipts where `chosen` is certified by `HostOracleContext` (and passes `ProtectedContract` fences and `ThymusGate`) and `rejected` fails the same host oracle on the same seed.
   - Enforces zero hold-out contamination (`HOLDOUT_CONTAMINATION_REFUSAL` on prompt hashes and task IDs), PCIV lineage untaintedness (`TAINTED_LINEAGE_RECEIPT_REFUSED`), and the **witness multiplicity guard** (`ALTERNATIVE_VALID_WITNESS_NOT_REJECTED` when `rejected` also passes the host oracle).
   - Compiles deterministic SFT and DPO JSONL sealed with a `SealedCausalWitness`, fits a low-rank `LowRankWeightAdapterV1` (LoRA) with zero base-model parameter drift (`0.0`), beats an equal-Frobenius-norm random adapter control (`build_equal_norm_random_control`) on held-out prompts, and emits a `WeightAdapterReceiptV1` with `authority_effect = 'None'`.

## Reproducing the Showcase

```bash
python workflows/wf54_five_seam_mechanism_showcase/run_five_seam_showcase.py
python -m pytest pfp_core/tests/test_llm_mechanisms.py workflows/wf54_five_seam_mechanism_showcase/tests/test_five_seam_showcase.py -q
```

## Claim Hygiene Summary

1. **What it supports:** Deterministic execution, receipt verification, and paired negative-control ablation across all five LLM intervention seams in this repository's test and local open-weight micro-model setting (`USD 0.00` live API spend).
2. **What it does not support:** Claims of accuracy gains on live frontier or open-weight checkpoints without a pinned held-out live campaign, or any claim that internal model interventions replace external Layer-3 `HostOracleContext` verification.
3. **The narrowest defensible claim:** Each of the five intervention seams is executable under `AuthorityEffect: None` with exact negative controls checked by this test suite at `USD 0.00` live API spend.
4. **The next test needed:** Run `OpenWeightMechanismRunnerV1` and `ReceiptToWeightPipelineV1` on a pinned local Gemma 4 checkpoint (`google/gemma-4-9b-it` in `eager` attention mode) over the 3-family algebraic pilot and the 4-task industry replacement suite under a pre-authorized `WholeRunBudget`.
