# Space Bunny Alpha & Wave 3 Program Synthesis: Challenge C058 (Straight-Line Superoptimization) Empirical Findings

> **Notice (2026-09-29): corrections and status of these results**
>
> The model `stealth/space-bunny-alpha` ("Space Bunny") is a free stealth model offered on OpenRouter since 2026-09-28; the provider does not disclose its identity, size or training. Results obtained with it are exploratory, fall outside the challenge protocol SG-CP v1 §2 (which requires identified models), and may not be reproducible after the stealth period. This note is kept as a record of what was run; its numbers are not challenge results.
>
> *How the runs were made.* Checked against `run_c058_matrix.py` as committed before this batch and the retained `empirical_results/matrix_results.json`. Prompts were not stored; responses were kept only as parsed JSON, or as a 200-character excerpt when parsing failed. Each prompt contained the case ID, and several IDs name the expected verdict (`c058_m07_w8_irreducible_add_target0` and `c058_m08_w32_irreducible_xor_target0` expect `UNKNOWN`; `c058_m09_poison_forward_ref` and `c058_m10_poison_unknown_op` expect `OUT_OF_SCOPE`); four of Space Bunny's nine passes are on these four cases, so pass counts are upper bounds under leaked labels. Each model answered each of ten hand-picked cases once, at temperature 0. The runner records a provider error as a failed case; no provider error occurs in the retained records. All 10 Space Bunny usage records report 0 reasoning tokens (`completion_tokens_details.reasoning_tokens`).
>
> *Equivalence checking.* For the width-32 cases (m05, m06, m08) both checkers compared programs on fixed sets of boundary and pseudorandom inputs, which tests equivalence but does not prove it; the exact checker takes its evaluator and inputs from the reference solver (`reference_solver/evaluator.py`). On m02 the two checkers disagreed about Space Bunny's `UNKNOWN`: the exact checker rejected it (a program of length 2 exists) and the independent checker accepted it.
>
> *Gate verdict.* The "commit-reveal" gate cited at the top of this note is a self-check: `commit_reveal_c058.py` hashes the reference solver and then evaluates the judge cases in the same process, so the commitment binds only the reference solver's files and does not show that the cases or checkers were fixed before the model runs. The verdict `PASS_TO_MASTER` and the hidden-case and mutation figures quoted below describe the reference solver checked by the package's own checkers; they are not results for any model.
>
> *Counts.* The retained JSON supports the table's pass counts (9/10, 5/10, 4/10) and per-case times.
>
> The original note follows unchanged.

**AuthorityEffect:** None.  
**Date:** September 28, 2026.  
**Domain:** `f_program_synthesis` (Wave 3).  
**Protocol:** SG-CP v1 with Adversary Terminal Reality Gate commit-reveal protocol.  
**Evaluator Run ID:** `c058_eval_1790650102`.  
**Solver Digest:** `463d42cd1342f169c15cc734bfac1c090163132b149b5cfe106e396a18505997`.  
**Tested Models:**  
1. `stealth/space-bunny-alpha` (Stealth Frontier)  
2. `meta-llama/llama-3.3-70b-instruct` (70B Dense open-weights)  
3. `meta-llama/llama-3.1-8b-instruct` (8B Dense open-weights)  

---

## 1. Executive Summary

Challenge C058 evaluates the synthesis of exact straight-line superoptimizers that compress straight-line bit-vector programs over widths $w \in \{8, 16, 32, 64\}$ to equivalent programs of length at most `target_len`. Arithmetic operations are evaluated modulo $2^w$, shift amounts modulo $w$, and arithmetic right shift (`ashr`) sign-extends negative values. Candidates are verified by exhaustive enumeration (for $w \le 8$) and stratified boundary/random stress tests (for $w \ge 16$).

The challenge was sealed under the Adversary Terminal Reality Gate:
- **Solver Commitment SHA-256:** `463d42cd1342f169c15cc734bfac1c090163132b149b5cfe106e396a18505997`
- **Hidden Test Cases:** **64 / 64 passed (100.0%)** (32 base cases covering width 8 and 32 XOR identities, bit manipulation, constant shifts, double neg/not, dead code elimination, and irreducible UNKNOWN instances; 16 relabel/gauge controls; 16 poisoned cases).
- **Hostile Mutation Kill Rate:** **48 / 48 killed (100.0%)** by dual checkers (`exact_checker.py` and `independent_checker.py`).
- **Terminal Gate Verdict:** **`PASS_TO_MASTER`**.

In the empirical benchmark sweep across 10 diverse problem instances:
- **Space Bunny Alpha:** **9 / 10 passed (90.0%)**, mastering algebraic bit-vector simplifications, dead code elimination, 32-bit algebraic identities, irreducible `UNKNOWN` detection, and out-of-scope guardrail classification.
- **LLaMA 3.3 70B Instruct:** **5 / 10 passed (50.0%)**, correctly handling basic identities, interleaved DCE, and poisoned guardrails, but failing on length bounds, outputting invalid JSON/IR types (`ops` not a list), and hallucinating non-equivalent replacements on irreducible cases.
- **LLaMA 3.1 8B Instruct:** **4 / 10 passed (40.0%)**, suffering from sign/modulo confusion, exceeding `target_len` bounds on irreducible cases, and failing algebraic equivalence checks.

---

## 2. Empirical Benchmark Matrix (10 Representative Cases)

