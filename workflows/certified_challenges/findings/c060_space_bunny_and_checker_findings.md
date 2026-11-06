# C060 Empirical Benchmark Findings: Checker Synthesis Scored by Mutation Kill Rate

**Challenge:** C060: Checker Synthesis Scored by Mutation Kill Rate  
**Domain:** `f_program_synthesis` (Domain F — Final Challenge)  
**Tier:** T2 | **Protocol:** SG-CP v1 (Adversary Terminal Reality Gate & Dual Checkers)  
**Date:** September 2026  
**Reality Gate Run ID:** `c060_eval_1790653492`  
**Solver SHA-256 Digest:** `a0a0daf0c0391ae9bd5d892412809b57ff1cbbe12ac21706c27b1f156a7a1095`  

---

## 1. Executive Summary

Challenge C060 evaluates whether autonomous models can synthesize a total, crash-proof mathematical certificate checker exposing `def check(case: Any, cert: Any) -> Dict[str, Any]` that verifies weighted-$\ell^1$ ($\Phi_1$) cochain repair self-certificates under exact rational arithmetic.

The verification harness enforces a dual scoring metric:
1. **Zero Autoimmunity:** Emits `ACCEPT` on all mathematically valid primal-dual certificates without false rejections.
2. **100% Mutation Kill Rate:** Detects and rejects all hostile certificate and schema mutations, emitting canonical typed rejection codes without crashing, raising unhandled exceptions, or drifting into floating-point imprecision.

Under the Adversary Terminal Reality Gate commit-reveal protocol:
- **Solver Commitment:** Committed SHA-256 digest `a0a0daf0c0391ae9bd5d892412809b57ff1cbbe12ac21706c27b1f156a7a1095` before revealing the judge packet.
- **Hidden Test Evaluation:** **64 / 64 (100.0%)** hidden evaluation cases passed across dual checkers (Exact Checker vs. Clean-Room Independent Mathematical Evaluator).
- **Mutation Stress Testing:** **48 / 48 (100.0%)** hostile checker mutants killed by the test suite with **0 escapes**.
- **Adversary Gate Verdict:** `PASS_TO_MASTER`.

In the empirical benchmark sweep across 10 diverse certificate verification problem instances:
- **Space Bunny Alpha:** **10 / 10 passed (100.0%)**
- **LLaMA 3.3 70B Instruct:** **5 / 10 passed (50.0%)**
- **LLaMA 3.1 8B Instruct:** **0 / 10 passed (0.0%)**

---

## 2. Empirical Benchmark Matrix

| Model | Tier | Passed / 10 | Pass Rate (%) | Mean Latency (s) | Primary Failure Modes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Space Bunny Alpha** | Stealth Frontier | **10 / 10** | **100.0%** | 0.83s | Flawless classification across all 5 valid and 5 invalid cases with exact typed rejection codes |
| **LLaMA 3.3 70B Instruct** | 70B Dense | 5 / 10 | 50.0% | 0.35s | Autoimmune false rejections on negative cochain & big integers; false acceptance of residual corruption; wrong rejection codes |
| **LLaMA 3.1 8B Instruct** | 8B Dense | 0 / 10 | 0.0% | 0.54s | 100% failure rate; severe autoimmunity (rejecting all 5 valid cases) and emitting wrong rejection codes on all 5 invalid cases |

---

## 3. Case-by-Case Breakdown

