# C050: Equational Theorem Proving with Checkable Rewrite Proofs — Empirical Benchmark Report & Space Bunny Alpha Findings

> **Correction notice (2026-09-29).** This note reports an exploratory model run. The run did not follow the challenge protocol SG-CP v1, and its figures should not be cited as a challenge result.
>
> - **Leakage.** Each prompt began with the judge's case ID (for example `c050_m09_poison_fake_note`), and in this series the ID names the expected verdict or construction. The case JSON sent with it carried the same ID. The scores therefore partly measure reading the ID, not solving the case.
> - **Model.** `stealth/space-bunny-alpha` ("Space Bunny") is a free stealth model on OpenRouter as of 2026-09-28. The provider does not disclose its identity, size or training. Results with it are exploratory, fall outside SG-CP v1 section 2, and may not be reproducible after the stealth period. The study of 2026-09-28 found that all 29 retained usage records for this model report zero reasoning tokens, although this note describes it as a reasoning model.
> - **Custody.** Prompts were not stored. Replies were kept only as parsed JSON or as a 200-character excerpt. Provider errors were scored as wrong answers. Each model saw n = 10 hand-picked cases with one reply per case.
> - **Gate label.** `PASS_TO_MASTER` certifies the reference solver against its own checkers. It says nothing about any model.
>
> The runner now sends an opaque per-run token instead of the case ID and never sends answer-bearing fields. It keeps prompts and full replies, records provider errors as `INFRA_ERROR`, and writes each run to a new folder; the second checker was also hardened. No new runs have been made since.

## 1. Challenge & Epistemic Boundary Overview
- **Challenge ID:** `C050`
- **Domain:** `e_formal_math` (Formal Mathematics, Equational Theorem Proving, Term Rewriting Systems)
- **Mathematical Invariant:** Birkhoff equational completeness; formal step-by-step term rewrite replay ($s = u_0 \leftrightarrow u_1 \leftrightarrow \dots \leftrightarrow u_k = t$) verified at exact subterm position paths $p$ with instantiated axiom substitutions $\sigma(l) \leftrightarrow \sigma(r)$, and finite algebraic countermodels ($\mathcal{M} \models E$ and $\mathcal{M} \not\models s = t$ with domain size $D \le 8$).
- **Adversary Reality Gate Status:** `PASS_TO_MASTER` (Commit SHA-256: `1a2f881bb4a1409ff2eeab1ca928eaadc1deb43ab29aafbca39d782066c6cb98`, 64/64 base cases passed, 48/48 hostile mutations defended/killed).

---

## 2. Empirical Benchmark Matrix (10 Diverse Equational Reasoning Cases)

| Model | Architecture / Tier | Pass Rate (Count) | Pass Rate (%) | Total Tokens | Key Strengths / Observed Failure Modes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Space Bunny Alpha** (`stealth/space-bunny-alpha`) | Stealth Frontier Reasoning | **7 / 10** | **70.0%** | 7,198 | Successfully emitted verified rewrite chains on double negation, combinators, associativity shifts, and commutative swaps; discovered valid size-2 countermodels for non-theorems and refuted fake textbook claims; correctly refused malformed syntax. Missed only on 1 transient API error and 2 list-nested table formatting issues. |
| **LLaMA 3.3 70B Instruct** (`meta-llama/llama-3.3-70b-instruct`) | 70B Dense | 4 / 10 | 40.0% | 6,188 | Emitted valid proofs on simple single-step swaps; but failed multi-step proofs by skipping intermediate rewrites (compressing two steps into one without justification) and emitted out-of-range position indices (e.g. index `[1]` on unary terms). |
| **LLaMA 3.1 8B Instruct** (`meta-llama/llama-3.1-8b-instruct`) | 8B Dense | 1 / 10 | 10.0% | 5,761 | Failed 9/10 cases; suffered AST position hallucination, emitted non-integer string types in algebraic operation tables, and erroneously returned `OUT_OF_SCOPE` on completely valid theorems. Passed only on the malformed syntax negative control. |

---

## 3. Detailed Comparative Insights

### A. Space Bunny Alpha's First-Order Term Rewriting Capability
Space Bunny Alpha showed strong mechanical discipline on formal term rewriting:
1. **Accurate Subterm Position Navigation**: Correctly identified root position `[]` and nested argument positions `[0]` and `[0, 0]` when performing subterm replacements.
2. **Valid Substitution Matching**: Formulated substitution mappings $\sigma = \{x \mapsto \dots\}$ that matched subterms without introducing extraneous variables or unground symbols.
3. **Finite Countermodel Synthesis**: In non-theorem cases, Space Bunny Alpha synthesized complete Cayley operation tables of size 2 ($D = \{0, 1\}$) satisfying the algebraic axioms (e.g. left unit $m(e, x) = x$) while witnessing failure of the goal equation under evaluation ($s \neq t$).
4. **Refutation of Adversarial Poisoning**: Successfully withstood the fake textbook bait (`c050_m09`) asserting that idempotency implies commutativity in Robbins algebras; rather than hallucinating a false proof, it generated a valid size-2 non-commutative countermodel ($m(0, 1) \neq m(1, 0)$).

### B. Dense Model Breakdown Modes
- **Skipped-Step Hallucination (70B)**: LLaMA 3.3 70B frequently claimed an equational jump $I(I(c)) \to c$ in a single rewrite step, failing to record the intermediate term $I(c)$. Under strict proof replay, such steps are detected and rejected.
- **Arity & Position Mismatch (70B & 8B)**: Both dense models repeatedly indexed child `1` on unary functions $f(x)$ or $I(x)$, which have only child `0`.
- **Type Coercion Failure (8B)**: LLaMA 3.1 8B failed to output integer arrays, emitting string literals and lists inside table cells, indicating a breakdown in adhering to formal JSON schema specifications under equational constraints.

---

## 4. Formal Claim Hygiene Summary

1. **What it supports:**
   - Supports that frontier reasoning models (such as Space Bunny Alpha) can generate checkable first-order term rewrite chains and construct small finite countermodels that pass formal deterministic checkers (70.0% in this 10-problem sample).
   - Supports that step-by-step rewrite verification and countermodel evaluation provide an effective dual gate that catches skipped steps, false countermodels, and out-of-bounds positions.

2. **What it does not support:**
   - Does not support that LLMs can replace automated equational provers (such as E, Twee, or Waldmeister) on complex multi-step lemmas (>10 steps).
   - Does not support that LLMs can find large countermodels ($D > 8$).
   - Does not support that 8B or 70B dense models can reliably perform formal term rewriting without external proof assistants.

3. **The narrowest defensible claim:**
   - In this 10-case evaluation of first-order equational theorem proving and countermodel construction, Space Bunny Alpha achieved a 70.0% pass rate under exact step-by-step rewrite replay and countermodel verification, outperforming LLaMA 3.3 70B (40.0%) and LLaMA 3.1 8B (10.0%).

4. **The next test needed:**
   - Comprehensive synthesis of Domain E (C041–C050) comparative benchmark tables and integration into the master PR (#210).
