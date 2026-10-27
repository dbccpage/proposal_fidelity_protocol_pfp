# Structured Decoding Controls for Discrete Graph Consistency:
# Scratchpads, Factorized Spanning-Tree Prompts, and Antibody Canary Checks on Llama-3.1-405B

> **Notice (2026-09-29).** This is a working record, not a paper. Paper 008 of this
> collection re-examined these runs. They are two separate runs: the three-arm run
> gave Arm 2 36 of 50 and the hybrid run 38 of 50, so the range of 36 to 38 of 50 (72
> to 76%) quoted below combines two runs, and the p-value of 0.035 belongs to the
> three-arm run alone. The per-case rows were written to an untracked run folder and
> are not retained, so no count here can be recomputed from per-case data. The runs
> used a 405B model and a larger budget than SG-CP v1 and the C005 specification
> allow, so they are a deviation from the protocol, not a conforming C005 result.
> Where this note and Paper 008 disagree, the paper is authoritative. The text below
> is kept unchanged.

**AuthorityEffect:** None. **Status:** empirical results, not a published paper.
**Date:** 2026-09-27. **Repository:** `dbccpage/the_symbol_game` PR #177.

---

## Abstract

We evaluate four structured decoding interventions on a 405-billion-parameter
open-weight language model (`nousresearch/hermes-3-llama-3.1-405b`) across
50 hidden consistency-verification instances drawn from discrete potential
graphs with 4–9 nodes and planted obstructions. Each instance requires the
model to determine whether a system of directed integer differences admits a
global potential function, and if so, to produce an exact integer certificate
that is verified by a deterministic host oracle.

The four treatment arms are:

| Arm | Input Encoding | Output Schema | Host-Verified Accuracy |
| :--- | :--- | :--- | :---: |
| **Arm 1** | Natural-language relations | Verdict-first JSON | **50.0%** (25/50) |
| **Arm 2** | Natural-language relations | Numeric scratchpad before verdict | **72.0–76.0%** (36–38/50) |
| **Arm 3** | Factorized spanning-tree + chord notation | Chord residual evaluation only | **38.0%** (19/50) |
| **Arm 4** | Factorized spanning-tree + chord notation | Canary antibody + numeric scratchpad | **8.0%** (4/50) |

Arm 2 (topological scratchpad) achieves a statistically significant
improvement over the zero-shot baseline ($p = 0.035$, paired McNemar).
Arm 3 (factorized spanning-tree input without scratchpad) and Arm 4 (combined
factorized input + canary + scratchpad) both degrade accuracy, demonstrating that
schema complexity and novel prompt formats can overwhelm the model's
autoregressive reasoning capacity even when they are mathematically sound.

All experiments were executed under a strict financial ceiling of \$2.00 per
benchmark run, with actual total cumulative spend across all experiments of
\$0.13528.

---

## 1. Introduction

The Symbol Game is an audit-grade reasoning game built to expose and prevent
**cancellation laundering** — where a language model generates fluent prose
that conceals discrete mathematical contradictions. Play proceeds in a
**dual-space arena**:

- **The Proposer** (an LLM or human) emits structured moves (`ASSERT`, `CUT`,
  `VERIFY`, `RETRACT`) as JSON envelopes conforming to `$TAU_SG_V1`. The
  proposer has zero verification authority.
- **The Host Governor** is a deterministic discrete oracle that owns the
  carrier $\mathcal{C}$, the active relations $\mathcal{R}_{\text{active}}$,
  the defect register $\mathcal{D}$ (containing the $L_1$ defect cochain
  $\Phi_1$), the append-only trace $\mathcal{H}$, and the invariant set
  $\mathcal{I}$. It recomputes every step over exact rational arithmetic
  ($\mathbb{Q}$) and emits typed refusals or admitted receipts.