| Case ID | Problem Description | Ground Truth | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `c060_m01` | Valid single-edge tree exact repair | ACCEPT | **PASS** (0.77s) | **PASS** (0.30s) | FAIL (`SCHEMA`) |
| `c060_m02` | Valid triangle with frustrated obstruction | ACCEPT | **PASS** (0.91s) | **PASS** (0.23s) | FAIL (`DUAL_VALUE_MISMATCH`) |
| `c060_m03` | Valid 4-cycle obstruction ($d_0^T y = 0$) | ACCEPT | **PASS** (0.86s) | **PASS** (0.31s) | FAIL (`PRIMAL_VALUE_MISMATCH`) |
| `c060_m04` | Valid negative cochain with signed dual | ACCEPT | **PASS** (0.75s) | FAIL (`DUAL_VALUE_MISMATCH`) | FAIL (`NONCANONICAL_RATIONAL`) |
| `c060_m05` | Valid big integers beyond $2^{64}$ | ACCEPT | **PASS** (0.67s) | FAIL (`RESIDUAL_MISMATCH`) | FAIL (`NONCANONICAL_RATIONAL`) |
| `c060_m06` | Corrupted residual vector | REJECT (`RESIDUAL_MISMATCH`) | **PASS** (1.06s) | FAIL (Accepted corrupted) | FAIL (`PRIMAL_VALUE_MISMATCH`) |
| `c060_m07` | Primal value mismatch ($9 \neq 10$) | REJECT (`PRIMAL_VALUE_MISMATCH`) | **PASS** (0.98s) | **PASS** (0.46s) | FAIL (`DUAL_VALUE_MISMATCH`) |
| `c060_m08` | Dual witness not in cokernel | REJECT (`DUAL_NOT_IN_COKERNEL`) | **PASS** (0.71s) | FAIL (Wrong code: `RESIDUAL_MISMATCH`) | FAIL (Wrong code: `SCHEMA`) |
| `c060_m09` | Dual bound violated ($\|y_e\| > w_e$) | REJECT (`DUAL_BOUND_VIOLATED`) | **PASS** (0.69s) | FAIL (Wrong code: `NONCANONICAL_RATIONAL`) | FAIL (Wrong code: `DUAL_NOT_IN_COKERNEL`) |
| `c060_m10` | Noncanonical slashed integer (`"1/1"`) | REJECT (`NONCANONICAL_RATIONAL`) | **PASS** (0.96s) | **PASS** (0.33s) | FAIL (Wrong code: `SCHEMA`) |

---

## 4. Key Failure Modes & Insights

1. **Space Bunny Alpha's Exact Rational Algebra:**
   - Space Bunny Alpha achieved a perfect 10/10 score, correctly distinguishing valid self-certificates (including large integers $> 2^{64}$ and negative cochains) from subtle algebraic corruptions.
   - For every corrupted case, it emitted the exact typed code in strict accordance with the prioritized rejection hierarchy.
2. **LLaMA 3.3 70B's Precision & Code Aliasing Pitfalls:**
   - On `c060_m04` (negative cochain), LLaMA 3.3 falsely claimed a dual value mismatch, failing to properly compute $(-3) \times (-7) = 21$.
   - On `c060_m05` (big integer $2^{64}+1$), LLaMA 3.3 converted strings to floating-point or fixed precision, causing low-bit truncation and an autoimmune false rejection (`RESIDUAL_MISMATCH`).
   - On `c060_m06`, LLaMA 3.3 falsely accepted a corrupted residual, demonstrating vulnerability to subtle numerical falsifications.
   - On `c060_m08` and `c060_m09`, LLaMA 3.3 recognized the inputs were invalid but misclassified the root cause into earlier priority buckets.
3. **LLaMA 3.1 8B Collapse (0% Pass Rate):**
   - The 8B model exhibited catastrophic collapse: it rejected all 5 valid certificates (severe autoimmunity) and assigned incorrect rejection codes to all 5 invalid certificates.
   - It treated negative strings (`"-7"`) and 20-digit integer strings as invalid rational syntax (`NONCANONICAL_RATIONAL`), demonstrating an inability to parse canonical grammar without drifting into regex heuristics.

---

## 5. Claim Hygiene

1. **What this supports:**
   - Supports that frontier models can synthesize exact mathematical certificate verification logic for weighted-$\ell^1$ coboundary repair under total rational arithmetic.
   - Supports that mutation stress-testing with 48 distinct corrupted checkers reliably falsifies inadequate checkers (including float precision drift, signed bound relaxation, and unreduced fractions).
2. **What this does not support:**
   - Does not support that LLMs can synthesize formal verified proof checkers for arbitrary higher cohomology or non-abelian complexes without an exact algorithmic oracle.
   - Does not support that 8B models can handle exact integer arithmetic beyond 64-bit boundaries without external tool use.
3. **Narrowest defensible claim:**
   - On the 10 benchmark instances evaluated, Space Bunny Alpha achieved 10/10 (100.0%), LLaMA 3.3 70B achieved 5/10 (50.0%), and LLaMA 3.1 8B achieved 0/10 (0.0%) under dual exact and independent clean-room verification.
4. **Next test needed:**
   - Expand checker synthesis to degree-2 2-cochain repair (2-simplices with face coboundaries) and non-Archimedean $p$-adic valuations under randomized fuzz testing.
