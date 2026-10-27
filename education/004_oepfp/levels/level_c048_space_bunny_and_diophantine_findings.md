# Empirical Findings: Challenge C048 (Ternary Quadratic Forms: Points & Local Obstructions)

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the notice of 2026-09-28. Every `PASS_TO_MASTER`
> label in this note is a reference self-score: the challenge's own reference solver
> passed its own package's checkers. It says nothing about any model. Paper 010,
> version 2.0.1, adds an erratum for the C045 to C050 runs: each prompt began with
> `Case ID: <id>`, and many identifiers name the expected verdict or answer (for
> example `c045_m02_trefoil_identify`, `c046_m05_check_non_confluent_group`,
> `c048_m01_solv_11_m2`), so the counts are not measures of unaided performance. The
> audit behind these notices is recorded in the collection's
> `verification/residuals.md`, section 8.

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_adversary/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. The package is now [`e_formal_math/c048_ternary_quadratic_forms/`](../../../../demos/certified_challenges/c048_ternary_quadratic_forms/). The retained `empirical_results/c048_space_bunny_matrix_report.json` matches the pass counts 10, 8 and 5 and the token totals 7,342, 3,763 and 3,764. The folder's `empirical_results/NOTICE_2026-09-29.md` records that each prompt began with an answer-bearing case ID, that prompts were not stored, and that the 29 retained usage records for `stealth/space-bunny-alpha` report zero reasoning tokens; statements below about this model's reasoning tokens are therefore unsupported. No phase-3 scoring receipt is retained for this challenge, so the `PASS_TO_MASTER (64/64, 48/48)` line is not backed by a file at the pin.

> **Correction notice (2026-09-28).** Paper 010 (version 2.0.0) re-derived the model
> counts for C017 and C045 to C050 from the retained run records; where they differ
> from this note, Paper 010 and its change log are authoritative. The C043 and C044 run
> reports were not retained, so Paper 010 reports no counts for them.
> `stealth/space-bunny-alpha` is an unidentified model offered anonymously on
> OpenRouter; its results cannot be reproduced. The text below is kept unchanged as a
> working record.

**Date:** 2026-09-28  
**Protocol:** SG-CP v1 (Symbol Game Challenge Protocol)  
**Evaluator Seam:** Dual Exact + Independent Checkers with Cryptographic Commit-Reveal  
**AuthorityEffect:** None  

---

## 1. Executive Summary

Challenge **C048 (`c048_ternary_quadratic_forms`)** tests arithmetic geometry, Diophantine equation solving, and local-global obstruction certification. Given integers $a, b, c$ ($|a|, |b|, |c| \le 10^{18}$):
1. **Rational Point Discovery (`RATIONAL_POINT`)**: Find a non-trivial integer point $(x, y, z) \ne (0, 0, 0)$ such that $a x^2 + b y^2 + c z^2 = 0$.
2. **Local Hilbert Obstruction (`LOCAL_OBSTRUCTION`)**: When no rational point exists by the Hasse-Minkowski theorem, exhibit a place $v \in \{\infty, 2, \text{odd primes } p\}$ where the Hilbert symbol $(-ac, -bc)_v = -1$, certifying that the form has no $p$-adic or real solutions.
3. **Out-of-Scope Witnessing (`OUT_OF_SCOPE`)**: Formally refuse malformed inputs with typed witness receipts.

