# Empirical Findings: Challenge C049 (Finite Category Universal Constructions)

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

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_adversary/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. The package is now [`e_formal_math/c049_finite_category_universal_constructions/`](../../../../pfp/tests/demo_004/e_formal_math/c049_finite_category_universal_constructions/). Its `empirical_results/` folder holds two runs that disagree: the three `results_*.json` files match this note (5, 6 and 4 passes; 12,681, 6,022 and 6,144 tokens), while `c049_space_bunny_matrix_report.json` records 9, 6 and 6 passes with 8,721, 8,549 and 6,508 tokens. Which run the note should cite is open. No phase-3 scoring receipt is retained for this challenge, so the `PASS_TO_MASTER (64/64, 48/48)` line is not backed by a file at the pin.

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

Challenge **C049 (`c049_finite_category_universal_constructions`)** evaluates category-theoretic computation, categorical limits and colimits, and functor adjunction verification in small finite categories ($\le 12$ objects, $\le 60$ morphisms):
1. **Limits and Colimits (`LIMIT` / `COLIMIT`)**: Compute products, equalizers, pullbacks, terminal objects, and their duals (coproducts, coequalizers, pushouts, initial objects). Output `EXISTS` with apex and projection/inclusion legs, or certify absence with `DOES_NOT_EXIST`.
2. **Adjunction Certification (`ADJUNCTION`)**: Given functors $F: C \to D$ and $G: D \to C$, certify an adjoint pair ($F \dashv G$) by exhibiting natural unit $\eta: 1_C \Rightarrow GF$ and counit $\varepsilon: FG \Rightarrow 1_D$ satisfying triangle identities, or refute adjunction with `NOT_ADJOINT` and a hom-set cardinality mismatch witness.
3. **Categorical Axiom Refusal (`OUT_OF_SCOPE`)**: Detect and refuse malformed categories that violate category axioms (missing identities, unclosed composition tables, or non-associative triples).

We developed, verified, and sealed the reference solver package under SG-CP v1:
- **Reference Solver:** Pure Python implementation (`category.py`, `limits.py`, `colimits.py`, `solver.py`) using categorical duality ($C^{\mathrm{op}}$) to evaluate limits and colimits via universal arrow factorizations, alongside naturality and triangle identity verification for adjunctions.
- **Judge Packet:** 64 hidden evaluation cases (40 base cases across limits, colimits, and adjunctions; 16 relabel and duality controls; 8 poisoned cases) and 48 hostile mutated certificates.
- **Commit-Reveal Gate:** **`PASS_TO_MASTER` (64/64 cases passed in 0.450s, 48/48 hostile mutations killed (100.0%))** sealed into `_intelligence/_adversary/runs/c049_eval_1790625868` (SHA-256: `88b989fd6c50851e0a9ffa799b9d817594508a8678e47636a146b8d51de78702`).

---

## 2. Theoretical Insights: Categorical Duality & Triangle Invariants

1. **Duality Reduction via $C^{\mathrm{op}}$**:
   Colimits in a finite category $C$ are identical to limits in the opposite category $C^{\mathrm{op}}$ where morphism arrows are reversed ($f^{\mathrm{op}}: Y \to X$ with $f^{\mathrm{op}} \circ g^{\mathrm{op}} = (g \circ f)^{\mathrm{op}}$). Implementing pushouts, coproducts, and initial objects as dual pullbacks, products, and terminal objects eliminates redundant search routines and preserves invariant symmetry.
2. **The Hom-Set Cardinality Filter**:
   For any adjoint pair $F \dashv G$, there is a natural bijection $\mathrm{Hom}_D(Fc, d) \cong \mathrm{Hom}_C(c, Gd)$. Testing $|\mathrm{Hom}_D(Fc, d)| = |\mathrm{Hom}_C(c, Gd)|$ for all pairs $(c, d) \in \mathrm{Ob}(C) \times \mathrm{Ob}(D)$ filters out non-adjoint functor pairs in $O(|C| \cdot |D|)$ time without generating candidate natural transformations.
3. **The Triangle Identity Closure**:
   When cardinalities match, candidate families of unit arrows $\eta_c: c \to G(F(c))$ and counit arrows $\varepsilon_d: F(G(d)) \to d$ must satisfy the triangle identities:
   $$\varepsilon_{Fc} \circ F(\eta_c) = \mathrm{id}_{Fc}, \quad G(\varepsilon_d) \circ \eta_{Gd} = \mathrm{id}_{Gd}$$
   This algebraic constraint rules out false adjunctions even when hom-sets have identical orders.