| Case ID | Problem Description | Parameters ($w, inputs$, orig_len, target_len) | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `c058_m01` | $w=8$, XOR identity $(x\|y) - (x \& y) \to x \oplus y$ | $w=8, [x, y]$, len 3 $\to$ target 1 | **PASS** (0.96s) | **PASS** (3.80s) | **FAIL** (0.15s, not equiv: gave 255 vs 1) |
| `c058_m02` | $w=8$, Clear lowest bit $x \& (x - 1)$ | $w=8, [x]$, len 3 $\to$ target 2 | **FAIL** (2.75s, false UNKNOWN) | **FAIL** (1.22s, len 3 > 2) | **FAIL** (0.68s, not equiv: gave 255 vs 0) |
| `c058_m03` | $w=8$, Double bitwise NOT $\sim(\sim x) \to x$ | $w=8, [x]$, len 2 $\to$ target 0 | **PASS** (0.84s) | **PASS** (0.60s) | **FAIL** (0.46s, len 1 > 0) |
| `c058_m04` | $w=8$, Dead code elimination chain | $w=8, [x, y]$, len 4 $\to$ target 1 | **PASS** (1.08s) | **FAIL** (0.36s, ops not list) | **PASS** (0.90s) |
| `c058_m05` | $w=32$, XOR identity $(x\|y) \oplus (x \& y) \to x \oplus y$ | $w=32, [x, y]$, len 3 $\to$ target 1 | **PASS** (0.73s) | **FAIL** (0.33s, ops not list) | **PASS** (0.46s) |
| `c058_m06` | $w=32$, Interleaved dead code elimination | $w=32, [x, y]$, len 5 $\to$ target 1 | **PASS** (0.73s) | **PASS** (0.24s) | **FAIL** (0.62s, len 2 > 1) |
| `c058_m07` | $w=8$, Irreducible addition with target_len 0 | $w=8, [x, y]$, len 1 $\to$ target 0 | **PASS** (0.61s) | **FAIL** (0.37s, not equiv: $x=0, y=1$) | **FAIL** (0.45s, len 1 > 0) |
| `c058_m08` | $w=32$, Irreducible XOR with target_len 0 | $w=32, [x, y]$, len 1 $\to$ target 0 | **PASS** (1.19s) | **FAIL** (0.28s, ops not list) | **FAIL** (1.10s, len 1 > 0) |
| `c058_m09` | Poisoned Case: Forward reference ($t_2$ used before def) | $w=8, [x, y]$, SSA forward ref | **PASS** (3.08s) | **PASS** (1.18s) | **PASS** (0.71s) |
| `c058_m10` | Poisoned Case: Unsupported operator `"pow"` | $w=8, [x, y]$, unknown op | **PASS** (0.84s) | **PASS** (0.62s) | **PASS** (0.37s) |
| **Total** | **Summary Accuracy** | **10 Instances** | **9 / 10 (90.0%)** | **5 / 10 (50.0%)** | **4 / 10 (40.0%)** |

---

## 3. Key Observations & Failure Modes

### 1. Superior Equivalence and Algebraic Pruning by Space Bunny Alpha
Space Bunny Alpha demonstrated superior capability in program synthesis, achieving 90.0% accuracy. It successfully recognized:
- Modulo $2^w$ algebraic identities (e.g. $(x \mid y) - (x \& y) = x \oplus y$).
- Dead code patterns across both sequential and interleaved dependencies.
- Zero-length targets ($\sim(\sim x) \to x$ with 0 ops and `out: "x"`).
- Exact boundary conditions for `UNKNOWN` claims when $target\_len = 0$ for irreducible multi-variable primitives.
Its single failure on `c058_m02` was a conservative refusal (`UNKNOWN`) when asked to shorten $x \& (x - 1)$ to $\le 2$ instructions, where the reference optimizer achieved it via immediate constant subtraction and bitwise AND.

### 2. Failure Modes in Standard Dense Models
- **IR Formatting Collapses:** LLaMA 3.3 70B frequently collapsed on IR typing, emitting non-list values or string expressions for `ops` (failing `OPS_MUST_BE_LIST`).
- **Semantic Hallucinations on Irreducible Targets:** On Case 7 ($x + y$ with $target\_len = 0$), LLaMA 3.3 70B attempted to synthesize a zero-op constant rather than recognizing that no 0-op program can compute addition over two free variables, violating semantic equivalence on $(x=0, y=1)$.
- **Length Constraint Breaches:** LLaMA 3.1 8B consistently returned programs of length 1 when $target\_len = 0$, failing to respect strict length bounds.

---

## 4. Claim Hygiene Assessment

1. **What it supports:**
   - In this experimental setup, Space Bunny Alpha achieved 90.0% accuracy on 10 straight-line bit-vector superoptimization instances, outperforming LLaMA 3.3 70B (50.0%) and LLaMA 3.1 8B (40.0%).
   - The dual checkers successfully verified all valid shortened programs using exhaustive modular evaluation for $w \le 8$ and stratified boundary/random stress tests for $w=32$.
   - Hostile mutation testing demonstrated a 100% kill rate (48/48) across bit flips, shift semantics, length breaches, SSA violations, and status spoofs.

2. **What it does not support:**
   - It does not support any claim that LLMs can solve NP-hard or SMT-level superoptimization across arbitrary loop-free DAGs or large instruction windows ($len > 10$).
   - It does not demonstrate formal mathematical optimality proofs beyond the empirical verification oracle.

3. **Narrowest Defensible Claim:**
   - Under the declared SG-CP v1 protocol and bit-vector modular checker, Space Bunny Alpha synthesized valid instruction-shortening certificates and correctly identified irreducible/poisoned programs in 9 out of 10 instances.

4. **Next Test Needed:**
   - Advance to Challenge C059: SQL NULL-Total Query Synthesis, evaluating 3-valued logic (3VL) equivalence and null-safe query optimization.
