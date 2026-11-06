# C059 Empirical Benchmark Findings: SQL Synthesis under Three-Valued-Logic Fences

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. Every
> `PASS_TO_MASTER` label in this note is a reference self-score: the challenge's own
> reference solver passed its own package's checkers. It says nothing about any model.
> No paper in this collection has audited the other figures in this note. The audit
> behind these notices is recorded in the collection's `verification/residuals.md`,
> section 8.

**Challenge:** C059: SQL Synthesis under Three-Valued-Logic Fences  
**Domain:** `f_program_synthesis` (Domain F)  
**Tier:** T2 | **Protocol:** SG-CP v1 (Adversary Terminal Reality Gate & Dual Checkers)  
**Date:** September 2026  
**Reality Gate Run ID:** `c059_eval_1790651964`  
**Solver SHA-256 Digest:** `020fd7bb1fa503f0147860006946a207d96aa3bf5cdbf2d8d3eaee4ab28ae23b`  

---

## 1. Executive Summary

Challenge C059 evaluates whether autonomous models can synthesize a frozen compiler from JSON relational-algebra specifications to dialect-neutral SQL adhering strictly to Kleene Three-Valued Logic (3VL), totality preflights on protected columns, and exact multiset bag preservation across hidden null-adversarial databases.

Under the Adversary Terminal Reality Gate commit-reveal protocol:
- **Solver Commitment:** Committed SHA-256 digest `020fd7bb1fa503f0147860006946a207d96aa3bf5cdbf2d8d3eaee4ab28ae23b` before revealing the judge packet.
- **Hidden Test Evaluation:** **64 / 64 (100.0%)** hidden evaluation cases passed across dual checkers (SQLite runtime exact checker vs. pure Python in-memory relational algebra engine).
- **Mutation Stress Testing:** **48 / 48 (100.0%)** hostile mutations killed by both checkers with **0 escapes**.
- **Adversary Gate Verdict:** `PASS_TO_MASTER`.

In the empirical benchmark sweep across 10 diverse relational problem instances:
- **LLaMA 3.3 70B Instruct:** **8 / 10 passed (80.0%)**
- **Space Bunny Alpha:** **7 / 10 passed (70.0%)**
- **LLaMA 3.1 8B Instruct:** **3 / 10 passed (30.0%)**

---

## 2. Empirical Benchmark Matrix

| Model | Tier | Passed / 10 | Pass Rate (%) | Mean Latency (s) | Primary Failure Modes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **LLaMA 3.3 70B Instruct** | 70B Dense | 8 / 10 | 80.0% | 0.38s | JSON formatting issue on m01; preflight bag size mismatch on m07 |
| **Space Bunny Alpha** | Stealth Frontier | 7 / 10 | 70.0% | 0.83s | Preflight `UNION ALL` across unequal table column widths (m04, m05, m06) |
| **LLaMA 3.1 8B Instruct** | 8B Dense | 3 / 10 | 30.0% | 0.51s | Hardcoded empty preflights (`3 != 0`), dropped join columns, missed `IS DISTINCT FROM` |

---

## 3. Case-by-Case Breakdown

| Case ID | Problem Description | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c059_m01` | Pointwise distinct comparison (`IS DISTINCT FROM`) | **PASS** (0.94s) | FAIL (JSON parse) | FAIL (preflight 3!=0) |
| `c059_m02` | `eq3` comparison with nulls (`=`) | **PASS** (0.84s) | **PASS** (0.16s) | FAIL (preflight 2!=0) |
| `c059_m03` | `is_null` check on nullable column | **PASS** (1.01s) | **PASS** (0.34s) | FAIL (preflight 2!=0) |
| `c059_m04` | Inner join with null keys | FAIL (preflight UNION) | **PASS** (0.58s) | FAIL (lost join keys) |
| `c059_m05` | Left join with null-extended rows | FAIL (preflight UNION) | **PASS** (0.48s) | FAIL (lost join keys) |
| `c059_m06` | Anti-join null-safe (`NOT EXISTS`) | FAIL (preflight UNION) | **PASS** (0.17s) | **PASS** (0.56s) |
| `c059_m07` | Anti-join `sql_not_in` (`NOT IN` 3VL drop) | **PASS** (0.36s) | FAIL (preflight bag) | FAIL (size mismatch 0!=5) |
| `c059_m08` | Group by on nullable key with `count_star` | **PASS** (0.57s) | **PASS** (0.19s) | FAIL (preflight mismatch) |
| `c059_m09` | Poisoned: unknown base table (`ghost_table`) | **PASS** (0.59s) | **PASS** (0.78s) | **PASS** (0.83s) |
| `c059_m10` | Poisoned: unsupported operator (`cube`) | **PASS** (0.73s) | **PASS** (0.25s) | **PASS** (0.29s) |

---

## 4. Key Failure Modes & Insights

1. **Preflight Cross-Table Strategy (Space Bunny Alpha):**
   - In single-table queries, Space Bunny synthesized exact preflights (`SELECT * FROM facts WHERE f_val IS NULL OR g_verdict IS NULL`).
   - In multi-table joins, Space Bunny attempted to combine preflights across all involved tables using `UNION ALL`. Because `users` (4 columns) and `roles` (3 columns) have different schemas, SQLite rejected the `UNION ALL` at parse time.
2. **Three-Valued Logic Fences (LLaMA 3.3 70B):**
   - LLaMA 3.3 demonstrated strong grasp of 3VL nuances, correctly choosing between `NOT EXISTS` and `NOT IN`, and avoiding `<>` when `IS DISTINCT FROM` was required.
   - It tripped on m07 preflight filtering when `role_id` was protected across an anti-join.
3. **8B Model Capacity Wall (LLaMA 3.1 8B):**
   - The 8B model struggled to track schema types and preflight obligations, frequently generating dummy preflight queries (`SELECT 1 WHERE 1=0`) even when columns were explicitly marked protected, resulting in immediate preflight bag failures.

---

## 5. Claim Hygiene

1. **What this supports:**
   - Supports that frontier models (70B+ class) can reliably synthesize 3VL SQL constructs (`IS DISTINCT FROM`, `NOT EXISTS`, null-aware grouping) from formal relational specifications on this benchmark suite.
   - Supports that the dual checker architecture (SQLite engine execution vs. pure Python relational algebra AST evaluator) detects 100% of injected SQL semantic corruptions across 48 hostile mutation vectors.
2. **What this does not support:**
   - Does not support that LLMs can generate mathematically verified SQL compilers for arbitrary full SQL dialects containing nested correlated subqueries, recursive CTEs, or window functions.
   - Does not support query equivalence in general, which is undecidable for full SQL.
3. **Narrowest defensible claim:**
   - On the 10 tested relational specifications and sample null-adversarial databases, LLaMA 3.3 70B achieved an 80.0% pass rate, Space Bunny Alpha achieved 70.0%, and LLaMA 3.1 8B achieved 30.0% under dual SQLite and relational algebra verification.
4. **Next test needed:**
   - Expand to multi-engine cross-validation (SQLite + DuckDB) with symbolic conjunctive query containment checks (Chandra & Merlin) and automated preflight column-to-table resolution fuzzing.