**Worked check (2026-10-20):** equal hom-set sizes are necessary for an adjunction, not sufficient; only a unit and counit satisfying both triangle identities certify $F \dashv G$. The duality rule is consistent: for $f: X \to Y$ and $g: Y \to Z$, $(g \circ f)^{\mathrm{op}} : Z \to X$ equals $f^{\mathrm{op}} \circ g^{\mathrm{op}}$. The identity functor on a poset is adjoint to itself with identity unit and counit, as in the 70B pass described below.

---

## 3. Empirical Benchmark Matrix: Space Bunny Alpha vs LLaMA 70B vs 8B

We benchmarked **Space Bunny Alpha (`stealth/space-bunny-alpha`)** against **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 calibrated category theory tasks:

| Model ID | Model Name | Parameter Tier | Verified Pass Rate | Cases Passed | Total Tokens | Spend (USD) | Primary Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `meta-llama/llama-3.3-70b-instruct` | LLaMA 3.3 70B Instruct | 70B Dense | **60.0%** | **6/10** | 6,022 | $0.00084 | Falsely claimed `DOES_NOT_EXIST` on poset product, coproduct, and poison bait |
| **`stealth/space-bunny-alpha`** | **Space Bunny Alpha** | **Stealth Frontier** | **50.0%** | **5/10** | 12,681 | **$0.00000** | Over-refusal (`OUT_OF_SCOPE`) on valid categories; reasoning token ceiling on case 8 |
| `meta-llama/llama-3.1-8b-instruct` | LLaMA 3.1 8B Instruct | 8B Dense | **40.0%** | **4/10** | 6,144 | $0.00019 | Hallucinated non-existent apex and leg identifiers; fell for poison bait claim |

### Observations:
- **LLaMA 3.3 70B Lead in Adjunction Verification**: LLaMA 3.3 70B achieved 60.0% (6/10), successfully verifying the identity adjunction $F \dashv F$ on posets and identifying hom-cardinality mismatch witnesses on non-adjoint pairs, but defaulted to claiming `DOES_NOT_EXIST` on multi-object limits.
- **Space Bunny Alpha Over-Refusal Dynamics**: Space Bunny Alpha correctly derived products and coproducts on posets and detected non-associative categories, but exhibited an over-refusal tendency, returning `OUT_OF_SCOPE` on valid categories with non-trivial composition tables. On the complex cardinality case, its chain of thought exceeded 4,000 tokens before emitting the final JSON envelope.
- **Small Model Hallucinations**: LLaMA 3.1 8B hallucinated object identifiers (`apex: "3"` in a 3-object category $\{0, 1, 2\}$) and copied non-morphism tokens into projection legs.

---

## 4. Claim Hygiene Quad

1. **What It Supports:**
   - In this finite category setting ($\le 12$ objects, $\le 60$ morphisms), the reference solver decides limits, colimits, and adjunctions, or certifies their absence, passing 64/64 cases in 0.450s.
   - Dual independent checkers agreed on 100% of cases and detected 48/48 hostile certificate mutations (100.0% kill rate).
   - Demonstrates that hom-set cardinality checks and triangle identities provide computable witnesses for adjunction decisions in finite categories.
2. **What It Does Not Support:**
   - It does not support infinite categories, enriched categories, or higher categories ($\infty, 1$).
   - It does not support unassisted language model generation of large natural transformations without external composition table evaluation.
3. **The Narrowest Defensible Claim:**
   - For finite categories with specified composition tables, open-weight language models reliably distinguish trivial discrete limits and large cardinality mismatches, but require algorithmic table verification to avoid over-refusals and object hallucinations. (2026-10-20: proposed, not supported as written; pass rates of 40% to 60% on ten cases are not "reliable", `stealth/space-bunny-alpha` is not an open-weight model, and the retained run records disagree as stated in the source check above.)
4. **The Next Test Needed:**
   - Implementation and verification of Challenge **C050: Equational Theorem Proving & Substitution Trees (`c050_equational_theorem_proving`)** evaluating first-order equational logic, term rewriting, and substitution tree indexing.