We developed, verified, and sealed the reference solver package under SG-CP v1:
- **Reference Solver:** Pure Python standard library implementation (`math`, Pollard's rho, Miller-Rabin primality, Holzer bound search, and Serre Hilbert symbol formulas over $\mathbb{Q}_v$).
- **Judge Packet:** 64 hidden cases (20 solvable, 20 obstructed across $\infty, 2, p$; 16 relabel and gauge controls; 8 poisoned cases) and 48 hostile mutations.
- **Commit-Reveal Gate:** **`PASS_TO_MASTER` (64/64 cases passed in 0.066s, 48/48 hostile mutations killed (100.0%))** sealed into `_intelligence/_adversary/runs/c048_eval_1790625286`.

---

## 2. Theoretical Insights: Local-Global Duality & Hilbert Verification

1. **Exact Local-Global Duality**:
   By the Hasse-Minkowski theorem, a ternary quadratic form $a x^2 + b y^2 + c z^2 = 0$ over $\mathbb{Q}$ has non-trivial solutions globally if and only if it has solutions locally at all places $v$. An obstruction is certified by a single place $v$ where $(-ac, -bc)_v = -1$.
2. **Serre Hilbert Symbol Valuation Order**:
   - At $\infty$: $(-ac, -bc)_\infty = -1 \iff a, b, c$ all have the same sign (definite form).
   - At $p = 2$: the $(\varepsilon, \omega)$ parity formula resolves obstruction in $\mathbb{Z}_2$ without square roots.
   - At odd primes $p \mid abc$ (the 2026-10-20 correction of "$p \mid 2abc$", which would include $p = 2$): Legendre symbols via Jacobi reciprocity determine local solvability in $O(\log p)$ steps.
3. **Asymmetry in Certification Cost**:
   Verifying a rational point requires only 1 substitution evaluation ($a x^2 + b y^2 + c z^2 == 0$). Verifying a local obstruction requires only 1 Hilbert symbol calculation at the declared place. Producing the witness requires search/descent or prime factorization.

**Worked check (2026-10-20):** dividing $a x^2 + b y^2 + c z^2 = 0$ by $-c$ gives $(-a/c)x^2 + (-b/c)y^2 = z^2$, and multiplying both symbol entries by the square $c^2$ gives the test $(-ac,-bc)_v = 1$ for local solvability, as used above. At $v=\infty$, $(u,w)_\infty=-1$ exactly when $u<0$ and $w<0$, that is $ac>0$ and $bc>0$, so $a,b,c$ share one sign. By Hilbert reciprocity $\prod_v (u,w)_v = 1$, the number of places with symbol $-1$ is even, so an obstructed form always has at least two obstructed places and a one-place certificate names one of them. The poison-bait form $x^2+y^2-z^2=0$ is solvable: $(3,4,5)$ gives $9+16-25=0$.

---

## 3. Empirical Benchmark Matrix: Space Bunny Alpha vs LLaMA 70B vs 8B

We benchmarked the frontier reasoning model **Space Bunny Alpha (`stealth/space-bunny-alpha`)** against **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 Diophantine tasks (4 rational point discovery, 4 local Hilbert obstructions, 1 out-of-scope malformed coefficient, and 1 poisoned bait):

| Model | Architecture | Pass Rate | Cases Passed | Total Tokens | Spend (USD) | Failure Mode / Characteristics |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Space Bunny Alpha** | Stealth Frontier | **100.0%** | **10/10** | 7,342 | ~$0.0000 | **100% convergence (10/10)**. Correctly recovered points $(1, 1, 1)$ and $(1, 0, 1)$, verified local obstructions at $\infty$ and odd primes/2, certified malformed input, and resisted poison bait. |
| **LLaMA 3.3 70B Instruct** | 70B Dense | **80.0%** | **8/10** | 3,763 | ~$0.0009 | Passed all local obstructions and refusals; hallucinated integer coordinates that violated equations ($a x^2 + b y^2 + c z^2 \ne 0$) on 2 solvable forms. |
| **LLaMA 3.1 8B Instruct** | 8B Dense | **50.0%** | **5/10** | 3,764 | ~$0.0002 | Emitted non-integer `'sqrt(2)'` coordinate strings, failed on rational point equation checks, copied literal `'p'` from system prompt, and fell for poisoned bait claim. |

### Observations:
- **Full Accuracy on Arithmetic Geometry by Space Bunny Alpha**: On Challenge C048, Space Bunny Alpha achieved the highest pass rate in the entire Domain E benchmark suite to date (100.0%, 10/10). Its chain-of-thought correctly evaluated Legendre symbols and avoided algebraic hallucinations.
- **Asymmetric Fallibility**: Dense models easily identified sign obstructions at $\infty$ and small prime obstructions, but frequently hallucinated incorrect integer coordinates on solvable quadratic forms (e.g. producing coordinates where the quadratic evaluated to 2, 9, or 48 instead of 0).
- **Poison Bait Resistance**: Space Bunny Alpha and LLaMA 3.3 70B correctly rejected the deceptive claim that $x^2 + y^2 - z^2 = 0$ was unsolvable, showing resistance to this one adversarial context note.

---

## 4. Claim Hygiene Quad

1. **What It Supports:**
   - In this diagonal ternary quadratic setting, the solver decides global solvability and outputs certified points or local Hilbert obstructions for 64/64 cases in 0.066s in pure Python.
   - Dual independent checkers agreed on 100% of cases and detected 48/48 hostile certificate mutations (100.0% kill rate).
   - Demonstrates that local Hilbert obstructions provide exact polynomial-time verifiable refutations of Diophantine solvability.
2. **What It Does Not Support:**
   - It does not support general non-diagonal or higher-degree Diophantine equations where the Hasse principle fails (e.g. Selmer curves $3x^3 + 4y^3 + 5z^3 = 0$).
   - It does not claim asymptotic superiority over PARI/GP for factoring $10^{30}$ semiprimes.
3. **The Narrowest Defensible Claim:**
   - For diagonal ternary quadratic forms $a x^2 + b y^2 + c z^2 = 0$ with $|a|, |b|, |c| \le 10^{18}$, the system deterministically finds an integer solution or certifies a local obstruction in $< 0.1$s.
4. **The Next Test Needed:**
   - Challenge **C049: Finite Category Universal Constructions (`c049_finite_category_universal_constructions`)** testing limits, colimits, adjunctions, and Kan extensions.