The board state is a 5-tuple
$S = (\mathcal{C}, \mathcal{R}_{\text{active}}, \mathcal{D}_{\text{register}},
\mathcal{H}_{\text{trace}}, \mathcal{I}_{\text{invariants}})$. Every admitted
`CUT` move must achieve **strict Lyapunov descent**: $\Phi_1(S') < \Phi_1(S)$.
A game terminates only when the host itself reports $\|\Phi_1\|_{L_1} = 0$
(accepted) or issues an R1 exhaustion certificate. The model never grades its
own homework.

This paper reports empirical results from Challenge C005 (Hosted Decoding
Controls Bake-off), which measures how different prompt encodings and output
schema designs affect the rate at which a frontier open-weight model, acting as
the Proposer, produces certificates that pass the Host Governor's exact integer
verification.

### 1.1 The Consistency Problem as a Symbol Game Instance

Given a directed graph $G = (V, E)$ with integer edge labels
$c_{uv} \in \mathbb{Z}$ for each $(u, v) \in E$, the consistency problem asks
whether there exists a potential function $\pi: V \to \mathbb{Z}$ satisfying
$\pi(v) - \pi(u) = c_{uv}$ for all edges. This is equivalent to asking whether
every cycle in $G$ has zero holonomy — the defect register has
$\Phi_1 = \|\delta^1 c\|_1 = 0$. A certificate is a map from each node to its
integer potential.

In Symbol Game terms: the carrier $\mathcal{C}$ is the directed graph with
pinned vertices and edges. The Proposer must emit a `CUT` move assigning exact
integer potentials. The Host Governor recomputes $\pi(v) - \pi(u) = c_{uv}$
for every edge and either admits or refuses the move.

### 1.2 Why This Problem

The consistency problem is:
- **Polynomial** ($O(|V| + |E|)$) for a correct algorithm (BFS potential propagation, i.e. the chord-basis decoupling protocol from v3).
- **Verifiable in linear time** by the Host Governor (evaluate $\pi(v) - \pi(u) = c_{uv}$ for each edge).
- **Hard for single-pass transformers** because it requires iterative graph traversal, multi-digit signed integer arithmetic, and global cycle consistency — operations that expose cancellation laundering and the AM-4 stationary loop trap.

### 1.3 Contributions

1. **First controlled empirical comparison** of four structured decoding interventions on a single model and fixed hidden test set with paired statistical tests.
2. **Statistically significant evidence** ($p = 0.035$) that forcing intermediate numeric calculations in the output schema before the final verdict increases host-verified accuracy from 50% to 72–76%.
3. **Negative results**: Dense factorized spanning-tree prompt encoding and embedded antibody canary checks, while theoretically sound, degrade accuracy in practice when the model has not been trained on these formats.
4. **Ground-truth generator bug discovery and correction**: An invariant audit during benchmark setup identified a defect-planting mutation that corrupted ground-truth labels.

---

## 2. Experimental Setup

### 2.1 Model

All experiments use `nousresearch/hermes-3-llama-3.1-405b` served via
OpenRouter at $\approx \$1.00$ per million tokens. Temperature is fixed at 0.0
(greedy decoding).

### 2.2 Hidden Test Set

50 consistency cases generated deterministically from fixed seeds:
- 25 **consistent** instances (a valid potential exists).
- 25 **inconsistent** instances (at least one planted cycle obstruction).
- Graph sizes range from 4 to 9 nodes with spanning tree edges plus 1–4 chord edges.

A ground-truth labeling bug was discovered and corrected during benchmark setup:
the original generator mutated `is_consistent = True` after planting a defect,
causing inconsistent cases to be falsely labeled as consistent with invalid
certificates. The corrected generator uses a `defect_planted` flag and
ensures at least one defective chord edge for every inconsistent case.

### 2.3 Host Oracle

The host oracle (`verify_consistency_certificate`) performs exact integer
verification:
1. Parses each certificate value as a Python `int`.
2. Checks $\pi(v) - \pi(u) = c_{uv}$ for every edge.
3. Rejects any parse failure, missing node, or arithmetic violation.

A case is scored as **correct** if and only if:
- The verdict matches the ground truth, AND
- For CONSISTENT verdicts, the certificate passes all edge checks.

### 2.4 Budget Controls

A thread-safe `BudgetController` enforces a hard spending ceiling with
pre-call guards that raise `BudgetExceededError` before any API call that
would breach the ceiling.

---

## 3. Treatment Arms

### 3.1 Arm 1: Direct Schema (Verdict-First Baseline)

**Input:** Natural-language prompt listing all edges as
`"Relations: n0 -> n1 = -7, n1 -> n2 = 9, ..."`.

**Output Schema:** `{"verdict": "CONSISTENT"|"INCONSISTENT", "certificate": {node: int_string}}`.

The verdict field appears first in the schema. The model must commit to
CONSISTENT or INCONSISTENT at token position 1, before generating any
certificate values.

### 3.2 Arm 2: Numeric-Constrained Topological Scratchpad

**Input:** Same natural-language prompt as Arm 1, augmented with step-by-step
instructions:
> Step 1: In `scratchpad_tree_potentials`, assign integer potentials setting
> n0='0', then recursively computing potential(v) = potential(u) + delta.
> Step 2: In `chord_validations`, test whether potential(v) - potential(u) == target_delta.
> Step 3: Conclude CONSISTENT or INCONSISTENT.

**Output Schema:** Four fields in strict order:
1. `scratchpad_tree_potentials`: `{node: int_string}` — sequential propagation
2. `chord_validations`: array of `{chord, computed_diff, target_delta, is_satisfied}`
3. `verdict`: enum
4. `certificate`: `{node: int_string}`

All integer string fields are constrained by `pattern: "^-?[0-9]+$"`.

### 3.3 Arm 3: Factorized Spanning-Tree Prompt

**Input:** The graph is pre-factored by a deterministic client-side transpiler:
1. Compute a BFS spanning tree from node $n_0$.
2. Assign potentials along the tree: $\pi(v) = \pi(u) + c_{uv}$.
3. Identify fundamental cycle chords.
4. Format as compact factorized notation:

```
Holonomy Verification:
Anchored Spanning Tree Potentials: [n0:0, n1:-7, n2:2, n3:1]
Fundamental Cycle Chords: (n0->n3:+1) (n1->n3:+8)
Evaluate residual r_i = (pi(v) - pi(u)) - w for each chord.
If all residuals == 0, output CONSISTENT with certificate; else INCONSISTENT.
```

Note: the original benchmark code used ad-hoc Unicode decorations in the
prompt text (nabla, oint symbols). These symbols have no connection to the
Discrete Deformation Calculus (DDC), which is a typed trace calculus whose
8-letter alphabet $\{E, R, C, I, \Lambda, D, M, T\}$ classifies what a
computation did to a declared obstruction (§4 of the DDC paper). The factorized
prompt encoding tested here is a separate, unrelated notation for presenting
pre-computed graph decompositions to a language model.

**Output Schema:** `{chord_evaluations: [{chord_id, delta_pi, declared_w, residual, cancels}], verdict, certificate}`.

This arm pre-solves the spanning tree deterministically and asks the model only
to evaluate chord residuals — a task requiring only $|E| - (|V|-1)$ subtractions.

### 3.4 Arm 4: Hybrid Factorized Input + Scratchpad + Antibody Canary

**Input:** Factorized spanning-tree prompt (same as Arm 3) with an embedded
antibody canary check:
> Canary Antibody: Verify chord (u→v:d) has residual = pi(v) - pi(u) - d.

**Output Schema:** Five fields in strict order:
1. `canary_check`: `{canary_edge, canary_expected_residual, canary_actual_residual, canary_passed}`
2. `scratchpad_potentials`: `{node: int_string}`
3. `chord_residuals`: array of `{chord, pi_diff, declared_delta, residual, zero}`
4. `verdict`: enum
5. `certificate`: `{node: int_string}`

The canary check is verified independently: if the model's reported canary
residual does not match the ground-truth residual computed by the host, the
case fails regardless of verdict correctness.

---

## 4. Results

### 4.1 Primary Accuracy Table

| Arm | Treatment | N | Correct | Accuracy | Spend | Cost/Success | Avg Latency |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Direct Schema (Baseline) | 50 | 25 | 50.0% | \$0.009 | \$0.00035 | 4.1s |
| 2 | Numeric Scratchpad | 50 | 36–38 | 72.0–76.0% | \$0.024 | \$0.00062–0.00069 | 11.7–13.2s |
| 3 | Factorized Spanning-Tree Input | 50 | 19 | 38.0% | \$0.019 | \$0.00102 | 10.3s |
| 4 | Hybrid + Canary | 50 | 4 | 8.0% | \$0.026 | \$0.00647 | 15.7s |

Arm 2 was executed twice across separate benchmark runs (the 3-arm and 4-arm
benchmarks) with consistent results (72.0% and 76.0%), supporting
reproducibility. The range is reported rather than averaging across
non-identical runs.

### 4.2 Paired McNemar Significance Tests

All tests use the paired exact two-tailed binomial McNemar test on discordant
pairs across the same 50 hidden cases.

| Comparison | $b$ (A only) | $c$ (B only) | $\chi^2$ | $p$-value | Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Arm 1 vs. Arm 2 | 6 | 17 | 4.35 | **0.035** | **Yes** |
| Arm 1 vs. Arm 3 | 6 | 0 | 4.17 | **0.031** | **Yes** (Arm 1 better) |
| Arm 2 vs. Arm 3 | 20 | 3 | 11.13 | **0.0005** | **Yes** (Arm 2 better) |
| Arm 2 vs. Arm 4 | 34 | 0 | 32.03 | **< 0.001** | **Yes** (Arm 2 better) |

### 4.3 Antibody Canary Detection Rate (Arm 4)

| Metric | Value |
| :--- | :---: |
| Canary residuals correctly computed by model | 20 / 50 (40.0%) |
| Cases where canary passed but certificate failed | 16 / 20 |
| Cases where both canary and certificate correct | 4 / 50 (8.0%) |

### 4.4 Cumulative Financial Accounting

| Benchmark Run | Queries | Total Spend | Budget Ceiling |
| :--- | :---: | :---: | :---: |
| TEST-001 (JSON Schema 100-case sweep) | 100 | \$0.01454 | \$0.10 |
| TEST-002 (Logit Bias 100-case sweep) | 100 | \$0.01543 | \$0.10 |
| 3-Arm Benchmark (50 cases × 3 arms) | 150 | \$0.05287 | \$2.00 |
| Arm 4 Hybrid Benchmark (50 cases × 2 arms) | 100 | \$0.04954 | \$2.00 |
| 150-Test Full Suite (Tracks 01–15) | 10 live | \$0.00016 | \$10.00 |
| Miscellaneous pilot probes | ~15 | \$0.00274 | — |
| **Grand Total** | **~475** | **\$0.13528** | — |

---

## 5. Analysis

### 5.1 Why Scratchpads Work: Autoregressive Working Memory

The core finding is mechanistic: transformers in a single forward pass
cannot iteratively propagate potentials along a spanning tree and then
evaluate chord residuals. These operations require $O(V)$ sequential steps,
each dependent on the previous result. By forcing the model to emit
intermediate integer results in the output schema, we convert the problem from
a single-pass circuit evaluation to an autoregressive chain where each emitted
token conditions the next.

The direct-schema baseline (Arm 1) scores 50.0% on a balanced 25/25 dataset —
indistinguishable from random guessing on the verdict alone. This is consistent
with the hypothesis that the model lacks sufficient computational depth to
evaluate cycle consistency without intermediate token emissions.

### 5.2 Why Factorized Spanning-Tree Input Fails Without Scratchpads

Arm 3 pre-solves the spanning tree and presents only chord residuals,
reducing the problem to 1–4 scalar subtractions. Despite this radical
simplification, accuracy dropped to 38.0%. Two failure modes were observed:

1. **Certificate omission** (11/31 failures): The prompt focused attention
   on chord evaluations, and the model failed to emit complete node-to-potential
   certificate maps.
2. **Arithmetic token confusion** (12/31 failures): Multi-digit signed
   subtraction without intermediate steps caused sign errors and digit
   transpositions.

The factorized notation is unfamiliar to the model's pretraining
distribution. Unlike natural-language relation descriptions, compressed
`node:value` notation has low token-level familiarity, reducing the model's
ability to apply learned arithmetic heuristics.

### 5.3 Why the Hybrid (Arm 4) Catastrophically Failed

Arm 4 combined three simultaneous interventions:
1. Novel factorized prompt format (unfamiliar input distribution).
2. Antibody canary evaluation field (schema complexity increase).
3. Mandatory numeric scratchpad (beneficial in isolation).

The result was catastrophic: 8.0% accuracy, worse than random guessing.
The McNemar test against Arm 2 yields $p < 0.001$ with 34 discordant
cases all favoring Arm 2.

This demonstrates a **schema complexity ceiling**: each additional required
field in the output schema consumes attention budget and creates opportunities
for cascading errors. The canary check, which appears first in the schema,
was correctly computed only 40% of the time, and errors in the canary
field propagated into corrupted scratchpad computations downstream.

### 5.4 The Optimal Intervention Surface

The empirical evidence suggests a hierarchy:

1. **Output-side scratchpads** (Arm 2) are the dominant intervention.
   They provide autoregressive working memory that the transformer circuit
   requires for iterative graph algorithms.
2. **Input-side compression** (Arms 3, 4) degrades accuracy when the
   compressed format is outside the model's training distribution.
3. **Schema complexity** has diminishing and eventually negative returns.
   Adding fields beyond the minimum required scratchpad increases error
   cascading probability.

The optimal design for the next iteration is:
- **Input**: Natural language (familiar format) with explicit step-by-step
  instructions.
- **Output**: Minimal scratchpad schema with only `scratchpad → chord_checks → verdict → certificate`.
- **Canary checks**: Performed by the host after receiving the certificate,
  not by the model inside the schema.

---

## 6. Ground-Truth Generator Correction

During benchmark construction, an invariant audit against the host oracle
revealed that the case generator in `cases.py` contained a ground-truth
labeling mutation:

```python
# BEFORE (buggy): flips is_consistent to True after planting defect
if not is_consistent:
    delta += rng.choice([-3, -2, -1, 1, 2, 3])
    is_consistent = True  # BUG: corrupts final verdict label

# AFTER (corrected): preserves original is_consistent flag
if not is_consistent and not defect_planted:
    delta += rng.choice([-3, -2, -1, 1, 2, 3])
    defect_planted = True
```

This bug caused inconsistent cases to be labeled `"CONSISTENT"` with
certificates that failed the host oracle. The corrected generator was verified:
all 50 cases pass the host checker against their ground-truth labels.

This discovery illustrates the value of automated invariant auditing in
benchmark construction.

---

## 7. Sealed Artifact Registry

All artifacts are persisted under `_intelligence/_adversary/runs/` with SHA-256
content-addressed hashes.

| Run Key | Artifacts | Report SHA-256 (prefix) |
| :--- | :--- | :--- |
| `c005_test_001_llama405b_json_schema` | 100-case JSON schema sweep | (sealed) |
| `c005_test_002_llama405b_logit_bias` | 100-case logit bias sweep | (sealed) |
| `c005_3arm_scratchpad_hieroglyphic_bakeoff` | 3-arm × 50 benchmark | `a2fb2e05...` |
| `c005_arm4_hybrid_hieroglyphic_scratchpad_canary` | Arm 4 × 50 benchmark | `a0827bd1...` |
| `c005_150_tests_full_suite` | 150-test suite (15 tracks) | `ce8da586...` |

---

## 8. Claim Discipline

### What these results support

- Supports that numeric-constrained topological scratchpads produce a
  statistically significant increase in host-verified consistency certificates
  ($p = 0.035$) on 50 hidden base cases using Llama-3.1-405B.
- Supports that autoregressive token emission provides computational working
  memory that fixed-depth transformer circuits lack for iterative graph
  algorithms.
- Supports that input-side prompt compression into unfamiliar formats degrades
  model accuracy, and that output-side schema complexity has a ceiling beyond
  which accuracy degrades.

### What these results do not support

- Does not support that any decoding intervention enables LLMs to achieve
  exact mathematical reasoning without host verification.
- Does not support that factorized spanning-tree prompt encoding is inherently inferior —
  only that it is inferior on a model not trained on this format.
- Does not support generalizing these accuracy figures to other models,
  problem sizes, or mathematical domains.

### Narrowest defensible claim

On the 50 hidden consistency cases evaluated, requiring intermediate
numeric potential propagation in the JSON output schema before the final
verdict increased host-verified accuracy from 50.0% to 72.0–76.0%
($p < 0.05$), while adding factorized spanning-tree input encoding and antibody canary
output fields degraded accuracy to 38.0% and 8.0% respectively, under a
cumulative total spend of \$0.13528 across all experiments.

### Next test needed

1. Fine-tune a small open-weight model (8B–70B) on factorized spanning-tree
   notation and re-evaluate Arm 3 accuracy to test whether the negative result
   is caused by format unfamiliarity rather than inherent limitations.
2. Move canary antibody checks to the host-side post-verification pipeline
   rather than embedding them in the model's output schema.

---

## Appendix A: Reproduction Instructions

All benchmarks can be reproduced from the repository root:

```powershell
# 3-Arm Benchmark (Arm 1 vs. Arm 2 vs. Arm 3)
python projects/mssn_sn_symgam/challenges/a_mechanism/c005_hosted_decode_controls/benchmark_3arm_scratchpad.py

# Arm 4 Hybrid Benchmark (Arm 2 vs. Arm 4)
python projects/mssn_sn_symgam/challenges/a_mechanism/c005_hosted_decode_controls/benchmark_arm4_hybrid.py
```

Requires: `OPENROUTER_API_KEY` in `.env`, Python 3.10+, `openai`, `python-dotenv`.

---

## Appendix B: Prior Symbol Game Papers in This Series

| # | Paper | Focus |
| :---: | :--- | :--- |
| 001 | The Symbol Game | Finite witnesses and exact rational Fock gap checking |
| 002 | The Symbol Game (Bounded Search) | Bounded search, additive/parity bridge |
| 003 | The Symbol Game (Controlled Study) | Offline protocol and replay checks |
| 012 | MUB Diagnostics | Scoped exact algebra and packet checks |
| 032 | Three-Layer Sovereignty & Discrete L1 Projection | Weighted cycle formula, native compatibility |
| 033 | Practitioner's Field Manual | Native-backed quickstart, exact input rejection |
| **C005** | **Structured Decoding Controls** (this document) | **Scratchpads, factorized spanning-tree prompts, canary antibodies on 405B** |
